#!/usr/bin/env python3
"""
Fix tables with "See PDF" placeholder by extracting actual content from PDF.
Searches for table content using the title and extracts structured data.
"""

import os
import re
import fitz  # PyMuPDF
from pathlib import Path
import xml.etree.ElementTree as ET
import shutil

PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_FIXED_CONTENT')

ET.register_namespace('', '')

def clean_text(text):
    """Clean up extracted text."""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('- ', '')  # Remove hyphenation
    return text.strip()

def find_table_content_in_pdf(doc, title_words, table_num):
    """Search PDF for table content using title keywords."""
    
    # Search for pages containing the title
    title_search = ' '.join(title_words[:4]).lower()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        text_lower = text.lower()
        
        # Check if page contains the table title
        if title_search not in text_lower:
            continue
        
        # Found a matching page - try to extract content
        
        # Try numbered list extraction (1), (2), etc.
        numbered_content = extract_numbered_list(text)
        if numbered_content and len(numbered_content) > 3:
            return numbered_content, page_num + 1
        
        # Try bullet point extraction
        bullet_content = extract_bullet_list(text)
        if bullet_content and len(bullet_content) > 3:
            return bullet_content, page_num + 1
        
        # Try PyMuPDF table extraction
        tables = page.find_tables()
        for t in tables:
            try:
                data = t.extract()
                if data and len(data) > 1:
                    # Skip metadata tables
                    first_cell = str(data[0][0] if data[0] else '')
                    if 'BioRef' in first_cell or 'Layout' in first_cell:
                        continue
                    if first_cell == 'Content' and len(data) < 3:
                        continue
                    
                    # Clean and return
                    cleaned_data = []
                    for row in data:
                        cleaned_row = [clean_text(str(cell) if cell else '') for cell in row]
                        if any(cleaned_row):  # Skip empty rows
                            cleaned_data.append(cleaned_row)
                    
                    if len(cleaned_data) > 1:
                        return cleaned_data, page_num + 1
            except:
                continue
        
        # Try dash-separated list extraction
        dash_content = extract_dash_list(text)
        if dash_content and len(dash_content) > 3:
            return dash_content, page_num + 1
    
    return None, None

def extract_numbered_list(text):
    """Extract numbered list items like (1), (2), etc."""
    items = []
    pattern = r'\((\d+)\)\s+([^(]+?)(?=\s*\(\d+\)|BioRef|$)'
    
    for match in re.finditer(pattern, text, re.DOTALL):
        num = match.group(1)
        content = clean_text(match.group(2))
        if len(content) > 15 and not content.startswith('BioRef'):
            items.append([f"({num})", content[:600]])
    
    if len(items) >= 3:
        return [["No.", "Description"]] + items
    return None

def extract_bullet_list(text):
    """Extract bullet point items."""
    items = []
    # Look for various bullet patterns
    pattern = r'[•·∙]\s*([^•·∙\n]+)'
    
    for match in re.finditer(pattern, text):
        content = clean_text(match.group(1))
        if len(content) > 10:
            items.append(["•", content[:600]])
    
    if len(items) >= 3:
        return [["", "Item"]] + items
    return None

def extract_dash_list(text):
    """Extract dash-separated items."""
    items = []
    # Look for items starting with dash
    pattern = r'[-–—]\s+([^-–—\n]{20,}?)(?=[-–—]|\n\n|$)'
    
    for match in re.finditer(pattern, text, re.DOTALL):
        content = clean_text(match.group(1))
        if len(content) > 15:
            items.append(["—", content[:600]])
    
    if len(items) >= 3:
        return [["", "Item"]] + items
    return None

def is_placeholder_table(table_elem):
    """Check if table has placeholder content."""
    table_text = ET.tostring(table_elem, encoding='unicode', method='text')
    return 'See PDF' in table_text

def get_title_words(title):
    """Get significant words from title for searching."""
    # Remove common words and get significant terms
    title = title.replace('-', ' ').replace('\n', ' ')
    words = title.split()
    # Filter out short words and common terms
    significant = [w for w in words if len(w) > 4 and w.lower() not in 
                   ['table', 'figure', 'that', 'which', 'this', 'with', 'from', 'have', 'been', 'when']]
    return significant[:5]

def update_table_content(table, content):
    """Replace table content with new data."""
    # Get existing title
    title_elem = table.find('title')
    title = title_elem.text if title_elem is not None and title_elem.text else ''
    
    # Clear existing content
    for child in list(table):
        table.remove(child)
    
    # Add title
    new_title = ET.SubElement(table, 'title')
    new_title.text = title
    
    # Determine columns
    num_cols = max(len(row) for row in content)
    
    tgroup = ET.SubElement(table, 'tgroup', {'cols': str(num_cols)})
    
    for i in range(num_cols):
        ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
    
    # Header row
    thead = ET.SubElement(tgroup, 'thead')
    head_row = ET.SubElement(thead, 'row')
    for cell in content[0]:
        entry = ET.SubElement(head_row, 'entry')
        entry.text = str(cell)[:500] if cell else ''
    
    # Body rows
    tbody = ET.SubElement(tgroup, 'tbody')
    for row in content[1:]:
        tr = ET.SubElement(tbody, 'row')
        for cell in row:
            entry = ET.SubElement(tr, 'entry')
            entry.text = str(cell)[:500] if cell else ''

def process_file(xml_file, doc, output_file):
    """Process an XML file and fix placeholder tables."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0, 0
    
    fixed_count = 0
    failed_count = 0
    
    for table in root.iter('table'):
        if not is_placeholder_table(table):
            continue
        
        # Get table title
        title_elem = table.find('title')
        title = title_elem.text if title_elem is not None and title_elem.text else ''
        
        # Get table number
        table_text = ET.tostring(table, encoding='unicode', method='text')
        match = re.search(r'Table\s+(\d+)', table_text)
        table_num = int(match.group(1)) if match else None
        
        if not table_num:
            print(f"    No table number found for: {title[:50]}")
            failed_count += 1
            continue
        
        # Get title words for searching
        title_words = get_title_words(title)
        
        if not title_words:
            print(f"    No searchable words in title: {title[:50]}")
            failed_count += 1
            continue
        
        # Search for content
        content, page = find_table_content_in_pdf(doc, title_words, table_num)
        
        if content:
            update_table_content(table, content)
            print(f"    Fixed Table {table_num} (page {page}, {len(content)-1} rows)")
            fixed_count += 1
        else:
            print(f"    Could not find: Table {table_num} - {title[:40]}")
            failed_count += 1
    
    # Write output
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return fixed_count, failed_count

def main():
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(PDF_FILE)
    print(f"PDF has {len(doc)} pages\n")
    
    total_fixed = 0
    total_failed = 0
    
    for xml_file in sorted(SOURCE_DIR.glob('*.xml')):
        if xml_file.name == 'Book.XML':
            shutil.copy(xml_file, OUTPUT_DIR / xml_file.name)
            continue
        
        output_file = OUTPUT_DIR / xml_file.name
        
        # Check if this file has placeholder tables
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'See PDF' not in content:
                shutil.copy(xml_file, output_file)
                continue
        
        print(f"Processing {xml_file.name}...")
        fixed, failed = process_file(xml_file, doc, output_file)
        total_fixed += fixed
        total_failed += failed
    
    doc.close()
    
    # Copy multimedia
    multimedia_src = SOURCE_DIR / 'multimedia'
    if multimedia_src.exists():
        multimedia_dst = OUTPUT_DIR / 'multimedia'
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
    
    print(f"\n=== Summary ===")
    print(f"Fixed: {total_fixed}")
    print(f"Failed: {total_failed}")

if __name__ == '__main__':
    main()
