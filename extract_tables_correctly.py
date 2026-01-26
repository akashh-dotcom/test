#!/usr/bin/env python3
"""
Extract table content correctly from PDF with precise title matching.
Each table gets unique content based on its exact title.
"""

import os
import re
import fitz
from pathlib import Path
import xml.etree.ElementTree as ET
import shutil

PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_CORRECT')

ET.register_namespace('', '')

def clean_text(text):
    """Clean extracted text."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def find_table_page_precise(doc, title):
    """Find the exact page containing this table title."""
    # Clean title - remove truncation markers
    title_clean = title.replace('-', ' ').replace('\n', ' ')
    title_clean = clean_text(title_clean)
    
    # Remove trailing incomplete words
    if title_clean.endswith(' emo') or title_clean.endswith(' de'):
        title_clean = title_clean.rsplit(' ', 1)[0]
    
    # Get significant words (skip common words)
    words = [w for w in title_clean.split() if len(w) > 4 and w.lower() not in 
             ['table', 'patients', 'during', 'which', 'there', 'these']]
    
    best_page = None
    best_score = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().lower()
        
        # Count matching words
        score = sum(1 for w in words if w.lower() in text)
        
        # Bonus for key distinctive words
        if title_clean[:40].lower() in text:
            score += 10
        
        if score > best_score:
            best_score = score
            best_page = (page_num, page.get_text())
    
    if best_score >= 3:
        return best_page
    
    return None, None

def extract_bullet_content(text, after_title):
    """Extract bullet point content after the title."""
    # Find the position after title
    title_pos = text.lower().find(after_title.lower()[:40])
    if title_pos < 0:
        return None
    
    # Get text after title
    after = text[title_pos:]
    
    items = []
    # Match bullet items (• character)
    for match in re.finditer(r'•\s*([^•]+?)(?=•|BioRef|Table\s+\d|$)', after, re.DOTALL):
        content = clean_text(match.group(1))
        if len(content) > 10 and 'BioRef' not in content and 'Layout' not in content:
            items.append(["•", content[:400]])
    
    if len(items) >= 2:
        return [["", "Item"]] + items
    return None

def extract_company_products(text, after_title):
    """Extract company/product table."""
    title_pos = text.lower().find(after_title.lower()[:40])
    if title_pos < 0:
        return None
    
    after = text[title_pos:]
    
    items = []
    # Look for lines with URLs
    lines = after.split('\n')
    
    i = 0
    current_company = None
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip metadata
        if 'BioRef' in line or 'Layout' in line or not line:
            i += 1
            continue
        
        # Company line (has URL)
        if 'www.' in line.lower() or '.com' in line.lower():
            current_company = clean_text(line)
        # Product line (comes after company, no URL)
        elif current_company and len(line) < 60 and line[0].isupper():
            product = clean_text(line)
            if product and 'Table' not in product:
                items.append([current_company, product])
                current_company = None
        
        i += 1
    
    if len(items) >= 3:
        return [["Company", "Products"]] + items
    return None

def extract_numbered_content(text, after_title):
    """Extract numbered list (1), (2), etc."""
    # Search the ENTIRE text (table captions can be at top or bottom of content)
    # Find all (number) positions
    positions = []
    for match in re.finditer(r'\((\d+)\)', text):
        num = int(match.group(1))
        if num <= 30:
            positions.append((match.start(), match.end(), num))
    
    if not positions:
        return None
    
    items = []
    for i, (start, end, num) in enumerate(positions):
        if i + 1 < len(positions):
            next_start = positions[i + 1][0]
            content = text[end:next_start]
        else:
            content = text[end:end + 500]
            # Stop at table or BioRef
            m = re.search(r'(Table\s+\d+\.|BioRef)', content)
            if m:
                content = content[:m.start()]
        
        content = clean_text(content)
        if len(content) > 15 and 'BioRef' not in content:
            items.append((num, content[:500]))
    
    items.sort(key=lambda x: x[0])
    
    if len(items) >= 3:
        return [["No.", "Description"]] + [[f"({i[0]})", i[1]] for i in items]
    return None

def extract_table_content(doc, title):
    """Extract content for a specific table based on its title."""
    page_num, text = find_table_page_precise(doc, title)
    
    if text is None:
        return None, None
    
    title_lower = title.lower()
    
    # Determine extraction method based on title
    if 'manufacturer' in title_lower or 'supplier' in title_lower:
        content = extract_company_products(text, title)
        if content:
            return content, page_num + 1
    
    if 'types of patient' in title_lower or 'patient' in title_lower and 'require' in title_lower:
        content = extract_bullet_content(text, title)
        if content:
            return content, page_num + 1
    
    if 'recommend' in title_lower or 'technique' in title_lower or 'guideline' in title_lower:
        content = extract_numbered_content(text, title)
        if content:
            return content, page_num + 1
        content = extract_bullet_content(text, title)
        if content:
            return content, page_num + 1
    
    # Fallback - try all methods
    content = extract_numbered_content(text, title)
    if content:
        return content, page_num + 1
    
    content = extract_bullet_content(text, title)
    if content:
        return content, page_num + 1
    
    content = extract_company_products(text, title)
    if content:
        return content, page_num + 1
    
    # Try PyMuPDF table extraction
    page = doc[page_num]
    tables = page.find_tables()
    for t in tables:
        try:
            data = t.extract()
            if data and len(data) >= 2:
                first = str(data[0][0] if data[0] else '')
                if 'BioRef' in first or 'Layout' in first or first == 'Content':
                    continue
                
                cleaned = []
                for row in data:
                    cleaned_row = [clean_text(str(c) if c else '') for c in row]
                    if any(cleaned_row):
                        cleaned.append(cleaned_row)
                
                if len(cleaned) >= 2:
                    return cleaned, page_num + 1
        except:
            continue
    
    return None, None

def is_placeholder_table(table_elem):
    """Check if table has placeholder content."""
    table_text = ET.tostring(table_elem, encoding='unicode', method='text')
    return 'See PDF' in table_text

def update_table_content(table, content):
    """Replace table content."""
    title_elem = table.find('title')
    title = title_elem.text if title_elem is not None else ''
    
    for child in list(table):
        table.remove(child)
    
    # Clean up title
    if title.endswith('-'):
        title = title.rstrip('-').strip()
    
    new_title = ET.SubElement(table, 'title')
    new_title.text = title
    
    num_cols = max(len(row) for row in content)
    tgroup = ET.SubElement(table, 'tgroup', {'cols': str(num_cols)})
    
    for i in range(num_cols):
        ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
    
    thead = ET.SubElement(tgroup, 'thead')
    head_row = ET.SubElement(thead, 'row')
    for cell in content[0]:
        entry = ET.SubElement(head_row, 'entry')
        entry.text = str(cell)[:500] if cell else ''
    
    tbody = ET.SubElement(tgroup, 'tbody')
    for row in content[1:]:
        tr = ET.SubElement(tbody, 'row')
        for cell in row:
            entry = ET.SubElement(tr, 'entry')
            entry.text = str(cell)[:500] if cell else ''

def make_clean_placeholder(table):
    """Create a clean placeholder for unfixable tables."""
    title_elem = table.find('title')
    title = title_elem.text if title_elem is not None else 'Table'
    
    for child in list(table):
        table.remove(child)
    
    new_title = ET.SubElement(table, 'title')
    new_title.text = title
    
    tgroup = ET.SubElement(table, 'tgroup', {'cols': '1'})
    ET.SubElement(tgroup, 'colspec', {'colname': 'c1'})
    
    thead = ET.SubElement(tgroup, 'thead')
    head_row = ET.SubElement(thead, 'row')
    entry = ET.SubElement(head_row, 'entry')
    entry.text = "Content"
    
    tbody = ET.SubElement(tgroup, 'tbody')
    row = ET.SubElement(tbody, 'row')
    entry = ET.SubElement(row, 'entry')
    entry.text = "For detailed content, please refer to the PDF document."

def process_file(xml_file, doc, output_file):
    """Process XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"  Error: {e}")
        return 0, 0
    
    fixed = 0
    failed = 0
    
    for table in root.iter('table'):
        if not is_placeholder_table(table):
            continue
        
        title_elem = table.find('title')
        title = title_elem.text if title_elem is not None else ''
        
        if not title:
            make_clean_placeholder(table)
            failed += 1
            continue
        
        content, page = extract_table_content(doc, title)
        
        if content and len(content) > 1:
            update_table_content(table, content)
            print(f"    Fixed: {title[:50]}... (page {page}, {len(content)-1} rows)")
            fixed += 1
        else:
            make_clean_placeholder(table)
            print(f"    Placeholder: {title[:50]}...")
            failed += 1
    
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return fixed, failed

def main():
    print("Extracting table content with precise matching\n")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF_FILE)
    
    total_fixed = 0
    total_failed = 0
    
    for xml_file in sorted(SOURCE_DIR.glob('*.xml')):
        if xml_file.name == 'Book.XML':
            shutil.copy(xml_file, OUTPUT_DIR / xml_file.name)
            continue
        
        output_file = OUTPUT_DIR / xml_file.name
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'See PDF' not in content:
                shutil.copy(xml_file, output_file)
                continue
        
        print(f"Processing {xml_file.name}...")
        fixed, failed = process_file(xml_file, doc, output_file)
        total_fixed += fixed
        total_failed += failed
    
    doc.close()
    
    # Copy multimedia
    multimedia_src = SOURCE_DIR / 'multimedia'
    if multimedia_src.exists():
        multimedia_dst = OUTPUT_DIR / 'multimedia'
        if multimedia_dst.exists():
            shutil.rmtree(multimedia_dst)
        shutil.copytree(multimedia_src, multimedia_dst)
    
    print(f"\n=== Summary ===")
    print(f"Fixed: {total_fixed}")
    print(f"Placeholder: {total_failed}")

if __name__ == '__main__':
    main()
