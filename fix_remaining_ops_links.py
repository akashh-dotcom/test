#!/usr/bin/env python3
"""
Fix ALL remaining OPS links in all part files
Replace any linkend starting with "9781683674832_v" with the correct XML ID
"""

import re
from pathlib import Path
import json

# Load the complete mapping
with open('/workspace/COMPLETE_CORRECT_MAPPING.json', 'r') as f:
    MAPPING = json.load(f)

def fix_all_ops_links_in_file(xml_file, mapping):
    """Fix all OPS links in a file"""
    
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixes = []
    
    # Find all links with OPS pattern
    for match in re.finditer(r'<link linkend="(9781683674832_v\d+_[cp]\d+(?:#[^"]*)?)"([^>]*)>([^<]+)</link>', content):
        ops_id = match.group(1)
        attrs = match.group(2)
        text = match.group(3)
        
        # Clean the OPS ID (remove .xhtml if present, though it shouldn't be there)
        ops_id_clean = ops_id.replace('.xhtml', '')
        
        # Look up in mapping
        xml_id = mapping.get(ops_id_clean)
        
        # If not found with anchor, try without
        if not xml_id and '#' in ops_id_clean:
            ops_id_no_anchor = ops_id_clean.split('#')[0]
            xml_id = mapping.get(ops_id_no_anchor)
        
        if xml_id:
            old_link = f'<link linkend="{ops_id}"{attrs}>{text}</link>'
            new_link = f'<link linkend="{xml_id}"{attrs}>{text}</link>'
            
            content = content.replace(old_link, new_link)
            fixes.append({
                'ops_id': ops_id,
                'xml_id': xml_id,
                'text': text[:50]
            })
    
    if content != original_content:
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes

def main():
    xml_dir = Path('/workspace/extracted_final')
    
    print("=" * 90)
    print("FIXING ALL REMAINING OPS LINKS IN ALL PART FILES")
    print("=" * 90 + "\n")
    
    print(f"Using mapping with {len(MAPPING)} entries\n")
    
    total_fixes = 0
    
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        file_path = xml_dir / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if file_path.exists():
            fixes = fix_all_ops_links_in_file(file_path, MAPPING)
            
            if fixes:
                print(f"✓ {part_id}: Fixed {len(fixes)} OPS links")
                for fix in fixes[:5]:
                    print(f"    {fix['ops_id']} → {fix['xml_id']}")
                    print(f"      {fix['text']}")
                if len(fixes) > 5:
                    print(f"    ... and {len(fixes) - 5} more")
                print()
                total_fixes += len(fixes)
            else:
                print(f"  {part_id}: No OPS links found")
    
    print("=" * 90)
    print(f"TOTAL FIXES: {total_fixes}")
    print("=" * 90)

if __name__ == '__main__':
    main()
