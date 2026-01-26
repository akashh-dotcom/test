#!/usr/bin/env python3
"""
Add remaining tables from PDF to XML files with proper DocBook structure.
Uses the same table format as existing tables in the XML files.
"""

import fitz  # PyMuPDF
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from collections import defaultdict
import shutil
import copy

# Paths - Updated for current workspace
PDF_FILE = Path('/workspace/9780989163286.pdf')
SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_tables_WITH_REMAINING_TABLES')

# Chapter to page range mapping (approximate, will be refined by scanning)
CHAPTER_PAGE_RANGES = {}

def extract_chapter_mapping(doc):
    """Extract chapter to page mapping from PDF"""
    print("Extracting chapter to page mapping...")
    
    chapter_starts = {}
    current_chapter = None
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Look for chapter headers
        chapter_match = re.search(r'(?:^|\n)\s*Chapter\s+(\d+)\s*\n', text, re.IGNORECASE)
        if chapter_match:
            ch_num = int(chapter_match.group(1))
            if ch_num not in chapter_starts:
                chapter_starts[ch_num] = page_num + 1
                print(f"  Chapter {ch_num} starts at page {page_num + 1}")
    
    return chapter_starts


def get_chapter_for_page(page_num, chapter_starts):
    """Determine which chapter a page belongs to"""
    current_chapter = None
    for ch_num in sorted(chapter_starts.keys()):
        if chapter_starts[ch_num] <= page_num:
            current_chapter = ch_num
        else:
            break
    return current_chapter


def extract_tables_from_pdf():
    """Extract all tables from PDF with their content"""
    print("=" * 80)
    print("EXTRACTING TABLES FROM PDF")
    print("=" * 80)
    
    doc = fitz.open(PDF_FILE)
    print(f"Total pages: {len(doc)}")
    
    # Get chapter mapping
    chapter_starts = extract_chapter_mapping(doc)
    
    tables = []
    
    print(f"\nScanning for tables...")
    
    for page_num in range(len(doc)):
        if (page_num + 1) % 100 == 0:
            print(f"  Progress: {page_num + 1}/{len(doc)} pages")
        
        page = doc[page_num]
        text = page.get_text()
        
        # Find table references with their titles
        # Pattern: "Table X." or "Table X:" followed by title
        table_patterns = [
            r'Table\s+(\d+)\.\s*([^\n]+)',  # Table 1. Title
            r'Table\s+(\d+):\s*([^\n]+)',   # Table 1: Title
            r'Table\s+(\d+)\s+([A-Z][^\n]+)',  # Table 1 Title starting with capital
        ]
        
        for pattern in table_patterns:
            for match in re.finditer(pattern, text):
                table_num = int(match.group(1))
                title = match.group(2).strip()
                
                # Clean up title
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 200:
                    title = title[:200] + "..."
                
                # Try to extract table content (look for structured data)
                start_pos = match.end()
                remaining = text[start_pos:start_pos + 2000]
                
                # Extract structured content (rows with multiple columns)
                lines = remaining.split('\n')
                table_content = []
                
                for line in lines[:30]:  # Look at next 30 lines
                    line = line.strip()
                    if not line:
                        if len(table_content) >= 2:
                            break
                        continue
                    
                    # Check if line looks like table data
                    # (contains numbers, multiple words/fields, etc.)
                    if re.search(r'\d', line) or re.search(r'\s{2,}', line):
                        table_content.append(line)
                    elif len(table_content) > 0 and len(line) < 100:
                        table_content.append(line)
                    elif len(table_content) >= 3:
                        break
                
                chapter = get_chapter_for_page(page_num + 1, chapter_starts)
                
                tables.append({
                    'page': page_num + 1,
                    'chapter': chapter,
                    'number': table_num,
                    'title': title,
                    'content': table_content
                })
    
    doc.close()
    
    # Deduplicate by (page, number)
    unique = {}
    for t in tables:
        key = (t['page'], t['number'])
        if key not in unique:
            unique[key] = t
    
    tables = list(unique.values())
    print(f"\nFound {len(tables)} unique table references in PDF")
    
    return tables


def get_existing_xml_tables():
    """Get tables already in XML files"""
    print("\n" + "=" * 80)
    print("ANALYZING EXISTING XML TABLES")
    print("=" * 80)
    
    existing = defaultdict(list)
    
    for xml_file in sorted(SOURCE_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if not ch_match:
            continue
        
        ch_num = int(ch_match.group(1))
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for table in root.iter('table'):
                title_elem = table.find('.//title')
                title = title_elem.text if title_elem is not None and title_elem.text else ""
                
                # Get content signature for matching
                entries = table.findall('.//entry')
                content_sig = " ".join([e.text[:20] if e.text else "" for e in entries[:5]])
                
                existing[ch_num].append({
                    'title': title,
                    'content_sig': content_sig
                })
        except Exception as e:
            print(f"  Error parsing {xml_file.name}: {e}")
    
    total = sum(len(v) for v in existing.values())
    print(f"Found {total} existing tables across {len(existing)} chapters")
    
    return existing


def create_docbook_table(table_data):
    """Create a proper DocBook table element"""
    
    # Create table element
    table = ET.Element('table', {'frame': 'all'})
    
    # Add title
    title = ET.SubElement(table, 'title')
    title.text = table_data['title'] if table_data['title'] else f"Table {table_data['number']}"
    
    # Parse content into rows
    content = table_data.get('content', [])
    if not content:
        # Create minimal table structure
        content = [f"Table {table_data['number']} content from page {table_data['page']}"]
    
    # Determine columns by analyzing content
    rows = []
    max_cols = 1
    
    for line in content:
        # Split on multiple spaces or tabs
        parts = re.split(r'\s{2,}|\t+', line)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            rows.append(parts)
            max_cols = max(max_cols, len(parts))
    
    if not rows:
        rows = [[f"See page {table_data['page']}"]]
        max_cols = 1
    
    # Create tgroup
    tgroup = ET.SubElement(table, 'tgroup', {'cols': str(max_cols)})
    
    # Add colspecs
    for i in range(max_cols):
        ET.SubElement(tgroup, 'colspec', {'colname': f'c{i+1}'})
    
    # Determine if first row is header
    has_header = len(rows) > 1 and len(rows[0]) == max_cols
    
    if has_header and len(rows) > 1:
        # Create thead
        thead = ET.SubElement(tgroup, 'thead')
        header_row = ET.SubElement(thead, 'row')
        for cell in rows[0]:
            entry = ET.SubElement(header_row, 'entry')
            entry.text = cell
        # Pad if needed
        for _ in range(max_cols - len(rows[0])):
            ET.SubElement(header_row, 'entry')
        data_rows = rows[1:]
    else:
        data_rows = rows
    
    # Create tbody
    tbody = ET.SubElement(tgroup, 'tbody')
    for row_data in data_rows:
        row = ET.SubElement(tbody, 'row')
        for cell in row_data:
            entry = ET.SubElement(row, 'entry')
            entry.text = cell
        # Pad if needed
        for _ in range(max_cols - len(row_data)):
            ET.SubElement(row, 'entry')
    
    return table


def is_table_duplicate(pdf_table, existing_tables):
    """Check if a PDF table already exists in XML"""
    
    pdf_title = pdf_table['title'].lower()[:50] if pdf_table['title'] else ""
    
    for xml_table in existing_tables:
        xml_title = xml_table['title'].lower()[:50] if xml_table['title'] else ""
        
        # Match by title similarity
        if pdf_title and xml_title:
            # Check if titles overlap significantly
            if pdf_title in xml_title or xml_title in pdf_title:
                return True
            
            # Check word overlap
            pdf_words = set(pdf_title.split())
            xml_words = set(xml_title.split())
            if len(pdf_words & xml_words) >= 3:
                return True
    
    return False


def add_tables_to_xml():
    """Main function to add missing tables"""
    
    # Step 1: Extract tables from PDF
    pdf_tables = extract_tables_from_pdf()
    
    # Step 2: Get existing XML tables
    existing_tables = get_existing_xml_tables()
    
    # Step 3: Find missing tables
    print("\n" + "=" * 80)
    print("IDENTIFYING MISSING TABLES")
    print("=" * 80)
    
    missing_tables = []
    for pdf_table in pdf_tables:
        ch = pdf_table['chapter']
        if ch is None:
            continue
        
        existing = existing_tables.get(ch, [])
        if not is_table_duplicate(pdf_table, existing):
            missing_tables.append(pdf_table)
    
    print(f"Found {len(missing_tables)} potentially missing tables")
    
    if not missing_tables:
        print("\nNo missing tables found!")
        return
    
    # Group by chapter
    tables_by_chapter = defaultdict(list)
    for t in missing_tables:
        if t['chapter']:
            tables_by_chapter[t['chapter']].append(t)
    
    # Step 4: Create output directory
    print("\n" + "=" * 80)
    print("ADDING MISSING TABLES")
    print("=" * 80)
    
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(SOURCE_DIR, OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")
    
    # Step 5: Add tables to XML files
    tables_added = 0
    
    for chapter, tables in sorted(tables_by_chapter.items()):
        xml_file = OUTPUT_DIR / f'ch{chapter:04d}.xml'
        
        if not xml_file.exists():
            print(f"\n  Chapter {chapter}: XML file not found, skipping {len(tables)} tables")
            continue
        
        print(f"\n  Chapter {chapter}: Adding {len(tables)} table(s)")
        
        # Parse XML
        ET.register_namespace('', '')
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find insertion point (end of first sect1 or chapter)
        insert_parent = None
        for sect in root.iter('sect1'):
            insert_parent = sect
            break
        
        if insert_parent is None:
            for ch in root.iter('chapter'):
                insert_parent = ch
                break
        
        if insert_parent is None:
            insert_parent = root
        
        for table_data in tables:
            # Create table element
            table_elem = create_docbook_table(table_data)
            
            # Insert table
            insert_parent.append(table_elem)
            
            print(f"    + Table {table_data['number']} (page {table_data['page']}): {table_data['title'][:50]}")
            tables_added += 1
        
        # Write back with pretty formatting
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    
    # Step 6: Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTables in PDF: {len(pdf_tables)}")
    print(f"Tables already in XML: {sum(len(v) for v in existing_tables.values())}")
    print(f"New tables added: {tables_added}")
    print(f"\nOutput saved to: {OUTPUT_DIR}")
    
    # Verify
    print("\nVerification - Tables per chapter in output:")
    for xml_file in sorted(OUTPUT_DIR.glob('ch*.xml')):
        ch_match = re.search(r'ch(\d+)', xml_file.name)
        if ch_match:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            count = len(list(root.iter('table')))
            if count > 0:
                print(f"  Chapter {int(ch_match.group(1)):02d}: {count} tables")


if __name__ == '__main__':
    add_tables_to_xml()
