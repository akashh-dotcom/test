#!/usr/bin/env python3
"""
Fix TOC linkends by updating them line-by-line based on section numbers in the text.
"""

import re
from pathlib import Path

def fix_toc_line_by_line(toc_path):
    """Update TOC linkends based on section numbers in titles."""
    with open(toc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    current_chapter = None

    for i, line in enumerate(lines):
        # Match tocentry with linkend
        match = re.search(r'(<tocentry linkend=")([^"]*)(">)(.*?)(</tocentry>)', line)
        if not match:
            new_lines.append(line)
            continue

        old_linkend = match.group(2)
        text = match.group(4).strip()

        # Try to extract section number from the text
        num_match = re.match(r'^([\d\.]+)\s+(.+)$', text)

        if num_match:
            section_num = num_match.group(1)
            title = num_match.group(2)
            parts = section_num.split('.')

            if parts:
                ch_num = int(parts[0])
                ch_id = f"ch{str(ch_num + 10).zfill(4)}"
                current_chapter = ch_num

                # Build correct ID based on section number
                if len(parts) == 1:
                    # Main chapter (e.g., "1 Introduction...")
                    new_linkend = ch_id
                elif len(parts) == 2:
                    # Section (e.g., "1.2 Terminology")
                    sec_num = int(parts[1])
                    new_linkend = f"{ch_id}s{str(sec_num).zfill(4)}"
                elif len(parts) == 3:
                    # Subsection (e.g., "1.4.1 Role of...")
                    sec_num = int(parts[1])
                    subsec_num = int(parts[2])
                    new_linkend = f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}"
                elif len(parts) == 4:
                    # Sub-subsection (e.g., "3.3.6.1 Local...")
                    sec_num = int(parts[1])
                    subsec_num = int(parts[2])
                    subsubsec_num = int(parts[3])
                    new_linkend = f"{ch_id}s{str(sec_num).zfill(4)}s{str(subsec_num).zfill(4)}s{str(subsubsec_num).zfill(4)}"
                else:
                    new_linkend = old_linkend

                # Reconstruct the line
                new_line = line.replace(
                    f'linkend="{old_linkend}"',
                    f'linkend="{new_linkend}"'
                )
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            # No number - might be "References", "Index", etc.
            # Keep the old linkend or assign a new one if needed
            new_lines.append(line)

    with open(toc_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("TOC linkends updated based on section numbers")

def main():
    toc_path = Path("/home/user/test/9781394266074-reference-converted/toc.9781394266074.xml")
    fix_toc_line_by_line(toc_path)
    print("Done!")

if __name__ == "__main__":
    main()
