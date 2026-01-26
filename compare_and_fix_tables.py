#!/usr/bin/env python3
"""
Compare final_output_tables with original COMPLETE.zip and fix missing tables.
"""

import os
import re
from pathlib import Path
from lxml import etree
from collections import defaultdict

ORIGINAL_XML = Path('/workspace/complete_original/docbook_complete/book.9780989163286.complete.xml')
FINAL_DIR = Path('/workspace/final_output_tables')

def get_text_content(element):
    """Get all text content from an element, including tail."""
    text = element.text or ''
    for child in element:
        text += get_text_content(child)
        text += child.tail or ''
    return text

def normalize_text(text):
    """Normalize text for comparison."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def extract_chapters_from_original(xml_path):
    """Extract chapter content from the original merged XML."""
    parser = etree.XMLParser(recover=True, remove_blank_text=False)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    
    chapters = {}
    
    # Find all sect1 elements with chapter IDs
    for sect1 in root.iter('sect1'):
        sect_id = sect1.get('id', '')
        # Match pattern ch####s0000 (chapter root sections)
        match = re.match(r'ch(\d{4})s0000', sect_id)
        if match:
            ch_num = int(match.group(1))
            chapters[ch_num] = sect1
            
    return chapters

def count_elements(element, tag):
    """Count specific elements in an XML tree."""
    count = 0
    for _ in element.iter(tag):
        count += 1
    return count

def extract_tables_from_chapter(chapter_elem):
    """Extract all tables from a chapter element."""
    tables = []
    for table in chapter_elem.iter('table'):
        tables.append(etree.tostring(table, encoding='unicode', pretty_print=True))
    return tables

def compare_chapters():
    """Compare chapters between original and final output."""
    print("=" * 80)
    print("CONTENT COMPARISON: Original vs Final Output")
    print("=" * 80)
    
    # Parse original
    parser = etree.XMLParser(recover=True, remove_blank_text=False)
    tree = etree.parse(str(ORIGINAL_XML), parser)
    root = tree.getroot()
    
    # Extract chapters from original
    original_chapters = extract_chapters_from_original(ORIGINAL_XML)
    
    print(f"\nFound {len(original_chapters)} chapters in original XML\n")
    
    comparison_results = []
    total_orig_tables = 0
    total_final_tables = 0
    
    for ch_num in sorted(original_chapters.keys()):
        orig_chapter = original_chapters[ch_num]
        final_path = FINAL_DIR / f'ch{ch_num:04d}.xml'
        
        if not final_path.exists():
            print(f"  ch{ch_num:04d}: MISSING in final output!")
            continue
        
        # Parse final chapter
        final_tree = etree.parse(str(final_path), parser)
        final_root = final_tree.getroot()
        
        # Count elements
        orig_tables = count_elements(orig_chapter, 'table')
        final_tables = count_elements(final_root, 'table')
        
        orig_paras = count_elements(orig_chapter, 'para')
        final_paras = count_elements(final_root, 'para')
        
        orig_figures = count_elements(orig_chapter, 'figure')
        final_figures = count_elements(final_root, 'figure')
        
        orig_sects = sum(count_elements(orig_chapter, f'sect{i}') for i in range(1, 7))
        final_sects = sum(count_elements(final_root, f'sect{i}') for i in range(1, 7))
        
        # Get text content
        orig_text = normalize_text(get_text_content(orig_chapter))
        final_text = normalize_text(get_text_content(final_root))
        
        # Calculate text similarity (simple word overlap)
        orig_words = set(orig_text.split())
        final_words = set(final_text.split())
        
        if orig_words:
            text_coverage = len(orig_words & final_words) / len(orig_words) * 100
        else:
            text_coverage = 100.0
        
        total_orig_tables += orig_tables
        total_final_tables += final_tables
        
        # Report differences
        table_diff = final_tables - orig_tables
        para_diff = final_paras - orig_paras
        
        status = "OK" if table_diff == 0 and text_coverage > 95 else "DIFF"
        
        comparison_results.append({
            'chapter': ch_num,
            'orig_tables': orig_tables,
            'final_tables': final_tables,
            'table_diff': table_diff,
            'orig_paras': orig_paras,
            'final_paras': final_paras,
            'orig_figures': orig_figures,
            'final_figures': final_figures,
            'text_coverage': text_coverage,
            'status': status
        })
        
        if orig_tables > 0 or final_tables != orig_tables:
            print(f"  ch{ch_num:04d}: Tables: {orig_tables} -> {final_tables} ({table_diff:+d}), "
                  f"Paras: {orig_paras} -> {final_paras}, Figs: {orig_figures} -> {final_figures}, "
                  f"Text: {text_coverage:.1f}% [{status}]")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tables in original: {total_orig_tables}")
    print(f"Total tables in final:    {total_final_tables}")
    print(f"Missing tables:           {total_orig_tables - total_final_tables}")
    
    # Find chapters with missing tables
    missing_table_chapters = [r for r in comparison_results if r['table_diff'] < 0]
    if missing_table_chapters:
        print(f"\nChapters with missing tables:")
        for r in missing_table_chapters:
            print(f"  ch{r['chapter']:04d}: missing {-r['table_diff']} tables")
    
    return comparison_results, original_chapters

def main():
    results, original_chapters = compare_chapters()
    
    # Ask about fixing tables
    missing_count = sum(1 for r in results if r['table_diff'] < 0)
    if missing_count > 0:
        print(f"\n{missing_count} chapters have missing tables.")
        print("The final_output_tables appears to be missing table content from the original.")

if __name__ == '__main__':
    main()
