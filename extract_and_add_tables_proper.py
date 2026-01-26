#!/usr/bin/env python3
"""
Extract tables from PDF and add them with proper DocBook structure.
This script properly parses table content from the PDF.
"""

import fitz  # PyMuPDF
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import shutil

# Paths
PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_PROPER_TABLES')


def get_chapter_mapping(doc):
    """Map page numbers to chapters"""
    chapter_pages = {}
    current_chapter = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        ch_match = re.search(r'(?:^|\n)\s*Chapter\s+(\d+)\s*\n', text, re.IGNORECASE)
        if ch_match:
            current_chapter = int(ch_match.group(1))
        
        chapter_pages[page_num] = current_chapter
    
    return chapter_pages


def extract_table_content(doc, page_num, table_start_pos, text):
    """Extract table content from PDF page"""
    
    # Get text after table header
    remaining = text[table_start_pos:]
    lines = remaining.split('\n')
    
    # Find table content
    table_lines = []
    in_table = False
    blank_count = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip the title line
        if i == 0:
            continue
            
        if not line:
            blank_count += 1
            if blank_count > 2 and len(table_lines) > 2:
                break
            continue
        
        blank_count = 0
        
        # Stop conditions
        if re.match(r'^(Chapter|CHAPTER|Figure|FIGURE)\s+\d+', line):
            break
        if re.match(r'^BioRef\s+\d{4}', line):
            continue  # Skip page headers
        if re.match(r'^\d{1,3}$', line):  # Page numbers
            continue
        if 'Page' in line and re.search(r'\d{1,4}\s*$', line):
            continue
            
        # Check if line looks like table data
        # Tables typically have multiple columns separated by spaces
        if re.search(r'\s{2,}', line) or len(table_lines) > 0:
            table_lines.append(line)
        elif len(line) < 100:
            table_lines.append(line)
        
        # Limit extraction
        if len(table_lines) > 30:
            break
    
    return table_lines


def parse_table_content_to_rows(lines):
    """Parse table lines into rows and columns"""
    if not lines:
        return [], 1
    
    rows = []
    max_cols = 1
    
    for line in lines:
        # Try to split on multiple spaces (2+) or tabs
        parts = re.split(r'\s{2,}|\t+', line)
        parts = [p.strip() for p in parts if p.strip()]
        
        if parts:
            rows.append(parts)
            max_cols = max(max_cols, len(parts))
    
    return rows, max_cols


def create_docbook_table(table_num, title, content_lines):
    """Create a proper DocBook table element"""
    
    # Parse content into rows
    rows, max_cols = parse_table_content_to_rows(content_lines)
    
    if not rows:
        rows = [[f"See original PDF for Table {table_num} content"]]
        max_cols = 1
    
    # Create table element
    table = ET.Element('table', {'frame': 'all'})
    
    # Add title
    title_elem = ET.SubElement(table, 'title')
    # Clean up title
    clean_title = re.sub(r'\s+', ' ', title).strip()
    clean_title = re.sub(r'BioRef.*$', '', clean_title).strip()
    if clean_title:
        title_elem.text = clean_title
    else:
        title_elem.text = f"Table {table_num}"
    
    # Create tgroup
    tgroup = ET.SubElement(table, 'tgroup', {'cols': str(max_cols)})
    
    # Add colspecs
    for i in range(max_cols):
        ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
    
    # Determine if first row is header (usually if rows have similar column count)
    has_header = len(rows) > 1
    
    if has_header:
        # Create thead
        thead = ET.SubElement(tgroup, 'thead')
        header_row = ET.SubElement(thead, 'row')
        for cell in rows[0]:
            entry = ET.SubElement(header_row, 'entry')
            entry.text = cell
        # Pad if needed
        for _ in range(max_cols - len(rows[0])):
            ET.SubElement(header_row, 'entry')
        data_rows = rows[1:]
    else:
        data_rows = rows
    
    # Create tbody
    tbody = ET.SubElement(tgroup, 'tbody')
    for row_data in data_rows:
        row = ET.SubElement(tbody, 'row')
        for cell in row_data:
            entry = ET.SubElement(row, 'entry')
            entry.text = cell
        # Pad if needed
        for _ in range(max_cols - len(row_data)):
            ET.SubElement(row, 'entry')
    
    return table


def extract_all_tables():
    """Extract all tables from PDF with proper content"""
    print("=" * 80)
    print("EXTRACTING TABLES FROM PDF WITH PROPER STRUCTURE")
    print("=" * 80)
    
    doc = fitz.open(PDF_FILE)
    print(f"Total pages: {len(doc)}")
    
    chapter_pages = get_chapter_mapping(doc)
    
    tables = []
    seen_tables = set()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        chapter = chapter_pages.get(page_num, 0)
        
        if chapter == 0:
            continue
        
        # Find table definitions: "Table X. Title" or "Table X: Title"
        for match in re.finditer(r'Table\s+(\d+)[\.\:]\s*([^\n]+)', text):
            table_num = int(match.group(1))
            title = match.group(2).strip()
            
            # Create unique key to avoid duplicates
            key = (chapter, table_num, title[:30])
            if key in seen_tables:
                continue
            seen_tables.add(key)
            
            # Extract table content
            content_lines = extract_table_content(doc, page_num, match.end(), text)
            
            tables.append({
                'page': page_num + 1,
                'chapter': chapter,
                'number': table_num,
                'title': title,
                'content': content_lines
            })
    
    doc.close()
    
    # Group by chapter
    by_chapter = defaultdict(list)
    for t in tables:
        by_chapter[t['chapter']].append(t)
    
    print(f"\nExtracted {len(tables)} tables from {len(by_chapter)} chapters")
    return by_chapter


def add_tables_to_xml(tables_by_chapter):
    """Add extracted tables to XML files with proper DocBook structure"""
    
    print("\n" + "=" * 80)
    print("ADDING TABLES TO XML FILES")
    print("=" * 80)
    
    # Create output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    print(f"Created: {OUTPUT_DIR}")
    
    total_added = 0
    
    for chapter, tables in sorted(tables_by_chapter.items()):
        xml_file = OUTPUT_DIR / f'ch{chapter:04d}.xml'
        
        if not xml_file.exists():
            print(f"\nChapter {chapter}: XML file not found, skipping {len(tables)} tables")
            continue
        
        print(f"\nChapter {chapter}: Processing {len(tables)} table(s)")
        
        # Parse XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Remove existing malformed tables (those with BioRef metadata)
        tables_to_remove = []
        for table in root.iter('table'):
            # Check if table has bad content
            entries = list(table.iter('entry'))
            if entries:
                first_entry_text = entries[0].text if entries[0].text else ""
                if 'BioRef' in first_entry_text or 'Layout' in first_entry_text:
                    tables_to_remove.append(table)
        
        # Remove bad tables
        for bad_table in tables_to_remove:
            parent = None
            for p in root.iter():
                if bad_table in list(p):
                    parent = p
                    break
            if parent is not None:
                parent.remove(bad_table)
        
        # Find insertion point (first sect1)
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
        
        # Add tables
        for table_data in sorted(tables, key=lambda x: x['number']):
            table_elem = create_docbook_table(
                table_data['number'],
                table_data['title'],
                table_data['content']
            )
            insert_parent.append(table_elem)
            print(f"  + Table {table_data['number']}: {table_data['title'][:60]}")
            total_added += 1
        
        # Write back
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    return total_added


def verify_output():
    """Verify the output files"""
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    total = 0
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            tree = ET.parse(xml_file)
            root = tree.getroot()
            count = len(list(root.iter('table')))
            if count > 0:
                print(f"  Chapter {ch_num:02d}: {count} tables")
                total += count
    
    print(f"\nTotal tables in output: {total}")
    return total


def main():
    # Extract tables
    tables_by_chapter = extract_all_tables()
    
    # Show what we found
    print("\nTables found by chapter:")
    for ch in sorted(tables_by_chapter.keys()):
        tables = tables_by_chapter[ch]
        print(f"  Chapter {ch}: {len(tables)} tables")
        for t in tables:
            print(f"    - Table {t['number']}: {t['title'][:50]}")
    
    # Add to XML
    total_added = add_tables_to_xml(tables_by_chapter)
    
    # Verify
    total_in_output = verify_output()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tables extracted from PDF: {sum(len(t) for t in tables_by_chapter.values())}")
    print(f"Tables added to XML: {total_added}")
    print(f"Total tables in output: {total_in_output}")
    print(f"\nOutput directory: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
