#!/usr/bin/env python3
"""
Split XML chapters into separate files while maintaining all formatting,
content, and multimedia references.
Handles chapters at both sect1 and sect2 levels.
"""

import os
import re
import shutil
from pathlib import Path
from collections import defaultdict
import hashlib

def extract_chapter_number_from_title(title_text):
    """Extract chapter number from title text like 'Chapter 12' or 'CHAPTER 12'"""
    if not title_text:
        return None
    match = re.search(r'(?:Chapter|CHAPTER)\s+(\d+)', title_text)
    if match:
        return int(match.group(1))
    return None

def get_content_hash(element_string):
    """Get hash of element content for deduplication"""
    return hashlib.md5(element_string.encode('utf-8')).hexdigest()

def element_to_string(element):
    """Convert element to string"""
    import xml.etree.ElementTree as ET
    return ET.tostring(element, encoding='unicode')

def find_chapter_sections(root):
    """
    Find all chapter sections at both sect1 and sect2 levels.
    Returns a dict of chapter_num -> [(section_element, level, hash), ...]
    """
    chapter_sections = defaultdict(list)

    # Find all sect1 elements
    for sect1 in root.findall('.//sect1'):
        # Check if this sect1 contains a chapter
        title_elem = sect1.find('.//title')
        if title_elem is not None and title_elem.text:
            chapter_num = extract_chapter_number_from_title(title_elem.text)
            if chapter_num:
                content_str = element_to_string(sect1)
                content_hash = get_content_hash(content_str)
                chapter_sections[chapter_num].append(('sect1', sect1, content_hash))

    # Find all sect2 elements that might contain chapters
    for sect2 in root.findall('.//sect2'):
        title_elem = sect2.find('title')
        if title_elem is not None and title_elem.text:
            chapter_num = extract_chapter_number_from_title(title_elem.text)
            if chapter_num:
                content_str = element_to_string(sect2)
                content_hash = get_content_hash(content_str)
                chapter_sections[chapter_num].append(('sect2', sect2, content_hash))

    return chapter_sections

def deduplicate_chapter_sections(chapter_sections):
    """
    Remove duplicate sections based on content hash.
    Returns dict of chapter_num -> [(level, element), ...]
    """
    deduplicated = {}

    for chapter_num, sections in chapter_sections.items():
        seen_hashes = set()
        unique_sections = []

        for level, element, content_hash in sections:
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_sections.append((level, element))

        if unique_sections:
            deduplicated[chapter_num] = unique_sections

    return deduplicated

def create_chapter_xml(chapter_num, sections, xml_declaration):
    """Create XML content for a chapter"""
    import xml.etree.ElementTree as ET

    # Create new chapter element
    new_chapter = ET.Element('chapter')
    new_chapter.set('id', f'ch{chapter_num:04d}')
    new_chapter.set('label', str(chapter_num))

    # Add empty title element
    title_elem = ET.SubElement(new_chapter, 'title')

    # For each section, we need to add it as a sect1
    for level, section in sections:
        if level == 'sect1':
            # Already at sect1 level, just append
            new_chapter.append(section)
        elif level == 'sect2':
            # Need to wrap sect2 in a sect1
            # Create a new sect1
            sect1 = ET.Element('sect1')
            sect1.set('id', f'ch{chapter_num:04d}s01')

            # Add the sect2 to this sect1
            sect1.append(section)

            new_chapter.append(sect1)

    # Convert to string with proper formatting
    xml_str = ET.tostring(new_chapter, encoding='unicode')

    # Combine with XML declaration
    full_xml = xml_declaration + '\n\n' + xml_str + '\n'

    return full_xml

def process_file(filepath, output_dir):
    """Process a single XML file and extract chapters"""
    import xml.etree.ElementTree as ET

    print(f"\nProcessing: {filepath.name}")

    try:
        # Parse the XML file
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Get the XML declaration
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline()

        xml_declaration = first_line.strip() if first_line.startswith('<?xml') else '<?xml version="1.0" encoding="UTF-8"?>'

        # Find all chapter sections
        chapter_sections = find_chapter_sections(root)

        if not chapter_sections:
            print(f"  No chapters found")
            return {}

        # Deduplicate
        deduplicated = deduplicate_chapter_sections(chapter_sections)

        # Report what we found
        for chapter_num in sorted(deduplicated.keys()):
            sections = deduplicated[chapter_num]
            print(f"  Found Chapter {chapter_num} with {len(sections)} section(s)")

        return {chapter_num: (deduplicated[chapter_num], xml_declaration)
                for chapter_num in deduplicated}

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    import xml.etree.ElementTree as ET

    # Directories
    source_dir = Path('/home/user/test/split_work')
    output_dir = Path('/home/user/test/split_output_final')

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("SPLITTING CHAPTERS")
    print("=" * 60)

    # Collect all chapters from all files
    all_chapters = {}

    # Process each XML file
    xml_files = sorted(source_dir.glob('ch*.xml'))

    for xml_file in xml_files:
        file_chapters = process_file(xml_file, output_dir)

        for chapter_num, (sections, xml_declaration) in file_chapters.items():
            if chapter_num not in all_chapters:
                all_chapters[chapter_num] = (sections, xml_declaration, xml_file.name)
            else:
                print(f"  Note: Chapter {chapter_num} already found in {all_chapters[chapter_num][2]}, skipping duplicate from {xml_file.name}")

    # Write all chapters
    print("\n" + "=" * 60)
    print("WRITING CHAPTER FILES")
    print("=" * 60)

    for chapter_num in sorted(all_chapters.keys()):
        sections, xml_declaration, source_file = all_chapters[chapter_num]

        # Create the XML content
        xml_content = create_chapter_xml(chapter_num, sections, xml_declaration)

        # Write to file
        output_filename = f'ch{chapter_num:03d}.xml'
        output_path = output_dir / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        print(f"  Created {output_filename} (Chapter {chapter_num}) from {source_file}")

    # Copy multimedia directory
    multimedia_src = source_dir / 'multimedia'
    multimedia_dst = output_dir / 'multimedia'

    if multimedia_src.exists():
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
        print(f"\nCopied multimedia directory")

    # Copy Book.XML and front matter
    book_xml = source_dir / 'Book.XML'
    if book_xml.exists():
        shutil.copy2(book_xml, output_dir / 'Book.XML')
        print(f"Copied Book.XML")

    # Copy ch001.xml as it contains front matter
    ch001 = source_dir / 'ch001.xml'
    if ch001.exists():
        shutil.copy2(ch001, output_dir / 'ch001.xml')
        print(f"Copied ch001.xml (front matter)")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total chapters created: {len(all_chapters)}")
    print(f"Chapter numbers: {sorted(all_chapters.keys())}")
    print(f"Output directory: {output_dir}")

    # Check for gaps
    if all_chapters:
        min_ch = min(all_chapters.keys())
        max_ch = max(all_chapters.keys())
        expected = set(range(1, max_ch + 1))
        found = set(all_chapters.keys())
        missing = expected - found
        if missing:
            print(f"\nMissing chapters: {sorted(missing)}")
            print("Note: Some chapters may be in the Table of Contents or front matter")

    return all_chapters

if __name__ == '__main__':
    main()
