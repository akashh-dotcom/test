#!/usr/bin/env python3
"""
Fix TOC to match all sect2/sect3 IDs found in XML files.
"""

import re
from pathlib import Path

def extract_all_section_ids(xml_path):
    """Extract all sect2 and sect3 IDs with their titles."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = []

    # Extract chapter number from filename
    ch_match = re.search(r'ch(\d{4})', xml_path.name)
    if not ch_match:
        return sections

    ch_id = f"ch{ch_match.group(1)}"

    # Extract sect2 and sect3
    for sect_type in ['sect2', 'sect3']:
        pattern = rf'<{sect_type} id="([^"]+)">\s*<title>([^<]+)</title>'
        for match in re.finditer(pattern, content):
            sect_id = match.group(1)
            title = match.group(2).strip()
            # Only include sections from this chapter
            if sect_id.startswith(ch_id):
                sections.append({
                    'id': sect_id,
                    'title': title,
                    'chapter': ch_id
                })

    return sections

def fix_toc_linkends(toc_path, xml_sections):
    """Update TOC linkends to match XML section IDs."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Build a mapping of title text to section ID
    title_to_id = {}
    for section in xml_sections:
        # Store both full title and section number
        title_to_id[section['title']] = section['id']
        # Also extract section number for matching
        num_match = re.match(r'^([\d\.]+)\s+(.+)$', section['title'])
        if num_match:
            section_num = num_match.group(1)
            title_text = num_match.group(2)
            title_to_id[f"{section_num}"] = section['id']
            title_to_id[title_text] = section['id']

    new_lines = []
    changes = 0

    for line in lines:
        # Check if this is a tocentry with linkend
        match = re.search(r'<tocentry linkend="([^"]+)">([^<]+)</tocentry>', line)
        if match:
            old_linkend = match.group(1)
            text = match.group(2).strip()

            # Skip Part entries
            if text.startswith('Part '):
                new_lines.append(line)
                continue

            # Try to find matching section ID
            new_linkend = None

            # First try exact title match
            if text in title_to_id:
                new_linkend = title_to_id[text]
            else:
                # Try to extract section number and match
                num_match = re.match(r'^([\d\.]+)\s+(.+)$', text)
                if num_match:
                    section_num = num_match.group(1)
                    title_text = num_match.group(2)

                    if section_num in title_to_id:
                        new_linkend = title_to_id[section_num]
                    elif title_text in title_to_id:
                        new_linkend = title_to_id[title_text]

            if new_linkend and new_linkend != old_linkend:
                # Replace the linkend
                new_line = line.replace(f'linkend="{old_linkend}"', f'linkend="{new_linkend}"')
                new_lines.append(new_line)
                changes += 1
                if changes <= 10:  # Show first 10 changes
                    print(f"  {old_linkend:30} → {new_linkend:30} | {text[:40]}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if changes > 0:
        with open(toc_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"\nUpdated {changes} linkends in TOC")
    else:
        print("\nNo changes needed")

    return changes

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("Extracting all section IDs from XML files...")
    all_sections = []
    for xml_file in sorted(base_dir.glob("sect1.*.xml")):
        sections = extract_all_section_ids(xml_file)
        all_sections.extend(sections)

    print(f"Found {len(all_sections)} sections")

    print("\nUpdating TOC linkends to match XML...")
    fix_toc_linkends(toc_path, all_sections)

    print("\nDone!")

if __name__ == "__main__":
    main()
