#!/usr/bin/env python3
"""
Split XML into proper DocBook structure with ISBN-based naming.
Follows the naming conventions:
- preface.{ISBN}.pr####.xml for front matter
- sect1.{ISBN}.ch####s0000.xml for chapters
- book.{ISBN}.xml for master file
"""

import os
import re
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

# Constants
ISBN = "9780989163286"
SOURCE_DIR = Path('/home/user/test/split_work')
OUTPUT_DIR = Path('/home/user/test/docbook_output')

def update_ids_recursive(element, old_root, new_root):
    """
    Recursively update all IDs in an element tree from old_root prefix to new_root prefix.
    This implements the CARDINAL RULE: all internal IDs must be prefixed with root ID.
    """
    # Update element's id attribute
    if 'id' in element.attrib:
        old_id = element.attrib['id']
        # Replace the old root prefix with new root prefix
        if old_id.startswith(old_root):
            # Keep the suffix after old_root
            suffix = old_id[len(old_root):]
            element.attrib['id'] = new_root + suffix
        else:
            # If it doesn't start with old_root, just prepend new_root
            element.attrib['id'] = new_root + old_id

    # Update linkend attributes
    if 'linkend' in element.attrib:
        old_linkend = element.attrib['linkend']
        if old_linkend.startswith(old_root):
            suffix = old_linkend[len(old_root):]
            element.attrib['linkend'] = new_root + suffix

    # Recursively process children
    for child in element:
        update_ids_recursive(child, old_root, new_root)

def create_preface_file(title, content_elements, preface_num, xml_declaration):
    """Create a preface file with proper structure and IDs"""
    preface_id = f"pr{preface_num:04d}"

    # Create preface root element
    root = ET.Element('preface')
    root.set('id', preface_id)

    # Add title
    title_elem = ET.SubElement(root, 'title')
    title_elem.text = title

    # Add content elements
    for elem in content_elements:
        # Update IDs to match new root
        update_ids_recursive(elem, '', preface_id)
        root.append(elem)

    # Convert to string
    xml_str = ET.tostring(root, encoding='unicode')
    return xml_declaration + '\n\n' + xml_str + '\n'

def create_chapter_file(chapter_num, sect1_element, xml_declaration):
    """Create a chapter file with proper structure and IDs"""
    chapter_id = f"ch{chapter_num:04d}s0000"

    # Clone the sect1 element
    new_sect1 = ET.Element('sect1')
    new_sect1.set('id', chapter_id)

    # Copy attributes except id
    for attr, value in sect1_element.attrib.items():
        if attr != 'id':
            new_sect1.set(attr, value)

    # Copy all children
    for child in sect1_element:
        new_sect1.append(child)

    # Get old root ID
    old_id = sect1_element.get('id', '')

    # Update all IDs recursively
    update_ids_recursive(new_sect1, old_id, chapter_id)

    # Convert to string
    xml_str = ET.tostring(new_sect1, encoding='unicode')
    return xml_declaration + '\n\n' + xml_str + '\n'

def extract_preface_sections(front_matter_file):
    """Extract individual sections from front matter file"""
    tree = ET.parse(front_matter_file)
    root = tree.getroot()

    with open(front_matter_file, 'r', encoding='utf-8') as f:
        xml_decl = f.readline().strip()

    prefaces = []

    # Find all sect1 elements
    sect1_elements = root.findall('.//sect1')

    if not sect1_elements:
        return prefaces

    # First sect1 contains: Title/Copyright, Preface, Editors, Contributors
    first_sect1 = sect1_elements[0]

    # Extract title/copyright (content before first sect2)
    title_copyright_content = []
    sect2_elements = []

    for child in first_sect1:
        if child.tag == 'sect2':
            sect2_elements.append(child)
        elif not sect2_elements:  # Before first sect2
            title_copyright_content.append(child)

    # Add title/copyright as pr0001
    if title_copyright_content:
        prefaces.append({
            'title': 'Title and Copyright',
            'content': title_copyright_content,
            'xml_decl': xml_decl
        })

    # Add each sect2 as a separate preface
    for sect2 in sect2_elements:
        title_elem = sect2.find('title')
        title = title_elem.text if title_elem is not None else 'Untitled'

        # Get all content except title
        content = [child for child in sect2 if child.tag != 'title']

        prefaces.append({
            'title': title,
            'content': content,
            'xml_decl': xml_decl
        })

    # Second sect1 if exists (Dedications + Acknowledgments)
    if len(sect1_elements) > 1:
        second_sect1 = sect1_elements[1]

        # Get dedications title
        title_elem = second_sect1.find('title')
        dedications_title = title_elem.text if title_elem is not None else 'Dedications'

        # Extract content before first sect2 (dedications)
        dedications_content = []
        acknowledgments_sect2 = None

        for child in second_sect1:
            if child.tag == 'sect2':
                acknowledgments_sect2 = child
                break
            elif child.tag != 'title':
                dedications_content.append(child)

        # Add dedications
        if dedications_content:
            prefaces.append({
                'title': dedications_title,
                'content': dedications_content,
                'xml_decl': xml_decl
            })

        # Add acknowledgments
        if acknowledgments_sect2 is not None:
            ack_title_elem = acknowledgments_sect2.find('title')
            ack_title = ack_title_elem.text if ack_title_elem is not None else 'Acknowledgments'
            ack_content = [child for child in acknowledgments_sect2 if child.tag != 'title']

            prefaces.append({
                'title': ack_title,
                'content': ack_content,
                'xml_decl': xml_decl
            })

    return prefaces

def process_chapter_file(chapter_xml_file):
    """Extract chapter information from a chapter file"""
    tree = ET.parse(chapter_xml_file)
    root = tree.getroot()

    with open(chapter_xml_file, 'r', encoding='utf-8') as f:
        xml_decl = f.readline().strip()

    # Find the sect1 or sect2 that contains the chapter
    # Look for title with "Chapter N" pattern
    for sect1 in root.findall('.//sect1'):
        title_elem = sect1.find('.//title')
        if title_elem is not None and title_elem.text:
            match = re.search(r'Chapter\s+(\d+)', title_elem.text)
            if match:
                chapter_num = int(match.group(1))
                return {
                    'chapter_num': chapter_num,
                    'sect1': sect1,
                    'xml_decl': xml_decl
                }

    # Try sect2
    for sect2 in root.findall('.//sect2'):
        title_elem = sect2.find('title')
        if title_elem is not None and title_elem.text:
            match = re.search(r'Chapter\s+(\d+)', title_elem.text)
            if match:
                chapter_num = int(match.group(1))
                # Wrap sect2 in a sect1
                wrapper_sect1 = ET.Element('sect1')
                wrapper_sect1.append(sect2)
                return {
                    'chapter_num': chapter_num,
                    'sect1': wrapper_sect1,
                    'xml_decl': xml_decl
                }

    return None

def main():
    print("=" * 70)
    print("DOCBOOK PROPER SPLITTING WITH ISBN-BASED NAMING")
    print("=" * 70)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Step 1: Process front matter
    print("\nStep 1: Processing Front Matter")
    print("-" * 70)

    front_matter_file = SOURCE_DIR / 'ch001.xml'
    prefaces = extract_preface_sections(front_matter_file)

    preface_files = []
    for i, preface_data in enumerate(prefaces, 1):
        filename = f"preface.{ISBN}.pr{i:04d}.xml"
        filepath = OUTPUT_DIR / filename

        content = create_preface_file(
            preface_data['title'],
            preface_data['content'],
            i,
            preface_data['xml_decl']
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Created: {filename} - {preface_data['title']}")
        preface_files.append(filename)

    # Step 2: Process chapters
    print("\nStep 2: Processing Chapters")
    print("-" * 70)

    chapter_files_map = {}

    # Process each source XML file
    for xml_file in sorted(SOURCE_DIR.glob('ch*.xml')):
        if xml_file.name == 'ch001.xml':
            continue  # Skip front matter

        chapter_info = process_chapter_file(xml_file)
        if chapter_info:
            chapter_num = chapter_info['chapter_num']
            if chapter_num not in chapter_files_map:
                chapter_files_map[chapter_num] = chapter_info

    # Write chapter files
    chapter_filenames = []
    for chapter_num in sorted(chapter_files_map.keys()):
        chapter_info = chapter_files_map[chapter_num]
        filename = f"sect1.{ISBN}.ch{chapter_num:04d}s0000.xml"
        filepath = OUTPUT_DIR / filename

        content = create_chapter_file(
            chapter_num,
            chapter_info['sect1'],
            chapter_info['xml_decl']
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Created: {filename} (Chapter {chapter_num})")
        chapter_filenames.append((chapter_num, filename))

    # Step 3: Copy multimedia
    print("\nStep 3: Copying Multimedia")
    print("-" * 70)

    multimedia_src = SOURCE_DIR / 'multimedia'
    multimedia_dst = OUTPUT_DIR / 'multimedia'

    if multimedia_src.exists():
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
        print(f"  Copied multimedia directory")

    # Step 4: Create Book.XML
    print("\nStep 4: Creating Book.XML")
    print("-" * 70)

    book_filename = f"book.{ISBN}.xml"
    book_path = OUTPUT_DIR / book_filename

    with open(book_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.2//EN"\n')
        f.write('  "http://www.oasis-open.org/docbook/xml/4.2/docbookx.dtd" [\n')

        # Preface entities
        for i in range(1, len(preface_files) + 1):
            f.write(f'<!ENTITY pr{i:04d} SYSTEM "preface.{ISBN}.pr{i:04d}.xml">\n')

        # Chapter entities
        for chapter_num, _ in chapter_filenames:
            f.write(f'<!ENTITY ch{chapter_num:04d}s0000 SYSTEM "sect1.{ISBN}.ch{chapter_num:04d}s0000.xml">\n')

        f.write(']>\n')
        f.write('<book id="mri-bioeffects-safety" lang="en">\n')
        f.write('  <title>MRI Bioeffects, Safety, and Patient Management</title>\n')
        f.write('  <subtitle>Second Edition</subtitle>\n')
        f.write('  <bookinfo>\n')
        f.write(f'    <isbn>{ISBN}</isbn>\n')
        f.write('    <authorgroup>\n')
        f.write('      <author>\n')
        f.write('        <firstname>Frank G.</firstname>\n')
        f.write('        <surname>Shellock</surname>\n')
        f.write('      </author>\n')
        f.write('      <author>\n')
        f.write('        <firstname>John V.</firstname>\n')
        f.write('        <surname>Crues</surname>\n')
        f.write('        <lineage>III</lineage>\n')
        f.write('      </author>\n')
        f.write('    </authorgroup>\n')
        f.write('    <publisher>\n')
        f.write('      <publishername>Biomedical Research Publishing Group</publishername>\n')
        f.write('    </publisher>\n')
        f.write('    <pubdate>2022</pubdate>\n')
        f.write('    <edition>Second Edition</edition>\n')
        f.write('    <copyright>\n')
        f.write('      <year>2022</year>\n')
        f.write('      <holder>Biomedical Research Publishing Group and Shellock R &amp; D Services, Inc.</holder>\n')
        f.write('    </copyright>\n')
        f.write('  </bookinfo>\n')

        # Include preface entities
        for i in range(1, len(preface_files) + 1):
            f.write(f'  &pr{i:04d};\n')

        # Include chapter entities
        for chapter_num, _ in chapter_filenames:
            f.write(f'  &ch{chapter_num:04d}s0000;\n')

        f.write('</book>\n')

    print(f"  Created: {book_filename}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Preface files: {len(preface_files)}")
    print(f"Chapter files: {len(chapter_filenames)}")
    print(f"Total chapters: 1-{max(chapter_files_map.keys())}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("\nFiles follow DocBook naming convention:")
    print(f"  - Prefaces: preface.{ISBN}.pr####.xml")
    print(f"  - Chapters: sect1.{ISBN}.ch####s0000.xml")
    print(f"  - Book: book.{ISBN}.xml")
    print("\nAll internal IDs updated to match root element IDs (CARDINAL RULE)")

if __name__ == '__main__':
    main()
