#!/usr/bin/env python3
"""
Fix all sect2/sect3 IDs in each XML file to match their parent chapter.
"""

import re
from pathlib import Path

def fix_sect_ids_in_file(xml_path):
    """Fix all sect2/sect3 IDs in a file based on its chapter number."""
    # Extract chapter ID from filename
    ch_match = re.search(r'ch(\d{4})', xml_path.name)
    if not ch_match:
        return 0

    ch_id = f"ch{ch_match.group(1)}"

    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    replacements = 0

    # Find all sect2 and sect3 elements with IDs and titles
    # Replace IDs that don't start with the correct chapter ID
    for sect_type in ['sect2', 'sect3']:
        pattern = rf'(<{sect_type} id=")([^"]+)("[^>]*>\s*<title>)([^<]+)(</title>)'

        matches = list(re.finditer(pattern, content))

        for match in reversed(matches):  # Process in reverse to avoid position shifting
            old_id = match.group(2)
            title = match.group(4).strip()

            # Check if ID starts with correct chapter
            if not old_id.startswith(ch_id):
                # Calculate new ID from title
                new_id = calculate_correct_id(ch_id, title)

                if new_id:
                    # Replace this specific occurrence
                    old_text = match.group(0)
                    new_text = match.group(1) + new_id + match.group(3) + match.group(4) + match.group(5)
                    content = content[:match.start()] + new_text + content[match.end():]
                    replacements += 1

    if replacements > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {xml_path.name}: {replacements} ID fixes")

    return replacements

def calculate_correct_id(ch_id, title):
    """Calculate correct ID from chapter ID and section title."""
    # Extract section number from title
    num_match = re.match(r'^([\d\.]+)\s', title)
    if not num_match:
        return None

    section_num = num_match.group(1)
    parts = [int(p) for p in section_num.split('.')]

    if len(parts) < 2:
        return None

    # Build ID based on section depth
    # parts[0] is chapter number (ignore, use ch_id instead)
    # parts[1] is section number
    # parts[2] is subsection number (if exists)
    # parts[3] is sub-subsection number (if exists)

    if len(parts) == 2:
        # Section like 17.2
        sec_num = parts[1]
        return f"{ch_id}s{str(sec_num).zfill(4)}"
    elif len(parts) == 3:
        # Subsection like 17.2.1
        sec_num = parts[1]
        subsec_num = parts[2]
        return f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}"
    elif len(parts) == 4:
        # Sub-subsection like 17.2.1.3
        sec_num = parts[1]
        subsec_num = parts[2]
        subsubsec_num = parts[3]
        return f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}s{str(subsubsec_num).zfill(4)}"

    return None

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("Fixing sect2/sect3 IDs in all XML files...")
    print("=" * 80)

    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0

    for xml_file in xml_files:
        total += fix_sect_ids_in_file(xml_file)

    print("=" * 80)
    print(f"\nTotal ID fixes: {total}")
    print("Done!")

if __name__ == "__main__":
    main()
