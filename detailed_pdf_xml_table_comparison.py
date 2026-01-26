#!/usr/bin/env python3
"""
Detailed table comparison between PDF and XML.
Focuses on finding and comparing the Chapter 9 table.
"""

import re
import fitz  # PyMuPDF
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# Constants
PDF_FILE = Path('/home/user/test/9780989163286.pdf')
FINAL_OUTPUT_DIR = Path('/home/user/test/final_output_tables')

def extract_ch9_table_from_xml():
    """Extract the Chapter 9 table from XML"""
    xml_file = FINAL_OUTPUT_DIR / 'ch0009.xml'

    if not xml_file.exists():
        print(f"Error: {xml_file} not found")
        return None

    tree = ET.parse(xml_file)
    root = tree.getroot()

    for table in root.iter('table'):
        table_data = {
            'headers': [],
            'rows': [],
            'xml_content': ET.tostring(table, encoding='unicode')
        }

        tgroup = table.find('.//tgroup')
        if tgroup is not None:
            # Get headers
            thead = tgroup.find('thead')
            if thead is not None:
                header_row = thead.find('.//row')
                if header_row is not None:
                    for entry in header_row.findall('entry'):
                        text = ''.join(entry.itertext()).strip()
                        table_data['headers'].append(text)

            # Get rows
            tbody = tgroup.find('tbody')
            if tbody is not None:
                for row in tbody.findall('row'):
                    row_data = []
                    for entry in row.findall('entry'):
                        text = ''.join(entry.itertext()).strip()
                        row_data.append(text)
                    table_data['rows'].append(row_data)

        return table_data

    return None

def find_chapter_9_pages(pdf_file):
    """Find pages that contain Chapter 9"""
    doc = fitz.open(pdf_file)
    chapter_9_pages = []

    print(f"Searching {len(doc)} pages for Chapter 9...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # Look for "Chapter 9" heading
        if re.search(r'Chapter\s+9\b', text, re.IGNORECASE):
            chapter_9_pages.append(page_num + 1)
            print(f"  Found 'Chapter 9' on page {page_num + 1}")

        # Also look for chapter content indicators
        if re.search(r'\(137\)\s*\(1986\)', text) or re.search(r'25\s+Patients', text):
            if page_num + 1 not in chapter_9_pages:
                chapter_9_pages.append(page_num + 1)
                print(f"  Found potential Chapter 9 table content on page {page_num + 1}")

    doc.close()
    return sorted(chapter_9_pages)

def search_for_table_content_in_pdf(pdf_file, search_terms):
    """Search PDF for specific table content"""
    doc = fitz.open(pdf_file)
    results = defaultdict(list)

    print(f"\nSearching PDF for table content indicators...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        for term in search_terms:
            if term.lower() in text.lower():
                results[term].append(page_num + 1)

    doc.close()
    return dict(results)

def extract_text_from_pages(pdf_file, pages):
    """Extract full text from specific pages"""
    doc = fitz.open(pdf_file)
    page_texts = {}

    for page_num in pages:
        if 1 <= page_num <= len(doc):
            page = doc[page_num - 1]
            text = page.get_text()
            page_texts[page_num] = text

    doc.close()
    return page_texts

def analyze_table_presence():
    """Main analysis"""
    print("=" * 100)
    print("DETAILED PDF vs XML TABLE COMPARISON - CHAPTER 9 FOCUS")
    print("=" * 100)

    # Step 1: Extract XML table
    print("\n1. Extracting Chapter 9 table from XML...")
    xml_table = extract_ch9_table_from_xml()

    if not xml_table:
        print("  ✗ No table found in XML")
        return

    print(f"  ✓ Found table with {len(xml_table['headers'])} columns and {len(xml_table['rows'])} rows")
    print(f"\n  Headers:")
    for i, header in enumerate(xml_table['headers'], 1):
        print(f"    {i}. {header}")

    print(f"\n  First 3 data rows:")
    for i, row in enumerate(xml_table['rows'][:3], 1):
        print(f"    Row {i}: {row[0]}, {row[1]}")

    # Step 2: Find Chapter 9 pages in PDF
    print(f"\n2. Locating Chapter 9 in PDF...")
    ch9_pages = find_chapter_9_pages(PDF_FILE)

    if ch9_pages:
        print(f"  ✓ Chapter 9 found on {len(ch9_pages)} page(s): {ch9_pages}")
    else:
        print(f"  ⚠️  Chapter 9 pages not clearly identified")

    # Step 3: Search for table content
    print(f"\n3. Searching PDF for table content...")

    # Search for key terms from the table
    search_terms = [
        '(137) (1986)',
        '(140) 1986',
        '(46) (1987)',
        'Reference and Year of Publication',
        'Number of Subjects',
        'SAR and Duration',
        'Core Temperature',
        '25 Patients',
        'ambient temperature 20 to 24'
    ]

    found_terms = search_for_table_content_in_pdf(PDF_FILE, search_terms)

    print(f"\n  Search results:")
    for term, pages in sorted(found_terms.items()):
        if pages:
            print(f"    '{term[:40]}...': Found on page(s) {pages}")

    # Step 4: Extract text from relevant pages
    if ch9_pages:
        print(f"\n4. Analyzing Chapter 9 pages in detail...")
        page_texts = extract_text_from_pages(PDF_FILE, ch9_pages)

        for page_num, text in page_texts.items():
            print(f"\n  Page {page_num}:")
            print(f"    Total characters: {len(text)}")

            # Look for table indicators
            has_reference_header = 'reference' in text.lower() and 'publication' in text.lower()
            has_subjects_header = 'number of subjects' in text.lower() or 'subjects' in text.lower()
            has_sar_header = 'sar' in text.lower()
            has_temperature = 'temperature' in text.lower()
            has_data_rows = '(137)' in text or '(140)' in text or '(46)' in text

            print(f"    Has 'Reference' header: {has_reference_header}")
            print(f"    Has 'Subjects' header: {has_subjects_header}")
            print(f"    Has 'SAR' header: {has_sar_header}")
            print(f"    Has 'Temperature' mentions: {has_temperature}")
            print(f"    Has data row indicators: {has_data_rows}")

            # Count potential table rows (citations from 1986-1987)
            citations = re.findall(r'\(\d+\)\s*\(19\d{2}\)', text)
            if citations:
                print(f"    Potential table rows (citations): {len(citations)}")
                print(f"    Sample citations: {citations[:5]}")

    # Step 5: Summary
    print("\n" + "=" * 100)
    print("COMPARISON SUMMARY")
    print("=" * 100)

    print(f"\nXML Table (Chapter 9):")
    print(f"  Columns: {len(xml_table['headers'])}")
    print(f"  Rows: {len(xml_table['rows'])}")
    print(f"  Headers: {', '.join(xml_table['headers'][:3])}...")

    print(f"\nPDF Analysis:")
    if ch9_pages:
        print(f"  Chapter 9 location: Pages {ch9_pages}")
    else:
        print(f"  Chapter 9 location: Not clearly identified")

    print(f"\n  Content match indicators:")
    total_matches = sum(1 for pages in found_terms.values() if pages)
    print(f"    Search terms found: {total_matches}/{len(search_terms)}")

    if total_matches >= len(search_terms) * 0.5:
        print(f"    ✓ Table content appears to be present in PDF")
    else:
        print(f"    ⚠️  Table content may not be fully represented in PDF")

    # Step 6: Detailed content extraction from likely table page
    all_found_pages = set()
    for pages in found_terms.values():
        all_found_pages.update(pages)

    if all_found_pages:
        most_likely_page = max(all_found_pages, key=lambda p: sum(1 for pages in found_terms.values() if p in pages))
        print(f"\n  Most likely table location: Page {most_likely_page}")

        # Extract and display text from that page
        page_text = extract_text_from_pages(PDF_FILE, [most_likely_page])
        if most_likely_page in page_text:
            text = page_text[most_likely_page]

            print(f"\n  Content preview from page {most_likely_page}:")
            # Show first 500 chars
            preview = text[:500].replace('\n', ' ')
            print(f"    {preview}...")

            # Try to identify table structure
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            print(f"\n  Text structure analysis:")
            print(f"    Total lines: {len(lines)}")

            # Look for table-like patterns
            table_start_idx = None
            for i, line in enumerate(lines):
                if 'reference' in line.lower() and 'publication' in line.lower():
                    table_start_idx = i
                    print(f"    Potential table header at line {i}: {line[:60]}")
                    break

            if table_start_idx is not None:
                # Show next 10 lines which might be table rows
                print(f"\n  Potential table rows (lines {table_start_idx + 1} to {table_start_idx + 10}):")
                for i in range(table_start_idx + 1, min(table_start_idx + 11, len(lines))):
                    print(f"    {lines[i][:80]}")

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

if __name__ == '__main__':
    analyze_table_presence()
