#!/usr/bin/env python3
"""
Fix tables with "See PDF" placeholder by extracting actual content from PDF.
Improved version that searches within correct chapter context.
"""

import os
import re
import fitz  # PyMuPDF
from pathlib import Path
import xml.etree.ElementTree as ET
from copy import deepcopy
import shutil

PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_FIXED_CONTENT')

ET.register_namespace('', '')

def get_element_text(elem):
    """Get all text from element."""
    text = elem.text or ''
    for child in elem:
        text += get_element_text(child)
        text += child.tail or ''
    return text

def find_chapter_pages(doc, chapter_num):
    """Find the page range for a specific chapter in the PDF."""
    start_page = None
    end_page = None
    
    chapter_pattern = rf'Chapter\s+{chapter_num}\b'
    next_chapter_pattern = rf'Chapter\s+{chapter_num + 1}\b'
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()[:500]  # Check first part of page
        
        if start_page is None and re.search(chapter_pattern, text):
            start_page = page_num
        elif start_page is not None and re.search(next_chapter_pattern, text):
            end_page = page_num
            break
    
    if start_page is not None and end_page is None:
        end_page = len(doc)  # Last chapter
    
    return start_page, end_page

def find_table_in_chapter(doc, start_page, end_page, table_title, table_num):
    """Find a table within a chapter's page range."""
    if start_page is None:
        start_page = 0
    if end_page is None:
        end_page = len(doc)
    
    # Clean up title for searching
    search_title = table_title.replace('-\n', '').replace('\n', ' ').strip()
    search_title_words = search_title.split()[:5]  # First 5 words
    
    for page_num in range(start_page, min(end_page, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        
        # Check if this page has the table
        title_found = all(word.lower() in text.lower() for word in search_title_words if len(word) > 3)
        table_ref = f"Table {table_num}." in text or f"Table {table_num} " in text
        
        if title_found or table_ref:
            # Try to extract numbered list (for tables like the claustrophobia one)
            content = extract_numbered_list_from_page(text, table_num, search_title)
            if content:
                return content, page_num + 1
            
            # Try structured table extraction
            tables = page.find_tables()
            for t in tables:
                try:
                    data = t.extract()
                    if data and len(data) > 1:
                        first_cell = str(data[0][0]) if data[0] else ""
                        # Skip metadata tables
                        if 'BioRef' in first_cell or 'Layout' in first_cell:
                            continue
                        # Skip placeholder tables
                        if 'Content' in first_cell and 'Details' in str(data[0]):
                            continue
                        # Skip wrong tables
                        if 'Radiation' in first_cell and 'claustrophobia' in search_title.lower():
                            continue
                        return data, page_num + 1
                except:
                    continue
    
    return None, None

def extract_numbered_list_from_page(text, table_num, title_hint):
    """Extract numbered list from page text."""
    # Look for numbered items (1), (2), etc.
    items = []
    
    # Find items pattern
    pattern = r'\((\d+)\)\s+([^(]+?)(?=\s*\(\d+\)|$)'
    
    for match in re.finditer(pattern, text, re.DOTALL):
        num = match.group(1)
        content = match.group(2).strip()
        content = re.sub(r'\s+', ' ', content)
        content = content.replace('- ', '')
        
        # Skip if too short or looks like page number
        if len(content) > 20 and not content.startswith('BioRef'):
            items.append([f"({num})", content[:500]])
    
    if len(items) >= 5:  # Good list found
        return [["Item", "Recommendation"]] + items
    
    return None

def is_placeholder_table(table_elem):
    """Check if table has placeholder content."""
    table_text = ET.tostring(table_elem, encoding='unicode', method='text')
    return 'See PDF' in table_text

def get_chapter_num_from_file(filename):
    """Extract chapter number from filename."""
    match = re.search(r'ch(\d+)', filename)
    return int(match.group(1)) if match else None

def process_file(xml_file, doc, chapter_pages_cache, output_file):
    """Process an XML file and fix placeholder tables."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0
    
    # Get chapter number
    chapter_num = get_chapter_num_from_file(xml_file.name)
    
    # Get chapter page range
    if chapter_num and chapter_num not in chapter_pages_cache:
        start_page, end_page = find_chapter_pages(doc, chapter_num)
        chapter_pages_cache[chapter_num] = (start_page, end_page)
        if start_page:
            print(f"  Chapter {chapter_num}: pages {start_page+1}-{end_page if end_page else 'end'}")
    
    start_page, end_page = chapter_pages_cache.get(chapter_num, (None, None))
    
    fixed_count = 0
    
    for table in root.iter('table'):
        if is_placeholder_table(table):
            # Get table title
            title_elem = table.find('title')
            title = title_elem.text if title_elem is not None and title_elem.text else ''
            
            # Get table number from content
            table_text = ET.tostring(table, encoding='unicode', method='text')
            match = re.search(r'Table\s+(\d+)', table_text)
            table_num = int(match.group(1)) if match else None
            
            if table_num:
                # Try to extract content from PDF within chapter
                content, page = find_table_in_chapter(doc, start_page, end_page, title, table_num)
                
                if content:
                    print(f"    Fixed Table {table_num} (page {page})")
                    
                    # Clear existing content
                    for child in list(table):
                        table.remove(child)
                    
                    # Add new title
                    new_title = ET.SubElement(table, 'title')
                    new_title.text = title
                    
                    # Add new content
                    num_cols = max(len(row) for row in content)
                    tgroup = ET.SubElement(table, 'tgroup', {'cols': str(num_cols)})
                    
                    for i in range(num_cols):
                        ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
                    
                    # First row as header
                    thead = ET.SubElement(tgroup, 'thead')
                    head_row = ET.SubElement(thead, 'row')
                    for cell in content[0]:
                        entry = ET.SubElement(head_row, 'entry')
                        entry.text = str(cell)[:500] if cell else ''
                    
                    # Remaining rows as body
                    tbody = ET.SubElement(tgroup, 'tbody')
                    for row in content[1:]:
                        tr = ET.SubElement(tbody, 'row')
                        for cell in row:
                            entry = ET.SubElement(tr, 'entry')
                            cell_text = str(cell) if cell else ''
                            cell_text = re.sub(r'\s+', ' ', cell_text).strip()
                            entry.text = cell_text[:500]
                    
                    fixed_count += 1
                else:
                    print(f"    Could not find content for Table {table_num}")
    
    # Write output
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return fixed_count

def main():
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(PDF_FILE)
    print(f"PDF has {len(doc)} pages")
    
    chapter_pages_cache = {}
    total_fixed = 0
    
    for xml_file in sorted(SOURCE_DIR.glob('*.xml')):
        if xml_file.name == 'Book.XML':
            shutil.copy(xml_file, OUTPUT_DIR / xml_file.name)
            continue
        
        print(f"\nProcessing {xml_file.name}...")
        output_file = OUTPUT_DIR / xml_file.name
        
        fixed = process_file(xml_file, doc, chapter_pages_cache, output_file)
        total_fixed += fixed
    
    doc.close()
    
    # Copy multimedia
    multimedia_src = SOURCE_DIR / 'multimedia'
    if multimedia_src.exists():
        multimedia_dst = OUTPUT_DIR / 'multimedia'
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
    
    print(f"\n=== Summary ===")
    print(f"Total tables fixed: {total_fixed}")

if __name__ == '__main__':
    main()
