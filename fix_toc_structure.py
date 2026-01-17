#!/usr/bin/env python3
"""
Restructure TOC to wrap frontmatter items in a single frontmatter chapter.
"""

import re
from pathlib import Path

def restructure_toc(toc_path):
    """Restructure the TOC to group frontmatter items."""

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into lines for processing
    lines = content.split('\n')

    # Find indices of frontmatter chapters (ch0001-ch0009)
    frontmatter_start = None
    frontmatter_end = None

    for i, line in enumerate(lines):
        # Look for first frontmatter chapter
        if frontmatter_start is None and '<tocchap>' in line:
            # Check next line for chapter ID
            if i + 1 < len(lines) and 'linkend="ch0001"' in lines[i + 1]:
                frontmatter_start = i

        # Look for first non-frontmatter chapter (ch0010)
        if frontmatter_start is not None and frontmatter_end is None:
            if '<tocchap>' in line:
                if i + 1 < len(lines):
                    match = re.search(r'linkend="(ch\d{4})"', lines[i + 1])
                    if match:
                        ch_id = match.group(1)
                        ch_num = int(ch_id[2:])
                        if ch_num >= 10:
                            frontmatter_end = i
                            break

    if frontmatter_start is None or frontmatter_end is None:
        print("Could not find frontmatter boundaries")
        return

    print(f"Frontmatter chapters from line {frontmatter_start} to {frontmatter_end}")

    # Build new content
    new_lines = []

    # Add everything before frontmatter
    new_lines.extend(lines[:frontmatter_start])

    # Add frontmatter wrapper
    new_lines.append('   <tocchap>')
    new_lines.append('      <tocentry>FRONT MATTER</tocentry>')

    # Add frontmatter chapters with extra indentation
    for line in lines[frontmatter_start:frontmatter_end]:
        if line.strip():
            new_lines.append('   ' + line)
        else:
            new_lines.append(line)

    # Close frontmatter wrapper
    new_lines.append('   </tocchap>')
    new_lines.append('')

    # Add remaining chapters
    new_lines.extend(lines[frontmatter_end:])

    # Write back
    new_content = '\n'.join(new_lines)

    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"TOC restructured successfully!")
    print(f"Wrapped {frontmatter_end - frontmatter_start} lines of frontmatter")

if __name__ == "__main__":
    toc_path = Path("/home/user/test/9781394266074-reference-converted/toc.9781394266074.xml")
    restructure_toc(toc_path)
