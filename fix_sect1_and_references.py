#!/usr/bin/env python3
"""
Fix sect1 IDs and assign proper IDs to sections without numbers (like References).
"""

import re
from pathlib import Path

def fix_sect1_and_unnumbered(xml_path):
    """Update sect1 ID and handle unnumbered sections."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = 0

    # Fix sect1 ID (ch0011s0000 -> ch0011)
    sect1_match = re.search(r'<sect1 id="(ch\d{4})s0000">', content)
    if sect1_match:
        ch_id = sect1_match.group(1)
        content = content.replace(f'<sect1 id="{ch_id}s0000">', f'<sect1 id="{ch_id}">')
        replacements += 1

        # Find all sections without numbers (like "References")
        # These typically have old IDs like ch0011s9000
        pattern = r'<sect2 id="(ch\d{4})s9000">\s*<title>([^<]+)</title>'
        matches = list(re.finditer(pattern, content))

        # Get the highest section number in this chapter
        all_sect_ids = re.findall(r'<sect2 id="(ch\d{4}s\d{4})">', content)
        max_sec = 0
        for sect_id in all_sect_ids:
            match = re.search(r's(\d{4})(?:s|$)', sect_id)
            if match:
                sec_num = int(match.group(1))
                if sec_num < 9000 and sec_num > max_sec:
                    max_sec = sec_num

        # Assign sequential IDs to unnumbered sections
        for i, match in enumerate(reversed(matches)):
            new_sec_num = max_sec + i + 1
            new_id = f"{ch_id}s{str(new_sec_num).zfill(4)}"
            old_pattern = f'<sect2 id="{ch_id}s9000">'
            # Replace only this occurrence (from the end)
            old_text = match.group(0)
            new_text = old_text.replace(f'id="{ch_id}s9000"', f'id="{new_id}"')
            content = content[:match.start()] + new_text + content[match.end():]
            replacements += 1

    if replacements > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {xml_path.name}: {replacements} replacements")

    return replacements

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("Fixing sect1 IDs and unnumbered sections...")
    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0
    for xml_file in xml_files:
        total += fix_sect1_and_unnumbered(xml_file)

    print(f"\nTotal replacements: {total}")
    print("Done!")

if __name__ == "__main__":
    main()
