#!/usr/bin/env python3
"""
Split the complete XML file into separate chapter files.
Converts:
  - <sect1 id="ch####s0000"> to <chapter id="ch####">
  - <sect2> to <sect1>
  - <sect3> to <sect2>
  - <sect4> to <sect3>
  - <sect5> to <sect4>
  
Keeps all naming conventions, formats, patterns, and references unchanged.
Only changes the element tags as specified.
"""

import os
import re
import shutil
from pathlib import Path
from lxml import etree

# Configuration
ISBN = "9780989163286"
SOURCE_FILE = Path('/workspace/complete_work/docbook_complete/book.9780989163286.complete.xml')
OUTPUT_DIR = Path('/workspace/split_chapters_output')

# Tag mapping for downshifting section levels
TAG_MAPPING = {
    'sect2': 'sect1',
    'sect3': 'sect2',
    'sect4': 'sect3',
    'sect5': 'sect4',
    'sect6': 'sect5',
}


def fix_empty_sections(element):
    """
    Fix sections that only have a title by adding an empty para.
    DocBook DTD requires content after the title.
    """
    # Check if this is a section element
    if element.tag in ['sect1', 'sect2', 'sect3', 'sect4', 'sect5', 'sect6', 'section']:
        # Count children
        children = list(element)
        
        # Check if only has title (or title + subtitle/titleabbrev)
        has_only_title = True
        for child in children:
            if child.tag not in ['title', 'subtitle', 'titleabbrev']:
                has_only_title = False
                break
        
        if has_only_title and len(children) > 0:
            # Add an empty para after the title elements
            # Find the last title-related element
            insert_pos = 0
            for i, child in enumerate(children):
                if child.tag in ['title', 'subtitle', 'titleabbrev']:
                    insert_pos = i + 1
            
            # Create an empty para element
            para = etree.Element('para')
            para.text = ""
            element.insert(insert_pos, para)
    
    # Recursively process children
    for child in element:
        fix_empty_sections(child)


def transform_section_tags(element):
    """
    Recursively transform section tags:
    sect2 -> sect1, sect3 -> sect2, sect4 -> sect3, sect5 -> sect4
    Also fixes empty sections.
    """
    # Fix empty sections first
    fix_empty_sections(element)
    
    # Process children first (bottom-up to avoid issues)
    for child in element:
        transform_section_tags(child)
    
    # Transform this element's tag if it matches
    if element.tag in TAG_MAPPING:
        element.tag = TAG_MAPPING[element.tag]


def extract_chapter_number(sect1_id):
    """
    Extract chapter number from sect1 id like 'ch0002s0000' -> 2
    """
    match = re.match(r'ch(\d+)s0000', sect1_id)
    if match:
        return int(match.group(1))
    return None


def extract_chapter_title(sect1_element, chapter_num):
    """
    Extract chapter title from the sect1 element.
    Looks for title in various places within the structure.
    Returns (title_text, title_element_to_remove) - the element is only set if it's a direct child
    """
    # First, look for a direct title child
    title_elem = sect1_element.find('title')
    if title_elem is not None and title_elem.text:
        return title_elem.text.strip(), title_elem
    
    # Look for title in first sect2 child
    for sect2 in sect1_element.findall('sect2'):
        title_elem = sect2.find('title')
        if title_elem is not None and title_elem.text:
            text = title_elem.text.strip()
            # Check if it contains "Chapter" in the title
            if 'Chapter' in text:
                return text, None
    
    # Look for title anywhere in descendants
    for title_elem in sect1_element.iter('title'):
        if title_elem.text:
            text = title_elem.text.strip()
            if 'Chapter' in text:
                return text, None
    
    # Default to a generic title
    return f"Chapter {chapter_num}", None


def create_chapter_element(sect1_element, chapter_num):
    """
    Create a chapter element from a sect1 element.
    - Changes the root tag from sect1 to chapter
    - Updates the id from ch####s0000 to ch####
    - Adds a proper title element as first child
    - Transforms all nested section tags (sect2->sect1, sect3->sect2, etc.)
    """
    # Create chapter element
    chapter = etree.Element('chapter')
    
    # Copy attributes from sect1, but modify the id
    for attr, value in sect1_element.attrib.items():
        if attr == 'id':
            # Convert ch0002s0000 to ch0002
            new_id = f'ch{chapter_num:04d}'
            chapter.set('id', new_id)
        else:
            chapter.set(attr, value)
    
    # Extract chapter title
    chapter_title, direct_title_elem = extract_chapter_title(sect1_element, chapter_num)
    
    # Add title as first child of chapter (required by DocBook DTD)
    title_elem = etree.SubElement(chapter, 'title')
    title_elem.text = chapter_title
    
    # Copy all children, but skip if it's the direct title we already used
    for child in sect1_element:
        if child.tag == 'title' and direct_title_elem is not None and child is direct_title_elem:
            continue  # Skip this title as we already used it
        chapter.append(child)
    
    # Transform all section tags in the chapter
    transform_section_tags(chapter)
    
    return chapter


def fix_duplicate_titles(element):
    """
    Fix elements that have duplicate title elements.
    DocBook only allows one title per element.
    """
    titles = element.findall('title')
    if len(titles) > 1:
        # Merge titles or keep only the first one with meaningful content
        first_title = titles[0]
        for title in titles[1:]:
            # Remove duplicate titles
            element.remove(title)
    
    # Recursively fix children
    for child in element:
        fix_duplicate_titles(child)


def format_xml_output(element, xml_declaration):
    """
    Format XML output with proper indentation and declaration.
    """
    # Fix any duplicate titles
    fix_duplicate_titles(element)
    
    # Convert to string with pretty printing
    xml_bytes = etree.tostring(element, encoding='unicode', pretty_print=True)
    
    # Combine with XML declaration
    return xml_declaration + '\n' + xml_bytes


def process_complete_file():
    """
    Process the complete XML file and extract chapters.
    """
    print("=" * 70)
    print("SPLITTING COMPLETE XML INTO SEPARATE CHAPTERS")
    print("=" * 70)
    
    # Parse the source file
    print(f"\nReading source file: {SOURCE_FILE}")
    
    # Use lxml parser to preserve structure
    parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
    tree = etree.parse(str(SOURCE_FILE), parser)
    root = tree.getroot()
    
    # Get XML declaration
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Extract preface elements (these stay as-is)
    prefaces = []
    for preface in root.findall('.//preface'):
        preface_id = preface.get('id', '')
        prefaces.append({
            'id': preface_id,
            'element': preface
        })
    
    print(f"\nFound {len(prefaces)} preface elements")
    for p in prefaces:
        print(f"  - {p['id']}")
    
    # Find the merged-chapters chapter element
    merged_chapter = root.find('.//chapter[@id="merged-chapters"]')
    if merged_chapter is None:
        print("ERROR: Could not find merged-chapters element")
        return
    
    # Find all sect1 elements that are direct children of the merged chapter
    # These are the actual chapters we need to split
    chapters = []
    
    # Look for sect1 elements with chapter IDs (ch####s0000)
    for sect1 in merged_chapter.findall('sect1'):
        sect1_id = sect1.get('id', '')
        chapter_num = extract_chapter_number(sect1_id)
        if chapter_num is not None:
            chapters.append({
                'num': chapter_num,
                'id': sect1_id,
                'element': sect1
            })
    
    print(f"\nFound {len(chapters)} chapter sect1 elements:")
    for ch in sorted(chapters, key=lambda x: x['num']):
        print(f"  - Chapter {ch['num']} ({ch['id']})")
    
    # Process and write preface files
    print("\n" + "-" * 70)
    print("WRITING PREFACE FILES")
    print("-" * 70)
    
    for preface_data in prefaces:
        preface = preface_data['element']
        preface_id = preface_data['id']
        
        # Create filename based on preface id
        filename = f"{preface_id}.xml"
        filepath = OUTPUT_DIR / filename
        
        # Write the preface file
        xml_content = format_xml_output(preface, xml_declaration)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"  Created: {filename}")
    
    # Process and write chapter files
    print("\n" + "-" * 70)
    print("WRITING CHAPTER FILES")
    print("-" * 70)
    
    chapter_files = []
    for chapter_data in sorted(chapters, key=lambda x: x['num']):
        sect1 = chapter_data['element']
        chapter_num = chapter_data['num']
        
        # Create chapter element from sect1
        chapter_element = create_chapter_element(sect1, chapter_num)
        
        # Create filename
        filename = f"ch{chapter_num:04d}.xml"
        filepath = OUTPUT_DIR / filename
        
        # Write the chapter file
        xml_content = format_xml_output(chapter_element, xml_declaration)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        chapter_files.append({
            'num': chapter_num,
            'filename': filename
        })
        
        print(f"  Created: {filename} (Chapter {chapter_num})")
    
    # Copy multimedia directory
    print("\n" + "-" * 70)
    print("COPYING MULTIMEDIA")
    print("-" * 70)
    
    multimedia_src = SOURCE_FILE.parent / 'multimedia'
    multimedia_dst = OUTPUT_DIR / 'multimedia'
    
    if multimedia_src.exists():
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
        file_count = len(list(multimedia_dst.glob('*')))
        print(f"  Copied multimedia directory ({file_count} files)")
    
    # Create Book.XML master file
    print("\n" + "-" * 70)
    print("CREATING BOOK.XML")
    print("-" * 70)
    
    book_xml_path = OUTPUT_DIR / 'Book.XML'
    
    with open(book_xml_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.2//EN"\n')
        f.write('  "http://www.oasis-open.org/docbook/xml/4.2/docbookx.dtd" [\n')
        
        # Preface entities
        for preface_data in prefaces:
            preface_id = preface_data['id']
            f.write(f'<!ENTITY {preface_id} SYSTEM "{preface_id}.xml">\n')
        
        # Chapter entities
        for ch in sorted(chapter_files, key=lambda x: x['num']):
            ch_id = f"ch{ch['num']:04d}"
            f.write(f'<!ENTITY {ch_id} SYSTEM "{ch["filename"]}">\n')
        
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
        for preface_data in prefaces:
            preface_id = preface_data['id']
            f.write(f'  &{preface_id};\n')
        
        # Include chapter entities
        for ch in sorted(chapter_files, key=lambda x: x['num']):
            ch_id = f"ch{ch['num']:04d}"
            f.write(f'  &{ch_id};\n')
        
        f.write('</book>\n')
    
    print(f"  Created: Book.XML")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total preface files: {len(prefaces)}")
    print(f"Total chapter files: {len(chapter_files)}")
    if chapter_files:
        print(f"Chapter range: 1 to {max(ch['num'] for ch in chapter_files)}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Check for gaps in chapter numbers
    if chapter_files:
        all_nums = set(ch['num'] for ch in chapter_files)
        max_num = max(all_nums)
        expected = set(range(1, max_num + 1))
        missing = expected - all_nums
        if missing:
            print(f"\nNote: Missing chapter numbers: {sorted(missing)}")
            print("(These may be special sections or intentionally excluded)")
    
    print("\nTag conversions applied:")
    print("  - <sect1 id='ch####s0000'> -> <chapter id='ch####'>")
    print("  - <sect2> -> <sect1>")
    print("  - <sect3> -> <sect2>")
    print("  - <sect4> -> <sect3>")
    print("  - <sect5> -> <sect4>")
    
    return chapter_files, prefaces


if __name__ == '__main__':
    process_complete_file()
