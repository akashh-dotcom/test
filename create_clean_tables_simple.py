#!/usr/bin/env python3
"""
Create XML files with ONLY the tables from PDF - simplified version.
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


def main():
    print("Opening PDF...")
    doc = fitz.open(PDF_FILE)
    print(f"Pages: {len(doc)}")
    
    # Map pages to chapters
    chapter_pages = {}
    current_ch = 0
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        m = re.search(r'(?:^|\n)\s*Chapter\s+(\d+)\s*\n', text, re.I)
        if m:
            current_ch = int(m.group(1))
        chapter_pages[page_num] = current_ch
    
    # Extract tables
    print("Extracting tables...")
    tables_by_chapter = defaultdict(list)
    seen = set()
    
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
            
            key = (chapter, table_num, title[:30])
            if key in seen:
                continue
            seen.add(key)
            
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
            
            tables_by_chapter[chapter].append({
                'number': table_num,
                'title': title[:150],
                'content': content
            })
    
    doc.close()
    
    total_pdf = sum(len(t) for t in tables_by_chapter.values())
    print(f"\nFound {total_pdf} tables in PDF")
    
    # Create output
    print("\nCreating output files...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    
    total_added = 0
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue
        
        ch_num = int(ch_match.group(1))
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Remove all existing tables
        removed = 0
        for parent in root.iter():
            for child in list(parent):
                if child.tag == 'table':
                    parent.remove(child)
                    removed += 1
        
        # Find insertion point
        insert_parent = root
        for sect in root.iter('sect1'):
            insert_parent = sect
            break
        
        # Add PDF tables
        chapter_tables = tables_by_chapter.get(ch_num, [])
        
        for t in sorted(chapter_tables, key=lambda x: x['number']):
            table = ET.SubElement(insert_parent, 'table', {'frame': 'all'})
            title_elem = ET.SubElement(table, 'title')
            title_elem.text = t['title']
            
            content = t.get('content')
            if content and len(content) >= 1:
                max_cols = max(len(r) for r in content)
                tgroup = ET.SubElement(table, 'tgroup', {'cols': str(max_cols)})
                for i in range(max_cols):
                    ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
                
                thead = ET.SubElement(tgroup, 'thead')
                hr = ET.SubElement(thead, 'row')
                for cell in content[0]:
                    e = ET.SubElement(hr, 'entry')
                    e.text = str(cell).strip() if cell else ""
                
                tbody = ET.SubElement(tgroup, 'tbody')
                for row in content[1:]:
                    r = ET.SubElement(tbody, 'row')
                    for cell in row:
                        e = ET.SubElement(r, 'entry')
                        e.text = str(cell).strip() if cell else ""
            else:
                tgroup = ET.SubElement(table, 'tgroup', {'cols': '2'})
                ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
                ET.SubElement(tgroup, 'colspec', {'colname': 'c2'})
                thead = ET.SubElement(tgroup, 'thead')
                hr = ET.SubElement(thead, 'row')
                ET.SubElement(hr, 'entry').text = "Item"
                ET.SubElement(hr, 'entry').text = "Description"
                tbody = ET.SubElement(tgroup, 'tbody')
                dr = ET.SubElement(tbody, 'row')
                ET.SubElement(dr, 'entry').text = f"Table {t['number']}"
                ET.SubElement(dr, 'entry').text = "See PDF"
        
        if chapter_tables or removed:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            print(f"  Ch {ch_num:02d}: -{removed} old, +{len(chapter_tables)} PDF")
            total_added += len(chapter_tables)
    
    print(f"\n{'='*60}")
    print(f"PDF tables: {total_pdf}")
    print(f"XML tables: {total_added}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
