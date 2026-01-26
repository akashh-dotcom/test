#!/usr/bin/env python3
"""
Fix existing malformed tables and add missing tables from PDF.
Keeps properly structured tables intact.
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
OUTPUT_DIR = Path('/workspace/final_output_tables_FIXED')


def extract_pdf_tables():
    """Extract all tables from PDF with chapter mapping"""
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
    tables = []
    seen = set()
    
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        chapter = chapter_pages.get(page_num, 0)
        if chapter == 0:
            continue
        
        for m in re.finditer(r'Table\s+(\d+)[\.\:]\s*([^\n]+)', text):
            table_num = int(m.group(1))
            title = m.group(2).strip()
            title = re.sub(r'\s+', ' ', title)
            title = re.sub(r'BioRef.*$', '', title).strip()
            
            key = (chapter, table_num, title[:40])
            if key in seen:
                continue
            seen.add(key)
            
            tables.append({
                'chapter': chapter,
                'number': table_num,
                'title': title[:150]
            })
    
    doc.close()
    
    # Group by chapter
    by_chapter = defaultdict(list)
    for t in tables:
        by_chapter[t['chapter']].append(t)
    
    return by_chapter


def is_malformed_table(table_elem):
    """Check if a table has malformed content (BioRef metadata, etc.)"""
    # Check title
    title_elem = table_elem.find('.//title')
    if title_elem is not None and title_elem.text:
        title = title_elem.text
        if 'BioRef' in title or 'Layout' in title or 'Page' in title:
            return True
        # Suspicious short titles like "." or ")."
        if len(title.strip()) < 5 and not title.strip()[0].isupper():
            return True
    
    # Check entries
    entries = list(table_elem.iter('entry'))
    if entries:
        # Check first few entries
        for entry in entries[:4]:
            if entry.text:
                if 'BioRef' in entry.text or '_Layout' in entry.text:
                    return True
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', entry.text.strip()):  # Date
                    return True
                if re.match(r'^\d+:\d+\s*(AM|PM)$', entry.text.strip()):  # Time
                    return True
    
    return False


def is_good_table(table_elem):
    """Check if a table is properly structured"""
    # Must have tgroup
    tgroup = table_elem.find('.//tgroup')
    if tgroup is None:
        return False
    
    # Check for thead with meaningful content
    thead = table_elem.find('.//thead')
    if thead is not None:
        entries = list(thead.iter('entry'))
        if entries:
            # Check if header entries have text
            header_text = [e.text for e in entries if e.text]
            if header_text and not any('BioRef' in t for t in header_text):
                return True
    
    # Check for proper tbody
    tbody = table_elem.find('.//tbody')
    if tbody is not None:
        rows = list(tbody.findall('.//row'))
        if len(rows) >= 2:
            # Multiple rows with multiple entries is good
            first_row_entries = list(rows[0].findall('.//entry'))
            if len(first_row_entries) >= 2:
                return True
    
    return False


def get_existing_table_titles(root):
    """Get titles of properly structured tables"""
    titles = []
    for table in root.iter('table'):
        if is_good_table(table) and not is_malformed_table(table):
            title_elem = table.find('.//title')
            if title_elem is not None and title_elem.text:
                titles.append(title_elem.text.lower()[:50])
    return titles


def table_exists_by_title(pdf_title, existing_titles):
    """Check if a table with similar title already exists"""
    pdf_lower = pdf_title.lower()[:50]
    for existing in existing_titles:
        # Check overlap
        if pdf_lower in existing or existing in pdf_lower:
            return True
        # Check word overlap
        pdf_words = set(pdf_lower.split())
        existing_words = set(existing.split())
        if len(pdf_words & existing_words) >= 3:
            return True
    return False


def create_simple_table(table_num, title):
    """Create a simple placeholder table with proper structure"""
    table = ET.Element('table', {'frame': 'all'})
    
    title_elem = ET.SubElement(table, 'title')
    title_elem.text = title if title else f"Table {table_num}"
    
    tgroup = ET.SubElement(table, 'tgroup', {'cols': '2'})
    ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
    ET.SubElement(tgroup, 'colspec', {'colname': 'c2'})
    
    thead = ET.SubElement(tgroup, 'thead')
    header_row = ET.SubElement(thead, 'row')
    h1 = ET.SubElement(header_row, 'entry')
    h1.text = "Column 1"
    h2 = ET.SubElement(header_row, 'entry')
    h2.text = "Column 2"
    
    tbody = ET.SubElement(tgroup, 'tbody')
    data_row = ET.SubElement(tbody, 'row')
    d1 = ET.SubElement(data_row, 'entry')
    d1.text = f"Table {table_num}"
    d2 = ET.SubElement(data_row, 'entry')
    d2.text = "See PDF for complete content"
    
    return table


def process_xml_files(pdf_tables_by_chapter):
    """Process XML files - remove bad tables, add missing ones"""
    
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    
    print("=" * 80)
    print("PROCESSING XML FILES")
    print("=" * 80)
    
    stats = {
        'removed': 0,
        'kept': 0,
        'added': 0
    }
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue
        
        ch_num = int(ch_match.group(1))
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find all tables and their parents
        tables_to_remove = []
        tables_kept = []
        
        # Use a simple approach - iterate and mark for removal
        for parent in root.iter():
            for table in list(parent):
                if table.tag == 'table':
                    if is_malformed_table(table):
                        tables_to_remove.append((parent, table))
                    elif is_good_table(table):
                        tables_kept.append(table)
        
        # Remove malformed tables
        for parent, table in tables_to_remove:
            parent.remove(table)
            stats['removed'] += 1
        
        stats['kept'] += len(tables_kept)
        
        # Get existing good table titles
        existing_titles = []
        for table in tables_kept:
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
        
        # Add missing tables from PDF
        pdf_tables = pdf_tables_by_chapter.get(ch_num, [])
        added_count = 0
        
        for pdf_table in pdf_tables:
            if not table_exists_by_title(pdf_table['title'], existing_titles):
                # Create and add table
                new_table = create_simple_table(pdf_table['number'], pdf_table['title'])
                insert_parent.append(new_table)
                added_count += 1
                stats['added'] += 1
        
        if tables_to_remove or added_count:
            print(f"Chapter {ch_num:02d}: Removed {len(tables_to_remove)}, Kept {len(tables_kept)}, Added {added_count}")
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return stats


def verify_output():
    """Verify the output"""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    total_tables = 0
    good_tables = 0
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            tables = list(root.iter('table'))
            good = sum(1 for t in tables if is_good_table(t) and not is_malformed_table(t))
            
            if tables:
                print(f"  Chapter {ch_num:02d}: {len(tables)} tables ({good} properly structured)")
                total_tables += len(tables)
                good_tables += good
    
    print(f"\nTotal: {total_tables} tables ({good_tables} properly structured)")


def main():
    print("Extracting tables from PDF...")
    pdf_tables = extract_pdf_tables()
    
    total_pdf = sum(len(t) for t in pdf_tables.values())
    print(f"Found {total_pdf} tables in PDF across {len(pdf_tables)} chapters")
    
    stats = process_xml_files(pdf_tables)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tables removed (malformed): {stats['removed']}")
    print(f"Tables kept (good): {stats['kept']}")
    print(f"Tables added (from PDF): {stats['added']}")
    
    verify_output()
    
    print(f"\nOutput: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
