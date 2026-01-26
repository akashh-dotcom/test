#!/usr/bin/env python3
"""
In-depth line-by-line content comparison between XML and PDF.
"""

import fitz
import re
from pathlib import Path
from lxml import etree
from difflib import SequenceMatcher
from collections import Counter

PDF_PATH = Path('/workspace/9780989163286.pdf')
XML_DIR = Path('/workspace/final_output_tables')

def extract_pdf_text():
    """Extract full text from PDF."""
    doc = fitz.open(str(PDF_PATH))
    full_text = []
    for page in doc:
        full_text.append(page.get_text())
    doc.close()
    return '\n'.join(full_text)

def extract_xml_text(xml_path):
    """Extract text from XML, preserving structure."""
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    
    lines = []
    
    def extract(elem, depth=0):
        if elem.text and elem.text.strip():
            lines.append(elem.text.strip())
        for child in elem:
            extract(child, depth + 1)
            if child.tail and child.tail.strip():
                lines.append(child.tail.strip())
    
    extract(root)
    return lines

def normalize_line(text):
    """Normalize a line for comparison."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.strip()

def find_line_in_pdf(line, pdf_text_normalized, min_words=3):
    """Check if a line exists in PDF text."""
    words = line.split()
    if len(words) < min_words:
        return True, 1.0  # Skip very short lines
    
    # Try to find the line
    if line in pdf_text_normalized:
        return True, 1.0
    
    # Try partial matching
    # Take chunks of words and search
    chunk_size = min(5, len(words))
    found_chunks = 0
    total_chunks = len(words) - chunk_size + 1
    
    for i in range(total_chunks):
        chunk = ' '.join(words[i:i+chunk_size])
        if chunk in pdf_text_normalized:
            found_chunks += 1
    
    if total_chunks > 0:
        ratio = found_chunks / total_chunks
        return ratio > 0.5, ratio
    
    return True, 1.0

def compare_chapter(ch_num, xml_path, pdf_text_normalized):
    """Compare a single chapter's content."""
    xml_lines = extract_xml_text(xml_path)
    
    results = {
        'total_lines': len(xml_lines),
        'found_lines': 0,
        'missing_lines': [],
        'coverage_scores': []
    }
    
    for line in xml_lines:
        norm_line = normalize_line(line)
        if len(norm_line) < 10:  # Skip very short lines
            results['found_lines'] += 1
            continue
        
        found, score = find_line_in_pdf(norm_line, pdf_text_normalized)
        results['coverage_scores'].append(score)
        
        if found:
            results['found_lines'] += 1
        else:
            results['missing_lines'].append(line[:100])  # Truncate for display
    
    return results

def main():
    print("=" * 100)
    print("IN-DEPTH LINE-BY-LINE CONTENT COMPARISON: XML vs PDF")
    print("=" * 100)
    
    # Extract and normalize PDF text
    print("\nExtracting PDF text...")
    pdf_text = extract_pdf_text()
    pdf_text_normalized = normalize_line(pdf_text)
    print(f"  PDF: {len(pdf_text):,} characters, {len(pdf_text.split()):,} words")
    
    # Compare each chapter
    print("\n" + "-" * 100)
    print(f"{'Chapter':<12} {'Total Lines':<15} {'Found':<12} {'Missing':<12} {'Coverage':<12} {'Status'}")
    print("-" * 100)
    
    all_results = {}
    total_lines = 0
    total_found = 0
    
    for xml_file in sorted(XML_DIR.glob('ch*.xml')):
        ch_name = xml_file.stem
        ch_num = int(ch_name[2:])
        
        results = compare_chapter(ch_num, xml_file, pdf_text_normalized)
        all_results[ch_name] = results
        
        total_lines += results['total_lines']
        total_found += results['found_lines']
        
        if results['total_lines'] > 0:
            coverage = results['found_lines'] / results['total_lines'] * 100
        else:
            coverage = 100.0
        
        status = "OK" if coverage >= 95 else "CHECK" if coverage >= 80 else "REVIEW"
        missing_count = len(results['missing_lines'])
        
        print(f"{ch_name:<12} {results['total_lines']:<15} {results['found_lines']:<12} {missing_count:<12} {coverage:>6.1f}%      {status}")
    
    # Summary
    print("-" * 100)
    overall = total_found / total_lines * 100 if total_lines > 0 else 100
    print(f"{'TOTAL':<12} {total_lines:<15} {total_found:<12} {total_lines - total_found:<12} {overall:>6.1f}%")
    
    # Show sample missing lines if any
    print("\n" + "=" * 100)
    print("DETAILED ANALYSIS BY CHAPTER")
    print("=" * 100)
    
    for ch_name, results in sorted(all_results.items()):
        if results['missing_lines']:
            print(f"\n{ch_name}: {len(results['missing_lines'])} lines not found in PDF")
            print("  Sample missing lines (may be formatting differences):")
            for i, line in enumerate(results['missing_lines'][:5]):
                print(f"    {i+1}. {line[:80]}...")
            if len(results['missing_lines']) > 5:
                print(f"    ... and {len(results['missing_lines']) - 5} more")
    
    # Content statistics
    print("\n" + "=" * 100)
    print("CONTENT STATISTICS")
    print("=" * 100)
    
    # Count elements in XML
    total_paras = 0
    total_tables = 0
    total_figures = 0
    total_sections = 0
    
    for xml_file in XML_DIR.glob('ch*.xml'):
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(str(xml_file), parser)
        root = tree.getroot()
        
        total_paras += len(list(root.iter('para')))
        total_tables += len(list(root.iter('table')))
        total_figures += len(list(root.iter('figure')))
        total_sections += sum(len(list(root.iter(f'sect{i}'))) for i in range(1, 6))
    
    print(f"\nXML Content Elements:")
    print(f"  - Paragraphs: {total_paras:,}")
    print(f"  - Tables: {total_tables}")
    print(f"  - Figures: {total_figures}")
    print(f"  - Sections: {total_sections}")
    
    print(f"\nOverall Coverage: {overall:.1f}%")
    print(f"Lines in XML: {total_lines:,}")
    print(f"Lines found in PDF: {total_found:,}")

if __name__ == '__main__':
    main()
