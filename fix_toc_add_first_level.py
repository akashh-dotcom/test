#!/usr/bin/env python3
"""
Fix TOC by adding the first toclevel1 entry that repeats the chapter title.
This matches the 9781394211319-reference format.
"""

import re
from pathlib import Path

def fix_toc(toc_path):
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find tocchap with tocentry followed by toclevel1
    # We need to add a first toclevel1 that repeats the chapter title
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Look for chapter tocentry (not Part entries)
        if '<tocentry linkend="ch' in line and '</tocentry>' in line:
            # Extract linkend and title
            linkend_match = re.search(r'linkend="(ch\d+)"', line)
            title_match = re.search(r'>([^<]+)</tocentry>', line)
            
            if linkend_match and title_match:
                linkend = linkend_match.group(1)
                title = title_match.group(1).strip()
                
                # Check if this is a chapter (numbered title like "1 Introduction..." or "10 ...")
                # and not a Part entry
                if re.match(r'^\d+\s+', title) and not title.startswith('Part '):
                    # Check if next non-empty line is toclevel1
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        new_lines.append(lines[j])
                        j += 1
                    
                    if j < len(lines) and '<toclevel1>' in lines[j]:
                        # Add first toclevel1 with chapter title
                        # Get the section linkend (e.g., ch0011s0000)
                        section_linkend = f"{linkend}s0000"
                        indent = '         '  # Match indentation
                        new_lines.append(f'{indent}<toclevel1>')
                        new_lines.append(f'{indent}   <tocentry linkend="{section_linkend}">{title}</tocentry>')
                        new_lines.append(f'{indent}</toclevel1>')
                    
                    i = j - 1  # Continue from where we left off
        
        i += 1
    
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Fixed TOC: {toc_path}")

if __name__ == "__main__":
    toc_path = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    fix_toc(toc_path)
