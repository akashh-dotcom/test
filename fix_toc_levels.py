#!/usr/bin/env python3
"""
Update TOC to use proper nesting levels:
- Sections (1.1, 1.2) → toclevel1
- Subsections (1.2.1, 1.4.1) → toclevel2 (nested inside parent's toclevel1)
"""

import re
from pathlib import Path

def fix_toc_nesting(toc_path):
    """Convert flat toclevel1 structure to properly nested toclevel1/toclevel2."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    changes = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a toclevel1 with a subsection (3-level number)
        if '<toclevel1>' in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Check if the entry has 3+ level numbering (e.g., 1.2.1)
            match = re.search(r'<tocentry linkend="[^"]+">(\d+\.\d+\.\d+(?:\.\d+)?)\s', next_line)
            if match:
                # This is a subsection, should be toclevel2
                new_lines.append(line.replace('<toclevel1>', '<toclevel2>'))
                new_lines.append(next_line)
                # Find closing tag
                i += 2
                while i < len(lines):
                    if '</toclevel1>' in lines[i]:
                        new_lines.append(lines[i].replace('</toclevel1>', '</toclevel2>'))
                        changes += 1
                        i += 1
                        break
                    else:
                        new_lines.append(lines[i])
                        i += 1
                continue

        new_lines.append(line)
        i += 1

    if changes > 0:
        with open(toc_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✅ Updated {changes} toclevel1 → toclevel2 for subsections")
    else:
        print("No changes needed")

    return changes

def main():
    toc_path = Path("/home/user/test/9781394266074-reference-converted/toc.9781394266074.xml")

    print("=" * 80)
    print("FIXING TOC NESTING LEVELS")
    print("=" * 80)
    print()

    fix_toc_nesting(toc_path)

    print()
    print("Done!")

if __name__ == "__main__":
    main()
