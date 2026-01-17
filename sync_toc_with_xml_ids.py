#!/usr/bin/env python3
"""
Sync TOC linkends with actual sect1/sect2/sect3 IDs from XML files.
"""

import re
from pathlib import Path

def extract_all_sections_from_xml(xml_path):
    """Extract all section IDs and titles from an XML file."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = {}

    # Extract sect1
    match = re.search(r'<sect1 id="([^"]+)">', content)
    if match:
        sect1_id = match.group(1)
        sections[sect1_id] = {'id': sect1_id, 'title': '', 'type': 'sect1'}

    # Extract sect2, sect3
    for sect_type in ['sect2', 'sect3']:
        pattern = rf'<{sect_type} id="([^"]+)">\s*<title>([^<]+)</title>'
        for match in re.finditer(pattern, content):
            sect_id = match.group(1)
            title = match.group(2).strip()
            sections[sect_id] = {
                'id': sect_id,
                'title': title,
                'type': sect_type
            }

    return sections

def sync_toc_with_xml_sections(toc_path, all_sections):
    """Update TOC linkends to match actual section IDs from XML."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Build title-to-ID mapping
    title_to_id = {}
    for sect_id, info in all_sections.items():
        title = info['title']
        if title:
            title_to_id[title] = sect_id

            # Also store section number mapping
            num_match = re.match(r'^([\d\.]+)\s+(.*)$', title)
            if num_match:
                section_num = num_match.group(1)
                title_text = num_match.group(2)
                # Store multiple mappings
                title_to_id[section_num] = sect_id
                if title_text:
                    title_to_id[f"{section_num} {title_text}"] = sect_id

    new_lines = []
    changes = 0
    skipped = 0

    for i, line in enumerate(lines):
        # Match tocentry elements
        match = re.search(r'(<tocentry linkend=")([^"]+)(">)([^<]+)(</tocentry>)', line)
        if match:
            old_linkend = match.group(2)
            text = match.group(4).strip()

            # Skip Part entries - they have their own linkends
            if text.startswith('Part '):
                new_lines.append(line)
                skipped += 1
                continue

            # Try to find matching section ID
            new_linkend = None

            # Try exact text match
            if text in title_to_id:
                new_linkend = title_to_id[text]
            else:
                # Try to match by section number
                num_match = re.match(r'^([\d\.]+)\s+(.*)$', text)
                if num_match:
                    section_num = num_match.group(1)
                    if section_num in title_to_id:
                        new_linkend = title_to_id[section_num]

            if new_linkend and new_linkend != old_linkend:
                # Update the linkend
                new_line = match.group(1) + new_linkend + match.group(3) + match.group(4) + match.group(5) + '\n'
                # Preserve the indentation
                indent_match = re.match(r'^(\s*)', line)
                if indent_match:
                    indent = indent_match.group(1)
                    new_line = indent + new_line.lstrip()

                new_lines.append(new_line)
                changes += 1
                if changes <= 20:
                    print(f"  {old_linkend:30} → {new_linkend:30} | {text[:35]}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    print(f"\nTotal changes: {changes}")
    print(f"Skipped (Parts): {skipped}")

    if changes > 0:
        with open(toc_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("\n✅ TOC updated successfully!")

    return changes

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("=" * 80)
    print("SYNCING TOC WITH XML SECTION IDs")
    print("=" * 80)

    print("\nExtracting all section IDs from XML files...")
    all_sections = {}
    xml_files = sorted(base_dir.glob("sect1.*.xml"))

    for xml_file in xml_files:
        sections = extract_all_sections_from_xml(xml_file)
        all_sections.update(sections)

    print(f"Found {len(all_sections)} total sections")

    print("\nUpdating TOC linkends...")
    print("=" * 80)
    sync_toc_with_xml_sections(toc_path, all_sections)

    print("\nDone!")

if __name__ == "__main__":
    main()
