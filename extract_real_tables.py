#!/usr/bin/env python3
"""
Extract real table content from PDF using PyMuPDF's table detection.
Creates proper DocBook tables with actual data.
"""

import fitz
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import shutil

PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_REAL_CONTENT')


def is_metadata_table(table_data):
    """Check if table is just page metadata (BioRef headers)"""
    if not table_data or len(table_data) < 2:
        return True
    
    first_row = " ".join(str(c) for c in table_data[0] if c)
    if 'BioRef' in first_row or 'Layout' in first_row:
        return True
    if re.search(r'\d{1,2}/\d{1,2}/\d{4}', first_row):  # Date pattern
        return True
    
    return False


def clean_cell(cell):
    """Clean a cell value"""
    if cell is None:
        return ""
    cell = str(cell).strip()
    cell = re.sub(r'\s+', ' ', cell)
    return cell


def extract_tables_with_content():
    """Extract tables from PDF with actual content"""
    print("=" * 80)
    print("EXTRACTING TABLES WITH CONTENT FROM PDF")
    print("=" * 80)
    
    doc = fitz.open(PDF_FILE)
    print(f"Total pages: {len(doc)}")
    
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
    all_tables = []
    
    for page_num in range(len(doc)):
        chapter = chapter_pages.get(page_num, 0)
        if chapter == 0:
            continue
        
        page = doc[page_num]
        text = page.get_text()
        
        # Find table references on this page
        table_refs = []
        for m in re.finditer(r'Table\s+(\d+)[\.\:]([^\n]+)', text):
            table_num = int(m.group(1))
            title = m.group(2).strip()
            title = re.sub(r'\s+', ' ', title)
            title = re.sub(r'BioRef.*$', '', title).strip()
            if title:
                table_refs.append({'number': table_num, 'title': title[:150]})
        
        if not table_refs:
            continue
        
        # Extract actual tables from page
        try:
            tables = page.find_tables()
            extracted = []
            for table in tables.tables:
                data = table.extract()
                if not is_metadata_table(data):
                    extracted.append(data)
        except:
            extracted = []
        
        # Match table refs with extracted content
        for i, ref in enumerate(table_refs):
            content = extracted[i] if i < len(extracted) else None
            
            all_tables.append({
                'page': page_num + 1,
                'chapter': chapter,
                'number': ref['number'],
                'title': ref['title'],
                'content': content
            })
    
    doc.close()
    
    # Deduplicate
    seen = set()
    unique = []
    for t in all_tables:
        key = (t['chapter'], t['number'], t['title'][:40])
        if key not in seen:
            seen.add(key)
            unique.append(t)
    
    # Group by chapter
    by_chapter = defaultdict(list)
    for t in unique:
        by_chapter[t['chapter']].append(t)
    
    print(f"Extracted {len(unique)} unique tables from {len(by_chapter)} chapters")
    return by_chapter


def create_docbook_table(table_num, title, content):
    """Create DocBook table with actual content"""
    table = ET.Element('table', {'frame': 'all'})
    
    title_elem = ET.SubElement(table, 'title')
    title_elem.text = title if title else f"Table {table_num}"
    
    if content and len(content) >= 1:
        # Determine column count
        max_cols = max(len(row) for row in content)
        if max_cols < 1:
            max_cols = 2
        
        tgroup = ET.SubElement(table, 'tgroup', {'cols': str(max_cols)})
        
        # Add colspecs
        for i in range(max_cols):
            ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
        
        # First row as header
        thead = ET.SubElement(tgroup, 'thead')
        header_row = ET.SubElement(thead, 'row')
        for cell in content[0]:
            entry = ET.SubElement(header_row, 'entry')
            entry.text = clean_cell(cell)
        # Pad if needed
        for _ in range(max_cols - len(content[0])):
            ET.SubElement(header_row, 'entry')
        
        # Remaining rows as body
        tbody = ET.SubElement(tgroup, 'tbody')
        for row_data in content[1:]:
            row = ET.SubElement(tbody, 'row')
            for cell in row_data:
                entry = ET.SubElement(row, 'entry')
                entry.text = clean_cell(cell)
            # Pad if needed
            for _ in range(max_cols - len(row_data)):
                ET.SubElement(row, 'entry')
    else:
        # Placeholder if no content extracted
        tgroup = ET.SubElement(table, 'tgroup', {'cols': '2'})
        ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
        ET.SubElement(tgroup, 'colspec', {'colname': 'c2'})
        
        thead = ET.SubElement(tgroup, 'thead')
        header_row = ET.SubElement(thead, 'row')
        h1 = ET.SubElement(header_row, 'entry')
        h1.text = "Content"
        h2 = ET.SubElement(header_row, 'entry')
        h2.text = "Description"
        
        tbody = ET.SubElement(tgroup, 'tbody')
        data_row = ET.SubElement(tbody, 'row')
        d1 = ET.SubElement(data_row, 'entry')
        d1.text = f"Table {table_num}"
        d2 = ET.SubElement(data_row, 'entry')
        d2.text = "See original PDF"
    
    return table


def is_malformed_table(table_elem):
    """Check if table has malformed content"""
    entries = list(table_elem.iter('entry'))
    for entry in entries[:4]:
        if entry.text:
            if 'BioRef' in entry.text or '_Layout' in entry.text:
                return True
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', entry.text.strip()):
                return True
    return False


def is_good_existing_table(table_elem):
    """Check if existing table is properly structured with good content"""
    if is_malformed_table(table_elem):
        return False
    
    thead = table_elem.find('.//thead')
    tbody = table_elem.find('.//tbody')
    
    if thead is not None and tbody is not None:
        header_entries = list(thead.iter('entry'))
        body_rows = list(tbody.findall('.//row'))
        
        if header_entries and body_rows:
            # Check header has meaningful content
            header_texts = [e.text for e in header_entries if e.text and e.text.strip()]
            if header_texts and 'Column' not in header_texts[0]:
                return True
    
    return False


def process_files(pdf_tables):
    """Process XML files"""
    print("\n" + "=" * 80)
    print("PROCESSING XML FILES")
    print("=" * 80)
    
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    
    stats = {'removed': 0, 'kept': 0, 'added': 0}
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue
        
        ch_num = int(ch_match.group(1))
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Track existing good tables
        good_tables = []
        tables_to_remove = []
        
        for parent in root.iter():
            for table in list(parent):
                if table.tag == 'table':
                    if is_good_existing_table(table):
                        good_tables.append(table)
                    else:
                        tables_to_remove.append((parent, table))
        
        # Remove bad tables
        for parent, table in tables_to_remove:
            parent.remove(table)
            stats['removed'] += 1
        
        stats['kept'] += len(good_tables)
        
        # Get existing titles
        existing_titles = []
        for table in good_tables:
            title_elem = table.find('.//title')
            if title_elem is not None and title_elem.text:
                existing_titles.append(title_elem.text.lower()[:50])
        
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
        
        # Add tables from PDF
        pdf_chapter_tables = pdf_tables.get(ch_num, [])
        added = 0
        
        for pdf_table in pdf_chapter_tables:
            pdf_title_lower = pdf_table['title'].lower()[:50]
            
            # Check if similar title exists
            exists = False
            for et in existing_titles:
                if pdf_title_lower in et or et in pdf_title_lower:
                    exists = True
                    break
                # Word overlap check
                pw = set(pdf_title_lower.split())
                ew = set(et.split())
                if len(pw & ew) >= 3:
                    exists = True
                    break
            
            if not exists:
                new_table = create_docbook_table(
                    pdf_table['number'],
                    pdf_table['title'],
                    pdf_table['content']
                )
                insert_parent.append(new_table)
                added += 1
                stats['added'] += 1
        
        if tables_to_remove or added:
            print(f"Chapter {ch_num:02d}: -{len(tables_to_remove)} malformed, +{added} new, ={len(good_tables)} kept")
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return stats


def main():
    # Extract tables with content
    pdf_tables = extract_tables_with_content()
    
    # Show sample
    print("\nSample extracted tables:")
    for ch in sorted(pdf_tables.keys())[:3]:
        for t in pdf_tables[ch][:2]:
            print(f"  Ch{ch} Table {t['number']}: {t['title'][:50]}")
            if t['content']:
                print(f"    Content rows: {len(t['content'])}")
    
    # Process files
    stats = process_files(pdf_tables)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Malformed tables removed: {stats['removed']}")
    print(f"Good tables kept: {stats['kept']}")
    print(f"New tables added: {stats['added']}")
    print(f"Total tables: {stats['kept'] + stats['added']}")
    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
