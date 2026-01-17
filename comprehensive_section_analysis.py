#!/usr/bin/env python3
"""
Comprehensive analysis including sect1, sect2, sect3, and sect4 elements.
"""

import re
from pathlib import Path

def extract_all_section_ids(xml_path):
    """Extract all sect1, sect2, sect3, sect4 IDs with their titles."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = []

    # Extract sect1
    match = re.search(r'<sect1 id="([^"]+)">', content)
    if match:
        sections.append({'type': 'sect1', 'id': match.group(1), 'file': xml_path.name})

    # Extract sect2, sect3, sect4
    for sect_type in ['sect2', 'sect3', 'sect4']:
        pattern = rf'<{sect_type} id="([^"]+)">\s*<title>([^<]+)</title>'
        for match in re.finditer(pattern, content):
            sections.append({
                'type': sect_type,
                'id': match.group(1),
                'title': match.group(2).strip(),
                'file': xml_path.name
            })

    return sections

def extract_toc_linkends(toc_path):
    """Extract all linkends from TOC."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    linkends = {}
    pattern = r'<tocentry linkend="([^"]+)">([^<]+)</tocentry>'
    for match in re.finditer(pattern, content):
        linkend = match.group(1)
        text = match.group(2).strip()
        linkends[linkend] = text

    return linkends

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")
    toc_path = base_dir / "toc.9781394266074.xml"

    print("Extracting all section IDs from XML files...")
    all_sections = []
    for xml_file in sorted(base_dir.glob("sect1.*.xml")):
        sections = extract_all_section_ids(xml_file)
        all_sections.extend(sections)

    print(f"Found {len(all_sections)} total sections")

    # Count by type
    by_type = {}
    for s in all_sections:
        by_type[s['type']] = by_type.get(s['type'], 0) + 1

    print("\nBreakdown by type:")
    for sect_type, count in sorted(by_type.items()):
        print(f"  {sect_type}: {count}")

    print("\nExtracting TOC linkends...")
    toc_linkends = extract_toc_linkends(toc_path)
    print(f"Found {len(toc_linkends)} TOC linkends")

    # Create ID mapping
    xml_ids = {s['id']: s for s in all_sections}

    # Check mismatches
    print("\n" + "=" * 80)
    print("CHECKING FOR MISMATCHES")
    print("=" * 80)

    missing_in_xml = [lid for lid in toc_linkends if lid not in xml_ids]
    missing_in_toc = [s for s in all_sections if s['type'] != 'sect1' and s['id'] not in toc_linkends]

    if missing_in_xml:
        print(f"\n⚠️  {len(missing_in_xml)} TOC linkends NOT found in XML:")
        for lid in missing_in_xml[:10]:
            print(f"  {lid:40} → {toc_linkends[lid][:50]}")
        if len(missing_in_xml) > 10:
            print(f"  ... and {len(missing_in_xml) - 10} more")
    else:
        print("\n✅ All TOC linkends have matching IDs in XML!")

    if missing_in_toc:
        print(f"\n⚠️  {len(missing_in_toc)} XML IDs NOT found in TOC:")
        for s in missing_in_toc[:10]:
            print(f"  {s['id']:40} → {s.get('title', 'N/A')[:50]}")
        if len(missing_in_toc) > 10:
            print(f"  ... and {len(missing_in_toc) - 10} more")
    else:
        print("\n✅ All XML section IDs are in TOC!")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total sections in XML: {len(all_sections)}")
    print(f"Total linkends in TOC: {len(toc_linkends)}")
    print(f"Missing in XML: {len(missing_in_xml)}")
    print(f"Missing in TOC: {len(missing_in_toc)}")

    matched = len(toc_linkends) - len(missing_in_xml)
    print(f"\nMatching rate: {matched}/{len(toc_linkends)} ({100*matched/len(toc_linkends):.1f}%)")

if __name__ == "__main__":
    main()
