#!/usr/bin/env python3
"""
Fix all part file links using the authoritative TOC as reference
Match by title text to find correct IDs
"""

import re
from pathlib import Path
import json

# Load TOC ID mapping
with open('/workspace/toc_id_mapping.json', 'r') as f:
    TOC_MAPPING = json.load(f)

def normalize_title(title):
    """Normalize title for matching"""
    # Remove special characters, extra spaces
    normalized = re.sub(r'[^\w\s]', ' ', title)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip().upper()

def find_toc_id_by_title(link_text, toc_mapping):
    """Find TOC ID that matches the link text"""
    
    link_norm = normalize_title(link_text)
    link_words = set(link_norm.split())
    
    if not link_words:
        return None
    
    best_match = None
    best_score = 0
    
    for toc_id, toc_title in toc_mapping.items():
        toc_norm = normalize_title(toc_title)
        toc_words = set(toc_norm.split())
        
        if not toc_words:
            continue
        
        # Calculate similarity
        common = len(link_words & toc_words)
        total = len(link_words | toc_words)
        score = common / total if total > 0 else 0
        
        # Boost score if it's an exact substring match
        if link_norm in toc_norm or toc_norm in link_norm:
            score += 0.3
        
        if score > best_score:
            best_score = score
            best_match = toc_id
    
    # Accept if score is high enough
    if best_score > 0.7:
        return best_match
    
    return None

def fix_part_file_using_toc(xml_file, toc_mapping):
    """Fix all links in a part file using TOC mapping"""
    
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixes = []
    
    # Find all links
    for match in re.finditer(r'<link linkend="([^"]+)">([^<]+(?:<[^>]+>[^<]+</[^>]+>)*[^<]*)</link>', content):
        current_id = match.group(1)
        link_text_raw = match.group(2)
        link_text = re.sub(r'<[^>]+>', '', link_text_raw).strip()
        
        # Find correct ID from TOC
        correct_id = find_toc_id_by_title(link_text, toc_mapping)
        
        if correct_id and correct_id != current_id:
            # Replace the link
            old_link = f'<link linkend="{current_id}">{link_text_raw}</link>'
            new_link = f'<link linkend="{correct_id}">{link_text_raw}</link>'
            
            if old_link in content:
                content = content.replace(old_link, new_link, 1)
                fixes.append({
                    'old_id': current_id,
                    'new_id': correct_id,
                    'text': link_text[:50]
                })
    
    if content != original_content:
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes

def main():
    xml_dir = Path('/workspace/extracted_final')
    
    print("=" * 90)
    print("FIXING ALL PART FILES USING AUTHORITATIVE TOC MAPPING")
    print("=" * 90 + "\n")
    
    print(f"Using TOC mapping with {len(TOC_MAPPING)} entries\n")
    
    total_fixes = 0
    
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        xml_file = xml_dir / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if not xml_file.exists():
            print(f"⚠️  {part_id}: File not found")
            continue
        
        print(f"Processing {part_id}...")
        fixes = fix_part_file_using_toc(xml_file, TOC_MAPPING)
        
        if fixes:
            print(f"  ✓ Fixed {len(fixes)} links:")
            for fix in fixes[:5]:
                print(f"    {fix['old_id']} → {fix['new_id']}")
                print(f"      {fix['text']}")
            if len(fixes) > 5:
                print(f"    ... and {len(fixes) - 5} more")
            print()
            total_fixes += len(fixes)
        else:
            print(f"  No changes needed\n")
    
    print("=" * 90)
    print(f"TOTAL FIXES USING TOC: {total_fixes}")
    print("=" * 90)
    
    return total_fixes

if __name__ == '__main__':
    fixes = main()
