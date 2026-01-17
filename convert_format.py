#!/usr/bin/env python3
"""
Convert XML files from reffering format to reference format.
Preserves content while changing file naming conventions and IDs.
"""

import os
import re
import shutil
from pathlib import Path

def convert_filename(old_name, isbn="9781394266074"):
    """Convert filename from reffering format to reference format."""
    # Handle book.xml - no change needed
    if old_name == f"book.{isbn}.xml":
        return old_name

    # Handle toc files - SKIP the one with double dots (wrong format)
    if old_name == f"toc.{isbn}..xml":
        return None  # Skip this file
    if old_name == f"toc.{isbn}.xml":
        return old_name

    # Handle preface pattern: ch0001-intro -> preface.ISBN.ch0001.xml
    match = re.match(rf"sect1\.{isbn}\.ch(\d{{4}})-intro\.xml", old_name)
    if match:
        ch_num = match.group(1)
        return f"preface.{isbn}.ch{ch_num}.xml"

    # Handle CamelCase pattern: Ch02Sec01 -> ch0002s0001
    match = re.match(rf"sect1\.{isbn}\.Ch(\d{{2}})Sec(\d{{2}})\.xml", old_name)
    if match:
        ch_num = match.group(1)
        sec_num = match.group(2)
        return f"sect1.{isbn}.ch00{ch_num}s00{sec_num}.xml"

    # Handle files with extra zeros: ch0003s000000 -> ch0003s0000
    match = re.match(rf"sect1\.{isbn}\.ch(\d{{4}})s(\d{{6}})\.xml", old_name)
    if match:
        ch_num = match.group(1)
        sec_num = match.group(2)
        # Reduce section number from 6 digits to 4 digits
        sec_num_4 = sec_num[-4:]  # Take last 4 digits
        return f"sect1.{isbn}.ch{ch_num}s{sec_num_4}.xml"

    # Handle other intro patterns: ch0004-intro -> ch0004s0000 (assuming section 0)
    match = re.match(rf"sect1\.{isbn}\.ch(\d{{4}})-intro\.xml", old_name)
    if match:
        ch_num = match.group(1)
        return f"sect1.{isbn}.ch{ch_num}s0000.xml"

    # If already in correct format, return as-is
    return old_name

def convert_id(old_id):
    """Convert ID from reffering format to reference format."""
    # Handle preface pattern: ch0001-intro -> ch0001
    if re.match(r"ch\d{4}-intro", old_id):
        return old_id.replace("-intro", "")

    # Handle CamelCase pattern: Ch02Sec01 -> ch0002s0001
    match = re.match(r"Ch(\d{2})Sec(\d{2})", old_id)
    if match:
        ch_num = match.group(1)
        sec_num = match.group(2)
        return f"ch00{ch_num}s00{sec_num}"

    # Handle files with extra zeros: ch0003s000000 -> ch0003s0000
    match = re.match(r"ch(\d{4})s(\d{6})", old_id)
    if match:
        ch_num = match.group(1)
        sec_num = match.group(2)
        sec_num_4 = sec_num[-4:]
        return f"ch{ch_num}s{sec_num_4}"

    # Handle other intro patterns
    if old_id.endswith("-intro"):
        return old_id.replace("-intro", "s0000")

    return old_id

def convert_entity_name(old_entity, isbn="9781394266074"):
    """Convert entity name from reffering format to reference format."""
    # Remove ISBN and extension to get the ID part
    pattern = rf"(sect1|preface|toc)\.{isbn}\.(.*?)(\.xml)?$"
    match = re.match(pattern, old_entity)
    if not match:
        return old_entity

    prefix = match.group(1)
    id_part = match.group(2)

    # Convert the ID part
    new_id = convert_id(id_part)

    # Special case for toc with empty ID
    if old_entity == f"toc.{isbn}.":
        return f"toc.{isbn}."

    # Reconstruct entity name
    if prefix == "preface":
        return f"preface.{isbn}.{new_id}"
    else:
        return f"sect1.{isbn}.{new_id}"

def update_file_content(content, isbn="9781394266074"):
    """Update all references within file content."""
    # Pattern to find all entity references and IDs

    # Update id attributes: id="Ch02Sec01" -> id="ch0002s0001"
    def replace_id(match):
        old_id = match.group(1)
        new_id = convert_id(old_id)
        return f'id="{new_id}"'
    content = re.sub(r'id="([^"]+)"', replace_id, content)

    # Update entity references in risprev, riscurrent, risnext
    def replace_entity_ref(match):
        tag = match.group(1)
        old_ref = match.group(2)
        closing = match.group(3)
        # Convert the reference
        parts = old_ref.split('.')
        if len(parts) >= 3:
            prefix = parts[0]  # sect1, preface, toc
            isbn_part = parts[1]
            id_part = '.'.join(parts[2:])
            new_id = convert_id(id_part)
            new_ref = f"{prefix}.{isbn_part}.{new_id}"
        else:
            new_ref = old_ref
        return f"<{tag}>{new_ref}</{closing}>"

    content = re.sub(r'<(risprev|riscurrent|risnext)>([^<]+)</(\w+)>', replace_entity_ref, content)

    # Update linkend attributes: linkend="Ch02Sec01" -> linkend="ch0002s0001"
    def replace_linkend(match):
        old_id = match.group(1)
        new_id = convert_id(old_id)
        return f'linkend="{new_id}"'
    content = re.sub(r'linkend="([^"]+)"', replace_linkend, content)

    return content

def convert_book_xml(content, old_to_new_map, isbn="9781394266074"):
    """Update book.xml with new entity declarations."""
    # Extract DOCTYPE and entity declarations
    doctype_start = content.find('<!DOCTYPE')
    doctype_end = content.find(']>', doctype_start) + 2

    if doctype_start == -1 or doctype_end == -1:
        return content

    # Get the parts
    before_doctype = content[:doctype_start]
    after_doctype = content[doctype_end:]

    # Build new entity declarations
    entities = []
    seen_entities = set()
    for old_file, new_file in sorted(old_to_new_map.items()):
        if old_file == f"book.{isbn}.xml":
            continue

        # Get entity name (without .xml extension)
        old_entity = old_file.replace('.xml', '')
        new_entity = new_file.replace('.xml', '')

        # Skip duplicates (e.g., toc files with double dots)
        if new_entity in seen_entities:
            continue
        seen_entities.add(new_entity)

        entities.append(f'<!ENTITY {new_entity} SYSTEM "{new_file}">')

    # Reconstruct DOCTYPE
    new_doctype = f'''<!DOCTYPE book PUBLIC "-//RIS Dev//DTD DocBook V4.3 -Based Variant V1.1//EN" "file:///c:/Inetpub/wwwroot/dtd/v1.1/RittDocBook.dtd" [{chr(10).join(entities)}]>'''

    return before_doctype + new_doctype + after_doctype

def main():
    """Main conversion function."""
    source_dir = Path("/home/user/test/9781394266074-reffering")
    output_dir = Path("/home/user/test/9781394266074-reference-converted")
    zip_output = Path("/home/user/test/9781394266074-reference.zip")

    isbn = "9781394266074"

    # Create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    # Build file mapping
    old_to_new_map = {}
    for file_path in source_dir.glob("*.xml"):
        old_name = file_path.name
        new_name = convert_filename(old_name, isbn)
        if new_name is not None:  # Skip files that should be excluded
            old_to_new_map[old_name] = new_name

    print(f"Converting {len(old_to_new_map)} files...")

    # Process each file
    for old_name, new_name in old_to_new_map.items():
        source_file = source_dir / old_name
        target_file = output_dir / new_name

        print(f"  {old_name} -> {new_name}")

        # Read content
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update content (except for book.xml which we handle separately)
        if old_name != f"book.{isbn}.xml":
            content = update_file_content(content, isbn)
        else:
            # Special handling for book.xml
            content = convert_book_xml(content, old_to_new_map, isbn)

        # Write to new file
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f"\nConversion complete! Files saved to: {output_dir}")

    # Create ZIP file
    print(f"Creating ZIP archive: {zip_output}")
    shutil.make_archive(
        str(zip_output.with_suffix('')),
        'zip',
        output_dir
    )

    print(f"\nZIP file created: {zip_output}")
    print(f"Total files converted: {len(old_to_new_map)}")

if __name__ == "__main__":
    main()
