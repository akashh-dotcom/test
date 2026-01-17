#!/usr/bin/env python3
"""
Final comprehensive fix for all section IDs.
Directly extract sections from XML files and update their IDs based on TOC linkends.
"""

import re
from pathlib import Path

def extract_section_structure_from_xml(xml_path):
    """Extract all sections with their IDs and titles from an XML file."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = []
    # Pattern to match sect elements with ID and title
    # <sect2 id="ch0011s1000">
    #    <title>1.1 Introduction</title>
    pattern = r'<sect(\d+)\s+id="([^"]+)"[^>]*>\s*<title>([^<]+)</title>'

    for match in re.finditer(pattern, content):
        level = int(match.group(1))
        old_id = match.group(2)
        title = match.group(3).strip()

        sections.append({
            'level': level,
            'old_id': old_id,
            'title': title
        })

    return sections

def calculate_new_id_from_title(title):
    """Calculate the correct ID from a section title like '1.4.1 Role of...'"""
    # Extract section number
    num_match = re.match(r'^([\d\.]+)\s', title)
    if not num_match:
        return None

    section_num = num_match.group(1)
    parts = [int(p) for p in section_num.split('.')]

    if not parts:
        return None

    ch_num = parts[0]
    ch_id = f"ch{str(ch_num + 10).zfill(4)}"

    if len(parts) == 1:
        # Chapter level - shouldn't happen in sections
        return ch_id
    elif len(parts) == 2:
        # Section like 1.2
        sec_num = parts[1]
        return f"{ch_id}s{str(sec_num).zfill(4)}"
    elif len(parts) == 3:
        # Subsection like 1.4.1
        sec_num = parts[1]
        subsec_num = parts[2]
        return f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}"
    elif len(parts) == 4:
        # Sub-subsection like 3.3.6.1
        sec_num = parts[1]
        subsec_num = parts[2]
        subsubsec_num = parts[3]
        return f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}s{str(subsubsec_num).zfill(4)}"

    return None

def update_xml_file_with_correct_ids(xml_path):
    """Update all IDs in an XML file to match the correct format."""
    # Extract sections
    sections = extract_section_structure_from_xml(xml_path)

    # Build ID mapping
    id_mapping = {}
    for section in sections:
        new_id = calculate_new_id_from_title(section['title'])
        if new_id and new_id != section['old_id']:
            id_mapping[section['old_id']] = new_id

    if not id_mapping:
        return 0

    # Read file
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply replacements
    replacements = 0
    for old_id, new_id in id_mapping.items():
        if f'id="{old_id}"' in content:
            content = content.replace(f'id="{old_id}"', f'id="{new_id}"')
            replacements += 1

    # Write back
    if replacements > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {xml_path.name}: {replacements} replacements")

    return replacements

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("Updating XML file IDs...")
    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0
    for xml_file in xml_files:
        total += update_xml_file_with_correct_ids(xml_file)

    print(f"\nTotal replacements: {total}")
    print("Done!")

if __name__ == "__main__":
    main()
