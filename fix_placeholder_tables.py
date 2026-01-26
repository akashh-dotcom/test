#!/usr/bin/env python3
"""
Fix tables with "See PDF" placeholder by extracting actual content from PDF.
"""

import os
import re
import fitz  # PyMuPDF
from pathlib import Path
import xml.etree.ElementTree as ET
from copy import deepcopy

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

def find_table_in_pdf(doc, table_title, table_num):
    """Find a table in PDF by its title and extract content."""
    # Clean up title for searching
    search_title = table_title.replace('-\n', '').replace('\n', ' ').strip()[:50]
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Look for the table title or "Table N" reference
        if search_title in text or f"Table {table_num}." in text:
            # Try to extract table content from this page
            tables = page.find_tables()
            
            for t in tables:
                try:
                    data = t.extract()
                    if data and len(data) > 1:
                        # Check if this looks like real content (not metadata)
                        first_cell = str(data[0][0]) if data[0] else ""
                        if 'BioRef' in first_cell or 'Layout' in first_cell:
                            continue
                        if 'Content' in first_cell and len(data) < 3:
                            continue  # Skip placeholder tables
                        
                        # Found real content
                        return data, page_num + 1
                except:
                    continue
            
            # If no structured table found, try to extract as text-based table
            # Look for numbered lists (1), (2), etc.
            table_content = extract_numbered_list(text, table_num)
            if table_content:
                return table_content, page_num + 1
    
    return None, None

def extract_numbered_list(text, table_num):
    """Extract numbered list content from text."""
    # Find the table section
    table_pattern = rf'Table\s+{table_num}\.\s*([^\n]+)'
    match = re.search(table_pattern, text)
    if not match:
        return None
    
    # Look for numbered items after the table title
    start_idx = match.end()
    
    # Find numbered items like (1), (2), etc.
    items = []
    pattern = r'\((\d+)\)\s+([^(]+?)(?=\(\d+\)|$)'
    
    # Get text after table title (up to next major section)
    remaining_text = text[start_idx:start_idx + 5000]
    
    for item_match in re.finditer(pattern, remaining_text, re.DOTALL):
        num = item_match.group(1)
        content = item_match.group(2).strip()
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        if len(content) > 10:  # Skip very short items
            items.append([f"({num})", content[:500]])  # Limit length
    
    if len(items) >= 3:  # Need at least 3 items to be a valid list
        return [["Item", "Description"]] + items
    
    return None

def create_table_element(title, content):
    """Create a properly structured table element."""
    table = ET.Element('table', {'frame': 'all'})
    
    title_elem = ET.SubElement(table, 'title')
    title_elem.text = title
    
    if not content or len(content) < 2:
        # No content available, create minimal table
        tgroup = ET.SubElement(table, 'tgroup', {'cols': '1'})
        ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
        tbody = ET.SubElement(tgroup, 'tbody')
        row = ET.SubElement(tbody, 'row')
        entry = ET.SubElement(row, 'entry')
        entry.text = "Content not available - see PDF"
        return table
    
    # Determine number of columns
    num_cols = max(len(row) for row in content)
    
    tgroup = ET.SubElement(table, 'tgroup', {'cols': str(num_cols)})
    
    for i in range(num_cols):
        ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
    
    # First row as header
    thead = ET.SubElement(tgroup, 'thead')
    head_row = ET.SubElement(thead, 'row')
    for cell in content[0]:
        entry = ET.SubElement(head_row, 'entry')
        entry.text = str(cell) if cell else ''
    
    # Remaining rows as body
    tbody = ET.SubElement(tgroup, 'tbody')
    for row in content[1:]:
        tr = ET.SubElement(tbody, 'row')
        for cell in row:
            entry = ET.SubElement(tr, 'entry')
            # Clean up cell content
            cell_text = str(cell) if cell else ''
            cell_text = re.sub(r'\s+', ' ', cell_text).strip()
            entry.text = cell_text[:500]  # Limit cell length
    
    return table

def is_placeholder_table(table_elem):
    """Check if table has placeholder content."""
    table_text = ET.tostring(table_elem, encoding='unicode', method='text')
    return 'See PDF' in table_text or ('Content' in table_text and 'Details' in table_text and len(table_text) < 100)

def process_file(xml_file, doc, output_file):
    """Process an XML file and fix placeholder tables."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0
    
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
                # Try to extract content from PDF
                content, page = find_table_in_pdf(doc, title, table_num)
                
                if content:
                    print(f"    Fixed Table {table_num} (found on page {page})")
                    
                    # Replace table content
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
    print(f"PDF: {PDF_FILE}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Open PDF
    doc = fitz.open(PDF_FILE)
    print(f"PDF has {len(doc)} pages")
    
    total_fixed = 0
    
    for xml_file in sorted(SOURCE_DIR.glob('*.xml')):
        if xml_file.name == 'Book.XML':
            # Just copy Book.XML
            import shutil
            shutil.copy(xml_file, OUTPUT_DIR / xml_file.name)
            continue
        
        print(f"\nProcessing {xml_file.name}...")
        output_file = OUTPUT_DIR / xml_file.name
        
        fixed = process_file(xml_file, doc, output_file)
        total_fixed += fixed
        
        if fixed > 0:
            print(f"  Fixed {fixed} table(s)")
    
    doc.close()
    
    # Copy multimedia
    import shutil
    multimedia_src = SOURCE_DIR / 'multimedia'
    if multimedia_src.exists():
        multimedia_dst = OUTPUT_DIR / 'multimedia'
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
        print("\nCopied multimedia folder")
    
    print(f"\n=== Summary ===")
    print(f"Total tables fixed: {total_fixed}")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
