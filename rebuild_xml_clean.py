#!/usr/bin/env python3
"""
Rebuild XML files cleanly:
1. Remove all BioRef metadata paragraphs
2. Remove paragraphs containing raw table data
3. Replace tables with properly extracted content from PDF
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
OUTPUT_DIR = Path('/workspace/final_output_tables_FINAL')


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
    
    # Extract tables
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
    
    total = sum(len(t) for t in tables_by_chapter.values())
    print(f"Found {total} tables in PDF")
    return tables_by_chapter


def is_bad_para(para_elem):
    """Check if a paragraph should be removed"""
    # Get text content
    text = ""
    if para_elem.text:
        text += para_elem.text
    for child in para_elem:
        if child.text:
            text += child.text
        if child.tail:
            text += child.tail
    
    text = text.strip()
    if not text:
        return False
    
    # BioRef metadata
    if 'BioRef' in text and ('Layout' in text or 'Page' in text):
        return True
    
    # Page numbers like "35" or "MRI Bioeffects, Safety, and Patient Management 35"
    if re.match(r'^(MRI Bioeffects.*?)?\s*\d{1,3}\s*$', text):
        return True
    
    # Standalone "Table X." references
    if re.match(r'^Table\s+\d+\.\s*$', text):
        return True
    
    # Paragraphs that are mostly numbers/data (raw table content)
    lines = text.split('\n')
    if len(lines) > 5:
        data_lines = 0
        for line in lines:
            line = line.strip()
            # Check if line looks like table data
            if re.match(r'^[\d\.\-\s]+$', line):  # Just numbers
                data_lines += 1
            elif re.match(r'^[A-Za-z\s]+\s+[\d\.\-]+', line):  # Label + number
                data_lines += 1
            elif len(line) < 20 and not re.search(r'[a-z]{5,}', line.lower()):  # Short, no real words
                data_lines += 1
        
        if data_lines > len(lines) * 0.6:
            return True
    
    # Force Index style data dumps
    if 'Force' in text and 'Index' in text:
        numbers = re.findall(r'\d+\.\d+', text)
        if len(numbers) >= 3:
            return True
    
    return False


def create_table_xml(table_data):
    """Create a proper DocBook table element"""
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
        # Minimal placeholder
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
        ET.SubElement(dr, 'entry').text = "Refer to PDF"
    
    return table


def clean_xml_file(xml_file, pdf_tables):
    """Clean and rebuild a single XML file"""
    ch_match = re.search(r'ch(\d+)', xml_file.name)
    if not ch_match:
        return 0, 0, 0
    
    ch_num = int(ch_match.group(1))
    
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Remove bad paragraphs and all existing tables
    paras_removed = 0
    tables_removed = 0
    
    for parent in list(root.iter()):
        to_remove = []
        for child in list(parent):
            if child.tag == 'para' and is_bad_para(child):
                to_remove.append(child)
            elif child.tag == 'table':
                to_remove.append(child)
        
        for child in to_remove:
            parent.remove(child)
            if child.tag == 'para':
                paras_removed += 1
            else:
                tables_removed += 1
    
    # Find insertion point
    insert_parent = root
    for sect in root.iter('sect1'):
        insert_parent = sect
        break
    
    # Add PDF tables
    chapter_tables = pdf_tables.get(ch_num, [])
    for t in sorted(chapter_tables, key=lambda x: x['number']):
        table_elem = create_table_xml(t)
        insert_parent.append(table_elem)
    
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return paras_removed, tables_removed, len(chapter_tables)


def main():
    # Extract tables from PDF
    pdf_tables = extract_pdf_tables()
    
    # Create output directory
    print("\nCreating output files...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    
    # Process files
    print("\nCleaning and rebuilding XML files:")
    total_paras = 0
    total_tables_removed = 0
    total_tables_added = 0
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        paras, tables_rm, tables_add = clean_xml_file(xml_file, pdf_tables)
        
        if paras or tables_rm or tables_add:
            ch_match = re.search(r'ch(\d+)', xml_file.name)
            ch_num = int(ch_match.group(1)) if ch_match else 0
            print(f"  Ch {ch_num:02d}: -{paras} bad paras, -{tables_rm} old tables, +{tables_add} PDF tables")
            total_paras += paras
            total_tables_removed += tables_rm
            total_tables_added += tables_add
    
    print(f"\n{'='*60}")
    print(f"Bad paragraphs removed: {total_paras}")
    print(f"Old tables removed: {total_tables_removed}")
    print(f"PDF tables added: {total_tables_added}")
    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
