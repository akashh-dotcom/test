#!/usr/bin/env python3
"""
Comprehensive table comparison across all chapters.
Compares tables between final_output_tables/ and DocBook versions.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# Paths
FINAL_OUTPUT_DIR = Path('/home/user/test/final_output_tables')
DOCBOOK_PROPER_DIR = Path('/home/user/test/docbook_proper_fixed')
DOCBOOK_SINGLE = Path('/home/user/test/docbook_single_fixed/book.9780989163286.complete.xml')

def extract_tables_from_file(xml_file):
    """Extract all tables from an XML file with detailed structure"""
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
                'frame': table.get('frame', 'none'),
                'file': xml_file.name,
                'title': '',
                'rows': 0,
                'cols': 0,
                'cells': 0,
                'headers': [],
                'sample_rows': [],
                'full_xml': ET.tostring(table, encoding='unicode')
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

                # Get body rows
                tbody = tgroup.find('tbody')
                if tbody is not None:
                    rows = tbody.findall('row')
                    table_data['rows'] = len(rows)

                    # Get sample rows (first 3)
                    for row in rows[:3]:
                        row_data = []
                        for entry in row.findall('entry'):
                            text = ''.join(entry.itertext()).strip()
                            row_data.append(text)
                        table_data['sample_rows'].append(row_data)

                    # Count total cells
                    for row in rows:
                        table_data['cells'] += len(row.findall('entry'))

            tables.append(table_data)

        # Also look for informal tables
        for table in root.iter('informaltable'):
            table_data = {
                'id': table.get('id', 'no-id'),
                'frame': table.get('frame', 'none'),
                'file': xml_file.name,
                'title': '(informal table - no title)',
                'rows': 0,
                'cols': 0,
                'cells': 0,
                'headers': [],
                'sample_rows': [],
                'full_xml': ET.tostring(table, encoding='unicode')
            }

            # Analyze tgroup
            tgroup = table.find('.//tgroup')
            if tgroup is not None:
                table_data['cols'] = int(tgroup.get('cols', 0))

                # Get body rows
                tbody = tgroup.find('tbody')
                if tbody is not None:
                    rows = tbody.findall('row')
                    table_data['rows'] = len(rows)

                    # Get sample rows (first 3)
                    for row in rows[:3]:
                        row_data = []
                        for entry in row.findall('entry'):
                            text = ''.join(entry.itertext()).strip()
                            row_data.append(text)
                        table_data['sample_rows'].append(row_data)

                    # Count total cells
                    for row in rows:
                        table_data['cells'] += len(row.findall('entry'))

            tables.append(table_data)

    except Exception as e:
        print(f"Error processing {xml_file}: {e}")

    return tables

def extract_chapter_number(filename):
    """Extract chapter number from filename"""
    match = re.search(r'ch(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def analyze_all_tables():
    """Analyze tables across all chapters"""

    print("=" * 100)
    print("COMPREHENSIVE TABLE COMPARISON - ALL CHAPTERS")
    print("=" * 100)

    # Collect tables from final_output_tables
    print("\n1. Analyzing final_output_tables/...")
    final_output_tables = {}
    xml_files = sorted(FINAL_OUTPUT_DIR.glob('ch*.xml'), key=lambda x: extract_chapter_number(x.name))

    for xml_file in xml_files:
        ch_num = extract_chapter_number(xml_file.name)
        tables = extract_tables_from_file(xml_file)
        final_output_tables[ch_num] = tables

    # Collect tables from DocBook proper fixed files
    print("2. Analyzing DocBook proper fixed files...")
    docbook_tables_by_chapter = defaultdict(list)

    if DOCBOOK_PROPER_DIR.exists():
        docbook_files = sorted(DOCBOOK_PROPER_DIR.glob('sect1.*.xml'), key=lambda x: extract_chapter_number(x.name))
        for xml_file in docbook_files:
            ch_num = extract_chapter_number(xml_file.name)
            tables = extract_tables_from_file(xml_file)
            if tables:
                docbook_tables_by_chapter[ch_num].extend(tables)

    # Also check single file if proper not found
    if not docbook_tables_by_chapter and DOCBOOK_SINGLE.exists():
        print("   (Checking DocBook single file as fallback...)")
        all_docbook_tables = extract_tables_from_file(DOCBOOK_SINGLE)

        # Group by chapter based on table ID
        for table in all_docbook_tables:
            table_id = table['id']
            match = re.search(r'ch(\d+)', table_id)
            if match:
                ch_num = int(match.group(1))
                docbook_tables_by_chapter[ch_num].append(table)

    # Summary statistics
    total_final = sum(len(tables) for tables in final_output_tables.values())
    total_docbook = sum(len(tables) for tables in docbook_tables_by_chapter.values())

    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)
    print(f"final_output_tables/ total tables: {total_final}")
    print(f"DocBook version total tables: {total_docbook}")
    print(f"Difference: {total_docbook - total_final} tables")

    # Chapter-by-chapter comparison
    print("\n" + "=" * 100)
    print("CHAPTER-BY-CHAPTER TABLE COUNT")
    print("=" * 100)
    print(f"{'Chapter':<10} {'final_output':<15} {'DocBook':<15} {'Difference':<15} {'Status'}")
    print("-" * 100)

    all_chapters = sorted(set(list(final_output_tables.keys()) + list(docbook_tables_by_chapter.keys())))

    for ch_num in all_chapters:
        final_count = len(final_output_tables.get(ch_num, []))
        docbook_count = len(docbook_tables_by_chapter.get(ch_num, []))
        diff = docbook_count - final_count

        if diff > 0:
            status = f"⚠️ DocBook has {diff} more"
        elif diff < 0:
            status = f"⚠️ final_output has {abs(diff)} more"
        else:
            status = "✓ Same count"

        print(f"Ch {ch_num:02d}      {final_count:<15d} {docbook_count:<15d} {diff:+15d} {status}")

    # Detailed table analysis
    print("\n" + "=" * 100)
    print("DETAILED TABLE ANALYSIS BY CHAPTER")
    print("=" * 100)

    for ch_num in all_chapters:
        final_tables = final_output_tables.get(ch_num, [])
        docbook_tables = docbook_tables_by_chapter.get(ch_num, [])

        if not final_tables and not docbook_tables:
            continue

        print(f"\n{'='*100}")
        print(f"CHAPTER {ch_num}")
        print(f"{'='*100}")

        # final_output_tables tables
        if final_tables:
            print(f"\n📊 final_output_tables/ch{ch_num:04d}.xml - {len(final_tables)} table(s)")
            print("-" * 100)

            for idx, table in enumerate(final_tables, 1):
                print(f"\n  Table {idx}:")
                print(f"    ID: {table['id']}")
                print(f"    Title: {table['title']}")
                print(f"    Dimensions: {table['rows']} rows × {table['cols']} columns = {table['cells']} cells")
                print(f"    Frame: {table['frame']}")

                if table['headers']:
                    print(f"    Headers ({len(table['headers'])}):")
                    for i, header in enumerate(table['headers'], 1):
                        print(f"      {i}. {header[:60]}{'...' if len(header) > 60 else ''}")

                if table['sample_rows']:
                    print(f"    Sample rows (showing first {len(table['sample_rows'])}):")
                    for row_idx, row in enumerate(table['sample_rows'], 1):
                        print(f"      Row {row_idx}:")
                        for col_idx, cell in enumerate(row, 1):
                            cell_preview = cell[:50].replace('\n', ' ')
                            print(f"        Col {col_idx}: {cell_preview}{'...' if len(cell) > 50 else ''}")
        else:
            print(f"\n📊 final_output_tables/ch{ch_num:04d}.xml - 0 tables")

        # DocBook tables
        if docbook_tables:
            print(f"\n📚 DocBook version (Chapter {ch_num}) - {len(docbook_tables)} table(s)")
            print("-" * 100)

            for idx, table in enumerate(docbook_tables, 1):
                print(f"\n  Table {idx}:")
                print(f"    ID: {table['id']}")
                print(f"    Title: {table['title']}")
                print(f"    Dimensions: {table['rows']} rows × {table['cols']} columns = {table['cells']} cells")
                print(f"    Frame: {table['frame']}")

                if table['headers']:
                    print(f"    Headers ({len(table['headers'])}):")
                    for i, header in enumerate(table['headers'], 1):
                        print(f"      {i}. {header[:60]}{'...' if len(header) > 60 else ''}")

                if table['sample_rows']:
                    print(f"    Sample rows (showing first {len(table['sample_rows'])}):")
                    for row_idx, row in enumerate(table['sample_rows'], 1):
                        print(f"      Row {row_idx}:")
                        for col_idx, cell in enumerate(row, 1):
                            cell_preview = cell[:50].replace('\n', ' ')
                            print(f"        Col {col_idx}: {cell_preview}{'...' if len(cell) > 50 else ''}")
        else:
            print(f"\n📚 DocBook version (Chapter {ch_num}) - 0 tables")

    # Find chapters with most tables
    print("\n" + "=" * 100)
    print("CHAPTERS WITH MOST TABLES")
    print("=" * 100)

    docbook_by_count = sorted(docbook_tables_by_chapter.items(), key=lambda x: len(x[1]), reverse=True)

    print("\nTop 10 chapters by table count (DocBook version):")
    print(f"{'Rank':<6} {'Chapter':<10} {'Tables':<10} {'Total Cells':<15}")
    print("-" * 50)

    for rank, (ch_num, tables) in enumerate(docbook_by_count[:10], 1):
        total_cells = sum(t['cells'] for t in tables)
        print(f"{rank:<6} Ch {ch_num:02d}     {len(tables):<10} {total_cells:<15}")

    # Identify table structure patterns
    print("\n" + "=" * 100)
    print("TABLE STRUCTURE ANALYSIS")
    print("=" * 100)

    all_docbook_tables = [t for tables in docbook_tables_by_chapter.values() for t in tables]

    if all_docbook_tables:
        # Analyze column counts
        col_counts = defaultdict(int)
        for table in all_docbook_tables:
            col_counts[table['cols']] += 1

        print("\nTable column distribution (DocBook):")
        print(f"{'Columns':<15} {'Count':<10} {'Percentage'}")
        print("-" * 50)
        for cols in sorted(col_counts.keys()):
            count = col_counts[cols]
            pct = (count / len(all_docbook_tables)) * 100
            print(f"{cols:<15} {count:<10} {pct:>6.1f}%")

        # Analyze row counts
        total_rows = sum(t['rows'] for t in all_docbook_tables)
        avg_rows = total_rows / len(all_docbook_tables)
        max_rows = max(t['rows'] for t in all_docbook_tables)
        min_rows = min(t['rows'] for t in all_docbook_tables)

        print(f"\nRow statistics (DocBook):")
        print(f"  Total rows across all tables: {total_rows}")
        print(f"  Average rows per table: {avg_rows:.1f}")
        print(f"  Maximum rows in a table: {max_rows}")
        print(f"  Minimum rows in a table: {min_rows}")

        # Find largest tables
        largest_tables = sorted(all_docbook_tables, key=lambda x: x['cells'], reverse=True)[:5]

        print(f"\nLargest tables by cell count (DocBook):")
        print(f"{'Rank':<6} {'Table ID':<30} {'Dimensions':<20} {'Cells':<10}")
        print("-" * 70)
        for rank, table in enumerate(largest_tables, 1):
            dims = f"{table['rows']}×{table['cols']}"
            print(f"{rank:<6} {table['id']:<30} {dims:<20} {table['cells']:<10}")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

    # Return data for report generation
    return {
        'final_output_tables': final_output_tables,
        'docbook_tables': docbook_tables_by_chapter,
        'total_final': total_final,
        'total_docbook': total_docbook
    }

if __name__ == '__main__':
    analyze_all_tables()
