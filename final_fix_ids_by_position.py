#!/usr/bin/env python3
"""
Fix IDs in XML files by updating them position by position.
"""

import re
from pathlib import Path

def fix_xml_ids_by_position(xml_path):
    """Update IDs in XML file by processing each section in order."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all sect elements with their positions
    pattern = r'(<sect\d+\s+id=")([^"]+)("[^>]*>\s*<title>)([^<]+)(</title>)'
    matches = list(re.finditer(pattern, content))

    # Process matches in reverse order to avoid position shifting
    replacements = 0
    for match in reversed(matches):
        old_id = match.group(2)
        title = match.group(4).strip()

        # Calculate new ID from title
        new_id = calculate_new_id_from_title(title)

        if new_id and new_id != old_id:
            # Replace this specific occurrence
            old_text = match.group(0)
            new_text = match.group(1) + new_id + match.group(3) + match.group(4) + match.group(5)
            content = content[:match.start()] + new_text + content[match.end():]
            replacements += 1

    if replacements > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {xml_path.name}: {replacements} replacements")

    return replacements

def calculate_new_id_from_title(title):
    """Calculate the correct ID from a section title."""
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
        return ch_id
    elif len(parts) == 2:
        sec_num = parts[1]
        return f"{ch_id}s{str(sec_num).zfill(4)}"
    elif len(parts) == 3:
        sec_num = parts[1]
        subsec_num = parts[2]
        return f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}"
    elif len(parts) == 4:
        sec_num = parts[1]
        subsec_num = parts[2]
        subsubsec_num = parts[3]
        return f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}s{str(subsubsec_num).zfill(4)}"

    return None

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("Restoring XML files and re-applying fixes...")
    # First restore
    import subprocess
    subprocess.run(['git', 'restore', 'sect1.*.xml'], cwd=base_dir, capture_output=True)

    print("\nUpdating XML file IDs by position...")
    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0
    for xml_file in xml_files:
        total += fix_xml_ids_by_position(xml_file)

    print(f"\nTotal replacements: {total}")
    print("Done!")

if __name__ == "__main__":
    main()
