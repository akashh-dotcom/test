#!/usr/bin/env python3
"""
Extract and display the table from PDF page 276 for detailed comparison.
"""

import fitz
from pathlib import Path

PDF_FILE = Path('/home/user/test/9780989163286.pdf')

def extract_page_276():
    """Extract full content from page 276"""
    doc = fitz.open(PDF_FILE)

    # Page 276 (0-indexed would be 275)
    page = doc[275]
    text = page.get_text()

    print("=" * 100)
    print("FULL TEXT FROM PAGE 276")
    print("=" * 100)
    print(text)
    print("\n" + "=" * 100)

    # Try to extract tables using layout mode
    print("\nTABLE EXTRACTION (Layout Mode)")
    print("=" * 100)
    text_layout = page.get_text("dict")

    # Look for blocks that might be tables
    blocks = text_layout.get("blocks", [])
    print(f"Found {len(blocks)} blocks on page")

    for idx, block in enumerate(blocks):
        if block.get("type") == 0:  # Text block
            lines = block.get("lines", [])
            if len(lines) > 5:  # Potential table
                print(f"\nBlock {idx} ({len(lines)} lines):")
                for line in lines[:10]:  # Show first 10 lines
                    text_line = ""
                    for span in line.get("spans", []):
                        text_line += span.get("text", "")
                    print(f"  {text_line}")

    doc.close()

if __name__ == '__main__':
    extract_page_276()
