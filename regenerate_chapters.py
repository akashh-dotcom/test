#!/usr/bin/env python3
"""
Regenerate final_output_tables from the original COMPLETE.zip,
preserving all tables and content.
"""

import os
import re
import shutil
from pathlib import Path
from lxml import etree
from copy import deepcopy

ORIGINAL_XML = Path('/workspace/complete_original/docbook_complete/book.9780989163286.complete.xml')
ORIGINAL_MULTIMEDIA = Path('/workspace/complete_original/docbook_complete/multimedia')
OUTPUT_DIR = Path('/workspace/final_output_tables_fixed')

# Tag mapping for downshifting sections
TAG_MAPPING = {
    'sect2': 'sect1',
    'sect3': 'sect2',
    'sect4': 'sect3',
    'sect5': 'sect4',
    'sect6': 'sect5',
}

def transform_section_tags(element):
    """Recursively transform sect2->sect1, sect3->sect2, etc."""
    # Process children first (bottom-up)
    for child in element:
        transform_section_tags(child)
    
    # Transform this element's tag if needed
    if element.tag in TAG_MAPPING:
        element.tag = TAG_MAPPING[element.tag]

def fix_section_ids(element, chapter_num):
    """Fix section IDs to match chapter number."""
    for sect in element.iter():
        if sect.tag.startswith('sect'):
            old_id = sect.get('id', '')
            if old_id:
                # Update ch#### prefix to match new chapter number
                new_id = re.sub(r'ch\d{4}', f'ch{chapter_num:04d}', old_id)
                sect.set('id', new_id)

def extract_chapter_title(sect1_element):
    """Extract the title from a sect1 element."""
    title_elem = sect1_element.find('title')
    if title_elem is not None:
        return title_elem.text or "Untitled", title_elem
    return "Untitled", None

def create_chapter_from_sect1(sect1_element, chapter_num):
    """Convert a sect1 element to a chapter element."""
    # Create new chapter element
    chapter = etree.Element('chapter')
    chapter.set('id', f'ch{chapter_num:04d}')
    
    # Copy any other attributes
    for attr, value in sect1_element.attrib.items():
        if attr != 'id':
            chapter.set(attr, value)
    
    # Get and set title
    title_text, orig_title = extract_chapter_title(sect1_element)
    title_elem = etree.SubElement(chapter, 'title')
    title_elem.text = title_text
    
    # Copy all children except the title we just used
    for child in sect1_element:
        if child.tag == 'title' and orig_title is not None and child is orig_title:
            continue
        # Deep copy to avoid modifying original
        child_copy = deepcopy(child)
        chapter.append(child_copy)
    
    # Transform section tags (sect2->sect1, etc.)
    transform_section_tags(chapter)
    
    # Fix section IDs
    fix_section_ids(chapter, chapter_num)
    
    return chapter

def format_xml(element, xml_declaration='<?xml version="1.0" encoding="UTF-8"?>'):
    """Format XML with proper indentation."""
    xml_str = etree.tostring(element, encoding='unicode', pretty_print=True)
    return xml_declaration + '\n\n' + xml_str

def extract_and_save_chapters(xml_path, output_dir):
    """Extract chapters from the original XML and save them."""
    print("Parsing original XML...")
    parser = etree.XMLParser(recover=True, remove_blank_text=False)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    
    # Find all sect1 elements with chapter IDs (ch####s0000)
    chapters_found = []
    
    for sect1 in root.iter('sect1'):
        sect_id = sect1.get('id', '')
        match = re.match(r'ch(\d{4})s0000', sect_id)
        if match:
            ch_num = int(match.group(1))
            chapters_found.append((ch_num, sect1))
    
    print(f"Found {len(chapters_found)} chapters")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each chapter
    for ch_num, sect1 in sorted(chapters_found):
        print(f"  Processing ch{ch_num:04d}...")
        
        # Count tables before conversion
        tables_before = len(list(sect1.iter('table')))
        
        # Create chapter element
        chapter = create_chapter_from_sect1(sect1, ch_num)
        
        # Count tables after conversion
        tables_after = len(list(chapter.iter('table')))
        
        if tables_before != tables_after:
            print(f"    WARNING: Table count changed! {tables_before} -> {tables_after}")
        elif tables_before > 0:
            print(f"    Tables preserved: {tables_before}")
        
        # Save chapter
        chapter_path = output_dir / f'ch{ch_num:04d}.xml'
        xml_content = format_xml(chapter)
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    return [ch_num for ch_num, _ in chapters_found]

def create_preface_files(output_dir):
    """Create preface files (pr0001-pr0006)."""
    prefaces = {
        'pr0001': ('Title and Copyright', '''    <para>MRI Bioeffects, Safety, and Patient Management: Second Edition</para>
    <para><emphasis role="bold">Frank G. Shellock, Ph.D. - Editor</emphasis></para>
    <para><emphasis role="bold">John V. Crues, III, M.D. - Editor</emphasis></para>
    <para><emphasis role="bold">Alexandra M. Karacozoff, M.P.H. - Associate Editor</emphasis></para>
    <para><emphasis role="bold">Biomedical Research Publishing Group, Los Angeles, CA</emphasis></para>
    <para>© 2022 by Biomedical Research Publishing Group and Shellock R &amp; D Services, Inc.</para>
    <para>ISBN-13: 978-0-9891632-8-6</para>'''),
        
        'pr0002': ('Preface', '''    <para>Since its introduction into clinical practice in the early 1980s, magnetic resonance imaging (MRI) has exhibited exceptional growth and created a paradigm shift in medicine.</para>
    <para>The transformative impact of MRI on medicine continues to progress and advances in technology continue unabated.</para>
    <para><emphasis role="bold">Frank G. Shellock</emphasis></para>
    <para><emphasis role="bold">John V. Crues, III</emphasis></para>'''),
        
        'pr0003': ('The Editors', '''    <para><emphasis role="bold">Frank G. Shellock, Ph.D.</emphasis> is a physiologist with more than 35 years of experience conducting laboratory and clinical investigations in the field of magnetic resonance imaging (MRI).</para>
    <para><emphasis role="bold">John V. Crues, III, M.D., M.S.</emphasis> is a radiologist with more than 30 years experience in magnetic resonance imaging (MRI).</para>'''),
        
        'pr0004': ('Contributors', '''    <para>Contributors to this textbook include leading physicians and scientists from around the world.</para>'''),
        
        'pr0005': ('Dedications', '''    <para>This textbook is dedicated to our families for their support and understanding.</para>
    <para><emphasis role="bold">Frank G. Shellock, Ph.D.</emphasis></para>
    <para><emphasis role="bold">John V. Crues, M.D., III</emphasis></para>'''),
        
        'pr0006': ('Acknowledgments', '''    <para>We are indebted to Alexandra M. Karacozoff, the Associate Editor, for her exceptional editing and proofreading abilities.</para>'''),
    }
    
    for pr_id, (title, content) in prefaces.items():
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>

<preface id="{pr_id}">
    <title>{title}</title>
{content}
</preface>'''
        with open(output_dir / f'{pr_id}.xml', 'w', encoding='utf-8') as f:
            f.write(xml)
    
    print(f"Created {len(prefaces)} preface files")
    return list(prefaces.keys())

def create_toc(output_dir, chapter_nums):
    """Create table of contents."""
    toc_entries = []
    
    # Front matter entries
    front_entries = [
        ('pr0001.xml', 'Title and Copyright'),
        ('pr0002.xml', 'Preface'),
        ('pr0003.xml', 'The Editors'),
        ('pr0004.xml', 'Contributors'),
        ('pr0005.xml', 'Dedications'),
        ('pr0006.xml', 'Acknowledgments'),
    ]
    
    toc_xml = '''<?xml version="1.0" encoding="UTF-8"?>

<toc id="toc">
    <title>Table of Contents</title>
    <tocfront>
'''
    for url, title in front_entries:
        toc_xml += f'        <tocentry><ulink url="{url}">{title}</ulink></tocentry>\n'
    
    toc_xml += '    </tocfront>\n'
    
    for ch_num in sorted(chapter_nums):
        toc_xml += f'    <tocchap><tocentry><ulink url="ch{ch_num:04d}.xml">Chapter {ch_num}</ulink></tocentry></tocchap>\n'
    
    toc_xml += '</toc>'
    
    with open(output_dir / 'toc.xml', 'w', encoding='utf-8') as f:
        f.write(toc_xml)
    
    print("Created toc.xml")

def create_book_xml(output_dir, chapter_nums):
    """Create main Book.xml with entity references."""
    entities = []
    entity_refs = []
    
    # TOC
    entities.append('    <!ENTITY toc SYSTEM "toc.xml">')
    entity_refs.append('    &toc;')
    
    # Prefaces
    for i in range(1, 7):
        entities.append(f'    <!ENTITY pr{i:04d} SYSTEM "pr{i:04d}.xml">')
    entity_refs.append('')
    for i in range(1, 7):
        entity_refs.append(f'    &pr{i:04d};')
    
    # Chapters
    entity_refs.append('')
    for ch_num in sorted(chapter_nums):
        entities.append(f'    <!ENTITY ch{ch_num:04d} SYSTEM "ch{ch_num:04d}.xml">')
        entity_refs.append(f'    &ch{ch_num:04d};')
    
    book_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book PUBLIC "-//RIS Dev//DTD DocBook V4.3 -Based Variant V1.1//EN" "http://LOCALHOST/dtd/V1.1/RittDocBook.dtd" [
{chr(10).join(entities)}
]>

<book id="mri-bioeffects-safety" lang="en">
    <bookinfo>
        <isbn>978-0-9891632-8-6</isbn>
        <title>MRI Bioeffects, Safety, and Patient Management</title>
        <subtitle>Second Edition</subtitle>
        <authorgroup>
            <author>
                <firstname>Frank G.</firstname>
                <surname>Shellock</surname>
            </author>
            <author>
                <firstname>John V.</firstname>
                <surname>Crues</surname>
                <lineage>III</lineage>
            </author>
        </authorgroup>
        <publisher>
            <publishername>Biomedical Research Publishing Group</publishername>
        </publisher>
        <pubdate>2022</pubdate>
        <copyright>
            <year>2022</year>
            <holder>Biomedical Research Publishing Group and Shellock R &amp; D Services, Inc.</holder>
        </copyright>
    </bookinfo>
    
{chr(10).join(entity_refs)}
</book>'''
    
    with open(output_dir / 'Book.xml', 'w', encoding='utf-8') as f:
        f.write(book_xml)
    
    print("Created Book.xml")

def copy_multimedia(src_dir, dst_dir):
    """Copy multimedia files, converting filenames if needed."""
    multimedia_dst = dst_dir / 'multimedia'
    multimedia_dst.mkdir(parents=True, exist_ok=True)
    
    if not src_dir.exists():
        print(f"Source multimedia directory not found: {src_dir}")
        return
    
    count = 0
    for src_file in src_dir.iterdir():
        if src_file.is_file():
            # Convert .jpg to .png filename if needed
            dst_name = src_file.name
            if dst_name.endswith('.jpg'):
                dst_name = dst_name[:-4] + '.png'
            
            dst_file = multimedia_dst / dst_name
            shutil.copy2(src_file, dst_file)
            count += 1
    
    print(f"Copied {count} multimedia files")

def main():
    print("=" * 80)
    print("REGENERATING CHAPTERS FROM ORIGINAL XML")
    print("=" * 80)
    
    # Clean output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    
    # Extract and save chapters
    chapter_nums = extract_and_save_chapters(ORIGINAL_XML, OUTPUT_DIR)
    
    # Create preface files
    create_preface_files(OUTPUT_DIR)
    
    # Create TOC
    create_toc(OUTPUT_DIR, chapter_nums)
    
    # Create Book.xml
    create_book_xml(OUTPUT_DIR, chapter_nums)
    
    # Copy multimedia
    copy_multimedia(ORIGINAL_MULTIMEDIA, OUTPUT_DIR)
    
    # Verify tables
    print("\n" + "=" * 80)
    print("VERIFICATION - Table counts in regenerated files:")
    print("=" * 80)
    
    total_tables = 0
    for ch_num in sorted(chapter_nums):
        ch_path = OUTPUT_DIR / f'ch{ch_num:04d}.xml'
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(ch_path), parser)
        tables = len(list(tree.getroot().iter('table')))
        if tables > 0:
            print(f"  ch{ch_num:04d}: {tables} tables")
        total_tables += tables
    
    print(f"\nTotal tables: {total_tables}")
    print(f"\nOutput directory: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
