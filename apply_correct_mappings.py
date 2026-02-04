#!/usr/bin/env python3
"""
Apply correct table/appendix ID mappings to part-level sect1 files
"""

import re
from pathlib import Path

def get_specific_mappings():
    """Define specific known mappings that were found"""
    return {
        # Part 2 - Chapter 12 tables
        "Table 2.1–1": "ch0012s0004ta01",
        "Table 2.1–2": "ch0012s0004ta12",
        "Table 2.1–3": "ch0012s0004ta13",
        "Table 2.1–4": "ch0012s0004ta14",
        "Table 2.1–5": "ch0012s0004ta21",
        "Table 2.1–6": "ch0012s0004ta24",
        "Table 2.1–7": "ch0012s0004ta26",
        "Table 2.1–8": "ch0012s0004ta29",
        "Table 2.1–9": "ch0012s0004ta30",
        "Table 2.1–10": "ch0012s0004ta32",
        "Table 2.1–11": "ch0012s0004ta33",
        "Table 2.1–12": "ch0012s0004ta35",
        "Table 2.1–13": "ch0012s0004ta36",
    }

def extract_comprehensive_mappings(extracted_dir):
    """Extract all table and appendix mappings from XML files"""
    mappings = get_specific_mappings()
    
    # Scan all sect1 files for tables and appendices
    for xml_file in Path(extracted_dir).glob('sect1.*.xml'):
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find tables with their labels
        # Look for <table id="..."> followed by text containing "Table X.Y-Z"
        table_blocks = re.findall(
            r'<table id="([^"]+)">\s*<title>.*?</title>',
            content,
            re.DOTALL
        )
        
        for match in re.finditer(r'<table id="([^"]+)">\s*<title>(.*?)</title>', content, re.DOTALL):
            table_id = match.group(1)
            title_content = match.group(2)
            
            # Extract table label from title
            label_match = re.search(r'Table\s+(\d+\.\d+)[–-](\d+)', title_content)
            if label_match:
                table_label = f"Table {label_match.group(1)}–{label_match.group(2)}"
                mappings[table_label] = table_id
                # Also add dash variant
                table_label_dash = f"Table {label_match.group(1)}-{label_match.group(2)}"
                mappings[table_label_dash] = table_id
    
    return mappings

def fix_file_with_mappings(file_path, mappings):
    """Fix a single file using the mappings"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixes_count = 0
    
    # Fix each link
    for match in re.finditer(r'<link linkend="([^"]+)">([^<]+)</link>', content):
        old_linkend = match.group(1)
        link_text = match.group(2).strip()
        
        # Skip if already fixed (not a broken link)
        if not old_linkend.startswith('9781683674832_v') and not old_linkend.startswith('ch0012s0004ta01'):
            continue
        
        # Try to find mapping by matching link text
        found_mapping = None
        for key, value in mappings.items():
            if key in link_text:
                found_mapping = value
                break
        
        if found_mapping:
            old_link = f'linkend="{old_linkend}"'
            new_link = f'linkend="{found_mapping}"'
            content = content.replace(old_link, new_link, 1)
            fixes_count += 1
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return fixes_count
    
    return 0

def main():
    extracted_dir = '/workspace/extracted_final'
    
    print("=" * 70)
    print("APPLYING CORRECT TABLE/APPENDIX MAPPINGS")
    print("=" * 70)
    
    print("\nExtracting comprehensive mappings...")
    mappings = extract_comprehensive_mappings(extracted_dir)
    print(f"  Total mappings: {len(mappings)}")
    
    print("\nFixing part-level sect1 files...")
    total_fixes = 0
    
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        sect1_file = Path(extracted_dir) / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if sect1_file.exists():
            fixes = fix_file_with_mappings(sect1_file, mappings)
            if fixes > 0:
                print(f"  Fixed {fixes} links in {sect1_file.name}")
                total_fixes += fixes
    
    print("\n" + "=" * 70)
    print(f"TOTAL: Fixed {total_fixes} links")
    print("=" * 70)

if __name__ == '__main__':
    main()
