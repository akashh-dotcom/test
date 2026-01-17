#!/usr/bin/env python3
"""
Fix TOC structure to match reference format:
- tocfront for front matter items (ch0001-ch0009)
- tocpart for Parts
- tocchap for chapters nested inside Parts
"""

import re
from pathlib import Path

def fix_toc_structure(toc_path):
    """Fix the TOC structure."""
    
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Build header (everything before first tocchap)
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
            
            # Extract info
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
                'title': title
            })
        else:
            i += 1
    
    # Categorize chapters
    front_matter = []  # ch0001-ch0009
    parts_and_chapters = []  # Everything else except Index and WILEY
    standalone = []  # Index, WILEY
    
    for ch in chapters:
        linkend = ch['linkend']
        title = ch['title']
        
        # Front matter: ch0001-ch0009
        if re.match(r'^ch000[1-9]$', linkend):
            front_matter.append(ch)
        elif title in ['Index', 'WILEY END USER LICENSE AGREEMENT']:
            standalone.append(ch)
        else:
            parts_and_chapters.append(ch)
    
    # Build new TOC
    new_lines = header.copy()
    
    # Remove trailing whitespace from header
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()
    new_lines.append('')
    
    # Add front matter as tocfront entries
    for ch in front_matter:
        linkend = ch['linkend']
        title = ch['title']
        new_lines.append(f'   <tocfront linkend="{linkend}">{title}</tocfront>')
    
    new_lines.append('')
    
    # Group chapters under parts
    # Parts: ch0010, ch0016, ch0021, ch0026, ch0030
    current_part = None
    part_content = []
    
    for ch in parts_and_chapters:
        title = ch['title']
        
        # Check if this is a Part entry
        if title.startswith('Part ') and ('I' in title[:8] or 'V' in title[:8]):
            # Output previous part if exists
            if current_part:
                output_tocpart(new_lines, current_part, part_content)
                part_content = []
            
            current_part = ch
        else:
            # Regular chapter - add to current part
            part_content.append(ch)
    
    # Output last part
    if current_part:
        output_tocpart(new_lines, current_part, part_content)
    
    # Add standalone items (Index, WILEY)
    for ch in standalone:
        for line in ch['lines']:
            new_lines.append(line)
        new_lines.append('')
    
    new_lines.append('')
    new_lines.append('</toc>')
    
    # Write back
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Fixed TOC structure: {toc_path}")
    print(f"- Front matter items: {len(front_matter)}")
    print(f"- Parts processed: 5")
    print(f"- Standalone items: {len(standalone)}")

def output_tocpart(new_lines, part_ch, chapters):
    """Output a tocpart with nested tocchap entries."""
    part_linkend = part_ch['linkend'].replace('ch', 'pt')
    part_title = part_ch['title']
    
    new_lines.append('   <tocpart>')
    new_lines.append(f'      <tocentry linkend="{part_linkend}">')
    new_lines.append(f'         {part_title}')
    new_lines.append('      </tocentry>')
    new_lines.append('')
    
    # Add chapters inside the part
    for ch in chapters:
        for line in ch['lines']:
            stripped = line.lstrip()
            if not stripped:
                new_lines.append('')
            else:
                # Add 3 more spaces to nest inside tocpart
                new_lines.append('   ' + line)
        new_lines.append('')
    
    new_lines.append('   </tocpart>')
    new_lines.append('')

if __name__ == "__main__":
    toc_path = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    if toc_path.exists():
        fix_toc_structure(toc_path)
