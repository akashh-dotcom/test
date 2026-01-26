#!/usr/bin/env python3
"""
Comprehensive table comparison between 9780989163286.pdf and final_output_tables/ XML files.
Uses PyMuPDF (fitz) for PDF processing.
"""

import os
import re
import fitz  # PyMuPDF
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
                'all_rows': [],
                'first_cell_text': []
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
                            if not table_data['first_cell_text'] and text:
                                table_data['first_cell_text'].append(text[:50])
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
                'all_rows': [],
                'first_cell_text': []
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
                            if not table_data['first_cell_text'] and text:
                                table_data['first_cell_text'].append(text[:50])
                        table_data['all_rows'].append(row_data)

                    for row in rows:
                        table_data['cells'] += len(row.findall('entry'))

            tables.append(table_data)

    except Exception as e:
        print(f"Error processing {xml_file}: {e}")

    return tables

def extract_text_blocks_from_pdf(pdf_file):
    """Extract text blocks from PDF to identify potential table regions"""
    doc = fitz.open(pdf_file)
    table_indicators = []

    print(f"Analyzing {len(doc)} pages for table patterns...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # Look for common table indicators
        # Pattern 1: Multiple rows with consistent formatting (tabs/spacing)
        lines = text.split('\n')

        # Look for chapter references
        chapter_match = re.search(r'Chapter\s+(\d+)', text, re.IGNORECASE)
        chapter_num = int(chapter_match.group(1)) if chapter_match else None

        # Pattern 2: Look for table-like structures (rows with multiple columns separated by whitespace)
        potential_tables = []
        current_table_lines = []

        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                if current_table_lines and len(current_table_lines) >= 3:
                    potential_tables.append(current_table_lines[:])
                current_table_lines = []
                continue

            # Check if line has table-like structure (multiple columns)
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 2:  # At least 2 columns
                current_table_lines.append(line.strip())
            else:
                if current_table_lines and len(current_table_lines) >= 3:
                    potential_tables.append(current_table_lines[:])
                current_table_lines = []

        if current_table_lines and len(current_table_lines) >= 3:
            potential_tables.append(current_table_lines[:])

        if potential_tables:
            table_indicators.append({
                'page': page_num + 1,
                'chapter': chapter_num,
                'num_tables': len(potential_tables),
                'tables': potential_tables
            })
            print(f"  Page {page_num + 1}: Found {len(potential_tables)} potential table(s) (Chapter {chapter_num})")

    doc.close()
    return table_indicators

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
                print(f"  Chapter {ch_num:02d}: {len(tables)} XML table(s)")

    total_xml_tables = sum(len(tables) for tables in xml_tables_by_chapter.values())
    print(f"\n✓ Total XML tables found: {total_xml_tables}")

    # Step 2: Extract table indicators from PDF
    print("\n2. Analyzing PDF for table-like structures...")
    print(f"   Opening: {PDF_FILE}")

    pdf_table_indicators = extract_text_blocks_from_pdf(PDF_FILE)

    total_pdf_table_regions = sum(t['num_tables'] for t in pdf_table_indicators)
    print(f"\n✓ Found {total_pdf_table_regions} potential table regions in PDF across {len(pdf_table_indicators)} pages")

    # Step 3: Group PDF tables by chapter
    pdf_by_chapter = defaultdict(list)
    for indicator in pdf_table_indicators:
        if indicator['chapter']:
            pdf_by_chapter[indicator['chapter']].extend(indicator['tables'])

    # Step 4: Compare
    print("\n" + "=" * 100)
    print("COMPARISON RESULTS")
    print("=" * 100)

    print(f"\n{'Chapter':<10} {'XML Tables':<15} {'PDF Table Regions':<20} {'Status'}")
    print("-" * 100)

    all_chapters = sorted(set(list(xml_tables_by_chapter.keys()) + list(pdf_by_chapter.keys())))

    for ch_num in all_chapters:
        xml_count = len(xml_tables_by_chapter.get(ch_num, []))
        pdf_count = len(pdf_by_chapter.get(ch_num, []))

        if xml_count == pdf_count:
            status = "✓ Match"
        elif xml_count > pdf_count:
            status = f"⚠️  XML has {xml_count - pdf_count} more"
        else:
            status = f"⚠️  PDF has {pdf_count - xml_count} more"

        print(f"Ch {ch_num:02d}      {xml_count:<15d} {pdf_count:<20d} {status}")

    # Step 5: Detailed analysis for Chapter 9 (the one with XML table)
    if 9 in xml_tables_by_chapter:
        print("\n" + "=" * 100)
        print("DETAILED ANALYSIS: CHAPTER 9 (Has XML Table)")
        print("=" * 100)

        xml_table = xml_tables_by_chapter[9][0]
        print(f"\nXML Table:")
        print(f"  File: {xml_table['file']}")
        print(f"  Dimensions: {xml_table['rows']} rows × {xml_table['cols']} columns")
        print(f"  Total cells: {xml_table['cells']}")
        print(f"  Headers: {xml_table['headers']}")
        if xml_table['all_rows']:
            print(f"  First row sample: {xml_table['all_rows'][0][:2]}")

        if 9 in pdf_by_chapter:
            print(f"\nPDF Table Regions in Chapter 9: {len(pdf_by_chapter[9])}")
            for idx, table in enumerate(pdf_by_chapter[9][:3], 1):
                print(f"\n  PDF Table Region {idx}:")
                print(f"    Lines: {len(table)}")
                if table:
                    print(f"    First line: {table[0][:80]}")
                    if len(table) > 1:
                        print(f"    Second line: {table[1][:80]}")

    # Step 6: Summary statistics
    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)

    print(f"\nXML Tables:")
    print(f"  Total: {total_xml_tables}")
    print(f"  Chapters with tables: {len(xml_tables_by_chapter)}")

    if xml_tables_by_chapter:
        total_xml_cells = sum(t['cells'] for tables in xml_tables_by_chapter.values() for t in tables)
        print(f"  Total cells: {total_xml_cells}")

    print(f"\nPDF Analysis:")
    print(f"  Pages with table-like structures: {len(pdf_table_indicators)}")
    print(f"  Potential table regions: {total_pdf_table_regions}")
    print(f"  Chapters identified with tables: {len(pdf_by_chapter)}")

    # List all pages with tables
    print(f"\nPages with table structures (first 20):")
    for indicator in pdf_table_indicators[:20]:
        ch_str = f"Ch {indicator['chapter']:02d}" if indicator['chapter'] else "Unknown"
        print(f"  Page {indicator['page']:3d} ({ch_str}): {indicator['num_tables']} table(s)")

    if len(pdf_table_indicators) > 20:
        print(f"  ... and {len(pdf_table_indicators) - 20} more pages")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

    print("\nNote: PDF table detection is heuristic-based and may include false positives.")
    print("For precise table extraction, manual verification is recommended.")

    return {
        'xml_tables': xml_tables_by_chapter,
        'pdf_indicators': pdf_table_indicators,
        'pdf_by_chapter': dict(pdf_by_chapter)
    }

if __name__ == '__main__':
    results = analyze_and_compare()
