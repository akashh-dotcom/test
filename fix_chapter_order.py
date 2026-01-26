#!/usr/bin/env python3
"""
Fix chapter structure by:
1. Identifying and removing ALL misplaced content between author info and main sections
2. Placing tables at their correct positions based on PDF references
"""

import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from copy import deepcopy
import shutil

SOURCE_DIR = Path('/workspace/final_output_tables_POSITIONED')
OUTPUT_DIR = Path('/workspace/final_output_tables_PDF_ORDER')

ET.register_namespace('', '')

def get_element_text(elem):
    """Get all text from an element including children."""
    text = elem.text or ''
    for child in elem:
        text += get_element_text(child)
        text += child.tail or ''
    return text

def is_main_section_title(title_text):
    """Check if this is a main content section (not author info)."""
    if not title_text:
        return False
    title_lower = title_text.lower().strip()
    
    main_sections = [
        'introduction', 'background', 'overview', 'methods', 'methodology',
        'physics', 'safety', 'discussion', 'conclusion', 'results',
        'magnetic properties', 'the mri signal', 'tissue properties',
        'key challenges', 'superconducting', 'gradient', 'rf coil',
        'references', 'acknowledgement'
    ]
    
    for section in main_sections:
        if section in title_lower:
            return True
    
    # Also check if it looks like a topic heading (all caps or specific patterns)
    if title_lower.isupper() and len(title_lower) > 5:
        return True
    
    return False

def is_author_section(sect_elem):
    """Check if this section is author information."""
    title_elem = sect_elem.find('title')
    if title_elem is None or not title_elem.text:
        return False
    
    title = title_elem.text.strip()
    
    # First check if it's a MAIN section (content section) - these are NOT author sections
    if is_main_section_title(title):
        return False
    
    # Author sections typically have names with degrees
    if any(deg in title for deg in ['PH.D.', 'Ph.D.', 'M.D.', 'M.D', 'R.N.', 'R.T.', 'MBA', 'FACHE']):
        return True
    
    # Check if it looks like a person's name (First Last or FIRST LAST)
    # Names typically have 2-4 words, no common content words
    words = title.split()
    if 2 <= len(words) <= 5:
        content_indicators = ['and', 'the', 'of', 'for', 'in', 'to', 'with', 'from', 'by',
                             'mri', 'safety', 'magnetic', 'field', 'imaging', 'resonance',
                             'physics', 'clinical', 'patients', 'effects', 'exposure',
                             'devices', 'implants', 'procedures', 'contrast', 'agents']
        title_lower = title.lower()
        if not any(word in title_lower for word in content_indicators):
            # Likely a person's name
            return True
    
    return False

def extract_tables(root):
    """Extract all tables from XML."""
    tables = []
    for table in root.iter('table'):
        table_copy = deepcopy(table)
        table_text = ET.tostring(table, encoding='unicode', method='text')
        
        match = re.search(r'Table\s+(\d+)', table_text, re.I)
        table_num = int(match.group(1)) if match else len(tables) + 1
        
        tables.append({
            'element': table_copy,
            'num': table_num
        })
    
    return tables

def remove_all_tables(elem):
    """Remove all tables from element tree."""
    for child in list(elem):
        if child.tag == 'table':
            elem.remove(child)
        else:
            remove_all_tables(child)

def clean_author_section(sect_elem):
    """
    Clean an author section by removing misplaced content.
    Keep: title, affiliation paragraphs (short, institutional text, no technical content)
    Remove: table references, long content paragraphs, tables, technical fragments
    Returns True if section was cleaned.
    """
    children = list(sect_elem)
    kept_paras = 0
    to_remove = []
    
    for child in children:
        if child.tag == 'title':
            continue
        elif child.tag == 'para':
            text = get_element_text(child).strip()
            
            # Check for technical content indicators
            has_technical_content = (
                'Table' in text or
                'Figure' in text or
                re.search(r'\(\d+\)', text) or  # Citations
                'MHz' in text or
                'Hz' in text or
                'MRI' in text or
                'magnetic' in text.lower() or
                'frequency' in text.lower() or
                len(text) > 300  # Too long for affiliation
            )
            
            # Check for affiliation indicators
            is_affiliation = (
                any(word in text for word in ['University', 'Hospital', 'Institute', 'Medical', 'School', 'Center', 'Department']) or
                re.search(r'\b[A-Z]{2}\b', text)  # State abbreviation like MD, CA
            ) and len(text) < 300
            
            if kept_paras < 2 and is_affiliation and not has_technical_content:
                kept_paras += 1
            elif not has_technical_content and len(text) < 100:
                # Short non-technical para, might be part of author info
                kept_paras += 1
            else:
                to_remove.append(child)
        elif child.tag == 'table':
            to_remove.append(child)
        else:
            # Keep other elements
            pass
    
    for child in to_remove:
        sect_elem.remove(child)
    
    return len(to_remove) > 0

def find_table_reference(root, table_num):
    """Find the paragraph that properly references this table."""
    best_para = None
    best_score = -999
    
    for para in root.iter('para'):
        text = get_element_text(para)
        
        # Look for table reference
        if not re.search(rf'\bTable\s+{table_num}\b', text, re.I):
            continue
        
        # Get parent to check if we're in a main section (not author section)
        # Skip references in short fragments
        if len(text) < 50:
            continue
        
        score = 0
        lower = text.lower()
        
        # Heavily penalize caption paragraphs
        if re.match(rf'^\s*Table\s+{table_num}\.', text.strip(), re.I):
            score -= 100
        
        # Prefer contextual references
        if re.search(rf'table\s+{table_num}\s+(?:shows|lists|provides|gives|presents|summarizes)', lower):
            score += 30
        if re.search(rf'(?:see|refer to|shown in|in)\s+table\s+{table_num}', lower):
            score += 25
        if re.search(rf'\(table\s+{table_num}\)', lower):
            score += 20
        
        # Prefer longer paragraphs (more context)
        if len(text) > 200:
            score += 10
        if len(text) > 400:
            score += 5
        
        if score > best_score:
            best_score = score
            best_para = para
    
    return best_para if best_score > -50 else None

def process_chapter(xml_file, output_file):
    """Process a chapter XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0
    
    # Step 1: Extract all tables
    all_tables = extract_tables(root)
    print(f"  Found {len(all_tables)} tables")
    
    # Step 2: Remove all tables from tree
    remove_all_tables(root)
    
    # Step 3: Clean author sections (remove misplaced content)
    cleaned_count = 0
    for sect in root.findall('.//sect1'):
        if is_author_section(sect):
            if clean_author_section(sect):
                cleaned_count += 1
    
    if cleaned_count > 0:
        print(f"  Cleaned {cleaned_count} author section(s)")
    
    # Step 4: Also remove any orphan paragraphs at chapter level before main sections
    main_section_found = False
    children = list(root)
    to_remove = []
    
    for i, child in enumerate(children):
        if child.tag == 'sect1':
            if is_main_section_title(child.find('title').text if child.find('title') is not None else ''):
                main_section_found = True
            elif not main_section_found and not is_author_section(child):
                # Suspicious section before main content
                pass
        elif child.tag == 'para' and not main_section_found:
            # Orphan paragraph before main content
            text = get_element_text(child)
            if 'BioRef' in text or len(text) > 100:
                to_remove.append(child)
    
    for child in to_remove:
        root.remove(child)
        print(f"  Removed orphan paragraph")
    
    # Step 5: Group tables by number
    tables_by_num = {}
    for t in all_tables:
        num = t['num']
        if num not in tables_by_num:
            tables_by_num[num] = []
        tables_by_num[num].append(t['element'])
    
    # Step 6: Find placement for each table
    placements = {}  # para -> list of tables
    unplaced = []
    
    for num in sorted(tables_by_num.keys()):
        para = find_table_reference(root, num)
        if para is not None:
            para_id = id(para)
            if para_id not in placements:
                placements[para_id] = {'para': para, 'tables': []}
            placements[para_id]['tables'].extend(tables_by_num[num])
            print(f"    Table {num} -> after reference")
        else:
            unplaced.extend(tables_by_num[num])
            print(f"    Table {num} -> append at end")
    
    # Step 7: Insert tables after their references
    def insert_tables(elem):
        i = 0
        while i < len(elem):
            child = elem[i]
            
            # Recurse first
            if len(child) > 0:
                insert_tables(child)
            
            # Check if tables should be inserted after this element
            if id(child) in placements:
                tables_to_add = placements[id(child)]['tables']
                for j, table_elem in enumerate(tables_to_add):
                    elem.insert(i + 1 + j, table_elem)
                i += len(tables_to_add)
            
            i += 1
    
    insert_tables(root)
    
    # Step 8: Append unplaced tables at end
    if unplaced:
        # Find last main section
        last_sect = None
        for sect in root.findall('.//sect1'):
            title = sect.find('title')
            if title is not None and is_main_section_title(title.text):
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
