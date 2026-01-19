#!/usr/bin/env python3
"""
Deep comparison script to verify contents between two ZIP files
and their extracted directories.
"""

import os
import zipfile
from pathlib import Path
import difflib

def get_zip_file_list(zip_path):
    """Get list of files in ZIP archive."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        return sorted([f for f in zip_ref.namelist() if not f.endswith('/')])

def get_directory_files(dir_path):
    """Get list of files in directory recursively."""
    files = []
    for root, dirs, filenames in os.walk(dir_path):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, dir_path)
            files.append(rel_path)
    return sorted(files)

def compare_file_contents(file1, file2):
    """Compare contents of two files and return differences."""
    try:
        with open(file1, 'r', encoding='utf-8') as f1:
            content1 = f1.readlines()
        with open(file2, 'r', encoding='utf-8') as f2:
            content2 = f2.readlines()

        diff = list(difflib.unified_diff(content1, content2,
                                        fromfile=file1,
                                        tofile=file2,
                                        lineterm=''))
        return diff
    except Exception as e:
        return [f"Error comparing files: {str(e)}"]

def analyze_file_sizes(dir_path):
    """Get file sizes for all files in directory."""
    file_sizes = {}
    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, dir_path)
            file_sizes[rel_path] = os.path.getsize(full_path)
    return file_sizes

def main():
    # Define paths
    zip1 = "9781394266074-converted.zip"
    zip2 = "9781394266074-reference-converted.zip"
    dir1 = "9781394266074-converted"
    dir2 = "9781394266074-reference-converted"

    print("=" * 80)
    print("DEEP COMPARISON: ZIP AND DIRECTORY CONTENTS")
    print("=" * 80)

    # Compare ZIP file lists
    print("\n1. COMPARING ZIP ARCHIVE CONTENTS")
    print("-" * 80)

    files_zip1 = get_zip_file_list(zip1)
    files_zip2 = get_zip_file_list(zip2)

    print(f"\nFiles in {zip1}: {len(files_zip1)}")
    print(f"Files in {zip2}: {len(files_zip2)}")

    # Files only in converted
    only_in_converted = set([os.path.basename(f) for f in files_zip1]) - set([os.path.basename(f) for f in files_zip2])
    print(f"\n✗ Files ONLY in converted (not in reference): {len(only_in_converted)}")
    for f in sorted(only_in_converted):
        print(f"  - {f}")

    # Files only in reference
    only_in_reference = set([os.path.basename(f) for f in files_zip2]) - set([os.path.basename(f) for f in files_zip1])
    print(f"\n✗ Files ONLY in reference (not in converted): {len(only_in_reference)}")
    for f in sorted(only_in_reference):
        print(f"  - {f}")

    # Compare directory contents
    print("\n\n2. COMPARING EXTRACTED DIRECTORY CONTENTS")
    print("-" * 80)

    files_dir1 = get_directory_files(dir1)
    files_dir2 = get_directory_files(dir2)

    print(f"\nFiles in {dir1}: {len(files_dir1)}")
    print(f"Files in {dir2}: {len(files_dir2)}")

    # Files only in dir1
    only_in_dir1 = set([os.path.basename(f) for f in files_dir1]) - set([os.path.basename(f) for f in files_dir2])
    print(f"\n✗ Files ONLY in converted dir (not in reference dir): {len(only_in_dir1)}")
    for f in sorted(only_in_dir1):
        matching_files = [file for file in files_dir1 if os.path.basename(file) == f]
        for mf in matching_files:
            print(f"  - {mf}")

    # Files only in dir2
    only_in_dir2 = set([os.path.basename(f) for f in files_dir2]) - set([os.path.basename(f) for f in files_dir1])
    print(f"\n✗ Files ONLY in reference dir (not in converted dir): {len(only_in_dir2)}")
    for f in sorted(only_in_dir2):
        matching_files = [file for file in files_dir2 if os.path.basename(file) == f]
        for mf in matching_files:
            print(f"  - {mf}")

    # Compare file sizes for common files
    print("\n\n3. COMPARING FILE SIZES FOR COMMON FILES")
    print("-" * 80)

    sizes_dir1 = analyze_file_sizes(dir1)
    sizes_dir2 = analyze_file_sizes(dir2)

    # Find files with same basename in both directories
    basenames_dir1 = {os.path.basename(f): f for f in files_dir1}
    basenames_dir2 = {os.path.basename(f): f for f in files_dir2}

    common_basenames = set(basenames_dir1.keys()) & set(basenames_dir2.keys())

    size_differences = []
    for basename in sorted(common_basenames):
        file1_rel = basenames_dir1[basename]
        file2_rel = basenames_dir2[basename]

        size1 = sizes_dir1[file1_rel]
        size2 = sizes_dir2[file2_rel]

        if size1 != size2:
            diff = abs(size1 - size2)
            size_differences.append({
                'file': basename,
                'converted_size': size1,
                'reference_size': size2,
                'difference': diff
            })

    if size_differences:
        print(f"\n⚠ Files with different sizes: {len(size_differences)}")
        print("\nFile                                           Converted    Reference    Difference")
        print("-" * 90)
        for item in sorted(size_differences, key=lambda x: x['difference'], reverse=True):
            print(f"{item['file']:45} {item['converted_size']:10} {item['reference_size']:10} {item['difference']:10}")
    else:
        print("\n✓ All common files have identical sizes")

    # Summary
    print("\n\n4. SUMMARY")
    print("=" * 80)
    print(f"Total files in converted: {len(files_dir1)}")
    print(f"Total files in reference: {len(files_dir2)}")
    print(f"Files only in converted: {len(only_in_dir1)}")
    print(f"Files only in reference: {len(only_in_dir2)}")
    print(f"Common files: {len(common_basenames)}")
    print(f"Files with size differences: {len(size_differences)}")

    # Identify potential naming pattern differences
    print("\n\n5. FILE NAMING PATTERN ANALYSIS")
    print("-" * 80)

    print("\nConverted naming patterns:")
    for f in sorted(only_in_dir1):
        print(f"  - {f}")

    print("\nReference naming patterns:")
    for f in sorted(only_in_dir2):
        print(f"  - {f}")

    # Check if intro files correspond to preface files
    intro_files = [f for f in only_in_dir1 if 'intro' in f.lower()]
    preface_files = [f for f in only_in_dir2 if 'preface' in f.lower()]

    if intro_files or preface_files:
        print("\n⚠ POTENTIAL NAMING CONVENTION DIFFERENCE:")
        print("  Converted uses 'intro' naming, Reference uses 'preface' naming")
        print(f"  Intro files in converted: {intro_files}")
        print(f"  Preface files in reference: {preface_files}")

    # Check Chapter 2 section naming
    ch02_converted = [f for f in only_in_dir1 if 'Ch02Sec' in f or 'ch0002s' in f]
    ch02_reference = [f for f in only_in_dir2 if 'Ch02Sec' in f or 'ch0002s' in f]

    if ch02_converted or ch02_reference:
        print("\n⚠ CHAPTER 2 SECTION NAMING DIFFERENCE:")
        print(f"  Converted format: {ch02_converted}")
        print(f"  Reference format: {ch02_reference}")

if __name__ == "__main__":
    main()
