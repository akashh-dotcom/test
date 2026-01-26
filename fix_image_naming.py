#!/usr/bin/env python3
"""
Fix image naming in final_output_tables to match the COMPLETE.zip convention.
Changes from: fig0001.png -> Ch0002f01.jpg (chapter-based naming)
"""

import os
import re
import shutil
from pathlib import Path
from collections import defaultdict

# Configuration
FINAL_OUTPUT_DIR = Path('/workspace/final_output_tables')
COMPLETE_DIR = Path('/workspace/complete_work/docbook_complete')
BACKUP_DIR = Path('/workspace/final_output_tables_backup')


def analyze_xml_files():
    """Analyze XML files to find figure references per chapter."""
    
    chapter_figures = defaultdict(list)  # chapter_num -> list of fig names
    
    xml_files = sorted(FINAL_OUTPUT_DIR.glob('ch*.xml'))
    
    for xml_file in xml_files:
        # Extract chapter number from filename (ch0002.xml -> 2)
        match = re.match(r'ch(\d+)\.xml', xml_file.name)
        if not match:
            continue
        
        chapter_num = int(match.group(1))
        
        # Read XML and find all figure references
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all fig references
        fig_refs = re.findall(r'fileref="(fig\d+\.png)"', content)
        
        for fig_ref in fig_refs:
            chapter_figures[chapter_num].append(fig_ref)
    
    return chapter_figures


def create_mapping(chapter_figures):
    """Create mapping from old fig names to new Ch####f## names."""
    
    mapping = {}  # old_name -> new_name
    
    for chapter_num in sorted(chapter_figures.keys()):
        figures = chapter_figures[chapter_num]
        
        # Track figure numbers per chapter
        fig_counter = 1
        seen_figs = set()
        
        for fig_name in figures:
            if fig_name in seen_figs:
                continue
            seen_figs.add(fig_name)
            
            # Create new name: Ch0002f01.png
            new_name = f"Ch{chapter_num:04d}f{fig_counter:02d}.png"
            mapping[fig_name] = new_name
            fig_counter += 1
    
    return mapping


def update_xml_files(mapping):
    """Update XML files with new image references."""
    
    xml_files = list(FINAL_OUTPUT_DIR.glob('ch*.xml'))
    xml_files.extend(FINAL_OUTPUT_DIR.glob('*.XML'))
    
    updated_count = 0
    
    for xml_file in xml_files:
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace all figure references
        for old_name, new_name in mapping.items():
            content = content.replace(f'fileref="{old_name}"', f'fileref="{new_name}"')
        
        if content != original_content:
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_count += 1
            print(f"  Updated: {xml_file.name}")
    
    return updated_count


def rename_image_files(mapping):
    """Rename image files in multimedia directory."""
    
    multimedia_dir = FINAL_OUTPUT_DIR / 'multimedia'
    
    renamed_count = 0
    missing_count = 0
    
    for old_name, new_name in mapping.items():
        old_path = multimedia_dir / old_name
        new_path = multimedia_dir / new_name
        
        if old_path.exists():
            # Rename the file
            shutil.move(str(old_path), str(new_path))
            renamed_count += 1
        else:
            missing_count += 1
    
    return renamed_count, missing_count


def main():
    print("=" * 70)
    print("FIX IMAGE NAMING IN final_output_tables")
    print("Converting: fig####.png -> Ch####f##.png")
    print("=" * 70)
    
    # Create backup
    print("\n1. Creating backup...")
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    shutil.copytree(FINAL_OUTPUT_DIR, BACKUP_DIR)
    print(f"   Backup created at: {BACKUP_DIR}")
    
    # Analyze XML files
    print("\n2. Analyzing XML files...")
    chapter_figures = analyze_xml_files()
    
    total_refs = sum(len(figs) for figs in chapter_figures.values())
    print(f"   Found {len(chapter_figures)} chapters with figure references")
    print(f"   Total figure references: {total_refs}")
    
    # Show sample per chapter
    print("\n   Figures per chapter:")
    for ch_num in sorted(chapter_figures.keys()):
        unique_figs = len(set(chapter_figures[ch_num]))
        print(f"     Chapter {ch_num}: {unique_figs} unique figures")
    
    # Create mapping
    print("\n3. Creating name mapping...")
    mapping = create_mapping(chapter_figures)
    print(f"   Created mapping for {len(mapping)} unique figures")
    
    # Show sample mappings
    print("\n   Sample mappings:")
    for i, (old, new) in enumerate(list(mapping.items())[:10]):
        print(f"     {old} -> {new}")
    if len(mapping) > 10:
        print(f"     ... and {len(mapping) - 10} more")
    
    # Rename image files
    print("\n4. Renaming image files...")
    renamed, missing = rename_image_files(mapping)
    print(f"   Renamed: {renamed} files")
    if missing > 0:
        print(f"   Missing: {missing} files (not found in multimedia)")
    
    # Update XML files
    print("\n5. Updating XML files...")
    updated = update_xml_files(mapping)
    print(f"   Updated: {updated} XML files")
    
    # Verify
    print("\n6. Verification...")
    multimedia_dir = FINAL_OUTPUT_DIR / 'multimedia'
    remaining_figs = list(multimedia_dir.glob('fig*.png'))
    new_ch_files = list(multimedia_dir.glob('Ch*.png'))
    
    print(f"   Old-style files remaining: {len(remaining_figs)}")
    print(f"   New-style files created: {len(new_ch_files)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Chapters processed: {len(chapter_figures)}")
    print(f"  Figures renamed: {renamed}")
    print(f"  XML files updated: {updated}")
    print(f"  Backup location: {BACKUP_DIR}")
    
    if remaining_figs:
        print(f"\n  Note: {len(remaining_figs)} fig*.png files remain")
        print(f"  These may be unused or referenced from other locations")


if __name__ == '__main__':
    main()
