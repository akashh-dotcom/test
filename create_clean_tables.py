#!/usr/bin/env python3
"""
Create XML files with ONLY the tables that exist in the PDF.
No duplicates, no extra tables - just the ~133 from the PDF.
"""

import fitz
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import shutil

PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_CLEAN')


def extract_all_pdf_tables():
    """Extract ALL tables from PDF with content"""
    print("=" * 80)
    print("EXTRACTING ALL TABLES FROM PDF")
    print("=" * 80)
    
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
    all_tables = []
    
    for page_num in range(len(doc)):
        chapter = chapter_pages.get(page_num, 0)
        if chapter == 0:
            continue
        
        page = doc[page_num]
        text = page.get_text()
        
        # Find table references
        for m in re.finditer(r'Table\s+(\d+)[\.\:]\s*([^\n]+)', text):
            table_num = int(m.group(1))
            title = m.group(2).strip()
            title = re.sub(r'\s+', ' ', title)
            title = re.sub(r'BioRef.*$', '', title).strip()
            
            if not title or len(title) < 3:
                continue
            
            all_tables.append({
                'page': page_num + 1,
                'chapter': chapter,
                'number': table_num,
                'title': title[:150]
            })
        
        # Try to extract table content from page
        try:
            tables = page.find_tables()
            page_tables = []
            for table in tables.tables:
                data = table.extract()
                # Filter out metadata tables
                if data and len(data) >= 2:
                    first_row = " ".join(str(c) for c in data[0] if c)
                    if 'BioRef' not in first_row and 'Layout' not in first_row:
                        page_tables.append(data)
            
            # Match content to table references
            for i, t in enumerate(all_tables):
                if t['page'] == page_num + 1 and 'content' not in t:
                    if i < len(page_tables):
                        t['content'] = page_tables[i] if i < len(page_tables) else None
        except:
            pass
    
    doc.close()
    
    # Deduplicate - keep unique (chapter, number, title[:30]) combinations
    seen = set()
    unique = []
    for t in all_tables:
        key = (t['chapter'], t['number'], t['title'][:30])
        if key not in seen:
            seen.add(key)
            unique.append(t)
    
    # Group by chapter
    by_chapter = defaultdict(list)
    for t in unique:
        by_chapter[t['chapter']].append(t)
    
    total = len(unique)
    print(f"\nFound {total} unique tables in PDF across {len(by_chapter)} chapters")
    
    # Show per chapter
    for ch in sorted(by_chapter.keys()):
        print(f"  Chapter {ch:02d}: {len(by_chapter[ch])} tables")
    
    return by_chapter


def clean_cell(cell):
    """Clean cell content"""
    if cell is None:
        return ""
    return re.sub(r'\s+', ' ', str(cell)).strip()


def create_table_element(table_data):
    """Create a DocBook table element"""
    table = ET.Element('table', {'frame': 'all'})
    
    # Title
    title_elem = ET.SubElement(table, 'title')
    title_elem.text = table_data['title']
    
    content = table_data.get('content')
    
    if content and len(content) >= 1:
        max_cols = max(len(row) for row in content) if content else 2
        max_cols = max(2, max_cols)  # At least 2 columns
        
        tgroup = ET.SubElement(table, 'tgroup', {'cols': str(max_cols)})
        for i in range(max_cols):
            ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
        
        # Header (first row)
        thead = ET.SubElement(tgroup, 'thead')
        header_row = ET.SubElement(thead, 'row')
        for j, cell in enumerate(content[0]):
            if j < max_cols:
                entry = ET.SubElement(header_row, 'entry')
                entry.text = clean_cell(cell)
        for _ in range(max_cols - len(content[0])):
            ET.SubElement(header_row, 'entry')
        
        # Body (remaining rows)
        tbody = ET.SubElement(tgroup, 'tbody')
        for row_data in content[1:]:
            row = ET.SubElement(tbody, 'row')
            for j, cell in enumerate(row_data):
                if j < max_cols:
                    entry = ET.SubElement(row, 'entry')
                    entry.text = clean_cell(cell)
            for _ in range(max_cols - len(row_data)):
                ET.SubElement(row, 'entry')
    else:
        # No content extracted - create placeholder
        tgroup = ET.SubElement(table, 'tgroup', {'cols': '2'})
        ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
        ET.SubElement(tgroup, 'colspec', {'colname': 'c2'})
        
        thead = ET.SubElement(tgroup, 'thead')
        hr = ET.SubElement(thead, 'row')
        ET.SubElement(hr, 'entry').text = "Column 1"
        ET.SubElement(hr, 'entry').text = "Column 2"
        
        tbody = ET.SubElement(tgroup, 'tbody')
        dr = ET.SubElement(tbody, 'row')
        ET.SubElement(dr, 'entry').text = f"Table {table_data['number']}"
        ET.SubElement(dr, 'entry').text = "See PDF for content"
    
    return table


def process_xml_files(pdf_tables):
    """Create clean XML files with only PDF tables"""
    print("\n" + "=" * 80)
    print("CREATING CLEAN XML FILES")
    print("=" * 80)
    
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    
    total_tables = 0
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue
        
        ch_num = int(ch_match.group(1))
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Remove ALL existing tables
        tables_removed = 0
        for parent in root.iter():
            for child in list(parent):
                if child.tag == 'table':
                    parent.remove(child)
                    tables_removed += 1
        
        # Find insertion point
        insert_parent = None
        for sect in root.iter('sect1'):
            insert_parent = sect
            break
        if insert_parent is None:
            for ch in root.iter('chapter'):
                insert_parent = ch
                break
        if insert_parent is None:
            insert_parent = root
        
        # Add tables from PDF for this chapter
        chapter_tables = pdf_tables.get(ch_num, [])
        
        for table_data in sorted(chapter_tables, key=lambda x: x['number']):
            table_elem = create_table_element(table_data)
            insert_parent.append(table_elem)
        
        if chapter_tables or tables_removed:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            print(f"  Chapter {ch_num:02d}: Removed {tables_removed} old, Added {len(chapter_tables)} from PDF")
            total_tables += len(chapter_tables)
    
    return total_tables


def main():
    # Extract all tables from PDF
    pdf_tables = extract_all_pdf_tables()
    
    pdf_total = sum(len(t) for t in pdf_tables.values())
    
    # Create clean XML files
    total = process_xml_files(pdf_tables)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tables in PDF: {pdf_total}")
    print(f"Tables in output XML: {total}")
    print(f"\nOutput: {OUTPUT_DIR}")
    
    # Verify
    print("\nVerification:")
    actual_total = 0
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            tree = ET.parse(xml_file)
            count = len(list(tree.getroot().iter('table')))
            if count > 0:
                print(f"  Chapter {int(ch_match.group(1)):02d}: {count} tables")
                actual_total += count
    
    print(f"\nTotal tables in XML: {actual_total}")


if __name__ == '__main__':
    main()
