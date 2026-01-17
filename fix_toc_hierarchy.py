#!/usr/bin/env python3
"""
Restructure TOC to properly nest chapters under parts and remove redundant structure.
"""

import re
from pathlib import Path

def parse_toc_chapters(content):
    """Parse all chapters from the TOC content."""
    chapters = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        if '<tocchap>' in lines[i]:
            chapter = {'start': i, 'lines': []}
            depth = 1
            chapter['lines'].append(lines[i])
            i += 1

            while i < len(lines) and depth > 0:
                if '<tocchap>' in lines[i]:
                    depth += 1
                elif '</tocchap>' in lines[i]:
                    depth -= 1

                chapter['lines'].append(lines[i])
                i += 1

            # Extract title
            for line in chapter['lines'][:5]:
                match = re.search(r'<tocentry[^>]*>([^<]+)</tocentry>', line)
                if match:
                    chapter['title'] = match.group(1)
                    break

            chapters.append(chapter)
        else:
            i += 1

    return chapters

def is_part_chapter(title):
    """Check if this is a part divider."""
    return title.startswith('Part ') and len(title) > 7

def is_standalone_chapter(title):
    """Check if this chapter should not be nested."""
    standalone_titles = ['Index', 'WILEY END USER LICENSE AGREEMENT']
    return any(standalone in title for standalone in standalone_titles)

def simplify_chapter(chapter_lines):
    """Remove redundant toclevel1 wrapper from chapter."""
    result = [chapter_lines[0]]  # Keep <tocchap>
    result.append(chapter_lines[1])  # Keep main <tocentry>

    i = 2
    # Skip to find toclevel1
    while i < len(chapter_lines) and '<toclevel1>' not in chapter_lines[i]:
        i += 1

    if i < len(chapter_lines):
        i += 1  # Skip <toclevel1>
        # Skip duplicate tocentry
        if i < len(chapter_lines) and '<tocentry' in chapter_lines[i]:
            i += 1

        # Copy toclevel2/3 content
        while i < len(chapter_lines):
            if '</toclevel1>' in chapter_lines[i]:
                break
            if '<toclevel2>' in chapter_lines[i] or '<toclevel3>' in chapter_lines[i] or \
               '</toclevel2>' in chapter_lines[i] or '</toclevel3>' in chapter_lines[i] or \
               '<tocentry' in chapter_lines[i]:
                result.append(chapter_lines[i])
            i += 1

    result.append('   </tocchap>')
    return result

def restructure_toc_hierarchy(toc_path):
    """Restructure TOC to nest chapters under parts."""

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Find header (everything before first tocchap)
    header_end = 0
    for i, line in enumerate(lines):
        if '<tocchap>' in line:
            header_end = i
            break

    header = lines[:header_end]

    # Parse chapters
    chapters_content = '\n'.join(lines[header_end:])
    chapters = parse_toc_chapters('\n'.join(lines))

    # Reorganize chapters
    new_body = []
    current_part = None

    for chapter in chapters:
        title = chapter.get('title', '')

        if is_standalone_chapter(title):
            # Close current part if open
            if current_part is not None:
                new_body.append('   </tocchap>')
                new_body.append('')
                current_part = None

            # Add standalone chapter
            simplified = simplify_chapter(chapter['lines'])
            new_body.extend(simplified)
            new_body.append('')

        elif is_part_chapter(title):
            # Close previous part if open
            if current_part is not None:
                new_body.append('   </tocchap>')
                new_body.append('')

            # Start new part
            new_body.append('   <tocchap>')
            new_body.append(f'      <tocentry linkend="{extract_linkend(chapter["lines"])}">{title}</tocentry>')
            new_body.append('')
            current_part = title

        else:
            # Regular chapter
            simplified = simplify_chapter(chapter['lines'])

            # Indent if inside a part
            if current_part is not None:
                indented = []
                for line in simplified:
                    if line.strip():
                        indented.append('   ' + line)
                    else:
                        indented.append(line)
                new_body.extend(indented)
            else:
                new_body.extend(simplified)
            new_body.append('')

    # Close final part if open
    if current_part is not None:
        new_body.append('   </tocchap>')
        new_body.append('')

    # Combine header and body
    result = header + new_body + ['</toc>']

    # Write back
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    print("TOC hierarchy restructured successfully!")
    print(f"- Processed {len(chapters)} chapters")
    print("- Chapters are now nested under their Part sections")
    print("- Removed redundant toclevel1 wrappers")
    print("- Standalone chapters (Index, EULA) are outside Parts")

def extract_linkend(lines):
    """Extract linkend from chapter lines."""
    for line in lines[:5]:
        match = re.search(r'linkend="([^"]+)"', line)
        if match:
            return match.group(1)
    return ""

if __name__ == "__main__":
    # Use path relative to script location
    script_dir = Path(__file__).parent
    toc_path = script_dir / "9781394266074-reference-converted" / "toc.9781394266074.xml"
    restructure_toc_hierarchy(toc_path)
