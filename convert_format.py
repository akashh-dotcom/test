#!/usr/bin/env python3
"""
Convert XML files from 9781394266074-reffering format to 9781394211319-reference format.
Main change: 6-digit section IDs to 4-digit section IDs
"""

import os
import re
import shutil
from pathlib import Path

SOURCE_DIR = Path("/workspace/9781394266074-reffering")
OUTPUT_DIR = Path("/workspace/9781394266074-converted")

def convert_section_id(match):
    """Convert 6-digit section ID to 4-digit format."""
    prefix = match.group(1)  # e.g., "ch0011s"
    digits = match.group(2)  # e.g., "001000" or "000000"
    
    # Convert 6-digit to 4-digit
    # s000000 -> s0000
    # s001000 -> s1000
    # s009000 -> s9000
    # s009100 -> s9100 (keep last 4 digits for sub-sections)
    
    if len(digits) == 6:
        # Take digits 2-5 to match reference format
        # s001000 -> s1000 (section 1, sub 000)
        # s002000 -> s2000 (section 2, sub 000)
        new_digits = digits[2:6]  # Remove first 2 digits
    else:
        new_digits = digits
    
    return prefix + new_digits

def convert_file_content(content):
    """Convert all section ID references in the content."""
    
    # Pattern to match section IDs like ch0011s001000, ch0003s000000
    # Format: ch####s###### (chapter + 6-digit section)
    pattern = r'(ch\d{4}s)(\d{6})'
    
    converted = re.sub(pattern, convert_section_id, content)
    
    # Also handle special cases like "ch0001-intro", "Ch02Sec01" etc. - leave as is
    # These don't have the 6-digit pattern
    
    return converted

def convert_filename(filename):
    """Convert filename from 6-digit to 4-digit section format."""
    # Pattern: sect1.9781394266074.ch0003s000000.xml -> sect1.9781394266074.ch0003s0000.xml
    pattern = r'(ch\d{4}s)(\d{6})(\.xml)'
    
    def replace_fn(match):
        prefix = match.group(1)
        digits = match.group(2)
        ext = match.group(3)
        new_digits = digits[2:6]  # Remove first 2 digits to match reference format
        return prefix + new_digits + ext
    
    return re.sub(pattern, replace_fn, filename)

def process_files():
    """Process all XML files in the source directory."""
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    processed = 0
    
    for filepath in SOURCE_DIR.glob("*.xml"):
        filename = filepath.name
        
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert content (section IDs)
        converted_content = convert_file_content(content)
        
        # Convert filename
        new_filename = convert_filename(filename)
        
        # Write to output
        output_path = OUTPUT_DIR / new_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        
        processed += 1
        print(f"Converted: {filename} -> {new_filename}")
    
    print(f"\nTotal files processed: {processed}")
    return processed

if __name__ == "__main__":
    count = process_files()
    print(f"\nConversion complete! {count} files written to {OUTPUT_DIR}")
