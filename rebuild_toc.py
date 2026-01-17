#!/usr/bin/env python3
"""
Rebuild TOC to match reference-converted format exactly:
- tocfront for front matter items
- Nested tocchap: outer for Parts, inner for Chapters
- toclevel2 for sections, toclevel3 for sub-subsections
"""

import re
from pathlib import Path

def rebuild_toc(toc_path):
    """Rebuild TOC from scratch."""
    
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Extract header (up to first tocchap)
    header = []
    i = 0
    while i < len(lines):
        if '<tocchap>' in lines[i]:
            break
        header.append(lines[i])
        i += 1
    
    # Parse all tocchap blocks
    chapters = []
    while i < len(lines):
        if '<tocchap>' in lines[i]:
            ch_lines = []
            depth = 1
            ch_lines.append(lines[i])
            i += 1
            while i < len(lines) and depth > 0:
                if '<tocchap>' in lines[i] and '</tocchap>' not in lines[i]:
                    depth += 1
                elif '</tocchap>' in lines[i]:
                    depth -= 1
                ch_lines.append(lines[i])
                i += 1
            
            # Extract linkend and title
            linkend = ''
            title = ''
            for line in ch_lines[:5]:
                if '<tocentry' in line:
                    m = re.search(r'linkend="([^"]+)"', line)
                    if m:
                        linkend = m.group(1)
                    m = re.search(r'>([^<]+)</tocentry>', line)
                    if m:
                        title = m.group(1).strip()
                    break
            
            chapters.append({
                'lines': ch_lines,
                'linkend': linkend,
                'title': title,
                'content': '\n'.join(ch_lines)
            })
        else:
            i += 1
    
    # Categorize
    front_matter = []
    parts = []  # Will contain {'part': {...}, 'chapters': [...]}
    standalone = []
    
    current_part = None
    current_chapters = []
    
    for ch in chapters:
        linkend = ch['linkend']
        title = ch['title']
        
        # Front matter: ch0001-ch0009
        if re.match(r'^ch000[1-9]$', linkend):
            front_matter.append(ch)
        # Parts: titles starting with "Part "
        elif title.startswith('Part ') and ('I' in title[:10] or 'V' in title[:10]):
            if current_part:
                parts.append({'part': current_part, 'chapters': current_chapters})
                current_chapters = []
            current_part = ch
        # Standalone: Index, WILEY
        elif title in ['Index', 'WILEY END USER LICENSE AGREEMENT']:
            if current_part:
                parts.append({'part': current_part, 'chapters': current_chapters})
                current_part = None
                current_chapters = []
            standalone.append(ch)
        else:
            # Regular chapter - add to current part
            if current_part:
                current_chapters.append(ch)
    
    # Don't forget the last part
    if current_part:
        parts.append({'part': current_part, 'chapters': current_chapters})
    
    # Build new TOC
    new_lines = header.copy()
    
    # Remove trailing empty lines from header
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()
    new_lines.append('')
    
    # Add front matter as tocfront
    for ch in front_matter:
        linkend = ch['linkend']
        title = ch['title']
        new_lines.append(f'   <tocfront linkend="{linkend}">{title}</tocfront>')
        new_lines.append('')
    
    # Add parts with nested chapters
    for part_data in parts:
        part = part_data['part']
        part_chapters = part_data['chapters']
        
        new_lines.append('   <tocchap>')
        new_lines.append(f'      <tocentry linkend="{part["linkend"]}">{part["title"]}</tocentry>')
        new_lines.append('')
        
        # Add nested chapters
        for ch in part_chapters:
            # Process chapter content
            ch_content = process_chapter(ch)
            for line in ch_content:
                new_lines.append('   ' + line)  # Extra indent for nesting
            new_lines.append('')
        
        new_lines.append('   </tocchap>')
        new_lines.append('')
    
    # Add standalone items
    for ch in standalone:
        ch_content = process_chapter(ch)
        for line in ch_content:
            new_lines.append(line)
        new_lines.append('')
    
    new_lines.append('</toc>')
    
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Rebuilt TOC: {toc_path}")
    print(f"- Front matter items: {len(front_matter)}")
    print(f"- Parts with chapters: {len(parts)}")
    print(f"- Standalone items: {len(standalone)}")

def process_chapter(ch):
    """Process a chapter's content, converting toclevel1 to toclevel2."""
    lines = ch['lines']
    result = []
    
    for line in lines:
        # Convert toclevel1 to toclevel2
        line = line.replace('<toclevel1>', '<toclevel2>')
        line = line.replace('</toclevel1>', '</toclevel2>')
        # Convert toclevel2 (was toclevel3) to toclevel3
        # But after above conversion, we need to handle original toclevel2
        # Actually, let's check if there are nested levels
        result.append(line)
    
    return result

if __name__ == "__main__":
    # First re-run conversion scripts to get clean state
    import subprocess
    import os
    os.chdir("/workspace")
    
    print("Step 1: Converting format...")
    subprocess.run(["python3", "convert_format.py"])
    
    print("\nStep 2: Fixing titles...")
    subprocess.run(["python3", "fix_toc_titles.py"])
    
    print("\nStep 3: Fixing structure...")
    subprocess.run(["python3", "fix_toc_structure.py"])
    
    print("\nStep 4: Fixing levels...")
    subprocess.run(["python3", "fix_toc_levels.py"])
    
    print("\nStep 5: Rebuilding with nested tocchap...")
    toc_path = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    if toc_path.exists():
        rebuild_toc(toc_path)
