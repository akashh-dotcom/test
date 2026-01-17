#!/usr/bin/env python3
"""
Complete TOC conversion to match reference-converted format:
- Front matter (ch0001-ch0009) -> tocfront entries
- Parts -> outer tocchap
- Chapters -> nested tocchap inside Part
- Sections -> toclevel2 directly in chapter (not wrapped in toclevel1)
"""

import re
from pathlib import Path

def convert_section_id(s):
    """Convert 6-digit section IDs to 4-digit (matching reference format)."""
    def replace(match):
        prefix = match.group(1)
        digits = match.group(2)
        if len(digits) == 6:
            # Take digits 2-5 (0-indexed: positions 2,3,4,5) to match reference
            # e.g., 001000 -> 1000, 002000 -> 2000
            new_digits = digits[2:6]
        else:
            new_digits = digits
        return prefix + new_digits
    
    return re.sub(r'(ch\d{4}s)(\d{6})', replace, s)

def parse_tocchap(lines, start_idx):
    """Parse a single tocchap block starting at given index."""
    ch_lines = []
    depth = 1
    i = start_idx + 1
    
    while i < len(lines) and depth > 0:
        if '<tocchap>' in lines[i] and '</tocchap>' not in lines[i]:
            depth += 1
        elif '</tocchap>' in lines[i]:
            depth -= 1
        if depth > 0:
            ch_lines.append(lines[i])
        i += 1
    
    # Extract info
    linkend = ''
    main_title = ''
    first_toclevel1_title = ''
    sections = []
    
    # First, get the main tocentry (chapter linkend)
    for line in ch_lines:
        if '<tocentry' in line and 'linkend=' in line:
            m_linkend = re.search(r'linkend="([^"]+)"', line)
            m_title = re.search(r'>([^<]+)</tocentry>', line)
            if m_linkend:
                linkend = m_linkend.group(1)
            if m_title:
                main_title = m_title.group(1).strip()
            break
    
    # Now find toclevel1 and extract its title and toclevel2 sections
    in_toclevel1 = False
    got_toclevel1_title = False
    
    for line in ch_lines:
        if '<toclevel1>' in line:
            in_toclevel1 = True
            continue
        
        if '</toclevel1>' in line:
            in_toclevel1 = False
            continue
        
        if in_toclevel1:
            # First tocentry in toclevel1 is the chapter title
            if '<tocentry' in line and not got_toclevel1_title:
                m_title = re.search(r'>([^<]+)</tocentry>', line)
                if m_title:
                    first_toclevel1_title = m_title.group(1).strip()
                    got_toclevel1_title = True
                continue
            
            # Look for toclevel2 entries
            if '<toclevel2>' in line:
                # Next line should have the tocentry
                continue
            
            if got_toclevel1_title and '<tocentry' in line:
                m_linkend = re.search(r'linkend="([^"]+)"', line)
                m_title = re.search(r'>([^<]+)</tocentry>', line)
                if m_linkend and m_title:
                    sections.append({
                        'linkend': m_linkend.group(1),
                        'title': m_title.group(1).strip()
                    })
    
    return {
        'linkend': linkend,
        'main_title': main_title,
        'title': first_toclevel1_title or main_title,
        'sections': sections,
        'end_idx': i
    }

def convert_toc(source_path, dest_path):
    """Convert TOC from source format to reference-converted format."""
    
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Extract header
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
            ch = parse_tocchap(lines, i)
            chapters.append(ch)
            i = ch['end_idx']
        else:
            i += 1
    
    # Categorize chapters
    front_matter = []
    parts_with_chapters = []
    standalone = []
    
    current_part = None
    current_chapters = []
    
    for ch in chapters:
        linkend = ch['linkend']
        title = ch['title']
        
        # Convert linkend
        linkend = convert_section_id(linkend)
        ch['linkend'] = linkend
        
        # Front matter: ch0001-ch0009
        if re.match(r'^ch000[1-9]$', linkend):
            front_matter.append(ch)
        # Parts: title starts with "Part "
        elif title.startswith('Part ') and ('I' in title[:10] or 'V' in title[:10]):
            if current_part is not None:
                parts_with_chapters.append({'part': current_part, 'chapters': current_chapters})
                current_chapters = []
            current_part = ch
        # Standalone
        elif title in ['Index', 'WILEY END USER LICENSE AGREEMENT']:
            if current_part is not None:
                parts_with_chapters.append({'part': current_part, 'chapters': current_chapters})
                current_part = None
                current_chapters = []
            standalone.append(ch)
        else:
            # Regular chapter
            if current_part is not None:
                current_chapters.append(ch)
    
    if current_part is not None:
        parts_with_chapters.append({'part': current_part, 'chapters': current_chapters})
    
    # Build new TOC
    new_lines = header.copy()
    
    # Remove trailing empty lines
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
    for part_data in parts_with_chapters:
        part = part_data['part']
        part_chapters = part_data['chapters']
        
        new_lines.append('   <tocchap>')
        new_lines.append(f'      <tocentry linkend="{part["linkend"]}">{part["title"]}</tocentry>')
        new_lines.append('')
        
        # Add nested chapters
        for ch in part_chapters:
            new_lines.append('      <tocchap>')
            new_lines.append(f'         <tocentry linkend="{ch["linkend"]}">{ch["title"]}</tocentry>')
            
            # Add sections as toclevel2
            for sec in ch['sections']:
                sec_linkend = convert_section_id(sec['linkend'])
                new_lines.append('            <toclevel2>')
                new_lines.append(f'               <tocentry linkend="{sec_linkend}">{sec["title"]}</tocentry>')
                new_lines.append('            </toclevel2>')
            
            new_lines.append('      </tocchap>')
            new_lines.append('')
        
        new_lines.append('   </tocchap>')
        new_lines.append('')
    
    # Add standalone items
    for ch in standalone:
        new_lines.append('   <tocchap>')
        new_lines.append(f'      <tocentry linkend="{ch["linkend"]}">{ch["title"]}</tocentry>')
        
        for sec in ch['sections']:
            sec_linkend = convert_section_id(sec['linkend'])
            new_lines.append('         <toclevel2>')
            new_lines.append(f'            <tocentry linkend="{sec_linkend}">{sec["title"]}</tocentry>')
            new_lines.append('         </toclevel2>')
        
        new_lines.append('   </tocchap>')
        new_lines.append('')
    
    new_lines.append('</toc>')
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Converted TOC: {dest_path}")
    print(f"- Front matter items: {len(front_matter)}")
    print(f"- Parts: {len(parts_with_chapters)}")
    for i, p in enumerate(parts_with_chapters):
        print(f"  Part {i+1}: {len(p['chapters'])} chapters")
    print(f"- Standalone items: {len(standalone)}")

if __name__ == "__main__":
    source = Path("/workspace/9781394266074-reffering/toc.9781394266074.xml")
    dest = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    
    # First run the format conversion for other files
    import subprocess
    subprocess.run(["python3", "convert_format.py"], cwd="/workspace")
    
    # Then convert TOC with complete structure
    convert_toc(source, dest)
