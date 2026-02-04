#!/usr/bin/env python3
"""
Create correct OPS to XML mapping by comparing actual content
"""

import re
from pathlib import Path

def get_ops_content_signature(ops_file):
    """Get a content signature from OPS file (title + first few paragraphs)"""
    try:
        with open(ops_file, 'r', encoding='utf-8') as f:
            content = f.read(5000)
        
        # Get title
        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1) if title_match else ""
        
        # Get h1 chapter info
        h1_match = re.search(
            r'<h1[^>]*>.*?<span class="chapterNumber">([^<]+)</span>.*?<span class="chapterTitle">([^<]+)</span>',
            content,
            re.DOTALL
        )
        
        if h1_match:
            ch_num = h1_match.group(1).strip()
            ch_title = h1_match.group(2).strip()
        else:
            ch_num = ""
            ch_title = title
        
        # Get first paragraph text
        para_match = re.search(r'<p[^>]*id="[^"]*">([^<]{50,200})', content)
        para_text = para_match.group(1) if para_match else ""
        
        return {
            'title': title,
            'chapter_num': ch_num,
            'chapter_title': ch_title,
            'para_text': para_text[:100],
            'file': str(ops_file)
        }
    except Exception as e:
        return None

def get_xml_chapter_signature(book_content, ch_id):
    """Get a content signature from XML chapter"""
    # Find chapter in book
    pattern = rf'<chapter id="{ch_id}"[^>]*>.*?<emphasis role="chapterNumber">([^<]+)</emphasis>.*?<emphasis role="chapterTitle">([^<]+)</emphasis>'
    match = re.search(pattern, book_content, re.DOTALL)
    
    if not match:
        return None
    
    ch_num = match.group(1).strip()
    ch_title = match.group(2).strip()
    
    return {
        'chapter_num': ch_num,
        'chapter_title': ch_title
    }

def find_xml_chapter_by_content(ops_signature, xml_dir):
    """Find XML chapter that matches OPS content"""
    # First try to match by chapter number and title in book.xml
    with open(Path(xml_dir) / 'book.9781683674832.xml', 'r', encoding='utf-8') as f:
        book_content = f.read()
    
    # Look for exact chapter number match
    if ops_signature['chapter_num']:
        pattern = rf'<chapter id="(ch\d+)"[^>]*>.*?<emphasis role="chapterNumber">{re.escape(ops_signature["chapter_num"])}</emphasis>'
        match = re.search(pattern, book_content, re.DOTALL)
        
        if match:
            ch_id = match.group(1)
            # Verify the title also matches (at least partially)
            xml_sig = get_xml_chapter_signature(book_content, ch_id)
            if xml_sig:
                # Check if titles match (allowing for minor differences)
                ops_title_clean = re.sub(r'[^\w\s]', '', ops_signature['chapter_title'].lower())
                xml_title_clean = re.sub(r'[^\w\s]', '', xml_sig['chapter_title'].lower())
                
                # Calculate similarity
                ops_words = set(ops_title_clean.split())
                xml_words = set(xml_title_clean.split())
                
                if ops_words and xml_words:
                    common = len(ops_words & xml_words)
                    total = len(ops_words | xml_words)
                    similarity = common / total if total > 0 else 0
                    
                    if similarity > 0.5:  # At least 50% word overlap
                        return ch_id, xml_sig
    
    return None, None

def main():
    ops_dir = '/workspace/OPS_extracted/OPS'
    xml_dir = '/workspace/extracted_final'
    
    # Get all broken link IDs from part-level files
    broken_links = set()
    for i in range(1, 19):
        part_id = f"pt{i:04d}"
        file_path = Path(xml_dir) / f"sect1.9781683674832.{part_id}s0001.xml"
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            links = re.findall(r'linkend="(9781683674832_v\d+_c\d+)"', content)
            broken_links.update(links)
    
    print("=" * 80)
    print("CORRECT OPS TO XML MAPPING")
    print("=" * 80)
    print(f"\nFound {len(broken_links)} unique broken link IDs\n")
    
    # Create mapping
    mapping = {}
    
    for ops_id in sorted(broken_links):
        ops_file = Path(ops_dir) / f"{ops_id}.xhtml"
        
        if ops_file.exists():
            ops_sig = get_ops_content_signature(ops_file)
            
            if ops_sig:
                xml_ch_id, xml_sig = find_xml_chapter_by_content(ops_sig, xml_dir)
                
                if xml_ch_id:
                    mapping[ops_id] = xml_ch_id
                    print(f"✓ {ops_id} → {xml_ch_id}")
                    print(f"  OPS: {ops_sig['chapter_num']} {ops_sig['chapter_title']}")
                    print(f"  XML: {xml_sig['chapter_num']} {xml_sig['chapter_title']}")
                else:
                    print(f"✗ {ops_id} - NO MATCH FOUND")
                    print(f"  OPS: {ops_sig['chapter_num']} {ops_sig['chapter_title']}")
            else:
                print(f"✗ {ops_id} - Could not read OPS file")
        else:
            print(f"✗ {ops_id} - OPS file not found")
        print()
    
    print("=" * 80)
    print("MAPPING SUMMARY")
    print("=" * 80)
    for ops_id, xml_id in sorted(mapping.items()):
        print(f"{ops_id} → {xml_id}")
    
    return mapping

if __name__ == '__main__':
    mapping = main()
