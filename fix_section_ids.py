#!/usr/bin/env python3
"""
Fix section IDs throughout XML files to match the proper hierarchical format:
- Chapters: ch0000
- Sections (1.1, 1.2): ch0000s0000
- Subsections (1.2.1, 1.2.2): ch0000s0000s0000

Also restructure XML to properly nest subsections inside parent sections.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

def parse_section_number(text):
    """Extract section number from text like '1.2.1 Title' -> (1, 2, 1)"""
    match = re.match(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?\s', text)
    if match:
        parts = [int(p) if p else None for p in match.groups()]
        return tuple(p for p in parts if p is not None)
    return None

def section_to_id(chapter_num, section_parts):
    """Convert section numbering to ID format.
    Examples:
    - (1,) -> ch0011s0001
    - (1, 2) -> ch0011s0001s0002
    - (1, 2, 3) -> ch0011s0001s0002s0003
    """
    if not section_parts:
        return f"ch{str(chapter_num).zfill(4)}"

    parts = [str(p).zfill(4) for p in section_parts]
    return f"ch{str(chapter_num).zfill(4)}s{'s'.join(parts)}"

def analyze_toc_structure(toc_path):
    """Parse TOC to extract the hierarchical structure of all sections."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all tocentry elements with linkends
    pattern = r'<tocentry linkend="([^"]*)">([\d\.]+)\s+([^<]+)</tocentry>'
    matches = re.findall(pattern, content)

    structure = {}
    for linkend, number, title in matches:
        # Parse section number
        parts = tuple(int(p) for p in number.split('.') if p)

        # Determine chapter number (first part)
        if parts:
            ch_num = parts[0]
            # Determine the correct ID based on hierarchy
            if len(parts) == 1:
                # Main chapter section (1, 2, 3)
                new_id = f"ch{str(ch_num + 10).zfill(4)}s{str(parts[0]).zfill(4)}"
            elif len(parts) == 2:
                # Subsection (1.2, 1.3)
                new_id = f"ch{str(ch_num + 10).zfill(4)}s{str(parts[1]).zfill(4)}"
            elif len(parts) == 3:
                # Sub-subsection (1.2.3, 1.4.1)
                parent_id = f"ch{str(ch_num + 10).zfill(4)}s{str(parts[1]).zfill(4)}"
                new_id = f"{parent_id}s{str(parts[2]).zfill(4)}"
            else:
                new_id = linkend

            structure[linkend] = {
                'new_id': new_id,
                'number': number,
                'title': title,
                'parts': parts
            }

    return structure

def update_toc_linkends(toc_path, id_mapping):
    """Update TOC linkends to use new ID format."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace linkends
    for old_id, info in id_mapping.items():
        new_id = info['new_id']
        # Replace linkend="old" with linkend="new"
        content = re.sub(
            f'linkend="{old_id}"',
            f'linkend="{new_id}"',
            content
        )

    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Updated TOC linkends: {len(id_mapping)} replacements")

def update_xml_file_ids(xml_path, id_mapping):
    """Update IDs in XML content files."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = 0
    # Update id attributes
    for old_id, info in id_mapping.items():
        new_id = info['new_id']
        # Replace id="old" with id="new"
        old_pattern = f'id="{old_id}"'
        new_pattern = f'id="{new_id}"'
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            replacements += 1

    if replacements > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {xml_path.name}: {replacements} ID replacements")

    return replacements

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("Analyzing TOC structure...")
    id_mapping = analyze_toc_structure(toc_path)

    print(f"\nFound {len(id_mapping)} sections to update")
    print("\nSample mappings:")
    for old_id, info in list(id_mapping.items())[:10]:
        print(f"  {old_id} -> {info['new_id']} ({info['number']} {info['title'][:40]})")

    print("\nUpdating TOC linkends...")
    update_toc_linkends(toc_path, id_mapping)

    print("\nUpdating XML file IDs...")
    xml_files = list(base_dir.glob("sect1.*.xml"))
    total_replacements = 0
    for xml_file in xml_files:
        replacements = update_xml_file_ids(xml_file, id_mapping)
        total_replacements += replacements

    print(f"\nTotal ID replacements across all files: {total_replacements}")
    print("\nDone! Section IDs have been updated.")

if __name__ == "__main__":
    main()
