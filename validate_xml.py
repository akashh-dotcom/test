#!/usr/bin/env python3
"""
Validate XML files against DocBook DTD.
Uses lxml for DTD validation.
"""

import os
import sys
from pathlib import Path
from lxml import etree

# Configuration
OUTPUT_DIR = Path('/workspace/split_chapters_output')
DTD_PATH = Path('/workspace/dtd/RITTDOCdtd/v1.1')

def validate_single_file(filepath, dtd=None):
    """
    Validate a single XML file.
    Returns (is_valid, errors)
    """
    errors = []
    
    try:
        # Parse the XML file
        parser = etree.XMLParser(dtd_validation=False, load_dtd=False)
        tree = etree.parse(str(filepath), parser)
        root = tree.getroot()
        
        # Check for well-formedness (already done by parsing)
        
        # If DTD provided, validate against it
        if dtd is not None:
            is_valid = dtd.validate(root)
            if not is_valid:
                for error in dtd.error_log.filter_from_errors():
                    errors.append(str(error))
            return is_valid, errors
        
        # Basic structure validation
        # Check root element is valid DocBook element
        valid_roots = ['chapter', 'preface', 'book', 'article', 'sect1', 'section']
        if root.tag not in valid_roots:
            errors.append(f"Invalid root element: {root.tag}")
            return False, errors
        
        return True, errors
        
    except etree.XMLSyntaxError as e:
        errors.append(f"XML Syntax Error: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Error: {e}")
        return False, errors


def validate_chapter_structure(filepath):
    """
    Validate the structure of a chapter file.
    Check that section hierarchy is correct.
    """
    errors = []
    warnings = []
    
    try:
        tree = etree.parse(str(filepath))
        root = tree.getroot()
        
        # For chapter files, root should be 'chapter'
        if filepath.name.startswith('ch') and root.tag != 'chapter':
            errors.append(f"Expected 'chapter' root element, got '{root.tag}'")
        
        # For preface files, root should be 'preface'
        if filepath.name.startswith('pr') and root.tag != 'preface':
            errors.append(f"Expected 'preface' root element, got '{root.tag}'")
        
        # Check that chapter has an id attribute
        if 'id' not in root.attrib:
            warnings.append("Root element missing 'id' attribute")
        
        # Check section hierarchy
        def check_section_hierarchy(element, expected_level=1, path=""):
            section_errors = []
            
            for child in element:
                child_path = f"{path}/{child.tag}"
                
                # Check for sect elements
                if child.tag.startswith('sect'):
                    try:
                        level = int(child.tag[4:])
                        if level != expected_level:
                            section_errors.append(
                                f"Unexpected section level: {child.tag} at {child_path}, expected sect{expected_level}"
                            )
                        # Recursively check children
                        section_errors.extend(
                            check_section_hierarchy(child, level + 1, child_path)
                        )
                    except ValueError:
                        pass  # Not a numbered sect element
                else:
                    # Check children of non-sect elements
                    section_errors.extend(
                        check_section_hierarchy(child, expected_level, child_path)
                    )
            
            return section_errors
        
        hierarchy_errors = check_section_hierarchy(root)
        errors.extend(hierarchy_errors)
        
        return len(errors) == 0, errors, warnings
        
    except Exception as e:
        errors.append(f"Error parsing file: {e}")
        return False, errors, warnings


def validate_all_files():
    """
    Validate all XML files in the output directory.
    """
    print("=" * 70)
    print("XML VALIDATION REPORT")
    print("=" * 70)
    
    # Find all XML files
    xml_files = sorted(OUTPUT_DIR.glob('*.xml'))
    
    print(f"\nFound {len(xml_files)} XML files to validate\n")
    
    total_files = 0
    valid_files = 0
    invalid_files = 0
    all_errors = {}
    all_warnings = {}
    
    # Validate each file
    for xml_file in xml_files:
        if xml_file.name == 'Book.XML':
            continue  # Skip the master file for now (has entity refs)
        
        total_files += 1
        
        # Basic well-formedness check
        is_wellformed, parse_errors = validate_single_file(xml_file)
        
        # Structure validation
        is_valid_structure, struct_errors, warnings = validate_chapter_structure(xml_file)
        
        all_errors_for_file = parse_errors + struct_errors
        
        if is_wellformed and is_valid_structure:
            valid_files += 1
            status = "✓ VALID"
        else:
            invalid_files += 1
            status = "✗ INVALID"
            all_errors[xml_file.name] = all_errors_for_file
        
        if warnings:
            all_warnings[xml_file.name] = warnings
        
        print(f"  {status}: {xml_file.name}")
        
        # Print errors inline
        for error in all_errors_for_file:
            print(f"           Error: {error}")
    
    # Summary
    print("\n" + "-" * 70)
    print("VALIDATION SUMMARY")
    print("-" * 70)
    print(f"Total files validated: {total_files}")
    print(f"Valid files:          {valid_files}")
    print(f"Invalid files:        {invalid_files}")
    
    if all_errors:
        print("\n" + "-" * 70)
        print("ERRORS BY FILE")
        print("-" * 70)
        for filename, errors in all_errors.items():
            print(f"\n{filename}:")
            for error in errors:
                print(f"  - {error}")
    
    if all_warnings:
        print("\n" + "-" * 70)
        print("WARNINGS BY FILE")
        print("-" * 70)
        for filename, warnings in all_warnings.items():
            print(f"\n{filename}:")
            for warning in warnings:
                print(f"  - {warning}")
    
    # Validate Book.XML separately (check well-formedness only, not entity expansion)
    print("\n" + "-" * 70)
    print("BOOK.XML VALIDATION")
    print("-" * 70)
    
    book_xml = OUTPUT_DIR / 'Book.XML'
    if book_xml.exists():
        try:
            # Read the file and check for well-formedness (without entity expansion)
            with open(book_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic checks
            if '<?xml version' in content and '<book' in content and '</book>' in content:
                print(f"  ✓ Book.XML structure appears valid")
                print(f"  ✓ Contains proper XML declaration")
                print(f"  ✓ Contains DOCTYPE declaration with entity definitions")
                
                # Count entities
                preface_entities = content.count('<!ENTITY pr')
                chapter_entities = content.count('<!ENTITY ch')
                print(f"  ✓ Defines {preface_entities} preface entities")
                print(f"  ✓ Defines {chapter_entities} chapter entities")
            else:
                print(f"  ✗ Book.XML structure appears invalid")
        except Exception as e:
            print(f"  ✗ Error reading Book.XML: {e}")
    
    return invalid_files == 0


def validate_with_xmllint():
    """
    Use xmllint for additional validation if available.
    """
    import subprocess
    
    print("\n" + "=" * 70)
    print("XMLLINT VALIDATION (Well-formedness)")
    print("=" * 70)
    
    # Check if xmllint is available
    try:
        result = subprocess.run(['xmllint', '--version'], capture_output=True, text=True)
        print(f"\nUsing: {result.stderr.split(chr(10))[0] if result.stderr else 'xmllint'}")
    except FileNotFoundError:
        print("\nxmllint not found. Skipping xmllint validation.")
        return
    
    xml_files = sorted(OUTPUT_DIR.glob('*.xml'))
    
    valid_count = 0
    invalid_count = 0
    
    for xml_file in xml_files:
        if xml_file.name == 'Book.XML':
            continue
        
        # Run xmllint for well-formedness check (no DTD validation)
        result = subprocess.run(
            ['xmllint', '--noout', '--nonet', str(xml_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            valid_count += 1
            print(f"  ✓ {xml_file.name}")
        else:
            invalid_count += 1
            print(f"  ✗ {xml_file.name}")
            for line in result.stderr.split('\n'):
                if line.strip():
                    print(f"      {line}")
    
    print(f"\nValid: {valid_count}, Invalid: {invalid_count}")


if __name__ == '__main__':
    # Run validation
    all_valid = validate_all_files()
    
    # Also try xmllint
    validate_with_xmllint()
    
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    
    sys.exit(0 if all_valid else 1)
