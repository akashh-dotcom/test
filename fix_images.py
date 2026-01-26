#!/usr/bin/env python3
"""
Fix image references in final_output_tables:
1. Copy original .jpg images from complete_original
2. Keep XML references as-is (they reference .jpg files)
"""

import shutil
from pathlib import Path
from lxml import etree
import re

ORIGINAL_MULTIMEDIA = Path('/workspace/complete_original/docbook_complete/multimedia')
OUTPUT_DIR = Path('/workspace/final_output_tables')
OUTPUT_MULTIMEDIA = OUTPUT_DIR / 'multimedia'

def get_xml_image_refs():
    """Get all image references from XML files."""
    refs = set()
    for xml_file in OUTPUT_DIR.glob('*.xml'):
        if xml_file.name == 'Book.xml':
            continue
        parser = etree.XMLParser(recover=True)
        try:
            tree = etree.parse(str(xml_file), parser)
            for img in tree.getroot().iter('imagedata'):
                fileref = img.get('fileref', '')
                if fileref:
                    refs.add(fileref)
        except:
            pass
    return refs

def main():
    print("=" * 80)
    print("FIXING IMAGE FILES")
    print("=" * 80)
    
    # Get all image references from XML
    xml_refs = get_xml_image_refs()
    print(f"\nImage references in XML: {len(xml_refs)}")
    
    # Check what exists in original
    original_files = set(f.name for f in ORIGINAL_MULTIMEDIA.iterdir() if f.is_file())
    print(f"Files in original multimedia: {len(original_files)}")
    
    # Clear and recreate multimedia folder
    if OUTPUT_MULTIMEDIA.exists():
        shutil.rmtree(OUTPUT_MULTIMEDIA)
    OUTPUT_MULTIMEDIA.mkdir(parents=True)
    
    # Copy all files from original
    copied = 0
    for src_file in ORIGINAL_MULTIMEDIA.iterdir():
        if src_file.is_file():
            dst_file = OUTPUT_MULTIMEDIA / src_file.name
            shutil.copy2(src_file, dst_file)
            copied += 1
    
    print(f"Copied {copied} files from original multimedia")
    
    # Check which XML refs are now satisfied
    current_files = set(f.name for f in OUTPUT_MULTIMEDIA.iterdir() if f.is_file())
    
    found = 0
    missing = []
    for ref in xml_refs:
        if ref in current_files:
            found += 1
        else:
            missing.append(ref)
    
    print(f"\nXML references satisfied: {found}/{len(xml_refs)}")
    
    if missing:
        print(f"\nStill missing {len(missing)} files:")
        for m in sorted(missing)[:20]:
            print(f"  - {m}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
    else:
        print("\n✓ All image references are satisfied!")
    
    # Verify
    print("\n" + "-" * 80)
    print("VERIFICATION")
    print("-" * 80)
    
    # Count by extension
    extensions = {}
    for f in OUTPUT_MULTIMEDIA.iterdir():
        ext = f.suffix.lower()
        extensions[ext] = extensions.get(ext, 0) + 1
    
    print("\nFiles in multimedia by extension:")
    for ext, count in sorted(extensions.items()):
        print(f"  {ext}: {count}")

if __name__ == '__main__':
    main()
