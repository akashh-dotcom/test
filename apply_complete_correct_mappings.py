#!/usr/bin/env python3
"""
Apply COMPLETE CORRECT mappings to all 18 part files
Uses the verified chapter and section mappings
"""

import re
from pathlib import Path
import html
import json

# Load the complete correct mapping
with open('/workspace/COMPLETE_CORRECT_MAPPING.json', 'r') as f:
    COMPLETE_MAPPING = json.load(f)

def extract_all_ops_links_from_part(ops_part_file):
    """Extract all links from OPS part file"""
    
    with open(ops_part_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all <a href="..."> links
    link_pattern = r'<a href="(9781683674832_v\d+_c\d+\.xhtml(?:#[^"]+)?)"[^>]*>([^<]+)</a>'
    
    links = []
    for match in re.finditer(link_pattern, content):
        href = match.group(1).replace('.xhtml', '')
        text = html.unescape(match.group(2)).strip()
        links.append({'href': href, 'text': text})
    
    return links

def apply_mapping_to_part_file(xml_part_file, ops_part_file, mapping):
    """Apply mapping to a single part file"""
    
    # Get all OPS links
    ops_links = extract_all_ops_links_from_part(ops_part_file)
    
    # Read XML file
    with open(xml_part_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    original_content = xml_content
    fixes = []
    
    # For each OPS link, find and fix the corresponding XML link
    for ops_link in ops_links:
        ops_href = ops_link['href']
        link_text = ops_link['text']
        
        # Get the correct XML ID from mapping
        xml_id = mapping.get(ops_href)
        
        if not xml_id:
            continue
        
        # Find this link in XML by text
        # Escape text for regex but allow flexible matching
        text_for_search = re.escape(link_text).replace(r'\ ', r'\s*').replace(r'\–', r'[–-]')
        
        # Find the link in XML
        xml_link_pattern = rf'<link linkend="([^"]+)">({text_for_search})</link>'
        xml_match = re.search(xml_link_pattern, xml_content)
        
        if xml_match:
            current_id = xml_match.group(1)
            actual_text = xml_match.group(2)
            
            if current_id != xml_id:
                # Replace
                old_link = f'<link linkend="{current_id}">{actual_text}</link>'
                new_link = f'<link linkend="{xml_id}">{actual_text}</link>'
                
                if old_link in xml_content:
                    xml_content = xml_content.replace(old_link, new_link, 1)
                    fixes.append({
                        'text': link_text[:55],
                        'old': current_id,
                        'new': xml_id
                    })
    
    # Write if changed
    if xml_content != original_content:
        with open(xml_part_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    return fixes

def main():
    ops_dir = Path('/workspace/OPS_extracted/OPS')
    xml_dir = Path('/workspace/extracted_final')
    
    print("=" * 90)
    print("APPLYING COMPLETE CORRECT MAPPINGS TO ALL PART FILES")
    print("=" * 90 + "\n")
    
    print(f"Using mapping with {len(COMPLETE_MAPPING)} entries\n")
    
    total_fixes = 0
    
    for i in range(1, 19):
        part_num = i
        part_id = f"pt{part_num:04d}"
        
        # Find files
        ops_part_file = list(ops_dir.glob(f'9781683674832_v*_p{part_num:02d}.xhtml'))
        if not ops_part_file:
            print(f"Part {part_num:02d}: No OPS file")
            continue
        
        xml_part_file = xml_dir / f"sect1.9781683674832.{part_id}s0001.xml"
        if not xml_part_file.exists():
            print(f"Part {part_num:02d}: No XML file")
            continue
        
        # Apply mapping
        fixes = apply_mapping_to_part_file(xml_part_file, ops_part_file[0], COMPLETE_MAPPING)
        
        if fixes:
            print(f"✓ Part {part_num:02d} ({part_id}): Fixed {len(fixes)} links")
            for fix in fixes[:5]:
                print(f"    {fix['old']} → {fix['new']}")
                print(f"      {fix['text']}")
            if len(fixes) > 5:
                print(f"    ... and {len(fixes) - 5} more")
            print()
            total_fixes += len(fixes)
        else:
            print(f"  Part {part_num:02d} ({part_id}): No changes needed")
    
    print("=" * 90)
    print(f"TOTAL FIXES APPLIED: {total_fixes}")
    print("=" * 90)
    
    return total_fixes

if __name__ == '__main__':
    fixes = main()
