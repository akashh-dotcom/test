#!/usr/bin/env python3
"""
Fix TOC chapter entries to show actual chapter names instead of "chapter".
"""

import re
from pathlib import Path

def fix_chapter_titles(toc_path):
    """Replace 'chapter' placeholders with actual chapter titles."""

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for tocchap entries with "chapter" placeholder
        if '<tocchap>' in line:
            # Check if next line has "chapter" as text
            if i + 1 < len(lines) and '>chapter</tocentry>' in lines[i + 1]:
                # Get the linkend from this line
                linkend_match = re.search(r'linkend="([^"]+)"', lines[i + 1])

                # Find the actual title in the next toclevel1
                actual_title = None
                j = i + 2
                while j < len(lines) and j < i + 10:
                    if '<toclevel1>' in lines[j]:
                        # Next line should have the title
                        if j + 1 < len(lines):
                            title_match = re.search(r'<tocentry[^>]*>([^<]+)</tocentry>', lines[j + 1])
                            if title_match:
                                actual_title = title_match.group(1)
                                break
                    if '</tocchap>' in lines[j]:
                        break
                    j += 1

                # Add the tocchap opening
                new_lines.append(line)

                # Replace the chapter line with actual title
                if actual_title and linkend_match:
                    linkend = linkend_match.group(1)
                    new_lines.append(f'      <tocentry linkend="{linkend}">{actual_title}</tocentry>')
                else:
                    new_lines.append(lines[i + 1])

                i += 2
                continue

        new_lines.append(line)
        i += 1

    # Write back
    new_content = '\n'.join(new_lines)

    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"TOC chapter titles fixed successfully!")

if __name__ == "__main__":
    toc_path = Path("/home/user/test/9781394266074-reference-converted/toc.9781394266074.xml")
    fix_chapter_titles(toc_path)
