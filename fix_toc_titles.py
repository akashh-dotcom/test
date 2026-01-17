#!/usr/bin/env python3
"""
Fix TOC to replace 'chapter' placeholders with actual chapter titles from toclevel1.
"""

import re
from pathlib import Path

def fix_toc_titles(toc_path):
    """Replace 'chapter' placeholders with actual chapter titles."""
    
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find tocchap blocks with "chapter" placeholder
    # and extract the actual title from toclevel1
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for tocentry with just "chapter" text
        if '<tocentry linkend="' in line and '>chapter</tocentry>' in line.lower():
            # Extract linkend
            linkend_match = re.search(r'linkend="([^"]+)"', line)
            if linkend_match:
                linkend = linkend_match.group(1)
                
                # Look ahead for the actual title in toclevel1
                actual_title = None
                for j in range(i + 1, min(i + 10, len(lines))):
                    if '<toclevel1>' in lines[j]:
                        # Next line should have the tocentry with title
                        if j + 1 < len(lines):
                            title_match = re.search(r'<tocentry[^>]*>([^<]+)</tocentry>', lines[j + 1])
                            if title_match:
                                actual_title = title_match.group(1).strip()
                                break
                    if '</tocchap>' in lines[j]:
                        break
                
                if actual_title:
                    # Get indentation
                    indent = re.match(r'^(\s*)', line).group(1)
                    new_lines.append(f'{indent}<tocentry linkend="{linkend}">{actual_title}</tocentry>')
                    i += 1
                    continue
        
        new_lines.append(line)
        i += 1
    
    # Write back
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Fixed TOC titles in {toc_path}")

if __name__ == "__main__":
    # Fix in converted directory
    toc_path = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    if toc_path.exists():
        fix_toc_titles(toc_path)
    
    # Also fix the duplicate toc file if exists
    toc_path2 = Path("/workspace/9781394266074-converted/toc.9781394266074..xml")
    if toc_path2.exists():
        fix_toc_titles(toc_path2)
