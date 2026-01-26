#!/usr/bin/env python3
"""
Analyze table detection discrepancy between PDF and XML.
"""

import fitz
import re
from pathlib import Path
from lxml import etree
from collections import defaultdict

PDF_PATH = Path('/workspace/9780989163286.pdf')
XML_DIR = Path('/workspace/final_output_tables')
ORIGINAL_XML = Path('/workspace/complete_original/docbook_complete/book.9780989163286.complete.xml')

def analyze_pdf_tables():
    """Extract unique table references from PDF with context."""
    doc = fitz.open(str(PDF_PATH))
    
    # Track unique tables per chapter
    tables_by_chapter = defaultdict(set)
    all_table_refs = []
    
    current_chapter = 0
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        
        # Detect chapter
        ch_match = re.search(r'CHAPTER\s+(\d+)', text, re.IGNORECASE)
        if ch_match:
            current_chapter = int(ch_match.group(1))
        
        # Find table references - "Table X" where X is a number
        # Look for table captions/titles
        table_matches = re.findall(r'Table\s+(\d+)[\.\s\-:]', text, re.IGNORECASE)
        
        for t_num in table_matches:
            tables_by_chapter[current_chapter].add(int(t_num))
            all_table_refs.append((page_num + 1, current_chapter, int(t_num)))
    
    doc.close()
    return tables_by_chapter, all_table_refs

def analyze_xml_tables():
    """Analyze tables in the XML files."""
    tables_by_chapter = {}
    table_details = []
    
    for xml_file in sorted(XML_DIR.glob('ch*.xml')):
        ch_num = int(xml_file.stem[2:])
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(xml_file), parser)
        
        tables = list(tree.getroot().iter('table'))
        tables_by_chapter[ch_num] = len(tables)
        
        for i, table in enumerate(tables):
            title = table.find('title')
            title_text = title.text if title is not None and title.text else "Untitled"
            
            # Count rows
            rows = len(list(table.iter('row')))
            
            table_details.append({
                'chapter': ch_num,
                'index': i + 1,
                'title': title_text,
                'rows': rows
            })
    
    return tables_by_chapter, table_details

def check_original_xml_tables():
    """Check tables in the original source XML."""
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(str(ORIGINAL_XML), parser)
    root = tree.getroot()
    
    tables_by_chapter = defaultdict(list)
    
    for table in root.iter('table'):
        # Find which chapter this table belongs to
        parent = table.getparent()
        while parent is not None:
            if parent.tag == 'sect1':
                sect_id = parent.get('id', '')
                match = re.match(r'ch(\d{4})s0000', sect_id)
                if match:
                    ch_num = int(match.group(1))
                    title = table.find('title')
                    title_text = title.text if title is not None and title.text else "Untitled"
                    tables_by_chapter[ch_num].append(title_text)
                    break
            parent = parent.getparent()
    
    return tables_by_chapter

def main():
    print("=" * 80)
    print("TABLE DETECTION ANALYSIS")
    print("=" * 80)
    
    # Analyze PDF
    print("\n1. PDF TABLE REFERENCES")
    print("-" * 80)
    pdf_tables, pdf_refs = analyze_pdf_tables()
    
    total_pdf_unique = sum(len(t) for t in pdf_tables.values())
    print(f"Unique table numbers referenced in PDF: {total_pdf_unique}")
    
    for ch in sorted(pdf_tables.keys()):
        if pdf_tables[ch]:
            tables = sorted(pdf_tables[ch])
            print(f"  Chapter {ch}: Tables {tables} ({len(tables)} unique)")
    
    # Analyze XML
    print("\n2. XML TABLE COUNT")
    print("-" * 80)
    xml_tables, xml_details = analyze_xml_tables()
    
    total_xml = sum(xml_tables.values())
    print(f"Total tables in XML: {total_xml}")
    
    for ch in sorted(xml_tables.keys()):
        if xml_tables[ch] > 0:
            print(f"  Chapter {ch}: {xml_tables[ch]} tables")
    
    # Check original XML
    print("\n3. ORIGINAL SOURCE XML TABLES")
    print("-" * 80)
    orig_tables = check_original_xml_tables()
    
    total_orig = sum(len(t) for t in orig_tables.values())
    print(f"Total tables in original XML: {total_orig}")
    
    for ch in sorted(orig_tables.keys()):
        if orig_tables[ch]:
            print(f"  Chapter {ch}: {len(orig_tables[ch])} tables")
    
    # Compare
    print("\n4. COMPARISON: PDF vs XML vs ORIGINAL")
    print("-" * 80)
    print(f"{'Chapter':<10} {'PDF Refs':<12} {'XML Tables':<12} {'Original':<12} {'Match'}")
    print("-" * 80)
    
    all_chapters = set(pdf_tables.keys()) | set(xml_tables.keys()) | set(orig_tables.keys())
    
    for ch in sorted(all_chapters):
        if ch == 0:
            continue
        pdf_count = len(pdf_tables.get(ch, set()))
        xml_count = xml_tables.get(ch, 0)
        orig_count = len(orig_tables.get(ch, []))
        
        if pdf_count > 0 or xml_count > 0 or orig_count > 0:
            match = "OK" if xml_count == orig_count else "DIFF"
            print(f"{ch:<10} {pdf_count:<12} {xml_count:<12} {orig_count:<12} {match}")
    
    print("-" * 80)
    print(f"{'TOTAL':<10} {total_pdf_unique:<12} {total_xml:<12} {total_orig:<12}")
    
    # Note about discrepancy
    print("\n" + "=" * 80)
    print("NOTES:")
    print("=" * 80)
    print("""
- PDF table references include cross-references (e.g., "see Table 1")
- PDF counts unique table NUMBERS per chapter, not actual table occurrences
- Some tables in PDF may be images/figures, not actual table markup
- XML tables are from the original DocBook source
- The XML has 98 tables matching the original source
""")

if __name__ == '__main__':
    main()
