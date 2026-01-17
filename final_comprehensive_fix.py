#!/usr/bin/env python3
"""
Final comprehensive fix to ensure TOC linkends match XML section IDs.
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_sections_by_chapter(base_dir):
    """Extract all sections organized by chapter."""
    by_chapter = defaultdict(list)

    for xml_file in sorted(base_dir.glob("sect1.*.xml")):
        # Extract chapter ID from filename
        ch_match = re.search(r'ch(\d{4})', xml_file.name)
        if not ch_match:
            continue

        ch_id = f"ch{ch_match.group(1)}"

        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract all sect2 and sect3
        for sect_type in ['sect2', 'sect3']:
            pattern = rf'<{sect_type} id="([^"]+)">\s*<title>([^<]+)</title>'
            for match in re.finditer(pattern, content):
                sect_id = match.group(1)
                title = match.group(2).strip()

                by_chapter[ch_id].append({
                    'id': sect_id,
                    'title': title,
                    'type': sect_type
                })

    return dict(by_chapter)

def fix_toc_with_context(toc_path, sections_by_chapter):
    """Fix TOC linkends maintaining chapter context."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    current_chapter = None
    changes = []

    for i, line in enumerate(lines):
        # Detect current chapter from tocchap entries
        if '<tocchap>' in line and i + 1 < len(lines):
            # Look ahead to find chapter linkend
            next_line = lines[i + 1]
            ch_match = re.search(r'<tocentry linkend="(ch\d{4})">', next_line)
            if ch_match:
                current_chapter = ch_match.group(1)

        # Process tocentry elements
        match = re.search(r'(<tocentry linkend=")([^"]+)(">)([^<]+)(</tocentry>)', line)
        if match and current_chapter:
            old_linkend = match.group(2)
            text = match.group(4).strip()

            # Skip Part entries
            if text.startswith('Part '):
                new_lines.append(line)
                continue

            # Skip if it's the chapter entry itself
            if old_linkend == current_chapter:
                new_lines.append(line)
                continue

            # Try to find matching section in current chapter
            new_linkend = None
            if current_chapter in sections_by_chapter:
                chapter_sections = sections_by_chapter[current_chapter]

                # Look for exact title match
                for section in chapter_sections:
                    if section['title'] == text:
                        new_linkend = section['id']
                        break

                # If not found, try section number match
                if not new_linkend:
                    num_match = re.match(r'^([\d\.]+)\s', text)
                    if num_match:
                        section_num = num_match.group(1)
                        for section in chapter_sections:
                            if section['title'].startswith(section_num + ' '):
                                new_linkend = section['id']
                                break

            if new_linkend and new_linkend != old_linkend:
                # Update linkend
                indent = re.match(r'^(\s*)', line).group(1)
                new_line = f'{indent}<tocentry linkend="{new_linkend}">{text}</tocentry>\n'
                new_lines.append(new_line)
                changes.append({
                    'line': i + 1,
                    'chapter': current_chapter,
                    'old': old_linkend,
                    'new': new_linkend,
                    'text': text
                })
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Write back
    if changes:
        with open(toc_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print(f"\n✅ Updated {len(changes)} TOC linkends")
        print("\nSample changes (first 15):")
        for change in changes[:15]:
            print(f"  Line {change['line']:4} | Ch {change['chapter']} | {change['old']:25} → {change['new']:25} | {change['text'][:35]}")

    return len(changes)

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("=" * 90)
    print("FINAL COMPREHENSIVE TOC FIX")
    print("=" * 90)

    print("\nExtracting all sections from XML files...")
    sections_by_chapter = extract_sections_by_chapter(base_dir)

    total_sections = sum(len(sects) for sects in sections_by_chapter.values())
    print(f"Found {total_sections} sections across {len(sections_by_chapter)} chapters")

    print("\nFixing TOC linkends with chapter context...")
    changes = fix_toc_with_context(toc_path, sections_by_chapter)

    if changes == 0:
        print("\n✅ No changes needed - TOC is already correct!")
    else:
        print(f"\n✅ Fixed {changes} linkends in TOC")

    print("\nDone!")

if __name__ == "__main__":
    main()
