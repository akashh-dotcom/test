#!/usr/bin/env python3
"""
Create TRULY CORRECT mapping by properly extracting chapters
"""

import re
from pathlib import Path
import html
import json

def get_xml_chapters_correct(book_path):
    """Extract XML chapters correctly - only those with chapter numbers"""
    with open(book_path, 'r', encoding='utf-8') as f:
        book = f.read()
    
    chapters = {}
    
    # Find each chapter individually
    chapter_pattern = r'<chapter id="(ch\d+)"[^>]*>(.*?)</chapter>'
    
    for match in re.finditer(chapter_pattern, book, re.DOTALL):
        ch_id = match.group(1)
        ch_content = match.group(2)
        
        # Extract chapter number and title from THIS chapter only
        num_match = re.search(r'<emphasis role="chapterNumber">([^<]+)</emphasis>', ch_content)
        title_match = re.search(r'<emphasis role="chapterTitle">([^<]+)</emphasis>', ch_content)
        
        if num_match and title_match:
            ch_num = num_match.group(1).strip().rstrip('.')
            ch_title = title_match.group(1).strip()
            chapters[ch_id] = {'num': ch_num, 'title': ch_title}
    
    return chapters

def get_ops_chapters_with_numbers(ops_dir):
    """Get OPS chapters with chapter numbers"""
    ops_chapters = {}
    
    for ops_file in sorted(Path(ops_dir).glob('9781683674832_v*_c*.xhtml')):
        try:
            with open(ops_file, 'r', encoding='utf-8') as f:
                content = f.read(5000)
            
            ops_id = ops_file.stem
            
            h1_match = re.search(
                r'<h1[^>]*>.*?<span class="chapterNumber">([^<]+)</span>.*?<span class="chapterTitle">([^<]+)</span>',
                content,
                re.DOTALL
            )
            
            if h1_match:
                ch_num = h1_match.group(1).strip().rstrip('.')
                ch_title = html.unescape(h1_match.group(2).strip())
                ops_chapters[ops_id] = {'num': ch_num, 'title': ch_title}
        except:
            pass
    
    return ops_chapters

def create_correct_mapping(ops_chapters, xml_chapters):
    """Create correct OPS to XML mapping"""
    
    # Build reverse index: num → xml_id
    num_to_xml = {}
    for xml_id, info in xml_chapters.items():
        num_to_xml[info['num']] = xml_id
    
    # Map
    mapping = {}
    unmapped = []
    
    for ops_id, ops_info in ops_chapters.items():
        ops_num = ops_info['num']
        
        if ops_num in num_to_xml:
            xml_id = num_to_xml[ops_num]
            mapping[ops_id] = xml_id
        else:
            unmapped.append((ops_id, ops_num, ops_info['title']))
    
    return mapping, unmapped

def main():
    ops_dir = Path('/workspace/OPS_extracted/OPS')
    book_path = Path('/workspace/extracted_final/book.9781683674832.xml')
    
    print("=" * 90)
    print("CREATING TRULY CORRECT MAPPING")
    print("=" * 90 + "\n")
    
    print("Extracting XML chapters (excluding frontmatter)...")
    xml_chapters = get_xml_chapters_correct(book_path)
    print(f"  Found {len(xml_chapters)} chapters with chapter numbers\n")
    
    print("Extracting OPS chapters...")
    ops_chapters = get_ops_chapters_with_numbers(ops_dir)
    print(f"  Found {len(ops_chapters)} OPS chapters\n")
    
    print("Creating mapping...")
    mapping, unmapped = create_correct_mapping(ops_chapters, xml_chapters)
    print(f"  Mapped: {len(mapping)}")
    print(f"  Unmapped: {len(unmapped)}\n")
    
    # Save
    with open('/workspace/CORRECT_chapter_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
    
    # Verify critical mappings
    print("=" * 90)
    print("CRITICAL VERIFICATIONS:")
    print("=" * 90)
    
    critical = [
        ('9781683674832_v1_c01', '1.1 Introduction', 'ch0007'),
        ('9781683674832_v1_c06', '2.1 Collection', 'ch0012'),
        ('9781683674832_v1_c08', '3.2 Staining', 'ch0014'),
    ]
    
    all_correct = True
    for ops_id, desc, expected_xml in critical:
        actual_xml = mapping.get(ops_id, 'NOT MAPPED')
        status = "✓" if actual_xml == expected_xml else "✗"
        
        print(f"{status} {ops_id} ({desc}) → {actual_xml}")
        if actual_xml != expected_xml:
            print(f"  EXPECTED: {expected_xml}")
            all_correct = False
    
    if all_correct:
        print("\n✅ ALL CRITICAL MAPPINGS CORRECT!")
    else:
        print("\n❌ SOME MAPPINGS STILL WRONG!")
    
    return mapping

if __name__ == '__main__':
    mapping = main()
