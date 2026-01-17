#!/usr/bin/env python3
"""
Fix entity references in book.xml to match the converted naming format.
"""

import re
from pathlib import Path

def fix_entity_references(book_path):
    """Update entity references in book.xml to use the new naming format."""

    with open(book_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix patterns:
    # 1. ch0001-intro -> ch0001 (preface pattern)
    # 2. Ch02Sec01 -> ch0002s0001 (CamelCase pattern)
    # 3. ch0003s000000 -> ch0003s0000 (6-digit to 4-digit)

    # Pattern 1: Remove -intro suffix
    content = re.sub(r'&sect1\.9781394266074\.ch(\d{4})-intro;',
                     r'&preface.9781394266074.ch\1;', content)

    # Pattern 2: Convert CamelCase ChXXSecYY to chXXsYY format
    def convert_camelcase_ref(match):
        ch_num = match.group(1)
        sec_num = match.group(2)
        # Convert Ch02Sec01 to ch0002s0001
        ch_padded = ch_num.zfill(4)
        sec_padded = sec_num.zfill(4)
        return f'&sect1.9781394266074.ch{ch_padded}s{sec_padded};'

    content = re.sub(r'&sect1\.9781394266074\.Ch(\d+)Sec(\d+);',
                     convert_camelcase_ref, content)

    # Pattern 3: Convert 6-digit section numbers to 4-digit
    # s000000 -> s0000, s000001 -> s0001, etc.
    def convert_section_number(match):
        prefix = match.group(1)
        section = match.group(2)
        # Convert 6-digit to 4-digit
        section_int = int(section)
        section_4digit = str(section_int).zfill(4)
        return f'{prefix}s{section_4digit};'

    content = re.sub(r'(&sect1\.9781394266074\.ch\d{4})s(\d{6});',
                     convert_section_number, content)

    # Write back
    with open(book_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Successfully fixed entity references in book.xml!")
    print("- Converted -intro suffix to preface entities")
    print("- Converted CamelCase references to lowercase")
    print("- Converted 6-digit section numbers to 4-digit")

if __name__ == "__main__":
    book_path = Path("/home/user/test/9781394266074-reference-converted/book.9781394266074.xml")
    fix_entity_references(book_path)
