#!/usr/bin/env python3
"""
Split XML chapters into separate files while maintaining all formatting,
content, and multimedia references.
"""

import os
import re
import shutil
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET

def extract_chapter_number_from_title(title_text):
    """Extract chapter number from title text like 'Chapter 12' or 'CHAPTER 12'"""
    if not title_text:
        return None
    match = re.search(r'(?:Chapter|CHAPTER)\s+(\d+)', title_text)
    if match:
        return int(match.group(1))
    return None

def analyze_xml_file(filepath):
    """Analyze an XML file to find all chapters it contains"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all chapter references
        chapter_refs = re.findall(r'(?:Chapter|CHAPTER)\s+(\d+)', content)

        if not chapter_refs:
            return []

        # Get unique chapters and return sorted
        unique_chapters = sorted(set(int(ch) for ch in chapter_refs))
        return unique_chapters

    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return []

def find_chapter_boundaries(content, chapter_numbers):
    """Find the boundaries of each chapter in the content"""
    boundaries = []

    # Look for section titles that contain chapter numbers
    pattern = r'<title>(?:Chapter|CHAPTER)\s+(\d+)\s+'

    for match in re.finditer(pattern, content):
        chapter_num = int(match.group(1))
        if chapter_num in chapter_numbers:
            boundaries.append({
                'chapter': chapter_num,
                'start': match.start(),
                'title_start': match.start()
            })

    return sorted(boundaries, key=lambda x: x['start'])

def split_file_by_sections(filepath, output_dir):
    """
    Split XML file by analyzing sect1 elements and their chapter markers.
    """
    print(f"\nProcessing: {filepath}")

    try:
        # Parse the XML file
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Get the XML declaration
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline()

        xml_declaration = first_line.strip() if first_line.startswith('<?xml') else '<?xml version="1.0" encoding="UTF-8"?>'

        # Find all sect1 elements
        namespace = ''
        if root.tag.startswith('{'):
            namespace = root.tag.split('}')[0] + '}'

        sect1_elements = root.findall('.//sect1')

        # Group sect1 elements by chapter
        chapter_sections = defaultdict(list)

        for sect1 in sect1_elements:
            # Look for chapter number in title
            title_elem = sect1.find('.//title')
            if title_elem is not None and title_elem.text:
                chapter_num = extract_chapter_number_from_title(title_elem.text)
                if chapter_num:
                    chapter_sections[chapter_num].append(sect1)

        if not chapter_sections:
            print(f"  No chapters found in {filepath}")
            return []

        created_files = []

        # Create separate files for each chapter
        for chapter_num in sorted(chapter_sections.keys()):
            sections = chapter_sections[chapter_num]

            # Create new chapter element
            new_chapter = ET.Element('chapter')
            new_chapter.set('id', f'ch{chapter_num:04d}')
            new_chapter.set('label', str(chapter_num))

            # Add title element
            title_elem = ET.SubElement(new_chapter, 'title')
            title_elem.text = ''

            # Add all sect1 elements for this chapter
            for sect1 in sections:
                new_chapter.append(sect1)

            # Create new tree
            new_tree = ET.ElementTree(new_chapter)

            # Write to file
            output_filename = f'ch{chapter_num:03d}.xml'
            output_path = output_dir / output_filename

            # Write XML with proper formatting
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_declaration + '\n\n')
                # Convert to string and write
                xml_str = ET.tostring(new_chapter, encoding='unicode')
                f.write(xml_str)
                f.write('\n')

            print(f"  Created: {output_filename} (Chapter {chapter_num})")
            created_files.append({
                'chapter': chapter_num,
                'filename': output_filename,
                'path': str(output_path)
            })

        return created_files

    except Exception as e:
        print(f"  Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_source_files(source_dir):
    """Analyze all source XML files to understand their structure"""
    print("=" * 60)
    print("ANALYZING SOURCE FILES")
    print("=" * 60)

    xml_files = sorted(Path(source_dir).glob('ch*.xml'))
    analysis = {}

    for xml_file in xml_files:
        chapters = analyze_xml_file(xml_file)
        analysis[xml_file.name] = chapters
        if chapters:
            print(f"{xml_file.name}: Chapters {chapters}")
        else:
            print(f"{xml_file.name}: No clear chapter markers (may be TOC or front matter)")

    return analysis

def main():
    # Directories
    source_dir = Path('/home/user/test/split_work')
    output_dir = Path('/home/user/test/split_output')

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # First, analyze the source files
    analysis = analyze_source_files(source_dir)

    print("\n" + "=" * 60)
    print("SPLITTING CHAPTERS")
    print("=" * 60)

    # Track all created chapters
    all_chapters = {}

    # Process each XML file
    xml_files = sorted(source_dir.glob('ch*.xml'))

    for xml_file in xml_files:
        created_files = split_file_by_sections(xml_file, output_dir)

        for file_info in created_files:
            chapter_num = file_info['chapter']
            if chapter_num in all_chapters:
                print(f"  WARNING: Chapter {chapter_num} appears in multiple source files!")
                print(f"    Previous: {all_chapters[chapter_num]['source']}")
                print(f"    Current: {xml_file.name}")
            else:
                all_chapters[chapter_num] = {
                    'filename': file_info['filename'],
                    'source': xml_file.name
                }

    # Copy multimedia directory
    multimedia_src = source_dir / 'multimedia'
    multimedia_dst = output_dir / 'multimedia'

    if multimedia_src.exists():
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
        print(f"\nCopied multimedia directory")

    # Copy Book.XML if it exists
    book_xml = source_dir / 'Book.XML'
    if book_xml.exists():
        shutil.copy2(book_xml, output_dir / 'Book.XML')
        print(f"Copied Book.XML")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total unique chapters created: {len(all_chapters)}")
    print(f"Chapter numbers: {sorted(all_chapters.keys())}")
    print(f"Output directory: {output_dir}")

    # Check for gaps
    if all_chapters:
        min_ch = min(all_chapters.keys())
        max_ch = max(all_chapters.keys())
        missing = [i for i in range(min_ch, max_ch + 1) if i not in all_chapters]
        if missing:
            print(f"\nMissing chapters: {missing}")

    return all_chapters

if __name__ == '__main__':
    main()
