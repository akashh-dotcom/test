#!/usr/bin/env python3
"""
Comprehensive link fixer for all 18 part-level sect1 files.
Maps XHTML file IDs (9781683674832_v*_c*) to actual XML chapter/table/appendix IDs.
"""

import re
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET

def extract_xhtml_to_chapter_mapping(ops_dir):
    """Map XHTML files to their chapter numbers by reading titles"""
    mapping = {}
    
    for xhtml_file in Path(ops_dir).glob('9781683674832_v*_c*.xhtml'):
        try:
            # Read first few lines to get title
            with open(xhtml_file, 'r', encoding='utf-8') as f:
                content = f.read(5000)
            
            # Extract title
            title_match = re.search(r'<title>([^<]+)</title>', content)
            if title_match:
                title = title_match.group(1).strip()
                
                # Extract chapter number (e.g., "1.1", "2.1", etc.)
                chapter_num_match = re.search(r'^(\d+\.\d+(?:\.\d+)?)\s+', title)
                if chapter_num_match:
                    chapter_num = chapter_num_match.group(1)
                    xhtml_id = xhtml_file.stem  # e.g., "9781683674832_v1_c01"
                    mapping[xhtml_id] = {
                        'chapter_num': chapter_num,
                        'title': title,
                        'file': str(xhtml_file)
                    }
        except Exception as e:
            print(f"Error processing {xhtml_file}: {e}")
    
    return mapping

def find_xml_chapter_by_number(xml_dir, chapter_num):
    """Find XML chapter ID by chapter number"""
    book_file = Path(xml_dir) / 'book.9781683674832.xml'
    
    if not book_file.exists():
        return None
    
    try:
        with open(book_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for chapter with matching number
        pattern = rf'<chapter id="(ch\d+)"[^>]*>.*?<emphasis role="chapterNumber">([^<]+)</emphasis>'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for ch_id, ch_num in matches:
            if ch_num.strip() == chapter_num:
                return ch_id
    except Exception as e:
        print(f"Error finding chapter {chapter_num}: {e}")
    
    return None

def extract_table_ids_from_xhtml(xhtml_file):
    """Extract table IDs from XHTML file"""
    table_ids = {}
    
    try:
        with open(xhtml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all table references with patterns like:
        # <a id="rt2-1-1" href="...#t2-1-1">Table 2.1–1</a>
        # or <span class="figureLabel" id="c02-tbl-0001">
        
        # Pattern 1: Table links
        table_links = re.findall(
            r'<a[^>]+id="([^"]+)"[^>]*>Table\s+(\d+\.\d+)[–-](\d+)</a>',
            content
        )
        for xhtml_id, section, table_num in table_links:
            table_key = f"Table {section}–{table_num}"
            table_ids[table_key] = xhtml_id
        
        # Pattern 2: Table captions
        table_captions = re.findall(
            r'<span class="figureLabel"[^>]+id="([^"]+)"[^>]*>.*?Table\s+(\d+\.\d+)[–-](\d+)',
            content,
            re.DOTALL
        )
        for xhtml_id, section, table_num in table_captions:
            table_key = f"Table {section}–{table_num}"
            if table_key not in table_ids:
                table_ids[table_key] = xhtml_id
        
        # Pattern 3: Appendix links
        appendix_links = re.findall(
            r'<a[^>]+href="[^#]+#([^"]+)"[^>]*>Appendix\s+(\d+\.\d+)[–-](\d+)',
            content
        )
        for xhtml_id, section, app_num in appendix_links:
            app_key = f"Appendix {section}–{app_num}"
            table_ids[app_key] = xhtml_id
        
    except Exception as e:
        print(f"Error extracting from {xhtml_file}: {e}")
    
    return table_ids

def map_xhtml_id_to_xml_id(xhtml_id_fragment, xml_dir, xhtml_mapping, chapter_mapping):
    """Map an XHTML ID fragment to XML chapter/table ID"""
    
    # Check if it's in the chapter mapping
    if xhtml_id_fragment in chapter_mapping:
        return chapter_mapping[xhtml_id_fragment]
    
    # Try to find in XHTML mapping
    for xhtml_file_id, info in xhtml_mapping.items():
        if xhtml_file_id == xhtml_id_fragment:
            chapter_num = info['chapter_num']
            xml_chapter_id = find_xml_chapter_by_number(xml_dir, chapter_num)
            if xml_chapter_id:
                chapter_mapping[xhtml_id_fragment] = xml_chapter_id
                return xml_chapter_id
    
    return None

def build_comprehensive_mapping(ops_dir, xml_dir):
    """Build comprehensive mapping from XHTML IDs to XML IDs"""
    
    print("Step 1: Mapping XHTML files to chapter numbers...")
    xhtml_mapping = extract_xhtml_to_chapter_mapping(ops_dir)
    print(f"  Found {len(xhtml_mapping)} XHTML chapters")
    
    print("\nStep 2: Mapping chapter numbers to XML chapter IDs...")
    chapter_id_mapping = {}
    for xhtml_id, info in xhtml_mapping.items():
        xml_chapter_id = find_xml_chapter_by_number(xml_dir, info['chapter_num'])
        if xml_chapter_id:
            chapter_id_mapping[xhtml_id] = xml_chapter_id
            print(f"  {xhtml_id} → {xml_chapter_id} ({info['chapter_num']} {info['title'][:50]}...)")
    
    print(f"\nMapped {len(chapter_id_mapping)} XHTML files to XML chapters")
    
    print("\nStep 3: Extracting table/appendix mappings from XHTML files...")
    table_mappings = {}
    for xhtml_id, info in xhtml_mapping.items():
        xhtml_file = info['file']
        tables = extract_table_ids_from_xhtml(xhtml_file)
        if tables:
            print(f"  {xhtml_id}: {len(tables)} tables/appendices found")
            table_mappings.update(tables)
    
    print(f"\nTotal table/appendix mappings: {len(table_mappings)}")
    
    return chapter_id_mapping, table_mappings, xhtml_mapping

def extract_xml_table_ids(xml_dir):
    """Extract all table IDs and their labels from XML files"""
    table_map = {}
    
    for xml_file in Path(xml_dir).glob('sect1.*.xml'):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find tables with labels
            for match in re.finditer(
                r'<table id="([^"]+)">\s*<title>.*?Table\s+(\d+\.\d+)[–-](\d+)',
                content,
                re.DOTALL
            ):
                table_id = match.group(1)
                section = match.group(2)
                num = match.group(3)
                table_key = f"Table {section}–{num}"
                table_map[table_key] = table_id
        except Exception as e:
            pass
    
    return table_map

def fix_part_level_sect1_file(file_path, chapter_mapping, xml_table_map, xhtml_mapping, xml_dir):
    """Fix links in a single part-level sect1 file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixes = []
    
    # Find all links
    for match in re.finditer(r'<link linkend="([^"]+)">([^<]+)</link>', content):
        old_linkend = match.group(1)
        link_text = match.group(2).strip()
        
        # Skip if not a broken link
        if not old_linkend.startswith('9781683674832_v'):
            continue
        
        new_linkend = None
        
        # Try to find table/appendix mapping first
        for key in xml_table_map:
            if key in link_text:
                new_linkend = xml_table_map[key]
                break
        
        # If not found, try chapter mapping
        if not new_linkend and old_linkend in chapter_mapping:
            new_linkend = chapter_mapping[old_linkend]
        
        # If still not found, try to match by chapter number in XHTML
        if not new_linkend:
            for xhtml_id, info in xhtml_mapping.items():
                if xhtml_id == old_linkend:
                    chapter_num = info['chapter_num']
                    new_linkend = find_xml_chapter_by_number(xml_dir, chapter_num)
                    break
        
        if new_linkend and new_linkend != old_linkend:
            # Replace the link
            old_link = f'linkend="{old_linkend}"'
            new_link = f'linkend="{new_linkend}"'
            content = content.replace(old_link, new_link, 1)
            fixes.append({
                'old': old_linkend,
                'new': new_linkend,
                'text': link_text[:60]
            })
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return fixes

def main():
    ops_dir = '/workspace/OPS_extracted/OPS'
    xml_dir = '/workspace/extracted_final'
    
    print("="*80)
    print("COMPREHENSIVE LINK FIXER FOR ALL PART-LEVEL SECT1 FILES")
    print("="*80)
    
    # Build mappings
    chapter_mapping, xhtml_table_mappings, xhtml_mapping = build_comprehensive_mapping(ops_dir, xml_dir)
    
    print("\nStep 4: Extracting XML table IDs...")
    xml_table_map = extract_xml_table_ids(xml_dir)
    print(f"  Found {len(xml_table_map)} tables in XML files")
    
    print("\nStep 5: Fixing all part-level sect1 files...")
    print("-" * 80)
    
    total_fixes = 0
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        file_path = Path(xml_dir) / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if file_path.exists():
            fixes = fix_part_level_sect1_file(
                file_path,
                chapter_mapping,
                xml_table_map,
                xhtml_mapping,
                xml_dir
            )
            
            if fixes:
                print(f"\n{file_path.name}:")
                for fix in fixes:
                    print(f"  ✓ {fix['old']} → {fix['new']}")
                    print(f"    Text: {fix['text']}...")
                total_fixes += len(fixes)
            else:
                # Check for remaining broken links
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                remaining = len(re.findall(r'linkend="9781683674832_v[^"]*"', content))
                if remaining > 0:
                    print(f"\n{file_path.name}: No fixes applied, {remaining} broken links remain")
    
    print("\n" + "="*80)
    print(f"TOTAL FIXES: {total_fixes}")
    print("="*80)

if __name__ == '__main__':
    main()
