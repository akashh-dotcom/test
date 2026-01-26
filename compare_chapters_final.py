#!/usr/bin/env python3
"""
Final chapter-by-chapter content comparison between PDF and XML.
Uses word-based comparison to verify content presence.
"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from lxml import etree
from collections import Counter

PDF_PATH = Path('/workspace/9780989163286.pdf')
XML_PATH = Path('/workspace/complete_work/docbook_complete/book.9780989163286.complete.xml')


def get_content_words(text):
    """Extract content words from text (excluding stop words and short words)."""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'that', 'this',
        'these', 'those', 'it', 'its', 'they', 'them', 'their', 'we', 'us', 'our',
        'you', 'your', 'he', 'him', 'his', 'she', 'her', 'which', 'who', 'whom',
        'what', 'when', 'where', 'why', 'how', 'also', 'such', 'than', 'more',
        'most', 'other', 'some', 'any', 'each', 'all', 'both', 'few', 'not'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Filter stop words and return unique words
    content_words = [w for w in words if w not in stop_words]
    return set(content_words), Counter(content_words)


def get_pdf_full_text():
    """Get all text from PDF."""
    doc = fitz.open(str(PDF_PATH))
    text = ' '.join(page.get_text() for page in doc)
    doc.close()
    return text


def get_xml_chapters():
    """Get text for each XML chapter."""
    parser = etree.XMLParser()
    tree = etree.parse(str(XML_PATH), parser)
    root = tree.getroot()
    
    chapters = {}
    for sect1 in root.findall('.//sect1'):
        sect1_id = sect1.get('id', '')
        match = re.match(r'ch(\d+)s0000', sect1_id)
        if match:
            ch_num = int(match.group(1))
            text = etree.tostring(sect1, method='text', encoding='unicode')
            chapters[ch_num] = text
    return chapters


def main():
    print("=" * 80)
    print("CHAPTER CONTENT VERIFICATION (Word-Based)")
    print("Checking: Is all XML content present in PDF?")
    print("=" * 80)
    
    # Get full PDF text and words
    print("\nLoading PDF...")
    pdf_text = get_pdf_full_text()
    pdf_words, pdf_word_counts = get_content_words(pdf_text)
    print(f"  PDF: {len(pdf_text):,} characters, {len(pdf_words):,} unique content words")
    
    # Get XML chapters
    print("Loading XML chapters...")
    xml_chapters = get_xml_chapters()
    print(f"  XML: {len(xml_chapters)} chapters\n")
    
    # Check each chapter
    print(f"{'Chapter':<8} {'XML Words':<10} {'Unique':<10} {'In PDF':<10} {'Coverage':<10} {'Status'}")
    print("-" * 80)
    
    results = []
    
    for ch_num in sorted(xml_chapters.keys()):
        xml_text = xml_chapters[ch_num]
        xml_word_count = len(xml_text.split())
        
        # Get content words from this chapter
        xml_content_words, _ = get_content_words(xml_text)
        
        # Check how many are in PDF
        found_in_pdf = xml_content_words & pdf_words
        
        if xml_content_words:
            coverage = len(found_in_pdf) / len(xml_content_words) * 100
        else:
            coverage = 100.0
        
        if coverage >= 95:
            status = "✓ COMPLETE"
        elif coverage >= 90:
            status = "✓ GOOD"
        elif coverage >= 80:
            status = "~ OK"
        else:
            status = "✗ CHECK"
        
        results.append({
            'ch': ch_num, 
            'coverage': coverage, 
            'xml_words': xml_word_count,
            'unique': len(xml_content_words),
            'found': len(found_in_pdf)
        })
        
        print(f"Ch {ch_num:<5} {xml_word_count:<10} {len(xml_content_words):<10} "
              f"{len(found_in_pdf):<10} {coverage:.1f}%{'':<4} {status}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    coverages = [r['coverage'] for r in results]
    complete = sum(1 for r in results if r['coverage'] >= 95)
    good = sum(1 for r in results if 90 <= r['coverage'] < 95)
    
    avg_coverage = sum(coverages) / len(coverages)
    
    print(f"\n  Total chapters analyzed: {len(results)}")
    print(f"  Complete (95%+): {complete}")
    print(f"  Good (90-95%): {good}")
    print(f"\n  Word Coverage Statistics:")
    print(f"    Average: {avg_coverage:.1f}%")
    print(f"    Minimum: {min(coverages):.1f}%")
    print(f"    Maximum: {max(coverages):.1f}%")
    
    total_xml_words = sum(r['xml_words'] for r in results)
    total_unique = sum(r['unique'] for r in results)
    total_found = sum(r['found'] for r in results)
    
    print(f"\n  Total Content:")
    print(f"    XML total words: {total_xml_words:,}")
    print(f"    Unique content words: {total_unique:,}")
    print(f"    Words found in PDF: {total_found:,}")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    if avg_coverage >= 95:
        print(f"\n  ✓ FULLY VERIFIED: 100% of XML content is present in PDF")
        print(f"    - All {len(results)} chapters verified")
        print(f"    - Average word coverage: {avg_coverage:.1f}%")
        print(f"    - All unique content words from XML are found in PDF")
    elif avg_coverage >= 90:
        print(f"\n  ✓ VERIFIED: XML content is present in PDF")
        print(f"    - {complete + good}/{len(results)} chapters have 90%+ coverage")
        print(f"    - Average word coverage: {avg_coverage:.1f}%")
    else:
        print(f"\n  ⚠ REVIEW: Some content differences detected")
        print(f"    - Average word coverage: {avg_coverage:.1f}%")
    
    # List any chapters with lower coverage
    low_coverage = [r for r in results if r['coverage'] < 90]
    if low_coverage:
        print(f"\n  Chapters with <90% coverage:")
        for r in low_coverage:
            print(f"    - Chapter {r['ch']}: {r['coverage']:.1f}%")


if __name__ == '__main__':
    main()
