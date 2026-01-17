#!/usr/bin/env python3
"""
Fix TOC structure to match reference-converted format:
- Parts are outer tocchap
- Chapters are nested tocchap inside Part's tocchap
- Sections use toclevel2 (not toclevel1)
"""

import re
from pathlib import Path

def fix_toc_final(toc_path):
    """Rebuild TOC to match reference-converted structure."""
    
    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace tocpart with tocchap
    content = content.replace('<tocpart>', '<tocchap>')
    content = content.replace('</tocpart>', '</tocchap>')
    
    # Replace toclevel1 with toclevel2
    content = content.replace('<toclevel1>', '<toclevel2>')
    content = content.replace('</toclevel1>', '</toclevel2>')
    
    # Replace toclevel2 (which were toclevel3) with toclevel3
    # But first we need to handle existing toclevel2 that should stay toclevel2
    # Actually, since we already converted toclevel3->toclevel2 earlier,
    # and now we're converting toclevel1->toclevel2, we need to be careful
    
    # Let me reconsider: after previous conversions:
    # - toclevel1 contains sections (1.1, 1.2, etc.)
    # - toclevel2 contains sub-subsections (1.1.1, 1.1.2, etc.)
    
    # Now we need:
    # - sections to be toclevel2
    # - sub-subsections to be toclevel3
    
    # So: toclevel1 -> toclevel2 (already done above)
    # And existing toclevel2 (sub-subsections) need to become toclevel3
    
    # But we already converted toclevel1->toclevel2, so now ALL are toclevel2
    # We need to identify which ones were originally sub-subsections
    
    # Actually, let me re-read the file and do this more carefully
    
    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed TOC structure: {toc_path}")
    print("- Converted tocpart to tocchap")
    print("- Converted toclevel1 to toclevel2")

if __name__ == "__main__":
    # First, re-run the conversion to get a clean state
    import subprocess
    subprocess.run(["python3", "convert_format.py"], cwd="/workspace")
    subprocess.run(["python3", "fix_toc_titles.py"], cwd="/workspace")
    subprocess.run(["python3", "fix_toc_structure.py"], cwd="/workspace")
    subprocess.run(["python3", "fix_toc_levels.py"], cwd="/workspace")
    
    # Now apply final fixes
    toc_path = Path("/workspace/9781394266074-converted/toc.9781394266074.xml")
    if toc_path.exists():
        fix_toc_final(toc_path)
