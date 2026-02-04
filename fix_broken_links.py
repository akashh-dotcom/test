#!/usr/bin/env python3
"""
Script to fix broken links in part-level sect1 files.
Analyzes the content and creates intelligent mappings for broken linkend references.
"""

import re
import os
from pathlib import Path
from collections import defaultdict

def extract_all_ids_from_book(book_path):
    """Extract all IDs from the book XML and its referenced files"""
    with open(book_path, 'r', encoding='utf-8') as f:
        book_content = f.read()
    
    # Find all IDs in the book
    ids = set(re.findall(r'id="([^"]+)"', book_content))
    return ids

def extract_all_ids_from_directory(directory):
    """Extract all IDs from all XML files in directory"""
    all_ids = {}
    
    for xml_file in Path(directory).glob('*.xml'):
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ids = re.findall(r'id="([^"]+)"', content)
        for id_val in ids:
            if id_val not in all_ids:
                all_ids[id_val] = []
            all_ids[id_val].append(str(xml_file))
    
    return all_ids

def analyze_broken_links_in_file(sect1_file, all_ids):
    """Analyze broken links in a specific part-level sect1 file"""
    with open(sect1_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all linkend references
    linkends = re.findall(r'<link linkend="([^"]+)">(.*?)</link>', content, re.DOTALL)
    
    broken = []
    valid = []
    
    for linkend, link_text in linkends:
        if linkend not in all_ids:
            broken.append((linkend, link_text.strip()))
        else:
            valid.append((linkend, link_text.strip()))
    
    return broken, valid

def find_chapter_number_from_link_text(link_text):
    """Extract chapter number from link text like '1.1. Introduction' or 'Table 2.1-1'"""
    # Match patterns like "1.1.", "2.1.", "3.2.1.", etc.
    match = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?', link_text)
    if match:
        return match.group(0)
    
    # Match table references like "Table 2.1-1"
    match = re.search(r'Table\s+(\d+\.\d+)[–-](\d+)', link_text)
    if match:
        return f"{match.group(1)}"
    
    # Match appendix references like "Appendix 1.1-1"
    match = re.search(r'Appendix\s+(\d+\.\d+)[–-](\d+)', link_text)
    if match:
        return f"{match.group(1)}"
    
    return None

def find_chapter_id_by_number(book_content, chapter_num_str, part_id):
    """Find chapter ID by chapter number string within a specific part"""
    # Extract part content
    part_pattern = rf'<part id="{part_id}">(.*?)(?=<part id=|</book>)'
    part_match = re.search(part_pattern, book_content, re.DOTALL)
    
    if not part_match:
        return None
    
    part_content = part_match.group(1)
    
    # Look for chapter with matching number
    # Pattern: <chapter ... <title> ... <emphasis role="chapterNumber">X.Y</emphasis>
    chapter_pattern = r'<chapter id="(ch\d+)"[^>]*>.*?<emphasis role="chapterNumber">([^<]+)</emphasis>'
    chapters = re.findall(chapter_pattern, part_content, re.DOTALL)
    
    for ch_id, ch_num in chapters:
        if ch_num.strip() == chapter_num_str:
            return ch_id
    
    return None

def find_table_or_appendix_id(extracted_dir, link_text, chapter_id):
    """Find table or appendix ID based on link text and chapter"""
    # If it's a table or appendix reference, we need to search in the chapter files
    if not chapter_id:
        return None
    
    # Search in all sect1 files for this chapter
    sect1_files = list(Path(extracted_dir).glob(f'sect1.9781683674832.{chapter_id}*.xml'))
    
    for sect1_file in sect1_files:
        with open(sect1_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for matching table title
        if 'Table' in link_text:
            # Extract table number from link text
            table_match = re.search(r'Table\s+\d+\.\d+[–-](\d+)', link_text)
            if table_match:
                table_num = int(table_match.group(1))
                # Look for table IDs in the file
                table_ids = re.findall(r'<table id="([^"]+)"', content)
                if table_ids and table_num <= len(table_ids):
                    return table_ids[table_num - 1] if table_num > 0 else table_ids[0]
        
        # Look for matching appendix
        if 'Appendix' in link_text:
            # For appendices, they might be in separate files or sections
            # Try to find by searching for the text
            appendix_match = re.search(r'Appendix\s+\d+\.\d+[–-](\d+)', link_text)
            if appendix_match:
                appendix_num = int(appendix_match.group(1))
                # Look for appendix IDs
                appendix_ids = re.findall(r'id="([^"]*appendix[^"]*)"', content, re.IGNORECASE)
                if not appendix_ids:
                    # Try to find by section
                    appendix_ids = re.findall(r'<sect2 id="([^"]+)"', content)
                if appendix_ids and appendix_num <= len(appendix_ids):
                    return appendix_ids[appendix_num - 1] if appendix_num > 0 else appendix_ids[0]
    
    # If we can't find a specific table/appendix, return the chapter ID as fallback
    return chapter_id

def fix_broken_links_in_file(sect1_file, book_path, extracted_dir, all_ids):
    """Fix broken links in a part-level sect1 file"""
    # Extract part ID from filename
    filename = Path(sect1_file).name
    part_match = re.search(r'pt(\d+)s0001', filename)
    if not part_match:
        return None
    
    part_id = f"pt{part_match.group(1)}"
    
    with open(book_path, 'r', encoding='utf-8') as f:
        book_content = f.read()
    
    with open(sect1_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    broken, valid = analyze_broken_links_in_file(sect1_file, all_ids)
    
    if not broken:
        return None
    
    print(f"\nProcessing {filename} (part {part_id}):")
    print(f"  Found {len(broken)} broken links")
    
    fixes_made = []
    new_content = content
    
    for broken_link, link_text in broken:
        # Try to find the correct ID
        chapter_num = find_chapter_number_from_link_text(link_text)
        
        if chapter_num:
            # Find the chapter ID
            chapter_id = find_chapter_id_by_number(book_content, chapter_num, part_id)
            
            if chapter_id:
                # If it's a table/appendix reference, try to find the specific ID
                if 'Table' in link_text or 'Appendix' in link_text:
                    target_id = find_table_or_appendix_id(extracted_dir, link_text, chapter_id)
                else:
                    target_id = chapter_id
                
                if target_id:
                    # Replace the broken link
                    old_link = f'linkend="{broken_link}"'
                    new_link = f'linkend="{target_id}"'
                    new_content = new_content.replace(old_link, new_link)
                    fixes_made.append({
                        'old': broken_link,
                        'new': target_id,
                        'text': link_text
                    })
                    print(f"    ✓ Fixed: {broken_link} → {target_id}")
                    print(f"      Link text: {link_text[:60]}...")
    
    if fixes_made:
        # Write the fixed content
        with open(sect1_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return fixes_made
    
    return None

def main():
    extracted_dir = '/workspace/extracted_final'
    book_path = f'{extracted_dir}/book.9781683674832.xml.new'
    
    print("=" * 70)
    print("ANALYZING AND FIXING BROKEN LINKS IN PART-LEVEL SECT1 FILES")
    print("=" * 70)
    
    # Extract all IDs from all files
    print("\nStep 1: Extracting all IDs from XML files...")
    all_ids = extract_all_ids_from_directory(extracted_dir)
    print(f"  Found {len(all_ids)} unique IDs across all files")
    
    # Process each part-level sect1 file
    print("\nStep 2: Fixing broken links in part-level sect1 files...")
    
    total_fixes = 0
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        sect1_file = Path(extracted_dir) / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if sect1_file.exists():
            fixes = fix_broken_links_in_file(str(sect1_file), book_path, extracted_dir, all_ids)
            if fixes:
                total_fixes += len(fixes)
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Fixed {total_fixes} broken links")
    print("=" * 70)

if __name__ == '__main__':
    main()
