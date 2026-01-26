#!/usr/bin/env python3
"""
Add the 97 missing tables from DocBook versions to final_output_tables XML files.
Inserts tables at appropriate positions based on content context.
"""

import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# Constants
DOCBOOK_PROPER_DIR = Path('/home/user/test/docbook_proper_fixed')
FINAL_OUTPUT_DIR = Path('/home/user/test/final_output_tables')
OUTPUT_DIR = Path('/home/user/test/final_output_tables_with_all_tables')

def extract_tables_with_context(xml_file):
    """Extract tables with surrounding context from DocBook XML"""
    tables_with_context = []

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Get all elements to find context
        all_elements = list(root.iter())

        for idx, elem in enumerate(all_elements):
            if elem.tag in ['table', 'informaltable']:
                context_before = []
                context_after = []

                # Get context before table (previous 5 elements with text)
                for i in range(max(0, idx - 20), idx):
                    prev_elem = all_elements[i]
                    text = ''.join(prev_elem.itertext()).strip()
                    if text and len(text) > 10:
                        context_before.append(text[:100])
                        if len(context_before) >= 3:
                            break

                # Get context after table
                for i in range(idx + 1, min(len(all_elements), idx + 20)):
                    next_elem = all_elements[i]
                    text = ''.join(next_elem.itertext()).strip()
                    if text and len(text) > 10:
                        context_after.append(text[:100])
                        if len(context_after) >= 2:
                            break

                # Get table XML
                table_xml = ET.tostring(elem, encoding='unicode')

                # Get table metadata
                title = ''
                title_elem = elem.find('.//title')
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()

                # Get first row content for matching
                first_row_text = []
                tgroup = elem.find('.//tgroup')
                if tgroup is not None:
                    tbody = tgroup.find('tbody')
                    if tbody is not None:
                        first_row = tbody.find('row')
                        if first_row is not None:
                            for entry in first_row.findall('entry'):
                                text = ''.join(entry.itertext()).strip()
                                if text:
                                    first_row_text.append(text[:50])

                tables_with_context.append({
                    'table_xml': table_xml,
                    'table_element': elem,
                    'title': title,
                    'context_before': context_before,
                    'context_after': context_after,
                    'first_row_text': first_row_text,
                    'file': xml_file.name
                })

    except Exception as e:
        print(f"Error processing {xml_file}: {e}")

    return tables_with_context

def find_insertion_point(final_output_xml, table_context):
    """Find the best insertion point for a table in final_output XML"""
    try:
        with open(final_output_xml, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ET.parse(final_output_xml)
        root = tree.getroot()

        # Strategy 1: Look for context before table
        best_match_score = 0
        best_insertion_point = None

        all_paras = list(root.iter('para'))

        for idx, para in enumerate(all_paras):
            para_text = ''.join(para.itertext()).strip()

            if not para_text or len(para_text) < 10:
                continue

            match_score = 0

            # Check if any context_before matches this paragraph
            for ctx in table_context['context_before']:
                if ctx[:50] in para_text or para_text[:50] in ctx:
                    match_score += 3
                elif any(word in para_text.lower() for word in ctx.lower().split()[:5]):
                    match_score += 1

            # Check for context after
            if idx + 1 < len(all_paras):
                next_para_text = ''.join(all_paras[idx + 1].itertext()).strip()
                for ctx in table_context['context_after']:
                    if ctx[:50] in next_para_text:
                        match_score += 2

            # Check for table-like content indicators
            if 'table' in para_text.lower() and len(para_text) < 100:
                match_score += 1

            if match_score > best_match_score:
                best_match_score = match_score
                best_insertion_point = idx

        return best_insertion_point, best_match_score

    except Exception as e:
        print(f"Error finding insertion point: {e}")
        return None, 0

def insert_table_into_xml(xml_file, table_element, insertion_point_idx):
    """Insert a table element at a specific position in XML"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Find the parent element and insertion position
        all_paras = list(root.iter('para'))

        if insertion_point_idx is None or insertion_point_idx >= len(all_paras):
            # Append at end of first section or chapter
            for sect in root.iter('sect1'):
                sect.append(table_element)
                return True
            for chapter in root.iter('chapter'):
                chapter.append(table_element)
                return True
            root.append(table_element)
            return True

        # Insert after the matched paragraph
        target_para = all_paras[insertion_point_idx]
        parent = None

        # Find parent of target_para
        for elem in root.iter():
            if target_para in list(elem):
                parent = elem
                break

        if parent is not None:
            # Find index of target_para in parent
            para_idx = list(parent).index(target_para)
            # Insert table after this paragraph
            parent.insert(para_idx + 1, table_element)
            return True

        return False

    except Exception as e:
        print(f"Error inserting table: {e}")
        return False

def add_tables_to_final_output():
    """Main function to add all tables"""

    print("=" * 100)
    print("ADDING TABLES FROM DOCBOOK TO final_output_tables")
    print("=" * 100)

    # Step 1: Create output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(FINAL_OUTPUT_DIR, OUTPUT_DIR)
    print(f"\n✓ Created output directory: {OUTPUT_DIR}")

    # Step 2: Extract all tables from DocBook
    print("\n1. Extracting tables from DocBook versions...")
    docbook_tables_by_chapter = defaultdict(list)

    docbook_files = sorted(DOCBOOK_PROPER_DIR.glob('sect1.*.xml'))

    for xml_file in docbook_files:
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            tables = extract_tables_with_context(xml_file)
            if tables:
                docbook_tables_by_chapter[ch_num].extend(tables)
                print(f"  Chapter {ch_num:02d}: {len(tables)} table(s)")

    total_tables = sum(len(tables) for tables in docbook_tables_by_chapter.values())
    print(f"\n✓ Total tables extracted: {total_tables}")

    # Step 3: Check existing tables in final_output
    print("\n2. Checking existing tables in final_output_tables...")
    existing_tables = {}

    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            tree = ET.parse(xml_file)
            root = tree.getroot()
            table_count = len(list(root.iter('table'))) + len(list(root.iter('informaltable')))
            if table_count > 0:
                existing_tables[ch_num] = table_count
                print(f"  Chapter {ch_num:02d}: {table_count} existing table(s)")

    # Step 4: Insert tables chapter by chapter
    print("\n3. Inserting tables into final_output_tables...")

    tables_added = 0
    tables_skipped = 0

    for ch_num in sorted(docbook_tables_by_chapter.keys()):
        tables = docbook_tables_by_chapter[ch_num]

        # Skip Chapter 9 if it already has the table
        if ch_num == 9 and ch_num in existing_tables:
            print(f"\n  Chapter {ch_num:02d}: Skipping ({existing_tables[ch_num]} table already exists)")
            tables_skipped += len(tables)
            continue

        final_xml = OUTPUT_DIR / f'ch{ch_num:04d}.xml'

        if not final_xml.exists():
            print(f"\n  Chapter {ch_num:02d}: XML file not found, skipping")
            continue

        print(f"\n  Chapter {ch_num:02d}: Processing {len(tables)} table(s)")

        for idx, table_data in enumerate(tables, 1):
            # Find insertion point
            insertion_idx, score = find_insertion_point(final_xml, table_data)

            print(f"    Table {idx}: ", end='')

            if score >= 2:  # Reasonable match found
                # Parse the table XML string back to element
                table_elem = ET.fromstring(table_data['table_xml'])

                # Insert into XML
                tree = ET.parse(final_xml)
                root = tree.getroot()

                # Find insertion point in tree
                all_paras = list(root.iter('para'))

                if insertion_idx is not None and insertion_idx < len(all_paras):
                    target_para = all_paras[insertion_idx]
                    parent = None

                    for elem in root.iter():
                        if target_para in list(elem):
                            parent = elem
                            break

                    if parent is not None:
                        para_idx = list(parent).index(target_para)
                        parent.insert(para_idx + 1, table_elem)

                        # Write back to file
                        tree.write(final_xml, encoding='utf-8', xml_declaration=True)
                        print(f"Inserted (match score: {score})")
                        tables_added += 1
                    else:
                        # Append to first section as fallback
                        for sect in root.iter('sect1'):
                            sect.append(table_elem)
                            tree.write(final_xml, encoding='utf-8', xml_declaration=True)
                            print(f"Appended to sect1 (score: {score})")
                            tables_added += 1
                            break
                else:
                    # Append to first section as fallback
                    for sect in root.iter('sect1'):
                        sect.append(table_elem)
                        tree.write(final_xml, encoding='utf-8', xml_declaration=True)
                        print(f"Appended to sect1 (no good match)")
                        tables_added += 1
                        break
            else:
                # Low score, append to end of first section
                table_elem = ET.fromstring(table_data['table_xml'])
                tree = ET.parse(final_xml)
                root = tree.getroot()

                for sect in root.iter('sect1'):
                    sect.append(table_elem)
                    tree.write(final_xml, encoding='utf-8', xml_declaration=True)
                    print(f"Appended (low match: {score})")
                    tables_added += 1
                    break

    # Step 5: Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"\nTables added: {tables_added}")
    print(f"Tables skipped (already exist): {tables_skipped}")
    print(f"Total tables in DocBook: {total_tables}")

    # Step 6: Verify
    print("\n4. Verifying updated files...")

    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            tree = ET.parse(xml_file)
            root = tree.getroot()
            table_count = len(list(root.iter('table'))) + len(list(root.iter('informaltable')))

            if table_count > 0:
                docbook_count = len(docbook_tables_by_chapter.get(ch_num, []))
                status = "✓" if table_count >= docbook_count else "⚠️"
                print(f"  Chapter {ch_num:02d}: {table_count} table(s) {status}")

    print(f"\n✓ Updated files saved to: {OUTPUT_DIR}")
    print("\n" + "=" * 100)
    print("COMPLETE")
    print("=" * 100)

if __name__ == '__main__':
    add_tables_to_final_output()
