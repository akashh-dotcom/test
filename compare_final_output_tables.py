#!/usr/bin/env python3
"""
Comprehensive comparison analysis of final_output_tables/ XML files.
Provides detailed content analysis, structure validation, and quality metrics.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict, Counter

# Constants
FINAL_OUTPUT_DIR = Path('/home/user/test/final_output_tables')
DOCBOOK_SINGLE = Path('/home/user/test/docbook_single_fixed/book.9780989163286.complete.xml')

def extract_text_from_xml(xml_file):
    """Extract all text content from XML file"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        # Get all text content
        text = ET.tostring(root, encoding='unicode', method='text')
        return text
    except Exception as e:
        print(f"Error reading {xml_file}: {e}")
        return ""

def count_elements(content):
    """Count various XML elements in content"""
    return {
        'paragraphs': len(re.findall(r'<para[>\s]', content)),
        'sections_sect1': len(re.findall(r'<sect1[>\s]', content)),
        'sections_sect2': len(re.findall(r'<sect2[>\s]', content)),
        'sections_sect3': len(re.findall(r'<sect3[>\s]', content)),
        'sections_sect4': len(re.findall(r'<sect4[>\s]', content)),
        'sections_sect5': len(re.findall(r'<sect5[>\s]', content)),
        'figures': len(re.findall(r'<figure[>\s]', content)),
        'tables': len(re.findall(r'<table[>\s]', content)),
        'emphasis_bold': len(re.findall(r'<emphasis role="bold">', content)),
        'emphasis_italic': len(re.findall(r'<emphasis role="italics?">', content)),
        'lists': len(re.findall(r'<(?:itemizedlist|orderedlist)[>\s]', content)),
        'titles': len(re.findall(r'<title>', content))
    }

def analyze_chapter(xml_file):
    """Detailed analysis of a single chapter"""
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract text
    text = extract_text_from_xml(xml_file)
    words = text.split()

    # Count elements
    elements = count_elements(content)

    # Extract chapter info
    chapter_match = re.search(r'<chapter id="(ch\d+)"', content)
    chapter_id = chapter_match.group(1) if chapter_match else "unknown"

    title_match = re.search(r'<title>([^<]+)</title>', content)
    title = title_match.group(1) if title_match else "No title"

    # Find all IDs
    all_ids = re.findall(r'\sid="([^"]+)"', content)

    # Find all image references
    image_refs = re.findall(r'fileref="([^"]+)"', content)

    return {
        'filename': xml_file.name,
        'chapter_id': chapter_id,
        'title': title,
        'word_count': len(words),
        'char_count': len(text),
        'elements': elements,
        'total_ids': len(all_ids),
        'unique_ids': len(set(all_ids)),
        'duplicate_ids': len(all_ids) - len(set(all_ids)),
        'image_refs': image_refs,
        'file_size': os.path.getsize(xml_file)
    }

def analyze_id_format(xml_file):
    """Check ID format compliance"""
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()

    all_ids = re.findall(r'\sid="([^"]+)"', content)

    issues = []

    for id_val in all_ids:
        # Check for proper format
        if id_val.startswith('ch'):
            # Should be ch####s#### pattern with 4-digit sections
            # ch0001s01 is wrong, should be ch0001s0001
            if re.match(r'ch\d{4}s\d{2}(?![0-9])', id_val):
                issues.append(f"2-digit section ID: {id_val}")
            # Check for proper 4-digit sections at all levels
            parts = id_val.split('s')[1:]  # Skip the chapter part
            for part in parts:
                if part and len(part) < 4 and not any(c.isalpha() for c in part):
                    if not (part.startswith('fg') or part.startswith('ta')):
                        issues.append(f"Short section ID: {id_val}")
                        break

    return issues

def compare_with_docbook_single():
    """Compare with the docbook single file version"""
    if not DOCBOOK_SINGLE.exists():
        return None

    with open(DOCBOOK_SINGLE, 'r', encoding='utf-8') as f:
        content = f.read()

    text = extract_text_from_xml(DOCBOOK_SINGLE)
    elements = count_elements(content)

    return {
        'word_count': len(text.split()),
        'elements': elements,
        'file_size': os.path.getsize(DOCBOOK_SINGLE)
    }

def main():
    print("=" * 80)
    print("COMPREHENSIVE ANALYSIS: final_output_tables/")
    print("=" * 80)

    # Get all XML chapter files
    xml_files = sorted(FINAL_OUTPUT_DIR.glob('ch*.xml'))

    print(f"\nFound {len(xml_files)} chapter XML files\n")

    # Analyze each chapter
    all_chapter_data = []
    total_words = 0
    total_elements = defaultdict(int)
    all_image_refs = []
    all_id_issues = []

    print("Analyzing chapters...")
    for xml_file in xml_files:
        data = analyze_chapter(xml_file)
        all_chapter_data.append(data)
        total_words += data['word_count']

        for key, value in data['elements'].items():
            total_elements[key] += value

        all_image_refs.extend(data['image_refs'])

        # Check ID format
        id_issues = analyze_id_format(xml_file)
        if id_issues:
            all_id_issues.append({
                'file': xml_file.name,
                'issues': id_issues
            })

    # Check Book.XML
    book_xml = FINAL_OUTPUT_DIR / 'Book.XML'
    if book_xml.exists():
        with open(book_xml, 'r', encoding='utf-8') as f:
            book_content = f.read()
        entity_count = len(re.findall(r'<!ENTITY', book_content))
    else:
        entity_count = 0

    # Compare with DocBook single file
    docbook_comparison = compare_with_docbook_single()

    # Generate report
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS REPORT")
    print("=" * 80)

    print("\n1. FILE INVENTORY")
    print("-" * 80)
    print(f"Total chapter files: {len(xml_files)}")
    print(f"Book.XML exists: {'Yes' if book_xml.exists() else 'No'}")
    if entity_count > 0:
        print(f"ENTITY declarations in Book.XML: {entity_count}")

    print("\n2. CONTENT VOLUME")
    print("-" * 80)
    print(f"Total words across all chapters: {total_words:,}")
    print(f"Total characters: {sum(d['char_count'] for d in all_chapter_data):,}")
    print(f"Average words per chapter: {total_words // len(xml_files):,}")

    print("\n3. STRUCTURE ANALYSIS")
    print("-" * 80)
    for key, value in sorted(total_elements.items()):
        print(f"  {key:20s}: {value:,}")

    total_sections = (total_elements['sections_sect1'] +
                     total_elements['sections_sect2'] +
                     total_elements['sections_sect3'] +
                     total_elements['sections_sect4'] +
                     total_elements['sections_sect5'])
    print(f"  {'Total sections':20s}: {total_sections:,}")

    print("\n4. IMAGE REFERENCES")
    print("-" * 80)
    print(f"Total image references: {len(all_image_refs)}")
    print(f"Unique images: {len(set(all_image_refs))}")

    # Show sample of image names
    unique_images = sorted(set(all_image_refs))
    if unique_images:
        print(f"\nSample image filenames (first 10):")
        for img in unique_images[:10]:
            print(f"  - {img}")

    # Check multimedia directory
    multimedia_dir = FINAL_OUTPUT_DIR / 'multimedia'
    if multimedia_dir.exists():
        image_files = list(multimedia_dir.glob('*'))
        print(f"\nMultimedia directory contains {len(image_files)} files")

    print("\n5. ID FORMAT VALIDATION")
    print("-" * 80)
    if all_id_issues:
        print(f"⚠️  Found ID format issues in {len(all_id_issues)} files:")
        for issue_data in all_id_issues[:5]:  # Show first 5
            print(f"\n  File: {issue_data['file']}")
            for issue in issue_data['issues'][:3]:  # Show first 3 per file
                print(f"    - {issue}")
        if len(all_id_issues) > 5:
            print(f"\n  ... and {len(all_id_issues) - 5} more files with issues")
    else:
        print("✓ All IDs follow proper format")

    print("\n6. CHAPTER-BY-CHAPTER SUMMARY")
    print("-" * 80)
    print(f"{'File':15s} {'Ch ID':12s} {'Words':>8s} {'Paras':>6s} {'Figs':>5s} {'Tables':>6s} {'Title'}")
    print("-" * 80)
    for data in all_chapter_data:
        print(f"{data['filename']:15s} "
              f"{data['chapter_id']:12s} "
              f"{data['word_count']:8,d} "
              f"{data['elements']['paragraphs']:6d} "
              f"{data['elements']['figures']:5d} "
              f"{data['elements']['tables']:6d} "
              f"{data['title'][:40]}")

    print("\n7. COMPARISON WITH DOCBOOK SINGLE FILE")
    print("-" * 80)
    if docbook_comparison:
        print(f"final_output_tables/ total words: {total_words:,}")
        print(f"DocBook single file words:        {docbook_comparison['word_count']:,}")

        diff = total_words - docbook_comparison['word_count']
        pct = (diff / docbook_comparison['word_count']) * 100

        if diff > 0:
            print(f"\n✓ final_output_tables has {diff:,} MORE words ({pct:.1f}% more)")
        elif diff < 0:
            print(f"\n⚠️  final_output_tables has {abs(diff):,} FEWER words ({abs(pct):.1f}% less)")
        else:
            print(f"\n✓ Both versions have identical word count")

        print("\nElement comparison:")
        print(f"{'Element':25s} {'final_output':>15s} {'DocBook Single':>15s} {'Difference':>12s}")
        print("-" * 70)
        for key in sorted(total_elements.keys()):
            final_val = total_elements[key]
            docbook_val = docbook_comparison['elements'].get(key, 0)
            diff_val = final_val - docbook_val
            diff_str = f"{diff_val:+d}" if diff_val != 0 else "same"
            print(f"{key:25s} {final_val:15,d} {docbook_val:15,d} {diff_str:>12s}")
    else:
        print("DocBook single file not found - skipping comparison")

    print("\n8. QUALITY ASSESSMENT")
    print("-" * 80)

    checks_passed = 0
    total_checks = 0

    # Check 1: All chapters present
    total_checks += 1
    if len(xml_files) == 36:
        print("✓ All 36 chapters present")
        checks_passed += 1
    else:
        print(f"⚠️  Expected 36 chapters, found {len(xml_files)}")

    # Check 2: Book.XML exists
    total_checks += 1
    if book_xml.exists():
        print("✓ Book.XML file exists")
        checks_passed += 1
    else:
        print("⚠️  Book.XML file missing")

    # Check 3: Content volume
    total_checks += 1
    if total_words > 250000:
        print(f"✓ Substantial content volume ({total_words:,} words)")
        checks_passed += 1
    else:
        print(f"⚠️  Low content volume ({total_words:,} words)")

    # Check 4: Images referenced
    total_checks += 1
    if len(all_image_refs) > 50:
        print(f"✓ Images referenced ({len(all_image_refs)} references)")
        checks_passed += 1
    else:
        print(f"⚠️  Few images referenced ({len(all_image_refs)} references)")

    # Check 5: Structure elements
    total_checks += 1
    if total_sections > 500:
        print(f"✓ Rich document structure ({total_sections} sections)")
        checks_passed += 1
    else:
        print(f"⚠️  Limited structure ({total_sections} sections)")

    # Check 6: Tables present
    total_checks += 1
    if total_elements['tables'] > 0:
        print(f"✓ Tables present ({total_elements['tables']} tables)")
        checks_passed += 1
    else:
        print("⚠️  No tables found")

    # Check 7: ID format
    total_checks += 1
    if not all_id_issues:
        print("✓ All IDs properly formatted")
        checks_passed += 1
    else:
        print(f"⚠️  ID format issues in {len(all_id_issues)} files")

    print(f"\nOverall: {checks_passed}/{total_checks} checks passed ({checks_passed*100//total_checks}%)")

    if checks_passed == total_checks:
        print("Grade: A+ (Excellent)")
    elif checks_passed >= total_checks * 0.8:
        print("Grade: B (Good)")
    else:
        print("Grade: C (Needs improvement)")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
