#!/usr/bin/env python3
"""
Comprehensive table comparison between 9780989163286.pdf and final_output_tables/ XML files.
Extracts tables from PDF and compares structure and content with XML tables.
"""

import os
import re
import pdfplumber
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# Constants
PDF_FILE = Path('/home/user/test/9780989163286.pdf')
FINAL_OUTPUT_DIR = Path('/home/user/test/final_output_tables')

def extract_tables_from_xml(xml_file):
    """Extract all tables from XML file with detailed structure"""
    tables = []

    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Find all table elements
        for table in root.iter('table'):
            table_data = {
                'id': table.get('id', 'no-id'),
                'file': xml_file.name,
                'title': '',
                'rows': 0,
                'cols': 0,
                'cells': 0,
                'headers': [],
                'all_rows': []
            }

            # Get title
            title_elem = table.find('.//title')
            if title_elem is not None and title_elem.text:
                table_data['title'] = title_elem.text.strip()

            # Analyze tgroup
            tgroup = table.find('.//tgroup')
            if tgroup is not None:
                table_data['cols'] = int(tgroup.get('cols', 0))

                # Get headers from thead
                thead = tgroup.find('thead')
                if thead is not None:
                    header_row = thead.find('.//row')
                    if header_row is not None:
                        for entry in header_row.findall('entry'):
                            text = ''.join(entry.itertext()).strip()
                            table_data['headers'].append(text)

                # Get all body rows
                tbody = tgroup.find('tbody')
                if tbody is not None:
                    rows = tbody.findall('row')
                    table_data['rows'] = len(rows)

                    for row in rows:
                        row_data = []
                        for entry in row.findall('entry'):
                            text = ''.join(entry.itertext()).strip()
                            row_data.append(text)
                        table_data['all_rows'].append(row_data)

                    # Count total cells
                    for row in rows:
                        table_data['cells'] += len(row.findall('entry'))

            tables.append(table_data)

        # Also check for informal tables
        for table in root.iter('informaltable'):
            table_data = {
                'id': table.get('id', 'no-id'),
                'file': xml_file.name,
                'title': '(informal table)',
                'rows': 0,
                'cols': 0,
                'cells': 0,
                'headers': [],
                'all_rows': []
            }

            tgroup = table.find('.//tgroup')
            if tgroup is not None:
                table_data['cols'] = int(tgroup.get('cols', 0))

                tbody = tgroup.find('tbody')
                if tbody is not None:
                    rows = tbody.findall('row')
                    table_data['rows'] = len(rows)

                    for row in rows:
                        row_data = []
                        for entry in row.findall('entry'):
                            text = ''.join(entry.itertext()).strip()
                            row_data.append(text)
                        table_data['all_rows'].append(row_data)

                    for row in rows:
                        table_data['cells'] += len(row.findall('entry'))

            tables.append(table_data)

    except Exception as e:
        print(f"Error processing {xml_file}: {e}")

    return tables

def extract_tables_from_pdf(pdf_file, start_page=1, end_page=None):
    """Extract all tables from PDF using pdfplumber"""
    all_tables = []

    print(f"Opening PDF: {pdf_file}")

    try:
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            end_page = end_page or total_pages

            print(f"Total pages in PDF: {total_pages}")
            print(f"Extracting tables from pages {start_page} to {end_page}...")

            for page_num in range(start_page - 1, min(end_page, total_pages)):
                page = pdf.pages[page_num]
                tables = page.extract_tables()

                if tables:
                    print(f"  Page {page_num + 1}: Found {len(tables)} table(s)")

                    for table_idx, table in enumerate(tables):
                        if table and len(table) > 0:
                            # Analyze table structure
                            table_data = {
                                'page': page_num + 1,
                                'table_num': table_idx + 1,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0,
                                'cells': sum(len(row) for row in table),
                                'headers': table[0] if table else [],
                                'all_rows': table,
                                'raw_table': table
                            }

                            all_tables.append(table_data)

    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

    return all_tables

def find_matching_tables(xml_table, pdf_tables, threshold=0.5):
    """Find PDF tables that might match an XML table based on structure and content"""
    matches = []

    for pdf_table in pdf_tables:
        score = 0.0
        max_score = 0.0

        # Compare dimensions
        if abs(xml_table['rows'] - pdf_table['rows']) <= 2:
            score += 1.0
        max_score += 1.0

        if abs(xml_table['cols'] - pdf_table['cols']) <= 1:
            score += 1.0
        max_score += 1.0

        # Compare headers
        if xml_table['headers'] and pdf_table['headers']:
            header_matches = 0
            for xml_header in xml_table['headers']:
                for pdf_header in pdf_table['headers']:
                    if pdf_header and xml_header.lower() in pdf_header.lower():
                        header_matches += 1
                        break
            if len(xml_table['headers']) > 0:
                score += (header_matches / len(xml_table['headers'])) * 2.0
            max_score += 2.0

        # Compare first row content (if not headers)
        if xml_table['all_rows'] and pdf_table['all_rows'] and len(pdf_table['all_rows']) > 1:
            xml_first = xml_table['all_rows'][0] if xml_table['all_rows'] else []
            pdf_first = pdf_table['all_rows'][1] if len(pdf_table['all_rows']) > 1 else []

            content_matches = 0
            for xml_cell in xml_first[:3]:  # Check first 3 cells
                for pdf_cell in pdf_first[:3]:
                    if pdf_cell and xml_cell and len(xml_cell) > 3 and xml_cell[:10].lower() in str(pdf_cell).lower():
                        content_matches += 1
                        break
            if xml_first:
                score += (content_matches / min(3, len(xml_first))) * 2.0
            max_score += 2.0

        # Calculate match percentage
        if max_score > 0:
            match_pct = score / max_score
            if match_pct >= threshold:
                matches.append({
                    'pdf_table': pdf_table,
                    'score': match_pct,
                    'page': pdf_table['page']
                })

    # Sort by score descending
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def analyze_and_compare():
    """Main analysis function"""

    print("=" * 100)
    print("TABLE COMPARISON: final_output_tables/ XML vs 9780989163286.pdf")
    print("=" * 100)

    # Step 1: Extract tables from XML files
    print("\n1. Extracting tables from final_output_tables/ XML files...")
    xml_tables_by_chapter = {}
    xml_files = sorted(FINAL_OUTPUT_DIR.glob('ch*.xml'))

    for xml_file in xml_files:
        ch_num_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_num_match:
            ch_num = int(ch_num_match.group(1))
            tables = extract_tables_from_xml(xml_file)
            if tables:
                xml_tables_by_chapter[ch_num] = tables
                print(f"  Chapter {ch_num}: {len(tables)} table(s)")

    total_xml_tables = sum(len(tables) for tables in xml_tables_by_chapter.values())
    print(f"\nTotal XML tables found: {total_xml_tables}")

    # Step 2: Extract tables from PDF
    print("\n2. Extracting tables from PDF...")
    print("   (This may take a few minutes for a large PDF...)")
    pdf_tables = extract_tables_from_pdf(PDF_FILE)

    print(f"\nTotal PDF tables found: {len(pdf_tables)}")

    # Step 3: Compare tables
    print("\n" + "=" * 100)
    print("COMPARISON RESULTS")
    print("=" * 100)

    print(f"\nSummary:")
    print(f"  XML tables: {total_xml_tables}")
    print(f"  PDF tables: {len(pdf_tables)}")
    print(f"  Difference: {len(pdf_tables) - total_xml_tables}")

    # Step 4: Try to match XML tables to PDF tables
    print("\n" + "=" * 100)
    print("MATCHING XML TABLES TO PDF TABLES")
    print("=" * 100)

    for ch_num, xml_tables in sorted(xml_tables_by_chapter.items()):
        print(f"\nChapter {ch_num}: {len(xml_tables)} XML table(s)")

        for idx, xml_table in enumerate(xml_tables, 1):
            print(f"\n  XML Table {idx}:")
            print(f"    File: {xml_table['file']}")
            print(f"    Title: {xml_table['title']}")
            print(f"    Dimensions: {xml_table['rows']} rows × {xml_table['cols']} cols = {xml_table['cells']} cells")

            if xml_table['headers']:
                print(f"    Headers: {', '.join(xml_table['headers'][:3])}{'...' if len(xml_table['headers']) > 3 else ''}")

            # Find matching PDF tables
            matches = find_matching_tables(xml_table, pdf_tables, threshold=0.4)

            if matches:
                print(f"\n    Potential PDF matches:")
                for match_idx, match in enumerate(matches[:3], 1):  # Show top 3 matches
                    pdf_t = match['pdf_table']
                    print(f"      Match {match_idx}: Page {pdf_t['page']}, {pdf_t['rows']}×{pdf_t['cols']} ({match['score']:.1%} confidence)")
            else:
                print(f"\n    ⚠️  No matching PDF table found")

    # Step 5: List PDF tables by page
    print("\n" + "=" * 100)
    print("PDF TABLES BY PAGE")
    print("=" * 100)

    tables_by_page = defaultdict(list)
    for table in pdf_tables:
        tables_by_page[table['page']].append(table)

    for page in sorted(tables_by_page.keys())[:50]:  # Show first 50 pages
        tables = tables_by_page[page]
        print(f"\nPage {page}: {len(tables)} table(s)")
        for idx, table in enumerate(tables, 1):
            print(f"  Table {idx}: {table['rows']}×{table['cols']} ({table['cells']} cells)")
            if table['headers'] and table['headers'][0]:
                preview = ', '.join(str(h)[:30] for h in table['headers'][:2] if h)
                print(f"    Headers: {preview}")

    if len(tables_by_page) > 50:
        print(f"\n... and {len(tables_by_page) - 50} more pages with tables")

    # Step 6: Detailed statistics
    print("\n" + "=" * 100)
    print("DETAILED STATISTICS")
    print("=" * 100)

    print("\nXML Tables:")
    print(f"  Total chapters with tables: {len(xml_tables_by_chapter)}")
    for ch_num, tables in sorted(xml_tables_by_chapter.items()):
        total_cells = sum(t['cells'] for t in tables)
        print(f"  Chapter {ch_num}: {len(tables)} table(s), {total_cells} cells")

    print("\nPDF Tables:")
    print(f"  Total pages with tables: {len(tables_by_page)}")
    print(f"  Total tables: {len(pdf_tables)}")
    print(f"  Total cells: {sum(t['cells'] for t in pdf_tables)}")

    if pdf_tables:
        avg_rows = sum(t['rows'] for t in pdf_tables) / len(pdf_tables)
        avg_cols = sum(t['cols'] for t in pdf_tables) / len(pdf_tables)
        max_table = max(pdf_tables, key=lambda t: t['cells'])

        print(f"  Average rows per table: {avg_rows:.1f}")
        print(f"  Average columns per table: {avg_cols:.1f}")
        print(f"  Largest table: {max_table['rows']}×{max_table['cols']} on page {max_table['page']}")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

    return {
        'xml_tables': xml_tables_by_chapter,
        'pdf_tables': pdf_tables,
        'tables_by_page': dict(tables_by_page)
    }

if __name__ == '__main__':
    results = analyze_and_compare()
