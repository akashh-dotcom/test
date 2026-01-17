#!/usr/bin/env python3
"""
Convert Part sections from tocchap to tocpart elements and fix subsection levels correctly.
This version properly handles nested toclevel elements based on context.
"""

import re
from pathlib import Path

def convert_to_tocpart(toc_path):
    """Convert Part tocchap elements to tocpart elements and fix nesting."""

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a tocchap followed by a Part entry
        if '<tocchap>' in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Check if next line is a Part (without linkend)
            if '<tocentry>Part ' in next_line:
                # Extract Part title
                match = re.search(r'<tocentry>(Part [^<]+)</tocentry>', next_line)
                if match:
                    part_title = match.group(1)
                    # Get indent
                    indent = re.match(r'^(\s*)', line).group(1)

                    # Determine linkend based on Part number
                    if part_title.startswith('Part V'):
                        linkend = 'ch0030'
                    elif part_title.startswith('Part IV'):
                        linkend = 'ch0026'
                    elif part_title.startswith('Part III'):
                        linkend = 'ch0021'
                    elif part_title.startswith('Part II'):
                        linkend = 'ch0016'
                    elif part_title.startswith('Part I'):
                        linkend = 'ch0010'
                    else:
                        linkend = 'unknown'

                    # Write tocpart opening and entry
                    new_lines.append(f'{indent}<tocpart>')
                    new_lines.append(f'{indent}   <tocentry linkend="{linkend}">{part_title}</tocentry>')
                    new_lines.append('')

                    # Skip the original tocchap and tocentry lines
                    i += 2

                    # Now process the content inside this Part
                    # We need to convert toclevel2->toclevel1, toclevel3->toclevel2
                    # But only if not already nested
                    depth = 1
                    while i < len(lines) and depth > 0:
                        current_line = lines[i]

                        # Check for tocchap open/close
                        if '<tocchap>' in current_line:
                            depth += 1
                        elif '</tocchap>' in current_line:
                            depth -= 1
                            if depth == 0:
                                # This is the closing tag for the Part
                                new_lines.append(f'{indent}</tocpart>')
                                i += 1
                                continue

                        # Convert toclevel numbers
                        # We need to decrement all levels by 1
                        # toclevel3 -> toclevel2, toclevel2 -> toclevel1
                        current_line = convert_toclevel(current_line)

                        new_lines.append(current_line)
                        i += 1

                    continue

        new_lines.append(line)
        i += 1

    # Write back
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print("Successfully converted tocchap to tocpart for all Parts!")
    print("- Parts now use <tocpart> elements")
    print("- Parts have linkend attributes")
    print("- Subsections now use toclevel1 (was toclevel2)")
    print("- Sub-subsections now use toclevel2 (was toclevel3)")

def convert_toclevel(line):
    """Convert toclevel numbers by decrementing by 1."""
    # Replace in order: toclevel3 first, then toclevel2
    # This ensures we don't double-convert

    # Handle closing tags first (to avoid issues with order)
    if '</toclevel3>' in line:
        line = line.replace('</toclevel3>', '</toclevel2>')
    elif '</toclevel2>' in line:
        line = line.replace('</toclevel2>', '</toclevel1>')

    # Handle opening tags
    if '<toclevel3>' in line:
        line = line.replace('<toclevel3>', '<toclevel2>')
    elif '<toclevel2>' in line:
        line = line.replace('<toclevel2>', '<toclevel1>')

    return line

if __name__ == "__main__":
    toc_path = Path("/home/user/test/9781394266074-reference-converted/toc.9781394266074.xml")
    convert_to_tocpart(toc_path)
