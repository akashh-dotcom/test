#!/usr/bin/env python3
"""
Script to merge all RITTDOC chapter files into a single fulloutput.xml file.
Preserves all content and properly remaps chapter IDs to avoid conflicts.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

def fix_chapter_ids(xml_content, chapter_num):
    """
    Fix chapter IDs in XML content to be unique.
    Changes ch0001 to ch{chapter_num:04d} for all IDs.
    """
    # Pattern to match chapter IDs
    old_id = "ch0001"
    new_id = f"ch{chapter_num:04d}"

    # Replace all occurrences of the old ID with the new ID
    xml_content = xml_content.replace(f'id="{old_id}"', f'id="{new_id}"')
    xml_content = xml_content.replace(f'"{old_id}s', f'"{new_id}s')

    return xml_content

def merge_chapters(input_dir, output_file):
    """
    Merge all chapter XML files into a single document.
    """
    input_path = Path(input_dir)

    # Get all chapter files sorted by name
    chapter_files = sorted(input_path.glob("ch*.xml"))

    print(f"Found {len(chapter_files)} chapter files to merge")

    # Start building the merged XML
    merged_content = []

    # Add XML declaration and root element
    merged_content.append('<?xml version="1.0" encoding="UTF-8"?>')
    merged_content.append('<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.2//EN"')
    merged_content.append('  "http://www.oasis-open.org/docbook/xml/4.2/docbookx.dtd">')
    merged_content.append('<book id="mri-bioeffects-safety" lang="en">')
    merged_content.append('  <title>MRI Bioeffects, Safety, and Patient Management</title>')
    merged_content.append('  <subtitle>Second Edition</subtitle>')
    merged_content.append('  <bookinfo>')
    merged_content.append('    <isbn>978-0-9891632-8-6</isbn>')
    merged_content.append('    <authorgroup>')
    merged_content.append('      <author>')
    merged_content.append('        <firstname>Frank G.</firstname>')
    merged_content.append('        <surname>Shellock</surname>')
    merged_content.append('      </author>')
    merged_content.append('      <author>')
    merged_content.append('        <firstname>John V.</firstname>')
    merged_content.append('        <surname>Crues</surname>')
    merged_content.append('        <lineage>III</lineage>')
    merged_content.append('      </author>')
    merged_content.append('    </authorgroup>')
    merged_content.append('    <publisher>')
    merged_content.append('      <publishername>Biomedical Research Publishing Group</publishername>')
    merged_content.append('    </publisher>')
    merged_content.append('    <pubdate>2022</pubdate>')
    merged_content.append('    <edition>Second Edition</edition>')
    merged_content.append('    <copyright>')
    merged_content.append('      <year>2022</year>')
    merged_content.append('      <holder>Biomedical Research Publishing Group and Shellock R &amp; D Services, Inc.</holder>')
    merged_content.append('    </copyright>')
    merged_content.append('  </bookinfo>')

    # Process each chapter
    for idx, chapter_file in enumerate(chapter_files, start=1):
        print(f"Processing {chapter_file.name}...")

        # Read the chapter file
        with open(chapter_file, 'r', encoding='utf-8') as f:
            chapter_content = f.read()

        # Remove XML declaration if present
        chapter_content = re.sub(r'<\?xml[^>]*\?>\s*', '', chapter_content)

        # Fix chapter IDs to be unique
        chapter_content = fix_chapter_ids(chapter_content, idx)

        # Extract the chapter element content (everything between <chapter> and </chapter>)
        chapter_match = re.search(r'<chapter[^>]*>(.+)</chapter>', chapter_content, re.DOTALL)
        if chapter_match:
            chapter_inner = chapter_match.group(0)
            # Update the label attribute
            chapter_inner = re.sub(r'label="1"', f'label="{idx}"', chapter_inner)
            merged_content.append('  ' + chapter_inner)
        else:
            print(f"Warning: Could not extract chapter content from {chapter_file.name}")

    # Close the book element
    merged_content.append('</book>')

    # Write the merged content
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merged_content))

    print(f"\nMerged content written to {output_file}")
    print(f"Total chapters merged: {len(chapter_files)}")

if __name__ == "__main__":
    input_directory = "extracted_rittdoc"
    output_filename = "fulloutput.xml"

    merge_chapters(input_directory, output_filename)
    print("Merge completed successfully!")
