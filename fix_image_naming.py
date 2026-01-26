#!/usr/bin/env python3
"""
Fix image naming convention from fig0001.png to Ch0001f01.png format.
"""

import os
import re
import shutil
from pathlib import Path

SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_FIXED_IMAGES')

def get_chapter_images(xml_file):
    """Extract image references from XML file."""
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all image references
    images = re.findall(r'fileref="(fig\d+\.png)"', content)
    return images

def create_image_mapping():
    """Create mapping from old names to new names."""
    mapping = {}
    
    # Process each chapter
    for xml_file in sorted(SOURCE_DIR.glob('ch*.xml')):
        chapter_name = xml_file.stem  # e.g., 'ch0001'
        chapter_num = chapter_name[2:]  # e.g., '0001'
        
        images = get_chapter_images(xml_file)
        
        # Create mapping for each image in this chapter
        for i, old_name in enumerate(images, 1):
            if old_name not in mapping:
                new_name = f"Ch{chapter_num}f{i:02d}.png"
                mapping[old_name] = new_name
    
    return mapping

def fix_xml_references(xml_file, mapping, output_file):
    """Update image references in XML file."""
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all image references
    for old_name, new_name in mapping.items():
        content = content.replace(f'fileref="{old_name}"', f'fileref="{new_name}"')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("Fixing image naming convention\n")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create image mapping
    print("Creating image mapping...")
    mapping = create_image_mapping()
    print(f"Found {len(mapping)} images to rename")
    
    # Show some examples
    print("\nExamples:")
    for i, (old, new) in enumerate(list(mapping.items())[:5]):
        print(f"  {old} -> {new}")
    
    # Copy and rename images
    print("\nRenaming images...")
    multimedia_src = SOURCE_DIR / 'multimedia'
    multimedia_dst = OUTPUT_DIR / 'multimedia'
    multimedia_dst.mkdir(parents=True, exist_ok=True)
    
    renamed = 0
    for old_name, new_name in mapping.items():
        src_file = multimedia_src / old_name
        dst_file = multimedia_dst / new_name
        
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            renamed += 1
        else:
            print(f"  Warning: {old_name} not found")
    
    # Copy any remaining images that weren't mapped
    for img_file in multimedia_src.glob('*.png'):
        if img_file.name not in mapping:
            dst_file = multimedia_dst / img_file.name
            if not dst_file.exists():
                shutil.copy2(img_file, dst_file)
    
    print(f"Renamed {renamed} images")
    
    # Update XML files
    print("\nUpdating XML references...")
    for xml_file in sorted(SOURCE_DIR.glob('*.xml')):
        output_file = OUTPUT_DIR / xml_file.name
        
        if xml_file.name == 'Book.XML':
            shutil.copy(xml_file, output_file)
        else:
            fix_xml_references(xml_file, mapping, output_file)
    
    print(f"\nDone! Output in {OUTPUT_DIR}")
    
    # Show verification
    print("\nVerification (ch0001.xml):")
    with open(OUTPUT_DIR / 'ch0001.xml', 'r') as f:
        content = f.read()
    refs = re.findall(r'fileref="([^"]+)"', content)[:5]
    for ref in refs:
        print(f"  {ref}")

if __name__ == '__main__':
    main()
