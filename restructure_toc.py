#!/usr/bin/env python3
"""
Restructure TOC to:
1. Wrap front matter items inside FRONT MATTER chapter
2. Nest numbered chapters inside their respective Parts
"""

import re
from pathlib import Path

def restructure_toc(toc_path):
    """Restructure the TOC hierarchy."""
    
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the content
    lines = content.split('\n')
    
    # Find header (before first tocchap)
    header_end = 0
    for i, line in enumerate(lines):
        if '<tocchap>' in line:
            header_end = i
            break
    
    header = lines[:header_end]
    
    # Parse all tocchap blocks
    chapters = []
    i = header_end
    while i < len(lines):
        if '<tocchap>' in lines[i]:
            chapter = {'start': i, 'lines': [], 'title': ''}
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
            
            # Extract title from first tocentry
            for line in chapter['lines'][:5]:
                match = re.search(r'<tocentry[^>]*>([^<]+)</tocentry>', line)
                if match:
                    chapter['title'] = match.group(1).strip()
                    break
            
            # Extract linkend
            for line in chapter['lines'][:5]:
                match = re.search(r'linkend="([^"]+)"', line)
                if match:
                    chapter['linkend'] = match.group(1)
                    break
            
            chapters.append(chapter)
        else:
            i += 1
    
    # Identify front matter chapters (ch0001-ch0009)
    front_matter = []
    main_content = []
    
    for ch in chapters:
        linkend = ch.get('linkend', '')
        # Front matter: ch0001 to ch0009
        if linkend in ['ch0001', 'ch0002', 'ch0003', 'ch0004', 'ch0005', 
                       'ch0006', 'ch0007', 'ch0008', 'ch0009']:
            front_matter.append(ch)
        else:
            main_content.append(ch)
    
    # Build the new TOC
    new_lines = header.copy()
    
    # Add FRONT MATTER wrapper
    new_lines.append('   <tocchap>')
    new_lines.append('      <tocentry linkend="frontmatter">FRONT MATTER</tocentry>')
    new_lines.append('')
    
    # Add front matter items as nested tocchap
    for ch in front_matter:
        # Indent each line by 3 more spaces
        for line in ch['lines']:
            if line.strip():
                new_lines.append('   ' + line)
            else:
                new_lines.append(line)
        new_lines.append('')
    
    new_lines.append('   </tocchap>')
    new_lines.append('')
    
    # Now handle main content - nest chapters inside Parts
    current_part = None
    part_open = False
    
    for ch in main_content:
        title = ch.get('title', '')
        linkend = ch.get('linkend', '')
        
        # Check if this is a Part
        if title.startswith('Part ') and ('I' in title or 'V' in title):
            # Close previous part if open
            if part_open:
                new_lines.append('   </tocchap>')
                new_lines.append('')
            
            # Start new Part
            new_lines.append('   <tocchap>')
            new_lines.append(f'      <tocentry linkend="{linkend}">{title}</tocentry>')
            new_lines.append('')
            current_part = title
            part_open = True
            
        # Check if this is Index or EULA (standalone, close part first)
        elif title in ['Index', 'WILEY END USER LICENSE AGREEMENT']:
            # Close current part if open
            if part_open:
                new_lines.append('   </tocchap>')
                new_lines.append('')
                part_open = False
            
            # Add standalone chapter
            for line in ch['lines']:
                new_lines.append(line)
            new_lines.append('')
            
        else:
            # Regular numbered chapter - nest inside current Part
            if part_open:
                # Indent by 3 spaces to nest inside Part
                for line in ch['lines']:
                    if line.strip():
                        new_lines.append('   ' + line)
                    else:
                        new_lines.append(line)
            else:
                # No Part open, add at top level
                for line in ch['lines']:
                    new_lines.append(line)
            new_lines.append('')
    
    # Close final Part if still open
    if part_open:
        new_lines.append('   </tocchap>')
        new_lines.append('')
    
    # Close toc
    new_lines.append('</toc>')
    
    # Write back
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Restructured TOC: {toc_path}")
    print(f"- Front matter items: {len(front_matter)}")
    print(f"- Main content items: {len(main_content)}")

if __name__ == "__main__":
    toc_path = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    if toc_path.exists():
        restructure_toc(toc_path)
    
    # Also fix duplicate toc
    toc_path2 = Path("/workspace/9781394266074-converted/toc.9781394266074..xml")
    if toc_path2.exists():
        restructure_toc(toc_path2)
