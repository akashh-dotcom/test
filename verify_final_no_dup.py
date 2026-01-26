#!/usr/bin/env python3
"""
Verify image references in final_output_tables_FINAL_NO_DUPLICATES vs PDF.
"""

import fitz
import re
from pathlib import Path
from lxml import etree
from collections import defaultdict

PDF_PATH = Path('/workspace/9780989163286.pdf')
XML_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
MULTIMEDIA_DIR = XML_DIR / 'multimedia'

def extract_image_refs_from_xml():
    """Extract all image references from XML files."""
    image_refs = defaultdict(list)
    
    for xml_file in sorted(XML_DIR.glob('*.xml')):
        if xml_file.name in ['Book.XML', 'Book.xml']:
            continue
        ch_name = xml_file.stem
        parser = etree.XMLParser(recover=True)
        try:
            tree = etree.parse(str(xml_file), parser)
            root = tree.getroot()
        except:
            continue
        
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
                
                # Check if file exists
                exists = (MULTIMEDIA_DIR / fileref).exists()
                
                image_refs[ch_name].append({
                    'fileref': fileref,
                    'title': title,
                    'exists': exists
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
        
        # Find figure references
        fig_matches = re.findall(r'(?:Figure|Fig\.?)\s+(\d+)', text, re.IGNORECASE)
        
        for fig_num in fig_matches:
            figure_refs[current_chapter].append(int(fig_num))
    
    doc.close()
    
    # Get unique figures per chapter
    unique_refs = {}
    for ch, figs in figure_refs.items():
        unique_refs[ch] = len(set(figs))
    
    return unique_refs

def check_multimedia_files():
    """Check what files exist in multimedia directory."""
    if not MULTIMEDIA_DIR.exists():
        return [], {}
    
    files = sorted([f.name for f in MULTIMEDIA_DIR.iterdir() if f.is_file()])
    
    # Analyze naming patterns
    patterns = defaultdict(int)
    for f in files:
        if re.match(r'Ch\d{4}f\d+\.', f):
            patterns['Ch####f##.ext'] += 1
        elif re.match(r'fig\d+\.', f):
            patterns['fig####.ext'] += 1
        else:
            patterns['other'] += 1
    
    return files, patterns

def main():
    print("=" * 100)
    print("IMAGE VERIFICATION: final_output_tables_FINAL_NO_DUPLICATES vs PDF")
    print("=" * 100)
    
    # Get XML image references
    print("\n1. EXTRACTING IMAGE REFERENCES FROM XML...")
    xml_images = extract_image_refs_from_xml()
    
    total_xml_refs = sum(len(refs) for refs in xml_images.values())
    total_exist = sum(sum(1 for r in refs if r['exists']) for refs in xml_images.values())
    total_missing = total_xml_refs - total_exist
    
    print(f"   Total image references in XML: {total_xml_refs}")
    print(f"   Files that exist: {total_exist}")
    print(f"   Missing files: {total_missing}")
    
    # Check multimedia files
    print("\n2. CHECKING MULTIMEDIA FILES...")
    multimedia_files, patterns = check_multimedia_files()
    print(f"   Total files in multimedia folder: {len(multimedia_files)}")
    print("   Naming patterns:")
    for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
        print(f"      {pattern}: {count}")
    
    # Get PDF figure references
    print("\n3. EXTRACTING FIGURE REFERENCES FROM PDF...")
    pdf_figures = extract_figure_refs_from_pdf()
    total_pdf = sum(pdf_figures.values())
    print(f"   Unique figures in PDF: {total_pdf}")
    
    # Detailed comparison by chapter
    print("\n" + "=" * 100)
    print("CHAPTER-BY-CHAPTER IMAGE COMPARISON")
    print("=" * 100)
    print(f"\n{'Chapter':<15} {'XML Refs':<12} {'Exist':<12} {'Missing':<12} {'PDF Figs':<12} {'Status'}")
    print("-" * 75)
    
    all_chapters = set()
    for ch in xml_images.keys():
        all_chapters.add(ch)
    for ch in pdf_figures.keys():
        all_chapters.add(f"ch{ch:04d}")
    
    missing_details = []
    
    for ch_name in sorted(all_chapters):
        xml_refs = xml_images.get(ch_name, [])
        xml_count = len(xml_refs)
        exist_count = sum(1 for r in xml_refs if r['exists'])
        missing_count = xml_count - exist_count
        
        # Get PDF count
        if ch_name.startswith('ch'):
            try:
                ch_num = int(ch_name[2:])
                pdf_count = pdf_figures.get(ch_num, 0)
            except:
                pdf_count = 0
        else:
            pdf_count = 0
        
        # Collect missing files
        for ref in xml_refs:
            if not ref['exists']:
                missing_details.append((ch_name, ref['fileref'], ref['title']))
        
        if xml_count > 0 or pdf_count > 0:
            status = "OK" if missing_count == 0 else f"MISSING {missing_count}"
            print(f"{ch_name:<15} {xml_count:<12} {exist_count:<12} {missing_count:<12} {pdf_count:<12} {status}")
    
    # Show missing files
    if missing_details:
        print("\n" + "-" * 75)
        print("MISSING IMAGE FILES:")
        print("-" * 75)
        for ch, fileref, title in missing_details[:30]:
            title_short = title[:30] if title else "(no title)"
            print(f"   {ch}: {fileref:<30} {title_short}")
        if len(missing_details) > 30:
            print(f"   ... and {len(missing_details) - 30} more")
    
    # Show sample of existing images
    print("\n" + "=" * 100)
    print("SAMPLE OF IMAGE REFERENCES (First 5 per chapter with images)")
    print("=" * 100)
    
    for ch_name in sorted(xml_images.keys()):
        refs = xml_images[ch_name]
        if refs:
            print(f"\n{ch_name}: {len(refs)} images")
            for i, ref in enumerate(refs[:5], 1):
                exists = "✓" if ref['exists'] else "✗"
                title = ref['title'][:35] if ref['title'] else "(no title)"
                print(f"   {i}. [{exists}] {ref['fileref']:<25} - {title}")
            if len(refs) > 5:
                print(f"   ... and {len(refs) - 5} more")
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"\nImage References in XML: {total_xml_refs}")
    print(f"Image Files That Exist:  {total_exist}")
    print(f"Missing Image Files:     {total_missing}")
    print(f"Files in Multimedia:     {len(multimedia_files)}")
    print(f"Unique Figures in PDF:   {total_pdf}")
    
    if total_missing == 0:
        print("\n✓ All XML image references point to existing files!")
    else:
        print(f"\n✗ {total_missing} image references point to missing files")
        
        # Check what files exist that aren't referenced
        referenced_files = set()
        for refs in xml_images.values():
            for r in refs:
                referenced_files.add(r['fileref'])
        
        unreferenced = set(multimedia_files) - referenced_files
        if unreferenced:
            print(f"\nNote: {len(unreferenced)} files in multimedia are not referenced by any XML")

if __name__ == '__main__':
    main()
