#!/usr/bin/env python3
"""
Fixed version: Properly remove duplicate tables
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from difflib import SequenceMatcher
import shutil

SOURCE_DIR = Path('/home/user/test/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/home/user/test/final_output_tables_FINAL_CLEANED')

def table_similarity(meta1, meta2):
    """Calculate similarity between two tables"""
    score = 0.0

    # Compare titles (weight: 30%)
    title1 = meta1.get('title', '').lower().strip()
    title2 = meta2.get('title', '').lower().strip()

    if title1 and title2 and len(title1) > 10 and len(title2) > 10:
        title_sim = SequenceMatcher(None, title1, title2).ratio()
        score += title_sim * 0.3

    # Compare first cell (weight: 40%)
    first1 = meta1.get('first_cell', '').lower().strip()
    first2 = meta2.get('first_cell', '').lower().strip()

    if first1 and first2 and len(first1) > 10 and len(first2) > 10:
        cell_sim = SequenceMatcher(None, first1[:100], first2[:100]).ratio()
        score += cell_sim * 0.4

    # Compare all text (weight: 20%)
    text1 = meta1.get('all_text', '').lower().strip()
    text2 = meta2.get('all_text', '').lower().strip()

    if text1 and text2:
        text_sim = SequenceMatcher(None, text1[:200], text2[:200]).ratio()
        score += text_sim * 0.2

    # Compare dimensions (weight: 10%)
    if meta1.get('rows') and meta2.get('rows'):
        if abs(meta1['rows'] - meta2['rows']) <= 1:
            score += 0.05

    if meta1.get('cols') and meta2.get('cols'):
        if abs(meta1['cols'] - meta2['cols']) <= 1:
            score += 0.05

    return score

def extract_table_metadata(table_elem):
    """Extract metadata from table element"""
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

    # Get tgroup info
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

        # Get all text
        all_text = ''.join(tgroup.itertext())
        metadata['all_text'] = all_text[:500]

    return metadata

def remove_duplicates():
    """Remove duplicate tables properly"""

    print("=" * 100)
    print("REMOVING DUPLICATE TABLES (FIXED)")
    print("=" * 100)

    # Create output directory
    print("\nCreating output directory...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    print(f"✓ Created: {OUTPUT_DIR}")

    total_removed = 0

    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue

        ch_num = int(ch_match.group(1))

        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Get all tables with metadata
        all_tables = []
        for table_elem in root.iter('table'):
            metadata = extract_table_metadata(table_elem)
            all_tables.append({
                'element': table_elem,
                'metadata': metadata
            })

        for table_elem in root.iter('informaltable'):
            metadata = extract_table_metadata(table_elem)
            all_tables.append({
                'element': table_elem,
                'metadata': metadata
            })

        if len(all_tables) < 2:
            continue

        # Find duplicates
        to_remove = set()

        for i in range(len(all_tables)):
            if i in to_remove:
                continue

            for j in range(i + 1, len(all_tables)):
                if j in to_remove:
                    continue

                similarity = table_similarity(
                    all_tables[i]['metadata'],
                    all_tables[j]['metadata']
                )

                # Threshold: 0.75 for duplicates
                if similarity >= 0.75:
                    to_remove.add(j)  # Remove later one

        if to_remove:
            print(f"\n  Chapter {ch_num:02d}: Found {len(to_remove)} duplicate(s)")

            # Remove duplicates
            for idx in sorted(to_remove, reverse=True):
                table_to_remove = all_tables[idx]['element']
                title = all_tables[idx]['metadata']['title'][:50]

                # Find parent and remove
                for parent in root.iter():
                    try:
                        parent.remove(table_to_remove)
                        print(f"    Removed: {title}")
                        total_removed += 1
                        break
                    except ValueError:
                        continue

            # Save
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)

    # Final count
    print("\n" + "=" * 100)
    print("FINAL TABLE COUNT")
    print("=" * 100)

    total_tables = 0

    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue

        ch_num = int(ch_match.group(1))

        tree = ET.parse(xml_file)
        root = tree.getroot()

        count = len(list(root.iter('table'))) + len(list(root.iter('informaltable')))

        if count > 0:
            total_tables += count
            print(f"  Chapter {ch_num:02d}: {count} table(s)")

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Duplicates removed: {total_removed}")
    print(f"Final table count: {total_tables}")
    print(f"\n✓ Output: {OUTPUT_DIR}")

if __name__ == '__main__':
    remove_duplicates()
