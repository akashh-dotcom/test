#!/usr/bin/env python3
"""
Simple content comparison between PDF and XML files.
"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from lxml import etree
from collections import Counter

# Configuration
PDF_PATH = Path('/workspace/9780989163286.pdf')
XML_PATH = Path('/workspace/complete_work/docbook_complete/book.9780989163286.complete.xml')

def extract_pdf_text(pdf_path):
    """Extract text from PDF file."""
    print(f"Extracting text from PDF: {pdf_path.name}")
    
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    print(f"  Total pages: {total_pages}")
    
    full_text = []
    chapter_pages = {}  # Track chapter start pages
    
    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        full_text.append(text)
        
        # Track chapter locations
        for match in re.finditer(r'Chapter\s+(\d+)', text, re.IGNORECASE):
            ch_num = int(match.group(1))
            if ch_num not in chapter_pages:
                chapter_pages[ch_num] = page_num + 1
    
    doc.close()
    
    return '\n'.join(full_text), chapter_pages, total_pages


def extract_xml_text(xml_path):
    """Extract text content from XML file."""
    print(f"Extracting text from XML: {xml_path.name}")
    
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    
    # Get all text content
    all_text = etree.tostring(root, method='text', encoding='unicode')
    
    # Find chapters
    chapters = []
    for sect1 in root.findall('.//sect1'):
        sect1_id = sect1.get('id', '')
        match = re.match(r'ch(\d+)s0000', sect1_id)
        if match:
            chapters.append(int(match.group(1)))
    
    return all_text, sorted(chapters)


def normalize_text(text):
    """Normalize text for comparison."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def count_words(text):
    """Count words in text."""
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words), Counter(words)


def find_phrases(text, phrases):
    """Find specific phrases in text."""
    results = {}
    text_lower = text.lower()
    for phrase in phrases:
        phrase_lower = phrase.lower()
        count = len(re.findall(re.escape(phrase_lower), text_lower))
        results[phrase] = count
    return results


def compare_word_overlap(words1, words2):
    """Compare word sets between two texts."""
    set1 = set(words1.keys())
    set2 = set(words2.keys())
    
    common = set1 & set2
    only_in_1 = set1 - set2
    only_in_2 = set2 - set1
    
    # Jaccard similarity
    if set1 | set2:
        jaccard = len(common) / len(set1 | set2)
    else:
        jaccard = 0
    
    return {
        'common': len(common),
        'only_in_pdf': len(only_in_1),
        'only_in_xml': len(only_in_2),
        'jaccard': jaccard,
        'common_words': common
    }


def main():
    print("=" * 70)
    print("CONTENT COMPARISON: PDF vs XML")
    print("=" * 70)
    
    # Extract PDF content
    print("\n" + "-" * 70)
    print("EXTRACTING CONTENT")
    print("-" * 70)
    
    pdf_text, pdf_chapters, pdf_pages = extract_pdf_text(PDF_PATH)
    xml_text, xml_chapters = extract_xml_text(XML_PATH)
    
    print(f"\n  PDF: {len(pdf_text):,} characters, {pdf_pages} pages")
    print(f"  XML: {len(xml_text):,} characters")
    
    # Word counts
    print("\n" + "-" * 70)
    print("WORD ANALYSIS")
    print("-" * 70)
    
    pdf_word_count, pdf_words = count_words(pdf_text)
    xml_word_count, xml_words = count_words(xml_text)
    
    print(f"\n  PDF word count: {pdf_word_count:,}")
    print(f"  XML word count: {xml_word_count:,}")
    print(f"  Difference: {abs(pdf_word_count - xml_word_count):,} words ({abs(pdf_word_count - xml_word_count) / max(pdf_word_count, xml_word_count) * 100:.1f}%)")
    
    # Word overlap
    overlap = compare_word_overlap(pdf_words, xml_words)
    print(f"\n  Unique words in PDF: {len(pdf_words):,}")
    print(f"  Unique words in XML: {len(xml_words):,}")
    print(f"  Common unique words: {overlap['common']:,}")
    print(f"  Words only in PDF: {overlap['only_in_pdf']:,}")
    print(f"  Words only in XML: {overlap['only_in_xml']:,}")
    print(f"  Vocabulary overlap (Jaccard): {overlap['jaccard']:.2%}")
    
    # Chapter comparison
    print("\n" + "-" * 70)
    print("CHAPTER STRUCTURE")
    print("-" * 70)
    
    print(f"\n  Chapters found in PDF: {len(pdf_chapters)}")
    if pdf_chapters:
        print(f"    Range: {min(pdf_chapters.keys())} to {max(pdf_chapters.keys())}")
        print(f"    Chapters: {sorted(pdf_chapters.keys())}")
    
    print(f"\n  Chapters found in XML: {len(xml_chapters)}")
    if xml_chapters:
        print(f"    Range: {min(xml_chapters)} to {max(xml_chapters)}")
        print(f"    Chapters: {xml_chapters}")
    
    # Compare chapter lists
    pdf_ch_set = set(pdf_chapters.keys())
    xml_ch_set = set(xml_chapters)
    common_chapters = pdf_ch_set & xml_ch_set
    
    print(f"\n  Common chapters: {len(common_chapters)}")
    print(f"  Only in PDF: {sorted(pdf_ch_set - xml_ch_set) if pdf_ch_set - xml_ch_set else 'None'}")
    print(f"  Only in XML: {sorted(xml_ch_set - pdf_ch_set) if xml_ch_set - pdf_ch_set else 'None'}")
    
    # Key phrase matching
    print("\n" + "-" * 70)
    print("KEY PHRASE MATCHING")
    print("-" * 70)
    
    test_phrases = [
        "MRI Bioeffects, Safety, and Patient Management",
        "Frank G. Shellock",
        "John V. Crues",
        "Basic MRI Physics",
        "static magnetic field",
        "radiofrequency",
        "gradient magnetic fields",
        "acoustic noise",
        "thermal effects",
        "implants and devices",
        "pregnancy",
        "contrast agents",
        "MRI safety",
        "Tesla",
        "SAR",
    ]
    
    pdf_phrases = find_phrases(pdf_text, test_phrases)
    xml_phrases = find_phrases(xml_text, test_phrases)
    
    print(f"\n  {'Phrase':<45} {'PDF':<8} {'XML':<8} {'Match'}")
    print(f"  {'-'*45} {'-'*8} {'-'*8} {'-'*5}")
    
    matches = 0
    for phrase in test_phrases:
        pdf_count = pdf_phrases[phrase]
        xml_count = xml_phrases[phrase]
        # Consider a match if both have the phrase (regardless of count)
        both_have = (pdf_count > 0 and xml_count > 0)
        match_char = "✓" if both_have else "✗"
        if both_have:
            matches += 1
        
        print(f"  {phrase:<45} {pdf_count:<8} {xml_count:<8} {match_char}")
    
    print(f"\n  Phrase matches: {matches}/{len(test_phrases)} ({matches/len(test_phrases)*100:.0f}%)")
    
    # Most common words comparison
    print("\n" + "-" * 70)
    print("TOP 20 MOST COMMON WORDS")
    print("-" * 70)
    
    # Exclude common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'that', 'this',
                  'these', 'those', 'it', 'its', 'they', 'them', 'their', 'we', 'us', 'our',
                  'you', 'your', 'he', 'him', 'his', 'she', 'her', 'which', 'who', 'whom',
                  'what', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
                  'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
                  'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'if', 'then'}
    
    pdf_filtered = {w: c for w, c in pdf_words.items() if w not in stop_words and len(w) > 2}
    xml_filtered = {w: c for w, c in xml_words.items() if w not in stop_words and len(w) > 2}
    
    pdf_top = sorted(pdf_filtered.items(), key=lambda x: x[1], reverse=True)[:20]
    xml_top = sorted(xml_filtered.items(), key=lambda x: x[1], reverse=True)[:20]
    
    print(f"\n  {'PDF Top Words':<25} {'Count':<8} {'XML Top Words':<25} {'Count'}")
    print(f"  {'-'*25} {'-'*8} {'-'*25} {'-'*8}")
    
    for i in range(20):
        pdf_word = pdf_top[i][0] if i < len(pdf_top) else ""
        pdf_cnt = pdf_top[i][1] if i < len(pdf_top) else 0
        xml_word = xml_top[i][0] if i < len(xml_top) else ""
        xml_cnt = xml_top[i][1] if i < len(xml_top) else 0
        print(f"  {pdf_word:<25} {pdf_cnt:<8} {xml_word:<25} {xml_cnt}")
    
    # Sample text comparison
    print("\n" + "-" * 70)
    print("SAMPLE CONTENT")
    print("-" * 70)
    
    # Find Chapter 1 content in both
    ch1_pdf_start = pdf_text.lower().find("chapter 1")
    ch1_xml_start = xml_text.lower().find("chapter 1")
    
    if ch1_pdf_start >= 0:
        print("\n  Chapter 1 start in PDF (first 300 chars):")
        sample = pdf_text[ch1_pdf_start:ch1_pdf_start+300].replace('\n', ' ')
        print(f"  \"{sample}...\"")
    
    if ch1_xml_start >= 0:
        print("\n  Chapter 1 start in XML (first 300 chars):")
        sample = xml_text[ch1_xml_start:ch1_xml_start+300].replace('\n', ' ')
        print(f"  \"{sample}...\"")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Calculate overall match score
    word_ratio = min(pdf_word_count, xml_word_count) / max(pdf_word_count, xml_word_count)
    phrase_ratio = matches / len(test_phrases)
    chapter_ratio = len(common_chapters) / max(len(pdf_ch_set), len(xml_ch_set)) if pdf_ch_set or xml_ch_set else 0
    vocab_overlap = overlap['jaccard']
    
    overall_score = (word_ratio + phrase_ratio + chapter_ratio + vocab_overlap) / 4
    
    print(f"\n  Word count similarity: {word_ratio:.1%}")
    print(f"  Key phrase match: {phrase_ratio:.1%}")
    print(f"  Chapter structure match: {chapter_ratio:.1%}")
    print(f"  Vocabulary overlap: {vocab_overlap:.1%}")
    print(f"  ----------------------------------------")
    print(f"  OVERALL MATCH SCORE: {overall_score:.1%}")
    
    if overall_score > 0.8:
        print("\n  ✓ CONCLUSION: PDF and XML content are highly consistent")
    elif overall_score > 0.6:
        print("\n  ~ CONCLUSION: PDF and XML content have good consistency")
    elif overall_score > 0.4:
        print("\n  ~ CONCLUSION: PDF and XML content have moderate consistency")
    else:
        print("\n  ✗ CONCLUSION: PDF and XML content have significant differences")


if __name__ == '__main__':
    main()
