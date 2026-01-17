#!/usr/bin/env python3
"""
Comprehensively fix all section IDs and linkends throughout the document.
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_section_info_from_toc(toc_path):
    """Parse TOC to extract all sections with their proper hierarchy."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sections = []
    current_chapter = None

    for i, line in enumerate(lines):
        # Match tocentry with linkend
        match = re.search(r'<tocentry linkend="([^"]*)">(.*?)</tocentry>', line)
        if not match:
            continue

        old_linkend = match.group(1)
        text = match.group(2).strip()

        # Determine if this is a chapter or section based on context
        # Check if it's inside a tocchap (chapter)
        is_chapter_title = '<tocchap>' in lines[max(0, i-5):i+1][-1] if i > 0 else False

        # Try to extract section number
        num_match = re.match(r'^([\d\.]+)\s+(.+)$', text)

        if num_match:
            section_num = num_match.group(1)
            title = num_match.group(2)

            parts = section_num.split('.')

            # Determine chapter number
            if parts:
                ch_num = int(parts[0])
                ch_id = f"ch{str(ch_num + 10).zfill(4)}"

                # Build the correct ID based on hierarchy
                if len(parts) == 1:
                    # Main chapter (e.g., "1 Introduction...")
                    new_id = ch_id
                    current_chapter = ch_num
                elif len(parts) == 2:
                    # Section (e.g., "1.2 Terminology")
                    sec_num = int(parts[1])
                    new_id = f"{ch_id}s{str(sec_num).zfill(4)}"
                elif len(parts) == 3:
                    # Subsection (e.g., "1.4.1 Role of...")
                    sec_num = int(parts[1])
                    subsec_num = int(parts[2])
                    new_id = f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}"
                elif len(parts) == 4:
                    # Sub-subsection (e.g., "3.3.6.1 Local...")
                    sec_num = int(parts[1])
                    subsec_num = int(parts[2])
                    subsubsec_num = int(parts[3])
                    new_id = f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}s{str(subsubsec_num).zfill(4)}"
                else:
                    new_id = old_linkend

                sections.append({
                    'old_id': old_linkend,
                    'new_id': new_id,
                    'number': section_num,
                    'title': title,
                    'line_num': i
                })
        else:
            # No number found (like "References"), assign sequential ID
            if current_chapter:
                # Count previous sections for this chapter
                ch_sections = [s for s in sections if s['new_id'].startswith(f"ch{str(current_chapter + 10).zfill(4)}")]
                # Find the highest section number
                max_sec = 0
                for s in ch_sections:
                    match = re.search(r's(\d{4})(?:s|$)', s['new_id'])
                    if match:
                        sec_num = int(match.group(1))
                        if sec_num > max_sec:
                            max_sec = sec_num

                new_id = f"ch{str(current_chapter + 10).zfill(4)}s{str(max_sec + 1).zfill(4)}"
                sections.append({
                    'old_id': old_linkend,
                    'new_id': new_id,
                    'number': '',
                    'title': text,
                    'line_num': i
                })

    return sections

def update_toc_with_new_ids(toc_path, sections):
    """Update TOC file with new linkend IDs."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create mapping
    id_map = {s['old_id']: s['new_id'] for s in sections}

    # Replace linkends
    for old_id, new_id in id_map.items():
        if old_id != new_id:
            content = re.sub(
                f'linkend="{re.escape(old_id)}"',
                f'linkend="{new_id}"',
                content
            )

    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Updated TOC with {len(id_map)} linkend changes")

def update_xml_file_ids(xml_path, sections):
    """Update IDs in XML content files."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create mapping
    id_map = {s['old_id']: s['new_id'] for s in sections}

    replacements = 0
    for old_id, new_id in id_map.items():
        if old_id != new_id and f'id="{old_id}"' in content:
            content = re.sub(
                f'id="{re.escape(old_id)}"',
                f'id="{new_id}"',
                content
            )
            replacements += 1

    if replacements > 0:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {xml_path.name}: {replacements} replacements")

    return replacements

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("Parsing TOC to extract section hierarchy...")
    sections = extract_section_info_from_toc(toc_path)

    print(f"\nFound {len(sections)} sections")
    print("\nSample mappings:")
    for section in sections[:15]:
        print(f"  {section['old_id']:20} -> {section['new_id']:30} | {section['number']:10} {section['title'][:40]}")

    print("\nUpdating TOC...")
    update_toc_with_new_ids(toc_path, sections)

    print("\nUpdating XML files...")
    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0
    for xml_file in xml_files:
        total += update_xml_file_ids(xml_file, sections)

    print(f"\nTotal replacements: {total}")
    print("Done!")

if __name__ == "__main__":
    main()
