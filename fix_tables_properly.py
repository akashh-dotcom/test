#!/usr/bin/env python3
"""
Fix tables by:
1. Removing misplaced paragraphs at the beginning of chapters
2. Keeping existing well-structured tables but moving them to correct positions
3. Removing duplicate/orphan content
"""

import os
import re
import fitz  # PyMuPDF
from pathlib import Path
import xml.etree.ElementTree as ET
from copy import deepcopy
import shutil

SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
POSITIONED_DIR = Path('/workspace/final_output_tables_POSITIONED')
OUTPUT_DIR = Path('/workspace/final_output_tables_FIXED_FINAL')

# Register namespace to avoid ns0: prefixes
ET.register_namespace('', '')

def get_element_text(elem):
    """Get all text from an element including children."""
    text = elem.text or ''
    for child in elem:
        text += get_element_text(child)
        text += child.tail or ''
    return text

def is_bad_para(elem):
    """Check if paragraph should be removed."""
    if elem.tag != 'para':
        return False
    
    text = get_element_text(elem).strip()
    if not text:
        return False
    
    # BioRef metadata
    if 'BioRef' in text and 'Layout' in text:
        return True
    
    # Standalone page numbers
    if re.match(r'^Page\s+\d+\s*$', text, re.I):
        return True
    if re.match(r'^\d{1,3}$', text):
        return True
    
    return False

def is_misplaced_content_early_section(text):
    """
    Check if text is misplaced content that shouldn't appear at the beginning.
    ONLY apply this to early sections (before INTRODUCTION/main content).
    """
    if not text:
        return False
    
    text_stripped = text.strip()
    
    # Patterns that indicate content from table areas (only remove at start of chapter)
    misplaced_patterns = [
        r'^implants\s+at\s+7\s*T\s*\(\d+\)',
        r'^Overview of various implants that have been tested',
        r'revealed that the evaluations were only conducted',
        # Short orphan fragments
        r'^o$',
        r'^at 7 T \(\d+\)\.',
        # Fragments that end with just "Table X" without context
        r'\.\s+Table\s+\d+$',  # Ends with ". Table N"
    ]
    
    for pattern in misplaced_patterns:
        if re.search(pattern, text_stripped, re.I):
            return True
    
    # Also check for content that's clearly from later in a chapter
    # appearing before INTRODUCTION (e.g., study results, implant tests)
    early_misplaced_indicators = [
        'subcutaneously implanted port catheters',
        'the aforementioned examples',
        'RF-induced heating',
    ]
    
    # Only flag if this is clearly a short fragment (not the full context)
    if len(text_stripped) < 500:  # Short paragraph
        for indicator in early_misplaced_indicators:
            if indicator.lower() in text_stripped.lower():
                # Check if it ends abruptly with "Table X" 
                if re.search(r'Table\s+\d+\s*$', text_stripped):
                    return True
    
    return False

def extract_tables_from_xml(root):
    """Extract all tables from XML with their context."""
    tables = {}
    
    for table in root.iter('table'):
        # Get table title
        title_elem = table.find('title')
        title = title_elem.text if title_elem is not None and title_elem.text else ''
        
        # Try to determine table number from title
        match = re.search(r'Table\s+(\d+)', title, re.I)
        if not match:
            # Check full content for table number (anywhere, not just at start)
            full_text = ET.tostring(table, encoding='unicode', method='text')
            match = re.search(r'Table\s+(\d+)', full_text, re.I)
        
        if match:
            table_num = int(match.group(1))
            if table_num not in tables:  # Keep first occurrence
                tables[table_num] = {
                    'element': deepcopy(table),
                    'title': title,
                    'number': table_num
                }
    
    return tables

def is_well_structured_table(table_elem):
    """Check if a table has proper DocBook structure."""
    tgroup = table_elem.find('tgroup')
    if tgroup is None:
        return False
    
    tbody = tgroup.find('tbody')
    if tbody is None:
        return False
    
    rows = tbody.findall('row')
    if len(rows) < 1:  # Need at least 1 data row
        return False
    
    # Check for BioRef content (malformed tables)
    table_text = ET.tostring(table_elem, encoding='unicode', method='text')
    if 'BioRef' in table_text and 'Layout' in table_text:
        return False
    
    return True

def clean_chapter(xml_file, output_file):
    """Clean chapter and place tables correctly."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return 0
    
    # Step 1: Extract existing well-structured tables
    chapter_tables = extract_tables_from_xml(root)
    good_tables = {num: data for num, data in chapter_tables.items() 
                   if is_well_structured_table(data['element'])}
    
    print(f"  Found {len(good_tables)} well-structured tables")
    
    # Step 2: Remove all tables and bad/misplaced paragraphs
    # Track section positions to determine which are "early" sections
    seen_introduction = False
    
    def is_introduction_section(elem):
        """Check if this section is the Introduction or main content section."""
        if elem.tag == 'sect1':
            title_elem = elem.find('title')
            if title_elem is not None and title_elem.text:
                title_lower = title_elem.text.lower().strip()
                return 'introduction' in title_lower or 'physics' in title_lower or 'background' in title_lower
        return False
    
    def clean_element(elem, in_early_section=False):
        nonlocal seen_introduction
        children_to_remove = []
        
        for i, child in enumerate(elem):
            if child.tag == 'table':
                children_to_remove.append(child)
            elif is_bad_para(child):
                children_to_remove.append(child)
            elif child.tag == 'para' and in_early_section:
                # Only check for misplaced content in early sections
                text = get_element_text(child)
                if is_misplaced_content_early_section(text):
                    children_to_remove.append(child)
            elif child.tag == 'sect1':
                # Check if we've reached main content
                if is_introduction_section(child):
                    seen_introduction = True
                # Early sections are those before Introduction
                is_early = not seen_introduction and i < 5
                clean_element(child, is_early)
            else:
                clean_element(child, in_early_section)
        
        for child in children_to_remove:
            elem.remove(child)
    
    clean_element(root)
    
    # Step 3: Find the BEST reference for each table (contextual references are preferred)
    table_references = {num: [] for num in good_tables.keys()}
    
    def find_table_references(parent):
        for child in parent:
            if child.tag == 'para':
                text = get_element_text(child)
                text_stripped = text.strip()
                lower_text = text.lower()
                
                for match in re.finditer(r'\bTable\s+(\d+)\b', text, re.I):
                    table_num = int(match.group(1))
                    if table_num in good_tables:
                        score = 0
                        
                        # PENALIZE table caption paragraphs (start with "Table X.")
                        if re.match(rf'^\s*Table\s+{table_num}\.\s', text_stripped, re.I):
                            score -= 20  # Heavy penalty for captions
                        
                        # Prefer contextual references with action verbs
                        context_words = ['provides', 'gives', 'shows', 'presents', 
                                        'summarizes', 'lists']
                        has_context = any(f'table {table_num}'.lower() in lower_text and word in lower_text 
                                         for word in context_words)
                        if has_context:
                            score += 15  # Strong preference for contextual references
                        
                        # Additional context for "overview"
                        if 'overview' in lower_text and f'table {table_num}' in lower_text:
                            if not re.match(rf'^\s*Table\s+{table_num}\.', text_stripped, re.I):
                                score += 5
                        
                        if len(text) > 150:
                            score += 3
                        if 'see table' in lower_text:
                            score += 5
                        
                        table_references[table_num].append({
                            'para': child,
                            'text': text,
                            'score': score
                        })
            
            if len(child) > 0:
                find_table_references(child)
    
    find_table_references(root)
    
    # Select best reference for each table
    best_refs = {}
    for table_num, refs in table_references.items():
        if refs:
            # Sort by score descending, then by text length (prefer more context)
            refs.sort(key=lambda r: (r['score'], len(r['text'])), reverse=True)
            best_refs[table_num] = refs[0]['para']
    
    # Step 4: Insert tables after their best references
    inserted_tables = set()
    
    def insert_tables(parent):
        children = list(parent)
        new_children = []
        
        for child in children:
            new_children.append(child)
            
            if child.tag == 'para':
                # Check if this is the best reference for any table
                for table_num, best_para in best_refs.items():
                    if child is best_para and table_num not in inserted_tables:
                        new_children.append(deepcopy(good_tables[table_num]['element']))
                        inserted_tables.add(table_num)
                        print(f"    Placed Table {table_num}")
            
            # Recurse
            if len(child) > 0:
                insert_tables(child)
        
        parent[:] = new_children
    
    insert_tables(root)
    
    # Step 4: Append any tables that weren't placed (at end of last sect1)
    remaining = set(good_tables.keys()) - inserted_tables
    if remaining:
        # Find last sect1
        last_sect = None
        for sect in root.iter('sect1'):
            last_sect = sect
        
        if last_sect is not None:
            for table_num in sorted(remaining):
                last_sect.append(deepcopy(good_tables[table_num]['element']))
                print(f"    Appended Table {table_num} at end")
    
    # Write output
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return len(good_tables)

def main():
    # Use POSITIONED_DIR as source since it has better table content
    # but we'll use SOURCE_DIR for structure
    source = POSITIONED_DIR if POSITIONED_DIR.exists() else SOURCE_DIR
    print(f"Using source: {source}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total_tables = 0
    
    for xml_file in sorted(source.glob('*.xml')):
        if xml_file.name == 'Book.XML':
            continue
        
        print(f"\nProcessing {xml_file.name}...")
        output_file = OUTPUT_DIR / xml_file.name
        
        tables = clean_chapter(xml_file, output_file)
        total_tables += tables
    
    # Copy and fix Book.XML
    book_src = source / 'Book.XML'
    if book_src.exists():
        print("\nCopying and fixing Book.XML...")
        with open(book_src, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(
            r'<!DOCTYPE\s+book\s+SYSTEM\s+["\'][^"\']+["\']\s*\[',
            '<!DOCTYPE book [',
            content
        )
        
        with open(OUTPUT_DIR / 'Book.XML', 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Copy multimedia
    multimedia_src = source / 'multimedia'
    if multimedia_src.exists():
        multimedia_dst = OUTPUT_DIR / 'multimedia'
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
        print("Copied multimedia folder")
    
    print(f"\n=== Summary ===")
    print(f"Total tables processed: {total_tables}")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
