# Book XML Processing Tools

This repository contains DocBook XML book files and Python scripts for processing Table of Contents (TOC) files.

## Contents

- **`9781394211319-reference/`** - Reference XML files (260 files)
- **`9781394266074-reference-converted/`** - Converted XML book files including TOC
- **`9781394266074-reffering/`** - Additional reference XML files
- **`fix_chapter_titles.py`** - Script to fix TOC chapter entry titles
- **`fix_toc_hierarchy.py`** - Script to restructure TOC hierarchy

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library: `re`, `pathlib`)

## How to Run

### 1. Fix Chapter Titles

This script replaces "chapter" placeholder text in TOC entries with actual chapter titles.

```bash
python3 fix_chapter_titles.py
```

### 2. Fix TOC Hierarchy

This script restructures the TOC to properly nest chapters under their parent Part sections and removes redundant structure.

```bash
python3 fix_toc_hierarchy.py
```

## Configuration

By default, the scripts operate on the TOC file located at:
```
./9781394266074-reference-converted/toc.9781394266074.xml
```

To process a different file, you can modify the `toc_path` variable in the `if __name__ == "__main__":` block of each script.

## What the Scripts Do

### `fix_chapter_titles.py`
- Scans TOC entries looking for generic "chapter" placeholders
- Extracts actual chapter titles from nested `toclevel1` entries
- Replaces placeholders with the correct chapter names

### `fix_toc_hierarchy.py`
- Parses all chapters from the TOC
- Identifies Part dividers and standalone chapters (Index, EULA)
- Nests regular chapters under their respective Parts
- Removes redundant `toclevel1` wrappers
- Keeps standalone chapters outside of Part nesting
