#!/usr/bin/env python3
"""
Script to fix table structures in RITTDOC XML files.
Converts paragraph-based table data to proper RITTDOC table structure.
"""

import os
import re
import shutil
from xml.etree import ElementTree as ET

# Define Table 2 data for ch0009.xml based on the image provided
TABLE_2_CH0009 = {
    "title": "Table 2. Overview of experimental data for core temperature rise in relation to RF energy exposure in association with MRI.",
    "cols": 7,
    "headers": [
        "Reference and Year of Publication",
        "Number of Subjects",
        "Exposure Type",
        "Dosimetry",
        "SAR and Duration",
        "Max Core Temperature Increase",
        "Mean Core Temperature Increase"
    ],
    "rows": [
        ["(137) (1986)", "25 Patients", "ambient temperature 20 to 24°C whole body", "No", "0.5 to 1.3 W/kg per sequence 40 to 90 min", "0.6°C", "-"],
        ["(140) 1986", "15 Patients", "ambient temperature 20 to 24°C head", "No", "0.8 to 1.2 W/kg", "0.2°C", "0.4 °C"],
        ["(46) (1987)", "50 Patients", "ambient temperature 20 to 24°C whole body", "No", "0.6 to 1 W/kg per sequence", "0.5°C", "0.2 °C"],
        ["(141) 1988", "35 Patients", "head", "No", "0.1 to 0.9", "0.1°C", "0.0°C"],
        ["(38) (1989)", "6 Volunteers", "whole body", "Partial", "3 to 4 W/kg 30 min", "-", "0 °C"],
        ["(47) (1994)", "6 Volunteers", "ambient temperature 21 to 23°C whole body", "Yes", "6 W/kg 16 min", "> 1°C", "0.5 °C"],
        ["(138) (2011)", "400 Children", "whole body, head", "No", "Unknown", "> 1°C (2%)", "-"],
        ["(139) (2016)", "25 Neonates", "Body", "No", "Unknown", "-", "0 °C"],
        ["(142) (2016)", "69 Patients", "Head", "No", "Unknown < 30 min", "> 1°C", "0.8 °C"]
    ]
}

# Define Table 1 data for ch0009.xml
TABLE_1_CH0009 = {
    "title": "Table 1. Limits to RF exposure in MRI equipment (2).",
    "cols": 4,
    "headers": [
        "Operating Mode",
        "Whole-body Averaged SAR",
        "Partial-body SAR",
        "Head SAR"
    ],
    "rows": [
        ["Normal Operating Mode", "2 W/kg", "2-10 W/kg", "3.2 W/kg"],
        ["First Level Controlled Operating Mode", "4 W/kg", "4-10 W/kg", "3.2 W/kg"],
        ["Second Level Controlled Operating Mode", "> 4 W/kg", "> (4-10) W/kg", "> 3.2 W/kg"]
    ]
}


def escape_xml(text):
    """Escape special XML characters."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text


def create_table_xml(table_data, indent="      "):
    """Create proper RITTDOC table XML from table data with proper indentation."""
    lines = []
    lines.append(f'{indent}<table frame="all">')
    lines.append(f'{indent}  <title/>')
    lines.append(f'{indent}  <tgroup cols="{table_data["cols"]}">')
    
    # Add colspec for each column
    for i in range(table_data["cols"]):
        lines.append(f'{indent}    <colspec colname="c{i+1}"/>')
    
    # Add header
    lines.append(f'{indent}    <thead>')
    lines.append(f'{indent}      <row>')
    for header in table_data["headers"]:
        lines.append(f'{indent}        <entry>{escape_xml(header)}</entry>')
    lines.append(f'{indent}      </row>')
    lines.append(f'{indent}    </thead>')
    
    # Add body
    lines.append(f'{indent}    <tbody>')
    for row in table_data["rows"]:
        lines.append(f'{indent}      <row>')
        for cell in row:
            lines.append(f'{indent}        <entry>{escape_xml(cell)}</entry>')
        lines.append(f'{indent}      </row>')
    lines.append(f'{indent}    </tbody>')
    
    lines.append(f'{indent}  </tgroup>')
    lines.append(f'{indent}</table>')
    
    return '\n'.join(lines)


def find_table_paragraph_range(content, table_marker):
    """
    Find the paragraph that contains the table marker and subsequent table-related paragraphs.
    Returns (start_match, end_position) or None if not found.
    """
    # Find the table marker paragraph
    pattern = rf'<para><emphasis role="bold">{re.escape(table_marker)}</emphasis>.*?</para>'
    match = re.search(pattern, content, re.DOTALL)
    return match


def fix_ch0009_tables(input_file, output_file):
    """Fix tables in ch0009.xml."""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix Table 2 in ch0009
    # The table data starts after "Table 2." caption and includes multiple paragraphs
    # We need to find and replace the table content
    
    # Pattern to match Table 2 section (from Table 2. caption to before the next regular paragraph)
    # Looking at the XML, Table 2 starts at line 87 and table data ends around line 111
    
    # First, let's find "Table 2." and the subsequent table data paragraphs
    table2_start_pattern = r'<para><emphasis role="bold">Table 2\.</emphasis>.*?</para>'
    table2_start_match = re.search(table2_start_pattern, content, re.DOTALL)
    
    if table2_start_match:
        print(f"Found Table 2 caption at position {table2_start_match.start()}")
        
        # Now we need to find all the table header and data paragraphs that follow
        # These are the paragraphs from line 88 to 111 in the original
        # The table ends before "BioRef 2021 V10 001-434_Layout 1" paragraph
        
        # Pattern to capture everything from Table 2 caption to (142) (2016) row
        # The table ends with the (142) row which is: "(142) (2016) 69 Patients Head No Unknown   < 30 min > 1°C 0.8 °C"
        
        # Build a pattern to match the entire table section
        # Start from Table 2 caption
        table2_section_pattern = (
            r'(<para><emphasis role="bold">Table 2\.</emphasis>.*?</para>\s*)'  # Table 2 caption
            r'(<para><emphasis role="bold">Reference.*?</para>\s*)'  # Reference header
            r'(<para><emphasis role="bold">Number of.*?</para>\s*)'  # Number of Subjects header
            r'(<para><emphasis role="bold">Exposure.*?</para>\s*)'  # Exposure Type etc header
            r'(<para><emphasis role="bold">Max Core.*?</para>\s*)'  # Max Core header
            r'(<para><emphasis role="bold">Mean Core.*?</para>\s*)'  # Mean Core header
            r'((?:<para>\([^<]+</para>\s*)+)'  # All data rows (starting with references like (137), etc.)
            r'((?:<para>(?:ambient|No|Yes|Partial|Unknown|whole body|head|Body|Head|\d|<|>|°C|-|W/kg)[^<]*</para>\s*)+)'  # Additional data paragraphs
        )
        
        # This is complex because the data is split across many paragraphs
        # Let's use a simpler approach: find the range between Table 2 caption and next content
        
        # Find everything from Table 2 caption to the next major content section
        # The table ends before "BioRef 2021 V10" paragraph (line 112)
        
        # Let's be more specific: match from Table 2 caption to "(142) (2016)..." row
        # and all the related data paragraphs
        
        start_pos = table2_start_match.start()
        
        # Find the end - look for the paragraph that starts with "BioRef 2021 V10"
        end_pattern = r'<para>BioRef 2021 V10 001-434_Layout 1.*?Page 259</para>'
        end_match = re.search(end_pattern, content[start_pos:], re.DOTALL)
        
        if end_match:
            end_pos = start_pos + end_match.start()
            
            # Extract the section to be replaced
            old_section = content[start_pos:end_pos]
            print(f"Table 2 section length: {len(old_section)} characters")
            
            # Create the new table XML with proper indentation (inside sect1)
            table2_xml = create_table_xml(TABLE_2_CH0009, indent="      ")
            
            # Add the table caption and then the table
            new_section = f'''      <para><emphasis role="bold">Table 2.</emphasis> Overview of experimental data for core temperature rise in relation to RF energy exposure in association with MRI.</para>
{table2_xml}
      '''
            
            # Replace the old section with the new one
            content = content[:start_pos] + new_section + content[end_pos:]
            print("Table 2 replaced successfully")
    
    # Write the output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def validate_xml(file_path):
    """Validate XML file."""
    try:
        ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        return False, str(e)


def main():
    # Setup directories
    input_dir = "/workspace/rittdoc_work/output"
    output_dir = "/workspace/final_output_tables"
    
    # Create output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    os.makedirs(os.path.join(output_dir, "multimedia"))
    
    # Copy all files first
    for filename in os.listdir(input_dir):
        src = os.path.join(input_dir, filename)
        if os.path.isfile(src):
            shutil.copy(src, output_dir)
    
    # Copy multimedia files
    multimedia_src = os.path.join(input_dir, "multimedia")
    if os.path.exists(multimedia_src):
        for filename in os.listdir(multimedia_src):
            src = os.path.join(multimedia_src, filename)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(output_dir, "multimedia"))
    
    # Fix tables in ch0009.xml
    ch0009_input = os.path.join(output_dir, "ch0009.xml")
    ch0009_output = os.path.join(output_dir, "ch0009.xml")
    
    print("Processing ch0009.xml...")
    fix_ch0009_tables(ch0009_input, ch0009_output)
    
    # Validate
    is_valid, error = validate_xml(ch0009_output)
    if is_valid:
        print("ch0009.xml is valid XML")
    else:
        print(f"ch0009.xml validation error: {error}")
    
    print("Done!")


if __name__ == "__main__":
    main()
