#!/usr/bin/env python3
"""
Fix Part entries to be labels only, not clickable links.
Parts should just be organizational containers, not links.
"""

import re
from pathlib import Path

def fix_part_links(toc_path):
    """Remove linkend from Part tocentry elements."""

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line contains a Part tocentry
        if '<tocentry' in line and 'Part ' in line and 'linkend=' in line:
            # Extract the title
            match = re.search(r'<tocentry linkend="[^"]*">(Part [^<]+)</tocentry>', line)
            if match:
                title = match.group(1)
                # Get the indentation
                indent = re.match(r'^(\s*)', line).group(1)
                # Create new line without linkend
                new_line = f'{indent}<tocentry>{title}</tocentry>'
                new_lines.append(new_line)
                i += 1
                continue

        new_lines.append(line)
        i += 1

    # Write back
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print("Fixed Part links successfully!")
    print("Parts are now labels without clickable links")

if __name__ == "__main__":
    toc_path = Path("/home/user/test/9781394266074-reference-converted/toc.9781394266074.xml")
    fix_part_links(toc_path)
