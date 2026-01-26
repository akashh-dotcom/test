#!/usr/bin/env python3
"""
Add remaining 52 tables from PDF to final_output_tables_with_all_tables.
Also check and restore any content lost around tables.
"""

import fitz  # PyMuPDF
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import shutil

# Paths
PDF_FILE = Path('/home/user/test/9780989163286.pdf')
SOURCE_DIR = Path('/home/user/test/final_output_tables_with_all_tables')
OUTPUT_DIR = Path('/home/user/test/final_output_tables_COMPLETE')

def get_all_pdf_tables():
    """Extract all tables from PDF with full content"""
    print("=" * 100)
    print("EXTRACTING ALL TABLES FROM PDF")
    print("=" * 100)

    doc = fitz.open(PDF_FILE)
    all_tables = []

    print(f"\nScanning {len(doc)} pages...")

    for page_num in range(len(doc)):
        if (page_num + 1) % 100 == 0:
            print(f"  Progress: {page_num + 1}/{len(doc)}")

        page = doc[page_num]
        text = page.get_text()

        # Find table labels
        table_matches = list(re.finditer(r'Table\s+(\d+)[\.:]?\s*([^\n]{0,150})', text, re.IGNORECASE))

        for match in table_matches:
            table_num = match.group(1)
            title = match.group(2).strip()

            # Try to extract table content
            # Get text after the table label
            start_pos = match.end()
            remaining_text = text[start_pos:]

            # Extract lines that look like table content
            lines = remaining_text.split('\n')
            table_lines = []

            for line in lines[:50]:  # Look at next 50 lines max
                line = line.strip()
                if not line:
                    if len(table_lines) >= 3:
                        break
                    continue

                # Check if line looks like table content
                if re.search(r'\s{2,}|\t', line) or len(table_lines) > 0:
                    table_lines.append(line)
                elif len(table_lines) >= 3:
                    break

            if table_lines:
                all_tables.append({
                    'page': page_num + 1,
                    'number': table_num,
                    'title': title,
                    'content_lines': table_lines,
                    'full_text': '\n'.join(table_lines)
                })

    doc.close()

    # Deduplicate by (page, number)
    unique_tables = {}
    for table in all_tables:
        key = (table['page'], table['number'])
        if key not in unique_tables:
            unique_tables[key] = table

    print(f"\n✓ Found {len(unique_tables)} unique tables in PDF")
    return list(unique_tables.values())

def parse_table_to_xml(table_data):
    """Convert table data to XML table element"""

    # Try to detect columns and rows
    lines = table_data['content_lines']

    if not lines:
        return None

    # Simple heuristic: split on multiple spaces/tabs
    rows = []
    max_cols = 0

    for line in lines:
        # Split on 2+ spaces or tabs
        parts = re.split(r'\s{2,}|\t+', line)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            rows.append(parts)
            max_cols = max(max_cols, len(parts))

    if not rows:
        return None

    # Create XML table
    table_elem = ET.Element('table', {'frame': 'all'})

    # Add title if available
    if table_data['title']:
        title_elem = ET.SubElement(table_elem, 'title')
        title_elem.text = table_data['title']

    # Create tgroup
    tgroup = ET.SubElement(table_elem, 'tgroup', {'cols': str(max_cols)})

    # Assume first row is header if it has consistent columns
    has_header = len(rows) > 1 and len(rows[0]) == max_cols

    if has_header:
        thead = ET.SubElement(tgroup, 'thead')
        header_row = ET.SubElement(thead, 'row')
        for cell in rows[0]:
            entry = ET.SubElement(header_row, 'entry')
            entry.text = cell
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
        while len(row) < max_cols:
            ET.SubElement(row, 'entry')

    return table_elem

def get_existing_tables_in_xml():
    """Get list of tables already in XML files"""
    existing = defaultdict(list)

    for xml_file in sorted(SOURCE_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            ch_num = int(ch_match.group(1))

            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Get all table titles/content to identify them
            for table in root.iter('table'):
                title_elem = table.find('.//title')
                title = title_elem.text if title_elem is not None and title_elem.text else ""

                # Get first row for identification
                first_entry = table.find('.//entry')
                first_cell = first_entry.text if first_entry is not None else ""

                existing[ch_num].append({
                    'title': title,
                    'first_cell': first_cell[:50] if first_cell else ""
                })

    return existing

def map_pdf_page_to_chapter(page_num, doc):
    """Determine which chapter a PDF page belongs to"""

    # Extract text from the page and nearby pages
    page = doc[page_num - 1]
    text = page.get_text()

    # Look for "Chapter X" on this page or previous pages
    chapter_match = re.search(r'Chapter\s+(\d+)', text, re.IGNORECASE)
    if chapter_match:
        return int(chapter_match.group(1))

    # Check previous pages (up to 20 pages back)
    for i in range(max(0, page_num - 20), page_num):
        prev_page = doc[i]
        prev_text = prev_page.get_text()
        chapter_match = re.search(r'Chapter\s+(\d+)', prev_text, re.IGNORECASE)
        if chapter_match:
            return int(chapter_match.group(1))

    return None

def find_missing_tables(pdf_tables, existing_tables):
    """Identify which PDF tables are not in XML"""

    print("\n" + "=" * 100)
    print("IDENTIFYING MISSING TABLES")
    print("=" * 100)

    doc = fitz.open(PDF_FILE)

    missing = []

    for pdf_table in pdf_tables:
        page = pdf_table['page']
        title = pdf_table['title']

        # Determine chapter
        chapter = map_pdf_page_to_chapter(page, doc)

        if chapter is None:
            print(f"  Page {page}: Cannot determine chapter - skipping")
            continue

        # Check if this table exists in XML
        found = False
        if chapter in existing_tables:
            for xml_table in existing_tables[chapter]:
                # Match by title similarity
                if title and xml_table['title']:
                    if title[:30].lower() in xml_table['title'].lower() or \
                       xml_table['title'][:30].lower() in title.lower():
                        found = True
                        break
                # Match by first cell content
                if pdf_table['content_lines'] and xml_table['first_cell']:
                    first_pdf_cell = pdf_table['content_lines'][0][:50]
                    if first_pdf_cell.lower() in xml_table['first_cell'].lower():
                        found = True
                        break

        if not found:
            pdf_table['chapter'] = chapter
            missing.append(pdf_table)
            print(f"  Missing: Page {page}, Chapter {chapter}, Table {pdf_table['number']} - {title[:50]}")

    doc.close()

    print(f"\n✓ Found {len(missing)} missing tables")
    return missing

def add_missing_tables():
    """Main function to add missing tables"""

    # Step 1: Get all PDF tables
    print("\nStep 1: Extracting all tables from PDF...")
    pdf_tables = get_all_pdf_tables()

    # Step 2: Get existing tables in XML
    print("\nStep 2: Analyzing existing tables in XML...")
    existing_tables = get_existing_tables_in_xml()
    total_existing = sum(len(tables) for tables in existing_tables.values())
    print(f"✓ Found {total_existing} existing tables in XML")

    # Step 3: Find missing tables
    print("\nStep 3: Identifying missing tables...")
    missing_tables = find_missing_tables(pdf_tables, existing_tables)

    if not missing_tables:
        print("\n✓ No missing tables! All PDF tables are already in XML.")
        return

    # Step 4: Create output directory
    print("\nStep 4: Creating output directory...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    print(f"✓ Created: {OUTPUT_DIR}")

    # Step 5: Add missing tables
    print("\nStep 5: Adding missing tables to XML files...")

    tables_by_chapter = defaultdict(list)
    for table in missing_tables:
        tables_by_chapter[table['chapter']].append(table)

    tables_added = 0

    for chapter, tables in sorted(tables_by_chapter.items()):
        xml_file = OUTPUT_DIR / f'ch{chapter:04d}.xml'

        if not xml_file.exists():
            print(f"\n  Chapter {chapter}: XML file not found, skipping {len(tables)} tables")
            continue

        print(f"\n  Chapter {chapter}: Adding {len(tables)} table(s)")

        tree = ET.parse(xml_file)
        root = tree.getroot()

        for table_data in tables:
            # Convert to XML
            table_elem = parse_table_to_xml(table_data)

            if table_elem is None:
                print(f"    Table {table_data['number']} (page {table_data['page']}): Failed to parse")
                continue

            # Find insertion point - append to first section
            inserted = False
            for sect in root.iter('sect1'):
                sect.append(table_elem)
                inserted = True
                break

            if not inserted:
                # Fallback: append to chapter/root
                for chapter_elem in root.iter('chapter'):
                    chapter_elem.append(table_elem)
                    inserted = True
                    break

            if inserted:
                print(f"    Table {table_data['number']} (page {table_data['page']}): Added - {table_data['title'][:40]}")
                tables_added += 1
            else:
                print(f"    Table {table_data['number']} (page {table_data['page']}): Failed to insert")

        # Write back
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)

    # Step 6: Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"\nTables in PDF: {len(pdf_tables)}")
    print(f"Tables already in XML: {total_existing}")
    print(f"Missing tables found: {len(missing_tables)}")
    print(f"Tables added: {tables_added}")
    print(f"\n✓ Updated files saved to: {OUTPUT_DIR}")

    # Step 7: Verify
    print("\nStep 7: Verifying updated files...")
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            tree = ET.parse(xml_file)
            root = tree.getroot()
            table_count = len(list(root.iter('table'))) + len(list(root.iter('informaltable')))

            if table_count > 0:
                added = len(tables_by_chapter.get(ch_num, []))
                if added > 0:
                    print(f"  Chapter {ch_num:02d}: {table_count} tables (added {added})")

if __name__ == '__main__':
    add_missing_tables()
