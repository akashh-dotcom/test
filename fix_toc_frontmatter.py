#!/usr/bin/env python3
"""
Convert frontmatter tocchap elements to tocfront elements to match reference format.
"""

import re
from pathlib import Path

def extract_title_from_chapter(lines, start_idx):
    """Extract the title from a tocchap block."""
    # Look for the first tocentry with actual content
    for i in range(start_idx, min(start_idx + 20, len(lines))):
        if '</tocchap>' in lines[i]:
            break
        # Look in toclevel1 for the real title
        if '<toclevel1>' in lines[i]:
            if i + 1 < len(lines):
                match = re.search(r'<tocentry[^>]*>([^<]+)</tocentry>', lines[i + 1])
                if match:
                    title = match.group(1).strip()
                    if title and title.lower() != 'content':
                        return title
        # Fallback to main tocentry
        match = re.search(r'<tocentry[^>]*>([^<]+)</tocentry>', lines[i])
        if match:
            title = match.group(1).strip()
            if title and title.lower() not in ['chapter', 'content']:
                return title
    return None

def restructure_toc(toc_path):
    """Convert frontmatter tocchap elements to tocfront elements."""

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a tocchap
        if '<tocchap>' in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            match = re.search(r'linkend="(ch\d{4})"', next_line)

            if match:
                ch_id = match.group(1)
                ch_num = int(ch_id[2:])

                # If it's frontmatter (ch0001-ch0009), convert to tocfront
                if 1 <= ch_num <= 9:
                    # Extract title from the chapter
                    title = extract_title_from_chapter(lines, i)

                    if title:
                        # Create tocfront element
                        # Check if there's a more specific linkend in toclevel1
                        linkend = ch_id
                        for j in range(i, min(i + 10, len(lines))):
                            if '</tocchap>' in lines[j]:
                                break
                            if '<toclevel1>' in lines[j] and j + 1 < len(lines):
                                toc_match = re.search(r'<tocentry linkend="([^"]+)">', lines[j + 1])
                                if toc_match:
                                    linkend = toc_match.group(1)
                                    break

                        new_lines.append(f'   <tocfront linkend="{linkend}">{title}</tocfront>')
                    else:
                        new_lines.append(f'   <tocfront linkend="{ch_id}">Content</tocfront>')

                    # Skip until end of this tocchap
                    depth = 1
                    i += 1
                    while i < len(lines) and depth > 0:
                        if '<tocchap>' in lines[i]:
                            depth += 1
                        elif '</tocchap>' in lines[i]:
                            depth -= 1
                        i += 1
                    continue

        new_lines.append(line)
        i += 1

    # Write back
    new_content = '\n'.join(new_lines)

    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"TOC restructured successfully!")
    print(f"Converted frontmatter chapters to tocfront elements")

if __name__ == "__main__":
    toc_path = Path("/home/user/test/9781394266074-reference-converted/toc.9781394266074.xml")
    restructure_toc(toc_path)
