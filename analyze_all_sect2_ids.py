#!/usr/bin/env python3
"""
Comprehensively analyze all XML files to extract sect2 IDs and verify TOC linkends match.
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_all_section_ids_from_xml(xml_path):
    """Extract all sect1 and sect2 IDs with their titles from an XML file."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = []

    # Extract sect1 (chapter level)
    sect1_match = re.search(r'<sect1 id="([^"]+)">', content)
    if sect1_match:
        sect1_id = sect1_match.group(1)
        # Try to find chapter title in the XML
        title_match = re.search(r'<chapterid>([^<]+)</chapterid>', content)
        if title_match:
            sections.append({
                'type': 'sect1',
                'id': sect1_id,
                'title': f'Chapter {title_match.group(1)}',
                'file': xml_path.name
            })
        else:
            sections.append({
                'type': 'sect1',
                'id': sect1_id,
                'title': 'Chapter',
                'file': xml_path.name
            })

    # Extract all sect2 elements (sections and subsections)
    # Pattern: <sect2 id="..."><title>...</title>
    pattern = r'<sect2 id="([^"]+)">\s*<title>([^<]+)</title>'
    for match in re.finditer(pattern, content):
        sect_id = match.group(1)
        title = match.group(2).strip()
        sections.append({
            'type': 'sect2',
            'id': sect_id,
            'title': title,
            'file': xml_path.name
        })

    return sections

def extract_all_toc_linkends(toc_path):
    """Extract all linkends from TOC with their text."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    linkends = []
    pattern = r'<tocentry linkend="([^"]+)">([^<]+)</tocentry>'
    for match in re.finditer(pattern, content):
        linkend = match.group(1)
        text = match.group(2).strip()
        linkends.append({
            'linkend': linkend,
            'text': text
        })

    return linkends

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("=" * 80)
    print("ANALYZING ALL XML FILES FOR SECT2 IDs")
    print("=" * 80)

    # Extract all section IDs from XML files
    all_sections = []
    xml_files = sorted(base_dir.glob("sect1.*.xml"))

    for xml_file in xml_files:
        sections = extract_all_section_ids_from_xml(xml_file)
        all_sections.extend(sections)

    print(f"\nFound {len(all_sections)} total sections across {len(xml_files)} files")

    # Extract all TOC linkends
    toc_linkends = extract_all_toc_linkends(toc_path)
    print(f"Found {len(toc_linkends)} linkends in TOC")

    # Create mappings
    xml_id_map = {s['id']: s for s in all_sections}
    toc_linkend_set = {t['linkend'] for t in toc_linkends}

    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)

    # Check for TOC linkends that don't have matching IDs in XML
    missing_in_xml = []
    for toc_entry in toc_linkends:
        linkend = toc_entry['linkend']
        if linkend not in xml_id_map:
            missing_in_xml.append(toc_entry)

    if missing_in_xml:
        print(f"\n⚠️  {len(missing_in_xml)} TOC linkends NOT FOUND in XML files:")
        for entry in missing_in_xml[:20]:  # Show first 20
            print(f"  - {entry['linkend']:30} → {entry['text'][:50]}")
        if len(missing_in_xml) > 20:
            print(f"  ... and {len(missing_in_xml) - 20} more")
    else:
        print("\n✓ All TOC linkends have matching IDs in XML files")

    # Check for XML IDs that aren't in TOC
    missing_in_toc = []
    for section in all_sections:
        if section['type'] == 'sect2' and section['id'] not in toc_linkend_set:
            missing_in_toc.append(section)

    if missing_in_toc:
        print(f"\n⚠️  {len(missing_in_toc)} XML sect2 IDs NOT FOUND in TOC:")
        for section in missing_in_toc[:20]:  # Show first 20
            print(f"  - {section['id']:30} → {section['title'][:50]} ({section['file']})")
        if len(missing_in_toc) > 20:
            print(f"  ... and {len(missing_in_toc) - 20} more")
    else:
        print("\n✓ All XML sect2 IDs are referenced in TOC")

    # Show sample of correctly matched entries
    print("\n" + "=" * 80)
    print("SAMPLE OF CORRECTLY MATCHED ENTRIES (first 20)")
    print("=" * 80)
    matched = 0
    for toc_entry in toc_linkends[:50]:
        linkend = toc_entry['linkend']
        if linkend in xml_id_map:
            xml_section = xml_id_map[linkend]
            print(f"✓ {linkend:30} → TOC: {toc_entry['text'][:40]:40} | XML: {xml_section['title'][:40]}")
            matched += 1
            if matched >= 20:
                break

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total XML sections (sect1 + sect2): {len(all_sections)}")
    print(f"Total TOC linkends: {len(toc_linkends)}")
    print(f"TOC linkends missing in XML: {len(missing_in_xml)}")
    print(f"XML sect2 IDs missing in TOC: {len(missing_in_toc)}")

    # Detailed breakdown by file
    print("\n" + "=" * 80)
    print("BREAKDOWN BY FILE (showing sect2 IDs)")
    print("=" * 80)

    by_file = defaultdict(list)
    for section in all_sections:
        if section['type'] == 'sect2':
            by_file[section['file']].append(section)

    for filename in sorted(by_file.keys())[:5]:  # Show first 5 files
        sections = by_file[filename]
        print(f"\n{filename}: {len(sections)} sect2 elements")
        for section in sections[:10]:  # Show first 10 from each
            in_toc = "✓" if section['id'] in toc_linkend_set else "✗"
            print(f"  {in_toc} {section['id']:30} → {section['title'][:50]}")
        if len(sections) > 10:
            print(f"  ... and {len(sections) - 10} more")

if __name__ == "__main__":
    main()
