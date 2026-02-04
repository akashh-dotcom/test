#!/usr/bin/env python3
"""
Build complete correct mapping:
1. Correct chapter-level mapping (already done)
2. Section-level mapping within each chapter
"""

import re
from pathlib import Path
import html
import json

# Load the correct chapter mapping
with open('/workspace/CORRECT_chapter_mapping.json', 'r') as f:
    CHAPTER_MAPPING = json.load(f)

def map_sections_for_chapter(ops_file, xml_chapter_id, xml_dir):
    """Map all section IDs from OPS file to XML sections"""
    
    if not ops_file.exists():
        return {}
    
    with open(ops_file, 'r', encoding='utf-8') as f:
        ops_content = f.read()
    
    # Extract OPS sections (h2, h3, section tags with IDs)
    ops_sections = []
    section_pattern = r'<(?:section|h2|h3)[^>]*id="([^"]+)"[^>]*>(.*?)</(?:section|h2|h3)>'
    
    for match in re.finditer(section_pattern, ops_content):
        sect_id = match.group(1)
        heading_raw = match.group(2)
        heading = html.unescape(re.sub(r'<[^>]+>', '', heading_raw)).strip()
        ops_sections.append((sect_id, heading))
    
    # Get XML sections
    xml_sections = []
    for xml_file in sorted(Path(xml_dir).glob(f'sect1.9781683674832.{xml_chapter_id}s*.xml')):
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read(2000)
        
        xml_id_match = re.search(r'<sect1 id="([^"]+)"', xml_content)
        title_match = re.search(r'<title>([^<]+(?:<[^>]+>[^<]+</[^>]+>)*)</title>', xml_content)
        
        if xml_id_match and title_match:
            xml_id = xml_id_match.group(1)
            xml_title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            xml_sections.append((xml_id, xml_title))
    
    # Map OPS sections to XML sections
    section_mappings = {}
    
    for ops_id, ops_heading in ops_sections:
        ops_norm = re.sub(r'[^\w\s]', '', ops_heading.upper())
        
        best_match = None
        best_score = 0
        
        for xml_id, xml_title in xml_sections:
            xml_norm = re.sub(r'[^\w\s]', '', xml_title.upper())
            
            if ops_norm and xml_norm:
                ops_words = set(ops_norm.split())
                xml_words = set(xml_norm.split())
                
                common = len(ops_words & xml_words)
                total = len(ops_words | xml_words)
                score = common / total if total > 0 else 0
                
                if score > best_score:
                    best_score = score
                    best_match = xml_id
        
        # Accept if score > 0.7 for good confidence
        if best_match and best_score > 0.7:
            section_mappings[ops_id] = best_match
    
    return section_mappings

def main():
    ops_dir = Path('/workspace/OPS_extracted/OPS')
    xml_dir = Path('/workspace/extracted_final')
    
    print("=" * 90)
    print("BUILDING COMPLETE CORRECT MAPPING (CHAPTERS + SECTIONS)")
    print("=" * 90 + "\n")
    
    print(f"Using {len(CHAPTER_MAPPING)} verified chapter mappings\n")
    
    # Build complete mapping
    complete_mapping = CHAPTER_MAPPING.copy()
    
    print("Mapping sections for all chapters...")
    total_sections = 0
    
    for i, (ops_id, xml_id) in enumerate(CHAPTER_MAPPING.items()):
        if i % 50 == 0 and i > 0:
            print(f"  Progress: {i}/{len(CHAPTER_MAPPING)}...")
        
        ops_file = ops_dir / f"{ops_id}.xhtml"
        section_mappings = map_sections_for_chapter(ops_file, xml_id, xml_dir)
        
        for ops_sect_id, xml_sect_id in section_mappings.items():
            full_key = f"{ops_id}#{ops_sect_id}"
            complete_mapping[full_key] = xml_sect_id
            total_sections += 1
    
    print(f"\n  Mapped {total_sections} section IDs")
    print(f"  Total mappings: {len(complete_mapping)}")
    
    # Save
    with open('/workspace/COMPLETE_CORRECT_MAPPING.json', 'w') as f:
        json.dump(complete_mapping, f, indent=2, sort_keys=True)
    
    print(f"\n✅ Saved to: COMPLETE_CORRECT_MAPPING.json")
    
    # Verify specific critical mappings
    print("\n" + "=" * 90)
    print("CRITICAL SECTION MAPPINGS:")
    print("=" * 90)
    
    critical_checks = [
        ('9781683674832_v1_c01#v1_c01-secc-007', 'Appendix 1.1-2', 'ch0007s0008'),
        ('9781683674832_v1_c01#v1_c01-secc-006', 'Appendix 1.1-1', 'ch0007s0007'),
    ]
    
    for key, desc, expected in critical_checks:
        actual = complete_mapping.get(key, 'NOT MAPPED')
        status = "✓" if actual == expected else "✗"
        print(f"{status} {key}")
        print(f"  {desc}: {actual} (expected: {expected})")
    
    return complete_mapping

if __name__ == '__main__':
    mapping = main()
