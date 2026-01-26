#!/usr/bin/env python3
"""
Verify image references in XML match the PDF content.
Check if images are in correct positions and correctly referenced.
"""

import fitz
import re
from pathlib import Path
from lxml import etree
from collections import defaultdict

PDF_PATH = Path('/workspace/9780989163286.pdf')
XML_DIR = Path('/workspace/final_output_tables')
MULTIMEDIA_DIR = XML_DIR / 'multimedia'

def extract_image_refs_from_xml():
    """Extract all image references from XML files."""
    image_refs = defaultdict(list)
    
    for xml_file in sorted(XML_DIR.glob('ch*.xml')):
        ch_name = xml_file.stem
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(xml_file), parser)
        root = tree.getroot()
        
        # Find all imagedata elements
        for img in root.iter('imagedata'):
            fileref = img.get('fileref', '')
            if fileref:
                # Get surrounding context
                parent = img.getparent()  # imageobject
                if parent is not None:
                    parent = parent.getparent()  # mediaobject
                if parent is not None:
                    parent = parent.getparent()  # figure
                
                title = ""
                if parent is not None and parent.tag == 'figure':
                    title_elem = parent.find('title')
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text
                
                image_refs[ch_name].append({
                    'fileref': fileref,
                    'title': title,
                    'exists': (MULTIMEDIA_DIR / fileref).exists()
                })
    
    return image_refs

def extract_figure_refs_from_pdf():
    """Extract figure references from PDF text."""
    doc = fitz.open(str(PDF_PATH))
    
    figure_refs = defaultdict(list)
    current_chapter = 0
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        
        # Detect chapter
        ch_match = re.search(r'CHAPTER\s+(\d+)', text, re.IGNORECASE)
        if ch_match:
            current_chapter = int(ch_match.group(1))
        
        # Find figure references - "Figure X" or "Fig. X"
        fig_matches = re.findall(r'(?:Figure|Fig\.?)\s+(\d+)[\.\s\-:]?\s*([^\n]{0,50})?', text, re.IGNORECASE)
        
        for fig_num, context in fig_matches:
            figure_refs[current_chapter].append({
                'page': page_num + 1,
                'fig_num': int(fig_num),
                'context': context.strip()[:50] if context else ""
            })
    
    doc.close()
    return figure_refs

def check_multimedia_files():
    """Check what files exist in multimedia directory."""
    if not MULTIMEDIA_DIR.exists():
        return []
    
    files = list(MULTIMEDIA_DIR.glob('*'))
    return sorted([f.name for f in files if f.is_file()])

def main():
    print("=" * 100)
    print("IMAGE VERIFICATION: XML References vs PDF vs Actual Files")
    print("=" * 100)
    
    # Get XML image references
    print("\n1. EXTRACTING IMAGE REFERENCES FROM XML...")
    xml_images = extract_image_refs_from_xml()
    
    total_xml_refs = sum(len(refs) for refs in xml_images.values())
    print(f"   Total image references in XML: {total_xml_refs}")
    
    # Check multimedia files
    print("\n2. CHECKING MULTIMEDIA FILES...")
    multimedia_files = check_multimedia_files()
    print(f"   Total files in multimedia folder: {len(multimedia_files)}")
    
    # Get PDF figure references
    print("\n3. EXTRACTING FIGURE REFERENCES FROM PDF...")
    pdf_figures = extract_figure_refs_from_pdf()
    
    total_pdf_refs = sum(len(refs) for refs in pdf_figures.values())
    unique_pdf_figs = {}
    for ch, refs in pdf_figures.items():
        unique_pdf_figs[ch] = len(set(r['fig_num'] for r in refs))
    total_unique_pdf = sum(unique_pdf_figs.values())
    print(f"   Total figure references in PDF: {total_pdf_refs}")
    print(f"   Unique figures in PDF: {total_unique_pdf}")
    
    # Detailed comparison by chapter
    print("\n" + "=" * 100)
    print("CHAPTER-BY-CHAPTER IMAGE COMPARISON")
    print("=" * 100)
    print(f"\n{'Chapter':<12} {'XML Refs':<12} {'Files Exist':<12} {'PDF Figs':<12} {'Status'}")
    print("-" * 60)
    
    all_chapters = set()
    for ch in xml_images.keys():
        ch_num = int(ch[2:])
        all_chapters.add(ch_num)
    for ch in pdf_figures.keys():
        all_chapters.add(ch)
    
    missing_files = []
    
    for ch_num in sorted(all_chapters):
        ch_name = f"ch{ch_num:04d}"
        
        xml_refs = xml_images.get(ch_name, [])
        xml_count = len(xml_refs)
        exist_count = sum(1 for r in xml_refs if r['exists'])
        pdf_count = unique_pdf_figs.get(ch_num, 0)
        
        # Check for missing files
        for ref in xml_refs:
            if not ref['exists']:
                missing_files.append((ch_name, ref['fileref']))
        
        status = "OK" if exist_count == xml_count else "MISSING"
        if xml_count == 0 and pdf_count == 0:
            status = "NO IMAGES"
        
        if xml_count > 0 or pdf_count > 0:
            print(f"{ch_name:<12} {xml_count:<12} {exist_count:<12} {pdf_count:<12} {status}")
    
    # Show missing files
    if missing_files:
        print("\n" + "-" * 60)
        print("MISSING IMAGE FILES:")
        for ch, fileref in missing_files:
            print(f"   {ch}: {fileref}")
    
    # Detailed image list per chapter
    print("\n" + "=" * 100)
    print("DETAILED IMAGE REFERENCES BY CHAPTER")
    print("=" * 100)
    
    for ch_name in sorted(xml_images.keys()):
        refs = xml_images[ch_name]
        if refs:
            print(f"\n{ch_name}: {len(refs)} images")
            for i, ref in enumerate(refs[:10], 1):
                exists = "✓" if ref['exists'] else "✗"
                title = ref['title'][:40] if ref['title'] else "(no title)"
                print(f"   {i:2}. [{exists}] {ref['fileref']:<25} - {title}")
            if len(refs) > 10:
                print(f"   ... and {len(refs) - 10} more images")
    
    # Summary statistics
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    total_exist = sum(sum(1 for r in refs if r['exists']) for refs in xml_images.values())
    
    print(f"\nImage References in XML: {total_xml_refs}")
    print(f"Image Files That Exist:  {total_exist}")
    print(f"Missing Image Files:     {total_xml_refs - total_exist}")
    print(f"Files in Multimedia:     {len(multimedia_files)}")
    print(f"Figure Refs in PDF:      {total_unique_pdf}")
    
    if total_xml_refs == total_exist:
        print("\n✓ All XML image references point to existing files!")
    else:
        print(f"\n✗ {total_xml_refs - total_exist} image references point to missing files")
    
    # Check naming convention
    print("\n" + "-" * 60)
    print("IMAGE NAMING ANALYSIS:")
    
    # Analyze naming patterns in XML
    xml_patterns = defaultdict(int)
    for ch_name, refs in xml_images.items():
        for ref in refs:
            fileref = ref['fileref']
            if re.match(r'Ch\d{4}f\d+\.', fileref):
                xml_patterns['Ch####f##.ext'] += 1
            elif re.match(r'fig\d+\.', fileref):
                xml_patterns['fig####.ext'] += 1
            else:
                xml_patterns['other'] += 1
    
    print("   XML image naming patterns:")
    for pattern, count in sorted(xml_patterns.items(), key=lambda x: -x[1]):
        print(f"      {pattern}: {count}")
    
    # Analyze naming in multimedia folder
    file_patterns = defaultdict(int)
    for f in multimedia_files:
        if re.match(r'Ch\d{4}f\d+\.', f):
            file_patterns['Ch####f##.ext'] += 1
        elif re.match(r'fig\d+\.', f):
            file_patterns['fig####.ext'] += 1
        else:
            file_patterns['other'] += 1
    
    print("   Multimedia file naming patterns:")
    for pattern, count in sorted(file_patterns.items(), key=lambda x: -x[1]):
        print(f"      {pattern}: {count}")

if __name__ == '__main__':
    main()
