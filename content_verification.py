#!/usr/bin/env python3
"""
Content verification script to check if intro files match preface files
and if Ch02Sec files match ch0002s files.
"""

import os
import difflib

def compare_files(file1, file2):
    """Compare two files and return if they are identical or similar."""
    if not os.path.exists(file1):
        return None, f"File not found: {file1}"
    if not os.path.exists(file2):
        return None, f"File not found: {file2}"

    try:
        with open(file1, 'r', encoding='utf-8') as f1:
            content1 = f1.read()
        with open(file2, 'r', encoding='utf-8') as f2:
            content2 = f2.read()

        if content1 == content2:
            return True, "Files are IDENTICAL"

        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, content1, content2).ratio()

        # Get line-by-line diff
        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)
        diff = list(difflib.unified_diff(lines1, lines2,
                                        fromfile=os.path.basename(file1),
                                        tofile=os.path.basename(file2),
                                        lineterm=''))

        return False, f"Files are DIFFERENT (Similarity: {similarity*100:.2f}%)\nDiff lines: {len(diff)}"

    except Exception as e:
        return None, f"Error: {str(e)}"

def main():
    print("=" * 80)
    print("CONTENT VERIFICATION: CHECKING FILE CORRESPONDENCES")
    print("=" * 80)

    # Define mappings between intro and preface files
    intro_preface_mappings = [
        ("9781394266074-converted/sect1.9781394266074.ch0001-intro.xml",
         "9781394266074-reference-converted/preface.9781394266074.ch0001.xml"),
        ("9781394266074-converted/sect1.9781394266074.ch0004-intro.xml",
         "9781394266074-reference-converted/preface.9781394266074.ch0004.xml"),
        ("9781394266074-converted/sect1.9781394266074.ch0005-intro.xml",
         "9781394266074-reference-converted/preface.9781394266074.ch0005.xml"),
    ]

    # Define mappings between Ch02Sec and ch0002s files
    ch02_mappings = [
        ("9781394266074-converted/sect1.9781394266074.Ch02Sec01.xml",
         "9781394266074-reference-converted/sect1.9781394266074.ch0002s0001.xml"),
        ("9781394266074-converted/sect1.9781394266074.Ch02Sec02.xml",
         "9781394266074-reference-converted/sect1.9781394266074.ch0002s0002.xml"),
        ("9781394266074-converted/sect1.9781394266074.Ch02Sec03.xml",
         "9781394266074-reference-converted/sect1.9781394266074.ch0002s0003.xml"),
        ("9781394266074-converted/sect1.9781394266074.Ch02Sec04.xml",
         "9781394266074-reference-converted/sect1.9781394266074.ch0002s0004.xml"),
        ("9781394266074-converted/sect1.9781394266074.Ch02Sec05.xml",
         "9781394266074-reference-converted/sect1.9781394266074.ch0002s0005.xml"),
    ]

    print("\n1. COMPARING INTRO vs PREFACE FILES")
    print("-" * 80)

    for converted, reference in intro_preface_mappings:
        print(f"\nComparing:")
        print(f"  Converted:  {os.path.basename(converted)}")
        print(f"  Reference:  {os.path.basename(reference)}")

        identical, message = compare_files(converted, reference)

        if identical is True:
            print(f"  ✓ {message}")
        elif identical is False:
            print(f"  ✗ {message}")
        else:
            print(f"  ⚠ {message}")

    print("\n\n2. COMPARING CHAPTER 2 SECTION FILES (Ch02Sec vs ch0002s)")
    print("-" * 80)

    for converted, reference in ch02_mappings:
        print(f"\nComparing:")
        print(f"  Converted:  {os.path.basename(converted)}")
        print(f"  Reference:  {os.path.basename(reference)}")

        identical, message = compare_files(converted, reference)

        if identical is True:
            print(f"  ✓ {message}")
        elif identical is False:
            print(f"  ✗ {message}")
        else:
            print(f"  ⚠ {message}")

    # Check the mysterious double-dot TOC file
    print("\n\n3. CHECKING DOUBLE-DOT TOC FILE")
    print("-" * 80)

    toc_double = "9781394266074-converted/toc.9781394266074..xml"
    toc_normal = "9781394266074-converted/toc.9781394266074.xml"

    if os.path.exists(toc_double):
        print(f"\n⚠ Found: {os.path.basename(toc_double)}")
        print(f"  Size: {os.path.getsize(toc_double)} bytes")

        if os.path.exists(toc_normal):
            print(f"\nComparing with: {os.path.basename(toc_normal)}")
            identical, message = compare_files(toc_double, toc_normal)
            print(f"  {message}")

    # Compare TOC files between converted and reference
    print("\n\n4. COMPARING TOC FILES BETWEEN CONVERTED AND REFERENCE")
    print("-" * 80)

    toc_converted = "9781394266074-converted/toc.9781394266074.xml"
    toc_reference = "9781394266074-reference-converted/toc.9781394266074.xml"

    print(f"\nComparing:")
    print(f"  Converted:  {os.path.basename(toc_converted)}")
    print(f"  Reference:  {os.path.basename(toc_reference)}")

    identical, message = compare_files(toc_converted, toc_reference)

    if identical is True:
        print(f"  ✓ {message}")
    elif identical is False:
        print(f"  ✗ {message}")

        # Show first few differences
        with open(toc_converted, 'r') as f1, open(toc_reference, 'r') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()

            diff = list(difflib.unified_diff(lines1[:50], lines2[:50],
                                            fromfile="converted",
                                            tofile="reference",
                                            lineterm=''))

            if diff:
                print("\n  First differences (showing first 50 lines):")
                for line in diff[:30]:  # Show first 30 diff lines
                    print(f"    {line.rstrip()}")
    else:
        print(f"  ⚠ {message}")

    # Summary
    print("\n\n5. SUMMARY OF FINDINGS")
    print("=" * 80)

    print("\nKey Findings:")
    print("1. Files with naming differences:")
    print("   - 'intro' files in converted correspond to 'preface' files in reference")
    print("   - 'Ch02Sec' files in converted correspond to 'ch0002s' files in reference")
    print("\n2. Extra file in converted:")
    print("   - toc.9781394266074..xml (double dot) - possibly a duplicate or old version")
    print("\n3. Size differences:")
    print("   - 31 common files have different sizes")
    print("   - TOC file has 1579 byte difference (largest)")
    print("\n4. Content verification:")
    print("   - Check above for detailed comparisons")

if __name__ == "__main__":
    main()
