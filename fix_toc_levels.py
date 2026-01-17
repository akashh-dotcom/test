#!/usr/bin/env python3
"""
Fix TOC level structure:
- Convert toclevel2 (that are children of the wrapper toclevel1) to toclevel1
- Convert toclevel3 to toclevel2
- Remove the wrapper toclevel1 that contains all sections
"""

import re
from pathlib import Path

def fix_toc_levels(toc_path):
    """Fix the toclevel structure in chapters."""
    
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Process each tocchap block
    def process_tocchap(match):
        tocchap_content = match.group(0)
        
        # Check if this tocchap has the problematic structure:
        # <tocchap>
        #    <tocentry>...</tocentry>
        #    <toclevel1>
        #       <tocentry>...</tocentry>  <- chapter title repeat
        #       <toclevel2>...</toclevel2>  <- these should be toclevel1
        #       <toclevel2>...</toclevel2>
        #    </toclevel1>
        # </tocchap>
        
        lines = tocchap_content.split('\n')
        new_lines = []
        
        in_wrapper_toclevel1 = False
        wrapper_depth = 0
        first_tocentry_in_wrapper = True
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Detect wrapper toclevel1 (the one that contains toclevel2 children)
            if '<toclevel1>' in stripped and '</toclevel1>' not in stripped:
                # Look ahead to see if this toclevel1 contains toclevel2
                has_toclevel2 = False
                for j in range(i+1, min(i+20, len(lines))):
                    if '<toclevel2>' in lines[j]:
                        has_toclevel2 = True
                        break
                    if '</toclevel1>' in lines[j]:
                        break
                
                if has_toclevel2:
                    # This is the wrapper - skip the opening tag
                    in_wrapper_toclevel1 = True
                    wrapper_depth = 1
                    first_tocentry_in_wrapper = True
                    i += 1
                    continue
                else:
                    new_lines.append(line)
            elif in_wrapper_toclevel1:
                if '<toclevel1>' in stripped and '</toclevel1>' not in stripped:
                    wrapper_depth += 1
                    new_lines.append(line)
                elif '</toclevel1>' in stripped:
                    wrapper_depth -= 1
                    if wrapper_depth == 0:
                        # End of wrapper - skip closing tag
                        in_wrapper_toclevel1 = False
                        i += 1
                        continue
                    else:
                        new_lines.append(line)
                elif '<tocentry' in stripped and first_tocentry_in_wrapper:
                    # First tocentry in wrapper is duplicate of chapter title - skip it
                    first_tocentry_in_wrapper = False
                    i += 1
                    continue
                elif '<toclevel2>' in stripped:
                    # Convert toclevel2 to toclevel1
                    new_lines.append(line.replace('<toclevel2>', '<toclevel1>'))
                elif '</toclevel2>' in stripped:
                    # Convert </toclevel2> to </toclevel1>
                    new_lines.append(line.replace('</toclevel2>', '</toclevel1>'))
                elif '<toclevel3>' in stripped:
                    # Convert toclevel3 to toclevel2
                    new_lines.append(line.replace('<toclevel3>', '<toclevel2>'))
                elif '</toclevel3>' in stripped:
                    # Convert </toclevel3> to </toclevel2>
                    new_lines.append(line.replace('</toclevel3>', '</toclevel2>'))
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            
            i += 1
        
        return '\n'.join(new_lines)
    
    # Process all tocchap blocks
    pattern = r'<tocchap>.*?</tocchap>'
    new_content = re.sub(pattern, process_tocchap, content, flags=re.DOTALL)
    
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Fixed toclevel structure in: {toc_path}")

if __name__ == "__main__":
    toc_path = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    if toc_path.exists():
        fix_toc_levels(toc_path)
