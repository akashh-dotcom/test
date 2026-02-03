#!/usr/bin/env python3
"""
Script to fix XML references in book.9781683674832.xml:
1. Add entity declarations for part-level sect1 files (pt00*s0001.xml)
2. Add entity references at the beginning of each part element
3. Fix broken links in part-level sect1 files
"""

import re
import os
from pathlib import Path

def extract_entity_declarations(book_path):
    """Extract the DOCTYPE entity declarations section from the book XML"""
    with open(book_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find DOCTYPE declaration
    doctype_match = re.search(r'<!DOCTYPE.*?\[', content, re.DOTALL)
    if not doctype_match:
        raise ValueError("No DOCTYPE found")
    
    # Find all entity declarations
    entity_section_match = re.search(r'<!DOCTYPE.*?\[(.*?)\]>', content, re.DOTALL)
    if not entity_section_match:
        raise ValueError("No entity declarations found")
    
    return content, entity_section_match.group(1)

def add_part_entity_declarations(book_path, output_path):
    """Add entity declarations for part-level sect1 files"""
    content, entity_declarations = extract_entity_declarations(book_path)
    
    # Create entity declarations for part-level sect1 files
    part_entities = []
    for i in range(1, 19):  # pt0001 to pt0018
        part_id = f"pt{i:04d}"
        entity_name = f"sect1.9781683674832.{part_id}s0001"
        entity_decl = f'<!ENTITY {entity_name} SYSTEM "{entity_name}.xml">'
        part_entities.append(entity_decl)
    
    # Insert part entities at the beginning of the entity declarations
    # Find the position after the DOCTYPE opening bracket
    doctype_start = content.find('[') + 1
    doctype_end = content.find(']>')
    
    # Get existing entities
    existing_entities = content[doctype_start:doctype_end]
    
    # Combine new entities with existing ones
    new_entities = '\n'.join(part_entities) + existing_entities
    
    # Reconstruct the content
    new_content = content[:doctype_start] + new_entities + content[doctype_end:]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Added {len(part_entities)} entity declarations for part-level sect1 files")
    return new_content

def add_part_entity_references(book_path, output_path):
    """Add entity references at the beginning of each part element"""
    with open(book_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all part elements and add the entity reference
    part_pattern = r'(<part id="(pt\d{4})">\s*<title>.*?</title>\s*<partintro>.*?</partintro>\s*)'
    
    def add_entity_ref(match):
        part_block = match.group(1)
        part_id = match.group(2)
        entity_ref = f"&sect1.9781683674832.{part_id}s0001;\n"
        return part_block + entity_ref
    
    new_content = re.sub(part_pattern, add_entity_ref, content, flags=re.DOTALL)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Count how many replacements were made
    count = len(re.findall(part_pattern, content, re.DOTALL))
    print(f"Added entity references to {count} part elements")
    return new_content

def find_chapter_ids_for_part(book_content, part_id):
    """Find all chapter IDs that belong to a specific part"""
    # Find the part section
    part_pattern = rf'<part id="{part_id}">(.*?)(?=<part id=|</book>)'
    part_match = re.search(part_pattern, book_content, re.DOTALL)
    
    if not part_match:
        return []
    
    part_content = part_match.group(1)
    
    # Find all chapter IDs in this part
    chapter_ids = re.findall(r'<chapter id="(ch\d+)"', part_content)
    return chapter_ids

def analyze_and_fix_links(extracted_dir, book_path):
    """Analyze broken links in part-level sect1 files and create a mapping"""
    with open(book_path, 'r', encoding='utf-8') as f:
        book_content = f.read()
    
    issues = []
    fixes = []
    
    # Process each part-level sect1 file
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        sect1_file = Path(extracted_dir) / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if not sect1_file.exists():
            issues.append(f"Missing file: {sect1_file}")
            continue
        
        with open(sect1_file, 'r', encoding='utf-8') as f:
            sect1_content = f.read()
        
        # Find all broken links (9781683674832_v1_c* pattern)
        broken_links = re.findall(r'linkend="(9781683674832_v1_c\d+)"', sect1_content)
        
        if broken_links:
            # Get chapter IDs for this part
            chapter_ids = find_chapter_ids_for_part(book_content, part_id)
            
            issues.append(f"\nPart {part_id}:")
            issues.append(f"  Broken links found: {len(set(broken_links))} unique")
            issues.append(f"  Chapters in part: {chapter_ids}")
            
            # For now, we'll replace broken links with the first chapter in the part
            # This is a heuristic - ideally we'd need a more sophisticated mapping
            if chapter_ids:
                for broken_link in set(broken_links):
                    fixes.append({
                        'file': sect1_file,
                        'part_id': part_id,
                        'broken_link': broken_link,
                        'suggested_fix': chapter_ids[0],  # Default to first chapter
                        'all_chapters': chapter_ids
                    })
    
    return issues, fixes

def main():
    extracted_dir = '/workspace/extracted_final'
    book_path = f'{extracted_dir}/book.9781683674832.xml'
    output_path = f'{extracted_dir}/book.9781683674832.xml.new'
    
    print("=" * 60)
    print("STEP 1: Adding entity declarations for part-level sect1 files")
    print("=" * 60)
    add_part_entity_declarations(book_path, output_path)
    
    print("\n" + "=" * 60)
    print("STEP 2: Adding entity references to part elements")
    print("=" * 60)
    add_part_entity_references(output_path, output_path)
    
    print("\n" + "=" * 60)
    print("STEP 3: Analyzing broken links in part-level sect1 files")
    print("=" * 60)
    issues, fixes = analyze_and_fix_links(extracted_dir, output_path)
    
    for issue in issues:
        print(issue)
    
    print("\n" + "=" * 60)
    print("SUMMARY OF FIXES NEEDED")
    print("=" * 60)
    print(f"Total broken link instances to fix: {len(fixes)}")
    
    # Group by file
    files_to_fix = {}
    for fix in fixes:
        file_path = str(fix['file'])
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append(fix)
    
    print(f"Files with broken links: {len(files_to_fix)}")
    
    return output_path, fixes

if __name__ == '__main__':
    output_path, fixes = main()
    print(f"\nUpdated book XML saved to: {output_path}")
