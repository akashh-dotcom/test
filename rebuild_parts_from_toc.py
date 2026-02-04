#!/usr/bin/env python3
"""
Rebuild all 18 part files using the authoritative toc.9781683674832.xml
This is the definitive source of truth for all chapter and section IDs
"""

import re
from pathlib import Path

def extract_part_structure_from_toc(toc_file):
    """Extract complete structure for all parts from TOC"""
    
    with open(toc_file, 'r', encoding='utf-8') as f:
        toc_content = f.read()
    
    parts = {}
    
    # Find all tocpart sections
    tocpart_pattern = r'<tocpart[^>]*>(.*?)</tocpart>'
    
    for part_match in re.finditer(tocpart_pattern, toc_content, re.DOTALL):
        part_content = part_match.group(1)
        
        # Get part ID and title
        part_entry = re.search(r'<tocentry linkend="(pt\d+s0001)">(.*?)</tocentry>', part_content, re.DOTALL)
        if not part_entry:
            continue
        
        part_id = part_entry.group(1)
        part_title_text = part_entry.group(2)
        
        # Extract section number and title
        section_match = re.search(r'SECTION (\d+)\s+(.*)', part_title_text, re.DOTALL)
        if section_match:
            section_num = section_match.group(1)
            section_title = re.sub(r'\s+', ' ', section_match.group(2).strip())
        else:
            section_num = "?"
            section_title = re.sub(r'\s+', ' ', part_title_text.strip())
        
        # Extract all chapters and their subsections
        chapters = []
        
        tocchap_pattern = r'<tocchap>(.*?)</tocchap>'
        for chap_match in re.finditer(tocchap_pattern, part_content, re.DOTALL):
            chap_content = chap_match.group(1)
            
            # Get chapter ID and title
            chap_entry = re.search(r'<tocentry linkend="(ch\d+)">(.*?)</tocentry>', chap_content, re.DOTALL)
            if chap_entry:
                ch_id = chap_entry.group(1)
                ch_title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', chap_entry.group(1))).strip()
                
                # Get all subsections (toclevel1)
                sections = []
                toclevel1_pattern = r'<toclevel1>.*?<tocentry linkend="([^"]+)">([^<]+(?:<[^>]+>[^<]+</[^>]+>)*[^<]*)</tocentry>'
                
                for sect_match in re.finditer(toclevel1_pattern, chap_content, re.DOTALL):
                    sect_id = sect_match.group(1)
                    sect_title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', sect_match.group(2))).strip()
                    sections.append({'id': sect_id, 'title': sect_title})
                
                chapters.append({
                    'id': ch_id,
                    'title': ch_title,
                    'sections': sections
                })
        
        parts[part_id] = {
            'section_num': section_num,
            'section_title': section_title,
            'chapters': chapters
        }
    
    return parts

def create_toc_id_to_title_mapping(toc_file):
    """Create a mapping of all IDs to their titles from TOC"""
    
    with open(toc_file, 'r', encoding='utf-8') as f:
        toc_content = f.read()
    
    mapping = {}
    
    # Find all tocentry elements
    tocentry_pattern = r'<tocentry linkend="([^"]+)">(.*?)</tocentry>'
    
    for match in re.finditer(tocentry_pattern, toc_content, re.DOTALL):
        linkend = match.group(1)
        title_text = match.group(2)
        title_clean = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', title_text)).strip()
        
        mapping[linkend] = title_clean
    
    return mapping

def compare_with_current_part_files(parts_from_toc, xml_dir):
    """Compare TOC structure with current part files"""
    
    print("\n" + "=" * 90)
    print("COMPARING TOC WITH CURRENT PART FILES")
    print("=" * 90 + "\n")
    
    for part_id, toc_info in sorted(parts_from_toc.items()):
        xml_file = Path(xml_dir) / f"sect1.9781683674832.{part_id}.xml"
        
        if not xml_file.exists():
            print(f"⚠️  {part_id}: XML file not found")
            continue
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Count linkends in XML
        xml_linkends = re.findall(r'linkend="([^"]+)"', xml_content)
        
        # Count expected entries from TOC
        toc_ids = [toc_info['section_num']]  # part itself
        for chapter in toc_info['chapters']:
            toc_ids.append(chapter['id'])
            toc_ids.extend([s['id'] for s in chapter['sections']])
        
        print(f"{part_id}:")
        print(f"  TOC entries: {len(toc_ids)}")
        print(f"  XML linkends: {len(xml_linkends)}")
        print(f"  TOC chapters: {len(toc_info['chapters'])}")
        print()

def main():
    toc_file = '/workspace/uploads/toc.9781683674832.xml'
    xml_dir = Path('/workspace/extracted_final')
    
    print("Extracting part structures from TOC...")
    parts = extract_part_structure_from_toc(toc_file)
    print(f"Extracted {len(parts)} parts\n")
    
    # Create ID to title mapping
    print("Creating ID to title mapping...")
    id_mapping = create_toc_id_to_title_mapping(toc_file)
    print(f"Mapped {len(id_mapping)} IDs to titles\n")
    
    # Save for reference
    import json
    with open('/workspace/toc_structure.json', 'w') as f:
        json.dump(parts, f, indent=2)
    
    with open('/workspace/toc_id_mapping.json', 'w') as f:
        json.dump(id_mapping, f, indent=2, sort_keys=True)
    
    print("✅ Saved TOC structure and mappings")
    
    # Compare with current files
    compare_with_current_part_files(parts, xml_dir)
    
    return parts, id_mapping

if __name__ == '__main__':
    parts, mapping = main()
