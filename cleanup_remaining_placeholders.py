#!/usr/bin/env python3
"""
Clean up remaining placeholder tables to have proper structure.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

SOURCE_DIR = Path('/workspace/final_output_tables_FIXED_TABLES')
OUTPUT_DIR = Path('/workspace/final_output_tables_COMPLETE_FIXED')

ET.register_namespace('', '')

def is_placeholder_table(table_elem):
    """Check if table has placeholder content."""
    table_text = ET.tostring(table_elem, encoding='unicode', method='text')
    return 'See PDF' in table_text

def fix_placeholder(table):
    """Replace broken placeholder with clean format."""
    title_elem = table.find('title')
    title = title_elem.text if title_elem is not None else 'Table'
    
    # Get table number
    table_text = ET.tostring(table, encoding='unicode', method='text')
    match = re.search(r'Table\s+(\d+)', table_text)
    table_num = match.group(1) if match else ''
    
    # Clear existing content
    for child in list(table):
        table.remove(child)
    
    # Add clean title
    new_title = ET.SubElement(table, 'title')
    # Clean up the title - remove truncation
    if title.endswith('-'):
        title = title.rstrip('-').strip()
    new_title.text = title
    
    # Add clean single-column table
    tgroup = ET.SubElement(table, 'tgroup', {'cols': '1'})
    ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
    
    thead = ET.SubElement(tgroup, 'thead')
    head_row = ET.SubElement(thead, 'row')
    entry = ET.SubElement(head_row, 'entry')
    entry.text = f"Table {table_num}" if table_num else "Table Content"
    
    tbody = ET.SubElement(tgroup, 'tbody')
    row = ET.SubElement(tbody, 'row')
    entry = ET.SubElement(row, 'entry')
    entry.text = "For detailed table content, please refer to the original PDF document."

def process_file(xml_file, output_file):
    """Process an XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  Error: {e}")
        return 0
    
    fixed = 0
    
    for table in root.iter('table'):
        if is_placeholder_table(table):
            title_elem = table.find('title')
            title = title_elem.text[:50] if title_elem is not None and title_elem.text else 'Unknown'
            fix_placeholder(table)
            print(f"    Cleaned: {title}...")
            fixed += 1
    
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return fixed

def main():
    print(f"Cleaning remaining placeholders\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = 0
    
    for xml_file in sorted(SOURCE_DIR.glob('*.xml')):
        if xml_file.name == 'Book.XML':
            shutil.copy(xml_file, OUTPUT_DIR / xml_file.name)
            continue
        
        output_file = OUTPUT_DIR / xml_file.name
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            if 'See PDF' not in f.read():
                shutil.copy(xml_file, output_file)
                continue
        
        print(f"Processing {xml_file.name}...")
        fixed = process_file(xml_file, output_file)
        total += fixed
    
    # Copy multimedia
    multimedia_src = SOURCE_DIR / 'multimedia'
    if multimedia_src.exists():
        multimedia_dst = OUTPUT_DIR / 'multimedia'
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
    
    print(f"\nTotal cleaned: {total}")

if __name__ == '__main__':
    main()
