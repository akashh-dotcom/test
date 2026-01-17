#!/usr/bin/env python3
"""
Simple approach: Just convert sect2 tags to sect3 for subsections.
This at least corrects the tag types, even if nesting needs more work.
"""

import re
from pathlib import Path

def convert_tags_only(xml_path):
    """Convert sect2 to sect3/sect4 based on ID structure."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    changes = 0
    sect_stack = []  # Track open sections

    for line in lines:
        new_line = line

        # Check for opening sect2 tags
        open_match = re.search(r'<sect2 id="(ch\d{4}(?:s\d{4})+)">', line)
        if open_match:
            sect_id = open_match.group(1)
            level = sect_id.count('s')  # Number of 's' indicates depth

            if level == 2:  # ch####s####s#### → sect3
                new_line = line.replace('<sect2 id=', '<sect3 id=')
                sect_stack.append('sect3')
                changes += 1
            elif level == 3:  # ch####s####s####s#### → sect4
                new_line = line.replace('<sect2 id=', '<sect4 id=')
                sect_stack.append('sect4')
                changes += 1
            elif level == 1:  # ch####s#### → keep as sect2
                sect_stack.append('sect2')
            else:
                sect_stack.append('sect2')

        # Check for closing sect2 tags
        elif '</sect2>' in line and sect_stack:
            last_type = sect_stack.pop()
            if last_type != 'sect2':
                new_line = line.replace('</sect2>', f'</{last_type}>')

        new_lines.append(new_line)

    if changes > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  {xml_path.name}: {changes} tags converted")

    return changes

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("=" * 80)
    print("CONVERTING SUBSECTION TAGS (sect2 → sect3/sect4)")
    print("=" * 80)
    print()

    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0

    for xml_file in xml_files:
        total += convert_tags_only(xml_file)

    print()
    print("=" * 80)
    print(f"Total tags converted: {total}")
    print("=" * 80)
    print()
    print("Note: This converts tags but doesn't restructure nesting.")
    print("Subsections are now <sect3> but may still be siblings of <sect2>.")
    print("Full nesting restructure is a more complex operation.")

if __name__ == "__main__":
    main()
