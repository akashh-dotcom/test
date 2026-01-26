#!/usr/bin/env python3
"""
Comprehensive scan of entire PDF to count and locate all tables.
Analyzes all 1,019 pages.
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from collections import defaultdict

PDF_FILE = Path('/home/user/test/9780989163286.pdf')

def detect_tables_on_page(page, page_num):
    """
    Detect tables on a page using multiple methods:
    1. Look for "Table X" labels
    2. Detect grid-like text structures
    3. Find multi-column aligned text
    """
    tables_found = []

    text = page.get_text()

    # Method 1: Look for explicit "Table" labels
    table_labels = re.findall(r'Table\s+(\d+)[\.:]?\s+([^\n]{0,100})', text, re.IGNORECASE)

    for table_num, title in table_labels:
        tables_found.append({
            'page': page_num,
            'type': 'labeled',
            'number': table_num,
            'title': title.strip()
        })

    # Method 2: Look for tabular data patterns
    # Check for multiple rows with consistent column separators
    lines = text.split('\n')

    # Look for patterns like:
    # - Multiple consecutive lines with 2+ tab/space-separated columns
    # - Headers followed by data rows
    # - Lines with similar spacing patterns

    in_table = False
    table_lines = []
    table_start_line = 0

    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            if in_table and len(table_lines) >= 3:
                # End of potential table
                tables_found.append({
                    'page': page_num,
                    'type': 'detected',
                    'lines': len(table_lines),
                    'start_line': table_start_line,
                    'sample': table_lines[0][:60] if table_lines else ''
                })
            in_table = False
            table_lines = []
            continue

        # Check if line looks like table content
        # Multiple spaces or tabs suggest columns
        parts = re.split(r'\s{2,}|\t+', line.strip())

        if len(parts) >= 2:
            if not in_table:
                in_table = True
                table_start_line = i
                table_lines = []
            table_lines.append(line)
        else:
            if in_table and len(table_lines) >= 3:
                tables_found.append({
                    'page': page_num,
                    'type': 'detected',
                    'lines': len(table_lines),
                    'start_line': table_start_line,
                    'sample': table_lines[0][:60] if table_lines else ''
                })
            in_table = False
            table_lines = []

    # Check for remaining table at end
    if in_table and len(table_lines) >= 3:
        tables_found.append({
            'page': page_num,
            'type': 'detected',
            'lines': len(table_lines),
            'start_line': table_start_line,
            'sample': table_lines[0][:60] if table_lines else ''
        })

    return tables_found

def scan_entire_pdf():
    """Scan all pages in PDF for tables"""

    print("=" * 100)
    print("COMPREHENSIVE PDF TABLE SCAN")
    print("=" * 100)
    print(f"\nScanning: {PDF_FILE}")

    doc = fitz.open(PDF_FILE)
    total_pages = len(doc)

    print(f"Total pages: {total_pages:,}")
    print("\nScanning all pages for tables...")
    print("(This will take a few minutes...)\n")

    all_tables = []
    labeled_tables = []
    pages_with_tables = set()

    # Scan each page
    for page_num in range(total_pages):
        if (page_num + 1) % 100 == 0:
            print(f"  Progress: {page_num + 1}/{total_pages} pages ({(page_num+1)*100/total_pages:.1f}%)")

        page = doc[page_num]
        tables = detect_tables_on_page(page, page_num + 1)

        if tables:
            all_tables.extend(tables)
            pages_with_tables.add(page_num + 1)

            # Separate labeled tables
            for table in tables:
                if table['type'] == 'labeled':
                    labeled_tables.append(table)

    doc.close()

    print(f"\n✓ Scan complete!\n")

    # Analysis
    print("=" * 100)
    print("RESULTS")
    print("=" * 100)

    print(f"\nLabeled Tables (explicit 'Table X' labels):")
    print(f"  Total: {len(labeled_tables)}")

    if labeled_tables:
        print(f"\n  Labeled tables by page:")
        for table in sorted(labeled_tables, key=lambda x: x['page']):
            title_preview = table['title'][:60] + "..." if len(table['title']) > 60 else table['title']
            print(f"    Page {table['page']:4d}: Table {table['number']:>3s} - {title_preview}")

    print(f"\nAll Detected Table Regions:")
    print(f"  Total detected regions: {len(all_tables)}")
    print(f"  Pages with tables: {len(pages_with_tables)}")

    # Group by chapter (approximate)
    # Look for chapter markers in the pages
    print(f"\n  Pages with labeled tables:")
    labeled_pages = sorted(set(t['page'] for t in labeled_tables))

    # Show in groups of 10
    for i in range(0, len(labeled_pages), 10):
        pages_group = labeled_pages[i:i+10]
        print(f"    {', '.join(str(p) for p in pages_group)}")

    # Deduplicate detected tables (same page)
    tables_by_page = defaultdict(list)
    for table in all_tables:
        tables_by_page[table['page']].append(table)

    print(f"\n  Table density:")
    print(f"    Pages with 1 table: {sum(1 for p in tables_by_page if len(tables_by_page[p]) == 1)}")
    print(f"    Pages with 2+ tables: {sum(1 for p in tables_by_page if len(tables_by_page[p]) >= 2)}")

    # Show first 20 labeled tables
    if labeled_tables:
        print(f"\n  First 20 labeled tables:")
        print(f"  {'Page':<6} {'Table#':<8} {'Title'}")
        print(f"  {'-'*80}")
        for table in sorted(labeled_tables, key=lambda x: x['page'])[:20]:
            title = table['title'][:60]
            print(f"  {table['page']:<6d} Table {table['number']:<3s} {title}")

    # Final count
    print("\n" + "=" * 100)
    print("FINAL COUNT")
    print("=" * 100)

    # Count unique labeled tables
    unique_labeled = {}
    for table in labeled_tables:
        key = (table['page'], table['number'])
        if key not in unique_labeled:
            unique_labeled[key] = table

    print(f"\nTotal Labeled Tables (Table 1, Table 2, etc.): {len(unique_labeled)}")
    print(f"Pages with labeled tables: {len(set(t['page'] for t in labeled_tables))}")
    print(f"Total pages scanned: {total_pages:,}")

    # Table numbering
    table_numbers = sorted(set(int(t['number']) for t in labeled_tables if t['number'].isdigit()))
    if table_numbers:
        print(f"\nTable numbers found: {min(table_numbers)} to {max(table_numbers)}")
        print(f"Range: {len(table_numbers)} unique table numbers")

    print("\n" + "=" * 100)

    return {
        'labeled_tables': labeled_tables,
        'unique_labeled': unique_labeled,
        'all_tables': all_tables,
        'pages_with_tables': pages_with_tables,
        'total_pages': total_pages
    }

if __name__ == '__main__':
    results = scan_entire_pdf()

    # Save detailed results
    print("\nSaving detailed results to: pdf_table_scan_results.txt")
    with open('pdf_table_scan_results.txt', 'w') as f:
        f.write("DETAILED TABLE LISTING\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"Total labeled tables: {len(results['unique_labeled'])}\n\n")

        for table in sorted(results['labeled_tables'], key=lambda x: x['page']):
            f.write(f"Page {table['page']:4d}: Table {table['number']:>3s} - {table['title']}\n")

    print("✓ Results saved!")
