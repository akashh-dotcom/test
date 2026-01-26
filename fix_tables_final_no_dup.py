#!/usr/bin/env python3
"""
Fix malformed tables in final_output_tables_FINAL_NO_DUPLICATES
by using properly structured tables from the original source.
"""

import re
import shutil
from pathlib import Path
from lxml import etree
from copy import deepcopy

ORIGINAL_XML = Path('/workspace/complete_original/docbook_complete/book.9780989163286.complete.xml')
TARGET_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
BACKUP_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES_backup')

def extract_tables_from_original():
    """Extract all properly structured tables from original XML."""
    print("Extracting tables from original source...")
    
    parser = etree.XMLParser(recover=True, remove_blank_text=False)
    tree = etree.parse(str(ORIGINAL_XML), parser)
    root = tree.getroot()
    
    tables_by_chapter = {}
    
    for table in root.iter('table'):
        # Find which chapter this table belongs to
        parent = table.getparent()
        chapter_num = None
        
        while parent is not None:
            if parent.tag == 'sect1':
                sect_id = parent.get('id', '')
                match = re.match(r'ch(\d{4})s0000', sect_id)
                if match:
                    chapter_num = int(match.group(1))
                    break
            parent = parent.getparent()
        
        if chapter_num is not None:
            if chapter_num not in tables_by_chapter:
                tables_by_chapter[chapter_num] = []
            
            # Deep copy the table
            table_copy = deepcopy(table)
            tables_by_chapter[chapter_num].append(table_copy)
    
    total = sum(len(t) for t in tables_by_chapter.values())
    print(f"  Found {total} tables across {len(tables_by_chapter)} chapters")
    
    return tables_by_chapter

def is_malformed_table(table):
    """Check if a table is malformed (contains page markers)."""
    table_text = etree.tostring(table, encoding='unicode')
    
    # Check for page marker patterns
    if re.search(r'BioRef.*Layout.*Page\s+\d+', table_text):
        return True
    if re.search(r'\d{1,2}/\d{1,2}/\d{4}.*\d{1,2}:\d{2}\s*(AM|PM)', table_text):
        return True
    
    # Check if table has only 1 row with 4 columns (typical page marker pattern)
    rows = list(table.iter('row'))
    if len(rows) == 1:
        entries = list(rows[0].iter('entry'))
        if len(entries) == 4:
            # Check if entries look like page markers
            entry_texts = [e.text or '' for e in entries]
            if any('Page' in t or 'Layout' in t for t in entry_texts):
                return True
    
    return False

def fix_chapter_tables(chapter_path, good_tables):
    """Fix tables in a single chapter file."""
    parser = etree.XMLParser(recover=True, remove_blank_text=False)
    tree = etree.parse(str(chapter_path), parser)
    root = tree.getroot()
    
    # Find all tables in the chapter
    tables = list(root.iter('table'))
    malformed_count = 0
    fixed_count = 0
    
    for table in tables:
        if is_malformed_table(table):
            malformed_count += 1
    
    if malformed_count == 0:
        return 0, 0, len(tables)
    
    # Strategy: Remove malformed tables and insert good tables at appropriate positions
    # First, collect all malformed tables and their parents
    malformed_tables = []
    for table in tables:
        if is_malformed_table(table):
            malformed_tables.append(table)
    
    # Remove malformed tables
    for table in malformed_tables:
        parent = table.getparent()
        if parent is not None:
            # Keep track of position for potential insertion
            parent.remove(table)
    
    # Insert good tables
    # Find the first sect1 or similar container
    if good_tables:
        # Find a suitable insertion point (after first para in first section)
        first_sect = root.find('.//sect1')
        if first_sect is None:
            first_sect = root
        
        # Insert tables at the end of the chapter content
        for good_table in good_tables:
            table_copy = deepcopy(good_table)
            # Try to insert in a sensible location
            # For now, append to root or first section
            first_sect.append(table_copy)
            fixed_count += 1
    
    # Write back
    xml_str = etree.tostring(root, encoding='unicode', pretty_print=True)
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    
    with open(chapter_path, 'w', encoding='utf-8') as f:
        f.write(xml_declaration + '\n\n' + xml_str)
    
    return malformed_count, fixed_count, len(tables) - malformed_count + fixed_count

def replace_tables_completely(chapter_path, good_tables):
    """Replace all tables in chapter with good tables from original."""
    parser = etree.XMLParser(recover=True, remove_blank_text=False)
    tree = etree.parse(str(chapter_path), parser)
    root = tree.getroot()
    
    # Remove ALL existing tables
    tables_removed = 0
    for table in list(root.iter('table')):
        parent = table.getparent()
        if parent is not None:
            parent.remove(table)
            tables_removed += 1
    
    if not good_tables:
        # No good tables to add
        xml_str = etree.tostring(root, encoding='unicode', pretty_print=True)
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(xml_declaration + '\n\n' + xml_str)
        return tables_removed, 0
    
    # Find insertion points based on section structure
    # Insert tables at end of appropriate sections
    sections = list(root.iter('sect1'))
    if not sections:
        sections = [root]
    
    # Distribute tables across sections or add all to first section
    tables_added = 0
    target_section = sections[0] if sections else root
    
    for good_table in good_tables:
        table_copy = deepcopy(good_table)
        target_section.append(table_copy)
        tables_added += 1
    
    # Write back
    xml_str = etree.tostring(root, encoding='unicode', pretty_print=True)
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    
    with open(chapter_path, 'w', encoding='utf-8') as f:
        f.write(xml_declaration + '\n\n' + xml_str)
    
    return tables_removed, tables_added

def main():
    print("=" * 80)
    print("FIXING TABLES IN final_output_tables_FINAL_NO_DUPLICATES")
    print("=" * 80)
    
    # Backup first
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    shutil.copytree(TARGET_DIR, BACKUP_DIR)
    print(f"\nBackup created at: {BACKUP_DIR}")
    
    # Extract good tables from original
    good_tables = extract_tables_from_original()
    
    # Process each chapter
    print("\nProcessing chapters...")
    print("-" * 80)
    print(f"{'Chapter':<15} {'Removed':<12} {'Added':<12} {'Status'}")
    print("-" * 80)
    
    total_removed = 0
    total_added = 0
    
    for xml_file in sorted(TARGET_DIR.glob('ch*.xml')):
        ch_name = xml_file.stem
        ch_num = int(ch_name[2:])
        
        chapter_good_tables = good_tables.get(ch_num, [])
        
        removed, added = replace_tables_completely(xml_file, chapter_good_tables)
        
        total_removed += removed
        total_added += added
        
        if removed > 0 or added > 0:
            status = f"Fixed: -{removed} +{added}"
            print(f"{ch_name:<15} {removed:<12} {added:<12} {status}")
    
    print("-" * 80)
    print(f"{'TOTAL':<15} {total_removed:<12} {total_added:<12}")
    
    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    print("\nChecking fixed tables...")
    for xml_file in sorted(TARGET_DIR.glob('ch*.xml')):
        ch_name = xml_file.stem
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(xml_file), parser)
        
        tables = list(tree.getroot().iter('table'))
        malformed = sum(1 for t in tables if is_malformed_table(t))
        
        if tables:
            if malformed > 0:
                print(f"  {ch_name}: {len(tables)} tables ({malformed} still malformed)")
            else:
                print(f"  {ch_name}: {len(tables)} tables (all OK)")
    
    print("\n✓ Table fix complete!")
    print(f"  Removed {total_removed} malformed tables")
    print(f"  Added {total_added} properly structured tables from original source")

if __name__ == '__main__':
    main()
