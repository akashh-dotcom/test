#!/usr/bin/env python3
"""
Place tables at their correct positions in the XML where they are referenced.
Tables should appear right after the paragraph that references them.
"""

import fitz
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import shutil
import copy

PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_POSITIONED')


def extract_pdf_tables():
    """Extract tables from PDF with content"""
    print("Extracting tables from PDF...")
    doc = fitz.open(PDF_FILE)
    
    # Map pages to chapters
    chapter_pages = {}
    current_ch = 0
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        m = re.search(r'(?:^|\n)\s*Chapter\s+(\d+)\s*\n', text, re.I)
        if m:
            current_ch = int(m.group(1))
        chapter_pages[page_num] = current_ch
    
    # Extract tables with content
    tables_by_chapter = defaultdict(dict)
    
    for page_num in range(len(doc)):
        chapter = chapter_pages.get(page_num, 0)
        if chapter == 0:
            continue
        
        page = doc[page_num]
        text = page.get_text()
        
        # Find table definitions
        for m in re.finditer(r'Table\s+(\d+)[\.\:]\s*([^\n]+)', text):
            table_num = int(m.group(1))
            title = m.group(2).strip()
            title = re.sub(r'\s+', ' ', title)
            title = re.sub(r'BioRef.*$', '', title).strip()
            
            if not title or len(title) < 3:
                continue
            
            # Skip if we already have this table
            if table_num in tables_by_chapter[chapter]:
                continue
            
            # Try to get content
            content = None
            try:
                page_tables = page.find_tables()
                for pt in page_tables.tables:
                    data = pt.extract()
                    if data and len(data) >= 2:
                        first = " ".join(str(c) for c in data[0] if c)
                        if 'BioRef' not in first and 'Layout' not in first:
                            content = data
                            break
            except:
                pass
            
            tables_by_chapter[chapter][table_num] = {
                'number': table_num,
                'title': title[:150],
                'content': content
            }
    
    doc.close()
    
    total = sum(len(t) for t in tables_by_chapter.values())
    print(f"Found {total} tables")
    return tables_by_chapter


def create_table_element(table_data):
    """Create a DocBook table element"""
    table = ET.Element('table', {'frame': 'all'})
    
    title = ET.SubElement(table, 'title')
    title.text = table_data['title']
    
    content = table_data.get('content')
    
    if content and len(content) >= 1:
        max_cols = max(len(r) for r in content)
        tgroup = ET.SubElement(table, 'tgroup', {'cols': str(max_cols)})
        
        for i in range(max_cols):
            ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
        
        # Header
        thead = ET.SubElement(tgroup, 'thead')
        hr = ET.SubElement(thead, 'row')
        for cell in content[0]:
            entry = ET.SubElement(hr, 'entry')
            entry.text = str(cell).strip() if cell else ""
        for _ in range(max_cols - len(content[0])):
            ET.SubElement(hr, 'entry')
        
        # Body
        tbody = ET.SubElement(tgroup, 'tbody')
        for row in content[1:]:
            r = ET.SubElement(tbody, 'row')
            for cell in row:
                entry = ET.SubElement(r, 'entry')
                entry.text = str(cell).strip() if cell else ""
            for _ in range(max_cols - len(row)):
                ET.SubElement(r, 'entry')
    else:
        # Placeholder
        tgroup = ET.SubElement(table, 'tgroup', {'cols': '2'})
        ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
        ET.SubElement(tgroup, 'colspec', {'colname': 'c2'})
        
        thead = ET.SubElement(tgroup, 'thead')
        hr = ET.SubElement(thead, 'row')
        ET.SubElement(hr, 'entry').text = "Content"
        ET.SubElement(hr, 'entry').text = "Details"
        
        tbody = ET.SubElement(tgroup, 'tbody')
        dr = ET.SubElement(tbody, 'row')
        ET.SubElement(dr, 'entry').text = f"Table {table_data['number']}"
        ET.SubElement(dr, 'entry').text = "See PDF"
    
    return table


def get_element_text(elem):
    """Get all text from an element including children"""
    text = elem.text or ""
    for child in elem:
        text += get_element_text(child)
        if child.tail:
            text += child.tail
    return text


def find_table_reference(elem, table_num):
    """Check if element references a specific table number"""
    text = get_element_text(elem)
    # Look for "Table X" reference
    pattern = rf'\bTable\s+{table_num}\b'
    return bool(re.search(pattern, text, re.I))


def is_bad_para(elem):
    """Check if paragraph should be removed"""
    text = get_element_text(elem)
    
    if 'BioRef' in text and ('Layout' in text or 'Page' in text):
        return True
    if re.match(r'^[ivxlcdm]+$', text.strip(), re.I) and len(text.strip()) < 5:
        return True
    if re.match(r'^\d{1,3}\s*$', text.strip()):
        return True
    
    return False


def process_chapter(xml_file, chapter_tables):
    """Process a single chapter file"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # First, remove existing tables and bad paragraphs
    for parent in list(root.iter()):
        to_remove = []
        for child in list(parent):
            if child.tag == 'table':
                to_remove.append(child)
            elif child.tag == 'para' and is_bad_para(child):
                to_remove.append(child)
        for child in to_remove:
            parent.remove(child)
    
    # Track which tables have been inserted
    inserted_tables = set()
    
    # Find where each table should be inserted
    # We'll iterate through all elements and find table references
    def insert_tables_after_references(parent):
        """Recursively find table references and insert tables after them"""
        children = list(parent)
        new_children = []
        
        for child in children:
            new_children.append(child)
            
            # Check if this element references any table
            if child.tag == 'para':
                text = get_element_text(child)
                
                # Find all table references in this paragraph
                for match in re.finditer(r'\bTable\s+(\d+)\b', text, re.I):
                    table_num = int(match.group(1))
                    
                    # If we have this table and haven't inserted it yet
                    if table_num in chapter_tables and table_num not in inserted_tables:
                        table_data = chapter_tables[table_num]
                        table_elem = create_table_element(table_data)
                        new_children.append(table_elem)
                        inserted_tables.add(table_num)
            
            # Recursively process children
            if len(child) > 0:
                insert_tables_after_references(child)
        
        # Replace parent's children with new list
        parent[:] = new_children
    
    # Process the document
    insert_tables_after_references(root)
    
    # Add any remaining tables that weren't referenced at the end
    remaining_tables = set(chapter_tables.keys()) - inserted_tables
    if remaining_tables:
        # Find last sect1 to append to
        last_sect = None
        for sect in root.iter('sect1'):
            last_sect = sect
        
        if last_sect is None:
            last_sect = root
        
        for table_num in sorted(remaining_tables):
            table_data = chapter_tables[table_num]
            table_elem = create_table_element(table_data)
            last_sect.append(table_elem)
    
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    return len(inserted_tables), len(remaining_tables)


def main():
    # Extract tables
    pdf_tables = extract_pdf_tables()
    
    # Create output directory
    print("\nCreating output files...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    
    # Process each chapter
    print("\nPlacing tables at correct positions:")
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue
        
        ch_num = int(ch_match.group(1))
        chapter_tables = pdf_tables.get(ch_num, {})
        
        if not chapter_tables:
            continue
        
        inserted, remaining = process_chapter(xml_file, chapter_tables)
        print(f"  Chapter {ch_num:02d}: {inserted} tables placed at references, {remaining} appended")
    
    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
