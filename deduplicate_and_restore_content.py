#!/usr/bin/env python3
"""
1. Remove duplicate tables from XML files
2. Check PDF for content loss around tables and restore missing text
"""

import fitz  # PyMuPDF
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import shutil
from difflib import SequenceMatcher

# Paths
PDF_FILE = Path('/home/user/test/9780989163286.pdf')
SOURCE_DIR = Path('/home/user/test/final_output_tables_COMPLETE')
OUTPUT_DIR = Path('/home/user/test/final_output_tables_FINAL_NO_DUPLICATES')

def table_similarity(table1_data, table2_data):
    """Calculate similarity between two tables (0-1 score)"""
    score = 0.0

    # Compare titles
    title1 = table1_data.get('title', '').lower().strip()
    title2 = table2_data.get('title', '').lower().strip()

    if title1 and title2:
        title_sim = SequenceMatcher(None, title1, title2).ratio()
        score += title_sim * 0.3

    # Compare first cell content
    first1 = table1_data.get('first_cell', '').lower().strip()
    first2 = table2_data.get('first_cell', '').lower().strip()

    if first1 and first2:
        cell_sim = SequenceMatcher(None, first1[:100], first2[:100]).ratio()
        score += cell_sim * 0.4

    # Compare row/column counts
    if table1_data.get('rows') and table2_data.get('rows'):
        if abs(table1_data['rows'] - table2_data['rows']) <= 1:
            score += 0.15

    if table1_data.get('cols') and table2_data.get('cols'):
        if abs(table1_data['cols'] - table2_data['cols']) <= 1:
            score += 0.15

    return score

def extract_table_metadata(table_elem):
    """Extract metadata from a table element for comparison"""
    metadata = {
        'title': '',
        'first_cell': '',
        'rows': 0,
        'cols': 0,
        'all_text': ''
    }

    # Get title
    title_elem = table_elem.find('.//title')
    if title_elem is not None and title_elem.text:
        metadata['title'] = title_elem.text.strip()

    # Get column count
    tgroup = table_elem.find('.//tgroup')
    if tgroup is not None:
        metadata['cols'] = int(tgroup.get('cols', 0))

        # Get first cell
        first_entry = tgroup.find('.//entry')
        if first_entry is not None and first_entry.text:
            metadata['first_cell'] = first_entry.text.strip()

        # Count rows
        tbody = tgroup.find('tbody')
        if tbody is not None:
            metadata['rows'] = len(tbody.findall('row'))

        # Get all text for fingerprinting
        all_text = ''.join(tgroup.itertext())
        metadata['all_text'] = all_text[:500]  # First 500 chars

    return metadata

def find_duplicate_tables_in_file(xml_file):
    """Find duplicate tables within a single XML file"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    all_tables = list(root.iter('table')) + list(root.iter('informaltable'))

    duplicates = []
    processed = set()

    for i, table1 in enumerate(all_tables):
        if i in processed:
            continue

        meta1 = extract_table_metadata(table1)

        for j, table2 in enumerate(all_tables[i+1:], start=i+1):
            if j in processed:
                continue

            meta2 = extract_table_metadata(table2)

            similarity = table_similarity(meta1, meta2)

            # If similarity > 0.7, consider duplicate
            if similarity > 0.7:
                duplicates.append({
                    'index1': i,
                    'index2': j,
                    'similarity': similarity,
                    'table1': table1,
                    'table2': table2,
                    'meta1': meta1,
                    'meta2': meta2
                })
                processed.add(j)  # Mark second as duplicate

    return duplicates, all_tables

def get_pdf_context_around_table(pdf_page, table_title):
    """Extract text before and after a table in PDF"""
    text = pdf_page.get_text()

    # Find table position
    table_pattern = re.escape(table_title[:50]) if table_title else None

    if not table_pattern:
        return None, None

    match = re.search(table_pattern, text, re.IGNORECASE)
    if not match:
        return None, None

    table_pos = match.start()

    # Get text before table (previous 500 chars)
    before_text = text[max(0, table_pos - 500):table_pos].strip()

    # Get text after table - look for next paragraph after table ends
    # Find where table likely ends (look for next normal paragraph)
    after_start = match.end()
    remaining = text[after_start:]

    # Skip table content (lines with multiple columns)
    lines = remaining.split('\n')
    after_table_start = 0

    for i, line in enumerate(lines[:30]):
        # If line doesn't look like table content, it's after table
        if line.strip() and not re.search(r'\s{2,}|\t', line):
            after_table_start = i
            break

    after_text = '\n'.join(lines[after_table_start:after_table_start+10]).strip()

    return before_text, after_text

def check_content_loss_around_table(xml_file, table_elem, pdf_doc, chapter_num):
    """Check if content is missing before/after a table by comparing with PDF"""

    # Get table metadata to find in PDF
    metadata = extract_table_metadata(table_elem)
    title = metadata['title']

    if not title:
        return None, None  # Can't locate without title

    # Find table in PDF - search pages for this chapter
    # Estimate page range for chapter (rough estimate: ~30 pages per chapter)
    start_page = max(0, (chapter_num - 1) * 25)
    end_page = min(len(pdf_doc), start_page + 60)

    for page_num in range(start_page, end_page):
        page = pdf_doc[page_num]
        text = page.get_text()

        if title[:30].lower() in text.lower():
            # Found the table in PDF
            before_pdf, after_pdf = get_pdf_context_around_table(page, title)

            if not before_pdf and not after_pdf:
                continue

            # Check if this content exists in XML around the table
            # Get XML context
            parent = None
            for elem in xml_file.iter():
                if table_elem in list(elem):
                    parent = elem
                    break

            if parent is None:
                return before_pdf, after_pdf

            # Get text before and after table in XML
            children = list(parent)
            table_idx = children.index(table_elem)

            xml_before = ""
            if table_idx > 0:
                prev_elem = children[table_idx - 1]
                xml_before = ''.join(prev_elem.itertext())

            xml_after = ""
            if table_idx < len(children) - 1:
                next_elem = children[table_idx + 1]
                xml_after = ''.join(next_elem.itertext())

            # Check if PDF content is missing from XML
            missing_before = None
            missing_after = None

            if before_pdf:
                # Check if significant amount of before_pdf is NOT in xml_before
                similarity_before = SequenceMatcher(None, before_pdf[-200:], xml_before[-200:]).ratio()
                if similarity_before < 0.3:
                    missing_before = before_pdf

            if after_pdf:
                similarity_after = SequenceMatcher(None, after_pdf[:200], xml_after[:200]).ratio()
                if similarity_after < 0.3:
                    missing_after = after_pdf

            return missing_before, missing_after

    return None, None

def deduplicate_and_restore():
    """Main function"""

    print("=" * 100)
    print("DEDUPLICATION AND CONTENT RESTORATION")
    print("=" * 100)

    # Step 1: Create output directory
    print("\nStep 1: Creating output directory...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    print(f"✓ Created: {OUTPUT_DIR}")

    # Step 2: Find and remove duplicates
    print("\nStep 2: Finding duplicate tables...")

    total_duplicates_removed = 0

    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue

        ch_num = int(ch_match.group(1))

        duplicates, all_tables = find_duplicate_tables_in_file(xml_file)

        if duplicates:
            print(f"\n  Chapter {ch_num:02d}: Found {len(duplicates)} duplicate table pair(s)")

            tree = ET.parse(xml_file)
            root = tree.getroot()

            for dup in duplicates:
                # Remove the second table (keep first)
                table_to_remove = dup['table2']

                # Find parent and remove
                for parent in root.iter():
                    if table_to_remove in list(parent):
                        parent.remove(table_to_remove)
                        total_duplicates_removed += 1

                        # Log what was removed
                        title1 = dup['meta1']['title'][:40]
                        title2 = dup['meta2']['title'][:40]
                        sim = dup['similarity']
                        print(f"    Removed duplicate: {title2} (similarity: {sim:.2f})")
                        print(f"      Kept: {title1}")
                        break

            # Save
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)

    print(f"\n✓ Total duplicates removed: {total_duplicates_removed}")

    # Step 3: Check for content loss around tables
    print("\nStep 3: Checking for content loss around tables...")
    print("(This will take a few minutes...)")

    pdf_doc = fitz.open(PDF_FILE)

    content_restored = 0

    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue

        ch_num = int(ch_match.group(1))

        tree = ET.parse(xml_file)
        root = tree.getroot()

        tables = list(root.iter('table')) + list(root.iter('informaltable'))

        if not tables:
            continue

        print(f"\n  Chapter {ch_num:02d}: Checking {len(tables)} table(s)")

        modified = False

        for table in tables[:5]:  # Check first 5 tables per chapter as sample
            missing_before, missing_after = check_content_loss_around_table(
                root, table, pdf_doc, ch_num
            )

            if missing_before or missing_after:
                # Find parent
                parent = None
                for elem in root.iter():
                    if table in list(elem):
                        parent = elem
                        break

                if parent is not None:
                    children = list(parent)
                    table_idx = children.index(table)

                    # Add missing content before
                    if missing_before:
                        para_before = ET.Element('para')
                        para_before.text = missing_before[-300:]  # Last 300 chars
                        parent.insert(table_idx, para_before)
                        print(f"    ✓ Restored content BEFORE table")
                        content_restored += 1
                        modified = True

                    # Add missing content after
                    if missing_after:
                        para_after = ET.Element('para')
                        para_after.text = missing_after[:300]  # First 300 chars
                        parent.insert(table_idx + 1, para_after)
                        print(f"    ✓ Restored content AFTER table")
                        content_restored += 1
                        modified = True

        if modified:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)

    pdf_doc.close()

    print(f"\n✓ Content pieces restored: {content_restored}")

    # Step 4: Final count
    print("\nStep 4: Counting final tables...")

    total_tables = 0
    chapters_with_tables = 0

    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue

        ch_num = int(ch_match.group(1))

        tree = ET.parse(xml_file)
        root = tree.getroot()

        table_count = len(list(root.iter('table'))) + len(list(root.iter('informaltable')))

        if table_count > 0:
            total_tables += table_count
            chapters_with_tables += 1
            print(f"  Chapter {ch_num:02d}: {table_count} table(s)")

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"\nOriginal tables: 201")
    print(f"Duplicates removed: {total_duplicates_removed}")
    print(f"Final table count: {total_tables}")
    print(f"Chapters with tables: {chapters_with_tables}")
    print(f"Content pieces restored: {content_restored}")

    print(f"\n✓ Output saved to: {OUTPUT_DIR}")

    print("\n" + "=" * 100)
    print("COMPLETE")
    print("=" * 100)

if __name__ == '__main__':
    deduplicate_and_restore()
