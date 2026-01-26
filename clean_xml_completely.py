#!/usr/bin/env python3
"""
Clean XML files completely:
1. Remove paragraphs with BioRef metadata
2. Remove paragraphs containing unstructured table data
3. Keep only properly structured content
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

SOURCE_DIR = Path('/workspace/final_output_tables_CLEAN')
OUTPUT_DIR = Path('/workspace/final_output_tables_FINAL')


def is_bioref_para(text):
    """Check if paragraph is BioRef metadata"""
    if not text:
        return False
    return 'BioRef' in text and ('Layout' in text or 'Page' in text)


def is_unstructured_table_data(text):
    """Check if paragraph looks like unstructured table data"""
    if not text:
        return False
    
    # Check for patterns that indicate raw table data dumped into para
    # Like: "Table 2." followed by data fragments
    if re.search(r'Table\s+\d+\.\s*$', text.strip()):
        return True
    
    # Check for force index style data
    if 'Force' in text and 'Index' in text and re.search(r'\d+\.\d+', text):
        return True
    
    # Check for rows of numbers separated by newlines/spaces
    lines = text.split('\n')
    if len(lines) > 3:
        number_lines = sum(1 for l in lines if re.match(r'^[\d\.\-\s]+$', l.strip()))
        if number_lines > len(lines) / 2:
            return True
    
    return False


def clean_xml_file(xml_file, output_file):
    """Clean a single XML file"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    removed = 0
    
    # Find and remove bad paragraphs
    for parent in list(root.iter()):
        children_to_remove = []
        
        for child in list(parent):
            if child.tag == 'para':
                # Get all text including tail
                text = ET.tostring(child, encoding='unicode', method='text')
                
                if is_bioref_para(text):
                    children_to_remove.append(child)
                elif is_unstructured_table_data(text):
                    children_to_remove.append(child)
        
        for child in children_to_remove:
            parent.remove(child)
            removed += 1
    
    # Also clean up inline table data fragments in remaining paras
    for para in root.iter('para'):
        if para.text:
            # Remove inline table fragments like "Table 2." at end
            para.text = re.sub(r'\s*Table\s+\d+\.\s*$', '', para.text)
            
            # Remove force index inline data
            if 'Force' in para.text and 'Index' in para.text:
                # Check if it's mostly data
                if re.search(r'\d+\.\d+.*\d+\.\d+', para.text):
                    para.text = re.sub(r'Force\s*Index.*$', '', para.text, flags=re.DOTALL)
    
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return removed


def main():
    print("=" * 60)
    print("CLEANING XML FILES")
    print("=" * 60)
    
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    
    total_removed = 0
    
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        output_file = xml_file  # Overwrite in place
        removed = clean_xml_file(xml_file, output_file)
        
        if removed > 0:
            ch_match = re.search(r'ch(\d+)', xml_file.name)
            ch_num = int(ch_match.group(1)) if ch_match else 0
            print(f"  Chapter {ch_num:02d}: Removed {removed} malformed paragraphs")
            total_removed += removed
    
    print(f"\nTotal paragraphs removed: {total_removed}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
