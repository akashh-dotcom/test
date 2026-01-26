#!/usr/bin/env python3
"""
Fix all placeholder tables by extracting content from PDF.
Handles numbered lists and various table formats.
"""

import os
import re
import fitz
from pathlib import Path
import xml.etree.ElementTree as ET
import shutil

PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_FIXED_TABLES')

ET.register_namespace('', '')

def clean_text(text):
    """Clean extracted text."""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('- ', '').strip()
    return text

def extract_numbered_list_from_text(text):
    """Extract numbered list (1), (2), etc. from text."""
    items = []
    
    # Find all positions of (number) patterns
    positions = []
    for match in re.finditer(r'\((\d+)\)', text):
        num = int(match.group(1))
        if num <= 50:  # Reasonable list number
            positions.append((match.start(), match.end(), num))
    
    # Extract content between consecutive numbers
    for i, (start, end, num) in enumerate(positions):
        if i + 1 < len(positions):
            next_start = positions[i + 1][0]
            content = text[end:next_start]
        else:
            # Last item - take up to "Table" or "BioRef" or end
            remaining = text[end:end + 800]
            match = re.search(r'(Table\s+\d+\.|BioRef)', remaining)
            if match:
                content = remaining[:match.start()]
            else:
                content = remaining
        
        content = clean_text(content)
        if len(content) > 15:
            items.append((num, content[:600]))
    
    # Sort by number and return
    items.sort(key=lambda x: x[0])
    
    if len(items) >= 3:
        return [["No.", "Recommendation"]] + [[f"({i[0]})", i[1]] for i in items]
    return None

def search_pdf_for_table(doc, title_hint, table_num):
    """Search PDF for a table, trying multiple strategies."""
    
    # Strategy 1: Search for title keywords
    title_words = [w for w in title_hint.lower().split() if len(w) > 4][:5]
    
    found_pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        text_lower = text.lower()
        
        # Check if this page has enough title words
        matches = sum(1 for w in title_words if w in text_lower)
        if matches >= 2:
            found_pages.append((page_num, text, matches))
    
    # Sort by match count
    found_pages.sort(key=lambda x: x[2], reverse=True)
    
    # Try each found page
    for page_num, text, _ in found_pages[:5]:
        # Try numbered list
        numbered = extract_numbered_list_from_text(text)
        if numbered:
            return numbered, page_num + 1
        
        # Try PyMuPDF table extraction
        page = doc[page_num]
        tables = page.find_tables()
        for t in tables:
            try:
                data = t.extract()
                if data and len(data) >= 2:
                    first = str(data[0][0] if data[0] else '')
                    if 'BioRef' in first or 'Layout' in first:
                        continue
                    if first == 'Content' and len(data) < 3:
                        continue
                    
                    cleaned = []
                    for row in data:
                        cleaned_row = [clean_text(str(c) if c else '') for c in row]
                        if any(cleaned_row):
                            cleaned.append(cleaned_row)
                    
                    if len(cleaned) >= 2:
                        return cleaned, page_num + 1
            except:
                continue
    
    return None, None

def update_table_content(table, content):
    """Replace table content."""
    title_elem = table.find('title')
    title = title_elem.text if title_elem is not None else ''
    
    for child in list(table):
        table.remove(child)
    
    new_title = ET.SubElement(table, 'title')
    new_title.text = title
    
    num_cols = max(len(row) for row in content)
    tgroup = ET.SubElement(table, 'tgroup', {'cols': str(num_cols)})
    
    for i in range(num_cols):
        ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
    
    thead = ET.SubElement(tgroup, 'thead')
    head_row = ET.SubElement(thead, 'row')
    for cell in content[0]:
        entry = ET.SubElement(head_row, 'entry')
        entry.text = str(cell)[:500] if cell else ''
    
    tbody = ET.SubElement(tgroup, 'tbody')
    for row in content[1:]:
        tr = ET.SubElement(tbody, 'row')
        for cell in row:
            entry = ET.SubElement(tr, 'entry')
            entry.text = str(cell)[:500] if cell else ''

def process_file(xml_file, doc, output_file):
    """Process XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  Error: {e}")
        return 0, 0
    
    fixed = 0
    failed = 0
    
    for table in root.iter('table'):
        table_text = ET.tostring(table, encoding='unicode', method='text')
        if 'See PDF' not in table_text:
            continue
        
        title_elem = table.find('title')
        title = title_elem.text if title_elem is not None else ''
        
        match = re.search(r'Table\s+(\d+)', table_text)
        table_num = int(match.group(1)) if match else None
        
        if not table_num or not title:
            failed += 1
            continue
        
        content, page = search_pdf_for_table(doc, title, table_num)
        
        if content:
            update_table_content(table, content)
            print(f"    Fixed Table {table_num}: {title[:40]}... (page {page}, {len(content)-1} rows)")
            fixed += 1
        else:
            print(f"    Failed Table {table_num}: {title[:40]}...")
            failed += 1
    
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return fixed, failed

def main():
    print(f"Fixing placeholder tables\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF_FILE)
    
    total_fixed = 0
    total_failed = 0
    
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
