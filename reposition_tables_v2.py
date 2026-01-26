#!/usr/bin/env python3
"""
Reposition tables v2 - simpler approach.
1. Extract all tables
2. Remove all tables from XML
3. Find reference positions for each table
4. Insert tables at correct positions
"""

import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from copy import deepcopy
import shutil

SOURCE_DIR = Path('/workspace/final_output_tables_POSITIONED')
OUTPUT_DIR = Path('/workspace/final_output_tables_CORRECT_POSITIONS')

ET.register_namespace('', '')

def get_element_text(elem):
    """Get all text from an element including children."""
    text = elem.text or ''
    for child in elem:
        text += get_element_text(child)
        text += child.tail or ''
    return text

def is_bad_para(text):
    """Check if paragraph text should be removed."""
    if not text:
        return False
    text = text.strip()
    
    # BioRef metadata
    if 'BioRef' in text and 'Layout' in text:
        return True
    if re.match(r'^\d{1,3}$', text):
        return True
    return False

def is_early_misplaced_fragment(text):
    """Check if this is a misplaced fragment at chapter start."""
    if not text:
        return False
    text_stripped = text.strip()
    
    if re.search(r'\.\s*Table\s+\d+$', text_stripped):
        if len(text_stripped) < 600:
            return True
    if re.match(r'^implants\s+at\s+\d+\s*T', text_stripped, re.I):
        return True
    if re.match(r'^o$', text_stripped):
        return True
    return False

def process_chapter(xml_file, output_file):
    """Process a chapter XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0
    
    # Step 1: Extract ALL tables (keep as list to preserve order and duplicates)
    all_tables = []
    for table in root.iter('table'):
        table_copy = deepcopy(table)
        table_text = ET.tostring(table, encoding='unicode', method='text')
        
        # Try to find table number
        match = re.search(r'Table\s+(\d+)', table_text, re.I)
        table_num = int(match.group(1)) if match else None
        
        all_tables.append({
            'element': table_copy,
            'num': table_num,
            'position': len(all_tables) + 1
        })
    
    if not all_tables:
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        return 0
    
    # Assign numbers to tables without explicit numbers
    used_nums = set(t['num'] for t in all_tables if t['num'] is not None)
    for table in all_tables:
        if table['num'] is None:
            table['num'] = table['position']
    
    print(f"  Found {len(all_tables)} tables: {[t['num'] for t in all_tables]}")
    
    # Step 2: Remove all tables from tree
    def remove_tables(elem):
        children_to_remove = [c for c in elem if c.tag == 'table']
        for c in children_to_remove:
            elem.remove(c)
        for c in elem:
            remove_tables(c)
    remove_tables(root)
    
    # Step 3: Remove bad paragraphs and early fragments
    seen_main_content = False
    def clean_element(elem, in_early_section=False):
        nonlocal seen_main_content
        to_remove = []
        for i, child in enumerate(elem):
            if child.tag == 'sect1':
                title = child.find('title')
                if title is not None and title.text:
                    t = title.text.lower()
                    if any(x in t for x in ['introduction', 'background', 'physics', 'overview', 'methods']):
                        seen_main_content = True
                clean_element(child, not seen_main_content)
            elif child.tag == 'para':
                text = get_element_text(child)
                if is_bad_para(text):
                    to_remove.append(child)
                elif in_early_section and is_early_misplaced_fragment(text):
                    to_remove.append(child)
                    print(f"    Removed fragment: {text[:40]}...")
            else:
                clean_element(child, in_early_section)
        for c in to_remove:
            elem.remove(c)
    clean_element(root)
    
    # Step 4: Find best placement for each table number
    # Build a map of table_num -> list of table elements
    tables_by_num = {}
    for t in all_tables:
        num = t['num']
        if num not in tables_by_num:
            tables_by_num[num] = []
        tables_by_num[num].append(t['element'])
    
    # Find reference paragraphs for each table number
    def find_reference_para(table_num):
        """Find the paragraph that references this table number."""
        best_para = None
        best_score = -999
        
        for para in root.iter('para'):
            text = get_element_text(para)
            if re.search(rf'\bTable\s+{table_num}\b', text, re.I):
                score = 0
                lower = text.lower()
                
                # Penalize caption paragraphs
                if re.match(rf'^\s*Table\s+{table_num}\.', text.strip(), re.I):
                    score -= 50
                
                # Prefer contextual references
                if re.search(rf'table\s+{table_num}\s+(?:gives|shows|provides|presents)', lower):
                    score += 20
                if 'see table' in lower:
                    score += 15
                if len(text) > 200:
                    score += 5
                
                if score > best_score:
                    best_score = score
                    best_para = para
        
        return best_para
    
    placements = {}  # para -> list of table elements to insert after it
    unplaced = []
    
    for num in sorted(tables_by_num.keys()):
        para = find_reference_para(num)
        if para is not None:
            if para not in placements:
                placements[para] = []
            placements[para].extend(tables_by_num[num])
            print(f"    Will place Table {num} ({len(tables_by_num[num])} table(s)) after reference")
        else:
            unplaced.extend(tables_by_num[num])
            print(f"    Will append Table {num} ({len(tables_by_num[num])} table(s)) at end")
    
    # Step 5: Insert tables after their reference paragraphs
    # We need to be careful about modifying the tree while iterating
    # So we'll use a marker-based approach
    
    # First, mark which paras need tables inserted after them
    para_to_tables = {}
    for para, tables in placements.items():
        # Create a unique id for this para
        para_id = id(para)
        para_to_tables[para_id] = tables
    
    def insert_tables_recursive(elem):
        # Process this element's children
        i = 0
        while i < len(elem):
            child = elem[i]
            
            # First recurse into child
            if len(child) > 0:
                insert_tables_recursive(child)
            
            # Check if we need to insert tables after this child
            if id(child) in para_to_tables:
                tables_to_insert = para_to_tables[id(child)]
                # Insert tables after current position
                for j, table_elem in enumerate(tables_to_insert):
                    elem.insert(i + 1 + j, table_elem)
                # Move index past the inserted tables
                i += len(tables_to_insert)
            
            i += 1
    
    insert_tables_recursive(root)
    
    # Step 6: Append unplaced tables at end
    if unplaced:
        last_sect = None
        for sect in root.iter('sect1'):
            last_sect = sect
        target = last_sect if last_sect is not None else root
        for table_elem in unplaced:
            target.append(table_elem)
    
    # Write output
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return len(all_tables)

def main():
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = 0
    for xml_file in sorted(SOURCE_DIR.glob('*.xml')):
        if xml_file.name == 'Book.XML':
            continue
        print(f"\nProcessing {xml_file.name}...")
        output_file = OUTPUT_DIR / xml_file.name
        total += process_chapter(xml_file, output_file)
    
    # Copy Book.XML
    book_src = SOURCE_DIR / 'Book.XML'
    if book_src.exists():
        print("\nCopying Book.XML...")
        with open(book_src, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'<!DOCTYPE\s+book\s+SYSTEM\s+["\'][^"\']+["\']\s*\[', '<!DOCTYPE book [', content)
        with open(OUTPUT_DIR / 'Book.XML', 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Copy multimedia
    multimedia_src = SOURCE_DIR / 'multimedia'
    if multimedia_src.exists():
        multimedia_dst = OUTPUT_DIR / 'multimedia'
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
        print("Copied multimedia folder")
    
    print(f"\n=== Summary ===")
    print(f"Total tables: {total}")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
