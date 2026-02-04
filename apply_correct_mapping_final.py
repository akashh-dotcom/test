#!/usr/bin/env python3
"""
Apply the correct OPS to XML mapping based on manual verification
"""

import re
from pathlib import Path

def get_correct_mapping():
    """
    Return the correct OPS ID to XML ID mapping
    Based on direct comparison of OPS XHTML content and XML chapter structure
    """
    return {
        # Part 3 - Aerobic Bacteriology
        "9781683674832_v1_c15": "ch0021",  # 3.4. Body Fluid Cultures
        "9781683674832_v1_c16": "ch0022",  # 3.5. Cerebrospinal Fluid Cultures
        "9781683674832_v1_c17": "ch0023",  # 3.6. Medical Devices
        "9781683674832_v1_c18": "ch0024",  # 3.7. Fecal and Other Gastrointestinal Cultures
        "9781683674832_v1_c19": "ch0024",  # 3.7.2. Campylobacter (subsection of ch0024)
        "9781683674832_v1_c20": "ch0024",  # 3.7.3. Helicobacter (subsection of ch0024)
        "9781683674832_v1_c21": "ch0025",  # 3.7.2. Quantitative Culture of Small-Bowel
        "9781683674832_v1_c22": "ch0028",  # 3.8. Genital Cultures
        
        # Part 15 - Environmental/Sterility
        "9781683674832_v4_c80": "ch0389",  # 15.3.4 Media Fill Test Procedure
    }

def fix_part_sect1_files(xml_dir, mapping):
    """Fix all part-level sect1 files with correct mapping"""
    
    total_fixes = 0
    
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        file_path = Path(xml_dir) / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if not file_path.exists():
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        file_fixes = 0
        
        # Find and replace broken links
        for ops_id, xml_id in mapping.items():
            if ops_id in content:
                # Replace all occurrences
                old_pattern = f'linkend="{ops_id}"'
                new_pattern = f'linkend="{xml_id}"'
                
                count = content.count(old_pattern)
                if count > 0:
                    content = content.replace(old_pattern, new_pattern)
                    file_fixes += count
                    print(f"  {ops_id} → {xml_id} ({count} occurrences)")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n✓ {file_path.name}: Fixed {file_fixes} links")
            total_fixes += file_fixes
    
    return total_fixes

def verify_mapping(xml_dir, mapping):
    """Verify the mapping by showing what OPS chapters map to what XML chapters"""
    print("=" * 80)
    print("VERIFICATION: OPS to XML Chapter Mapping")
    print("=" * 80)
    
    # Read book.xml to get chapter titles
    with open(Path(xml_dir) / 'book.9781683674832.xml', 'r', encoding='utf-8') as f:
        book_content = f.read()
    
    # Read OPS files to get their titles
    ops_dir = '/workspace/OPS_extracted/OPS'
    
    for ops_id in sorted(mapping.keys()):
        xml_id = mapping[ops_id]
        
        # Get OPS title
        ops_file = Path(ops_dir) / f"{ops_id}.xhtml"
        if ops_file.exists():
            with open(ops_file, 'r', encoding='utf-8') as f:
                ops_content = f.read(2000)
            
            title_match = re.search(r'<title>([^<]+)</title>', ops_content)
            ops_title = title_match.group(1) if title_match else "Unknown"
        else:
            ops_title = "File not found"
        
        # Get XML title
        xml_pattern = rf'<chapter id="{xml_id}"[^>]*>.*?<emphasis role="chapterNumber">([^<]+)</emphasis>.*?<emphasis role="chapterTitle">([^<]+)</emphasis>'
        xml_match = re.search(xml_pattern, book_content, re.DOTALL)
        
        if xml_match:
            xml_num = xml_match.group(1).strip()
            xml_title = xml_match.group(2).strip()
            xml_full = f"{xml_num} {xml_title}"
        else:
            xml_full = "Not found in book.xml"
        
        print(f"\n{ops_id} → {xml_id}")
        print(f"  OPS: {ops_title}")
        print(f"  XML: {xml_full}")

def main():
    xml_dir = '/workspace/extracted_final'
    
    print("=" * 80)
    print("APPLYING CORRECT OPS TO XML MAPPING")
    print("=" * 80)
    
    mapping = get_correct_mapping()
    
    print(f"\nTotal mappings to apply: {len(mapping)}\n")
    
    # Verify mapping first
    verify_mapping(xml_dir, mapping)
    
    print("\n" + "=" * 80)
    print("FIXING PART-LEVEL SECT1 FILES")
    print("=" * 80 + "\n")
    
    total_fixes = fix_part_sect1_files(xml_dir, mapping)
    
    print("\n" + "=" * 80)
    print(f"TOTAL FIXES APPLIED: {total_fixes}")
    print("=" * 80)

if __name__ == '__main__':
    main()
