#!/usr/bin/env python3
"""
Quick line-by-line comparison between final_output_tables XML and PDF.
Also checks table detection.
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from lxml import etree
from collections import Counter

PDF_PATH = Path('/workspace/9780989163286.pdf')
XML_DIR = Path('/workspace/final_output_tables')

def extract_pdf_text_by_page():
    """Extract text from PDF page by page."""
    doc = fitz.open(str(PDF_PATH))
    pages = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        pages.append((page_num + 1, text))
    doc.close()
    return pages

def extract_xml_text(xml_path):
    """Extract all text from an XML file."""
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    
    def get_text(elem):
        text = elem.text or ''
        for child in elem:
            text += get_text(child)
            text += child.tail or ''
        return text
    
    return get_text(root)

def normalize(text):
    """Normalize text for comparison."""
    text = re.sub(r'\s+', ' ', text.lower())
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def get_content_words(text):
    """Get significant content words."""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
                  'that', 'these', 'those', 'it', 'its', 'they', 'their', 'them', 'we',
                  'our', 'you', 'your', 'he', 'she', 'his', 'her', 'which', 'who',
                  'whom', 'what', 'where', 'when', 'why', 'how', 'all', 'each', 'every',
                  'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
                  'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'}
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    return [w for w in words if w not in stop_words]

def extract_tables_from_pdf(pages):
    """Try to detect tables in PDF by looking for table-like patterns."""
    table_indicators = []
    for page_num, text in pages:
        # Look for "Table" followed by number
        matches = re.findall(r'Table\s+(\d+[\.\-]?\d*)', text, re.IGNORECASE)
        for m in matches:
            table_indicators.append((page_num, f"Table {m}"))
    return table_indicators

def count_tables_in_xml():
    """Count tables in all XML files."""
    total = 0
    by_chapter = {}
    for xml_file in sorted(XML_DIR.glob('ch*.xml')):
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(xml_file), parser)
        count = len(list(tree.getroot().iter('table')))
        if count > 0:
            by_chapter[xml_file.stem] = count
        total += count
    return total, by_chapter

def main():
    print("=" * 80)
    print("QUICK CONTENT COMPARISON: XML vs PDF")
    print("=" * 80)
    
    # Extract PDF text
    print("\nExtracting PDF text...")
    pdf_pages = extract_pdf_text_by_page()
    pdf_full_text = ' '.join(text for _, text in pdf_pages)
    pdf_words = get_content_words(pdf_full_text)
    pdf_word_set = set(pdf_words)
    
    print(f"  PDF: {len(pdf_pages)} pages, {len(pdf_words)} content words")
    
    # Extract XML text per chapter
    print("\nExtracting XML text per chapter...")
    xml_chapters = {}
    for xml_file in sorted(XML_DIR.glob('ch*.xml')):
        ch_num = xml_file.stem
        text = extract_xml_text(xml_file)
        words = get_content_words(text)
        xml_chapters[ch_num] = {
            'text': text,
            'words': words,
            'word_set': set(words)
        }
    
    # Compare each chapter
    print("\n" + "-" * 80)
    print("CHAPTER-BY-CHAPTER COMPARISON")
    print("-" * 80)
    print(f"{'Chapter':<10} {'XML Words':<12} {'In PDF':<12} {'Coverage':<10} {'Status'}")
    print("-" * 80)
    
    total_xml_words = 0
    total_found = 0
    
    for ch_num in sorted(xml_chapters.keys()):
        ch_data = xml_chapters[ch_num]
        xml_word_count = len(ch_data['words'])
        found_in_pdf = len(ch_data['word_set'] & pdf_word_set)
        
        if xml_word_count > 0:
            coverage = found_in_pdf / len(ch_data['word_set']) * 100
        else:
            coverage = 100.0
        
        status = "OK" if coverage >= 90 else "CHECK"
        print(f"{ch_num:<10} {xml_word_count:<12} {found_in_pdf:<12} {coverage:>6.1f}%    {status}")
        
        total_xml_words += xml_word_count
        total_found += found_in_pdf
    
    # Overall stats
    print("-" * 80)
    overall = total_found / len(set(w for ch in xml_chapters.values() for w in ch['words'])) * 100 if total_xml_words > 0 else 100
    print(f"{'TOTAL':<10} {total_xml_words:<12} {total_found:<12} {overall:>6.1f}%")
    
    # Table comparison
    print("\n" + "=" * 80)
    print("TABLE DETECTION ANALYSIS")
    print("=" * 80)
    
    # Tables in XML
    xml_table_count, xml_tables_by_ch = count_tables_in_xml()
    print(f"\nTables in XML files: {xml_table_count}")
    for ch, count in sorted(xml_tables_by_ch.items()):
        print(f"  {ch}: {count} tables")
    
    # Tables mentioned in PDF
    pdf_table_refs = extract_tables_from_pdf(pdf_pages)
    print(f"\nTable references found in PDF: {len(pdf_table_refs)}")
    
    # Show sample table references from PDF
    if pdf_table_refs:
        print("  Sample table references:")
        for page, ref in pdf_table_refs[:15]:
            print(f"    Page {page}: {ref}")
        if len(pdf_table_refs) > 15:
            print(f"    ... and {len(pdf_table_refs) - 15} more")
    
    # Check a sample table in XML
    print("\n" + "-" * 80)
    print("SAMPLE TABLE FROM XML (ch0001):")
    print("-" * 80)
    
    ch0001_path = XML_DIR / 'ch0001.xml'
    if ch0001_path.exists():
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(ch0001_path), parser)
        tables = list(tree.getroot().iter('table'))
        if tables:
            table_xml = etree.tostring(tables[0], encoding='unicode', pretty_print=True)
            # Show first 40 lines
            lines = table_xml.split('\n')[:40]
            print('\n'.join(lines))
            if len(table_xml.split('\n')) > 40:
                print("... (truncated)")
        else:
            print("No tables found in ch0001.xml")

if __name__ == '__main__':
    main()
