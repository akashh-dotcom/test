#!/usr/bin/env python3
"""
Update all IDs in XML files to match the TOC linkends.
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_id_mapping_from_toc(toc_path):
    """Extract all linkends from TOC with their section numbers."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all tocentry elements
    pattern = r'<tocentry linkend="([^"]+)">([^<]+)</tocentry>'
    matches = re.findall(pattern, content)

    id_to_text = {}
    for linkend, text in matches:
        id_to_text[linkend] = text.strip()

    return id_to_text

def update_xml_file(xml_path, id_mapping):
    """Update IDs in an XML file based on section titles."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all sect1, sect2, sect3 elements with IDs and titles
    # Pattern: <sect2 id="old_id">...<title>Section Title</title>
    original_content = content
    replacements = 0

    # First, build a mapping of old IDs to new IDs based on title matching
    old_to_new = {}

    # Find all section elements
    sect_pattern = r'<sect\d+ id="([^"]+)">\s*(?:<title>([^<]+)</title>|.*?<title>([^<]+)</title>)'
    for match in re.finditer(sect_pattern, content, re.DOTALL):
        old_id = match.group(1)
        title = match.group(2) or match.group(3)
        if title:
            title = title.strip()
            # Find matching linkend from TOC
            for linkend, toc_text in id_mapping.items():
                # Check if the title matches (handle cases where section number might differ)
                if title in toc_text or toc_text.endswith(title):
                    if old_id != linkend:
                        old_to_new[old_id] = linkend
                        break

    # Apply replacements
    for old_id, new_id in old_to_new.items():
        # Replace id="old" with id="new"
        if f'id="{old_id}"' in content:
            content = content.replace(f'id="{old_id}"', f'id="{new_id}"')
            replacements += 1

    if replacements > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {xml_path.name}: {replacements} ID updates")

    return replacements

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("Extracting ID mapping from TOC...")
    id_mapping = extract_id_mapping_from_toc(toc_path)
    print(f"Found {len(id_mapping)} linkends in TOC")

    print("\nUpdating XML files...")
    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0
    for xml_file in xml_files:
        total += update_xml_file(xml_file, id_mapping)

    print(f"\nTotal updates: {total}")
    print("Done!")

if __name__ == "__main__":
    main()
