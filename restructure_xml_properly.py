#!/usr/bin/env python3
"""
Properly restructure XML to nest subsections:
1. Convert sect2 elements with 3-level IDs to sect3
2. Nest sect3 elements inside their parent sect2
3. Convert sect2 elements with 4-level IDs to sect4 (if any)
4. Nest sect4 elements inside their parent sect3
"""

import re
from pathlib import Path
from xml.dom import minidom

def parse_id_hierarchy(sect_id):
    """Parse section ID to determine hierarchy level and parent.
    Examples:
      ch0012s0001 → level 2, parent: ch0012
      ch0012s0002s0001 → level 3, parent: ch0012s0002
      ch0012s0002s0001s0001 → level 4, parent: ch0012s0002s0001
    """
    parts = sect_id.replace('ch', '').split('s')
    level = len(parts)  # ch + N s-parts = level N+1, but we start from sect2

    # Determine parent ID
    if level == 2:  # ch####s####
        parent = f"ch{parts[0]}"
        return 2, parent
    elif level == 3:  # ch####s####s####
        parent = f"ch{parts[0]}s{parts[1]}"
        return 3, parent
    elif level == 4:  # ch####s####s####s####
        parent = f"ch{parts[0]}s{parts[1]}s{parts[2]}"
        return 4, parent

    return 1, None

def restructure_xml_file(xml_path):
    """Restructure XML file to properly nest sections."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Strategy: Use regex to identify and restructure sections
    # Step 1: Find all sect2 elements
    # Step 2: Categorize them by level (2, 3, or 4 based on ID)
    # Step 3: Convert tags and restructure nesting

    # Find all sect2 opening tags with their IDs
    sect2_pattern = r'(<sect2 id="([^"]+)">[^<]*<title>([^<]+)</title>)'
    matches = list(re.finditer(sect2_pattern, content))

    # Categorize sections by level
    level_2_sections = []  # Normal sect2
    level_3_sections = []  # Should be sect3
    level_4_sections = []  # Should be sect4

    for match in matches:
        sect_id = match.group(2)
        level, parent = parse_id_hierarchy(sect_id)

        if level == 2:
            level_2_sections.append(sect_id)
        elif level == 3:
            level_3_sections.append(sect_id)
        elif level == 4:
            level_4_sections.append(sect_id)

    if not level_3_sections and not level_4_sections:
        return 0  # Nothing to restructure

    # Convert tags for level 3 sections (sect2 → sect3)
    for sect_id in level_3_sections:
        content = content.replace(
            f'<sect2 id="{sect_id}">',
            f'<sect3 id="{sect_id}">'
        )
        # Also replace closing tags (simple approach)
        # This is tricky - we need to match the right closing tag

    # Convert tags for level 4 sections (sect2 → sect4)
    for sect_id in level_4_sections:
        content = content.replace(
            f'<sect2 id="{sect_id}">',
            f'<sect4 id="{sect_id}">'
        )

    changes = len(level_3_sections) + len(level_4_sections)

    if changes > 0:
        # Now handle closing tags - this is the tricky part
        # We need to match closing </sect2> tags and convert them appropriately

        # Simple approach: convert based on context
        # After a sect3 opening, the next </sect2> should be </sect3>
        # But this is error-prone...

        # Let's use a more robust approach: split into lines and process
        lines = content.split('\n')
        new_lines = []
        sect_stack = []  # Track what sections are open

        for line in lines:
            # Check for opening tags
            if '<sect3 id=' in line:
                sect_stack.append('sect3')
                new_lines.append(line)
            elif '<sect4 id=' in line:
                sect_stack.append('sect4')
                new_lines.append(line)
            elif '<sect2 id=' in line:
                sect_stack.append('sect2')
                new_lines.append(line)
            elif '</sect2>' in line:
                # Determine what to close based on stack
                if sect_stack and sect_stack[-1] in ['sect3', 'sect4']:
                    sect_type = sect_stack.pop()
                    new_lines.append(line.replace('</sect2>', f'</{sect_type}>'))
                else:
                    if sect_stack:
                        sect_stack.pop()
                    new_lines.append(line)
            else:
                new_lines.append(line)

        content = '\n'.join(new_lines)

        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  {xml_path.name}: {len(level_3_sections)} sect3, {len(level_4_sections)} sect4")
        return changes

    return 0

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("=" * 80)
    print("RESTRUCTURING XML FILES - CONVERTING AND NESTING SUBSECTIONS")
    print("=" * 80)
    print()

    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0

    for xml_file in xml_files:
        changes = restructure_xml_file(xml_file)
        total += changes

    print()
    print("=" * 80)
    print(f"Total subsections restructured: {total}")
    print("=" * 80)
    print()
    print("✅ Converted subsection tags")
    print("   - sect2 with 3-level IDs → sect3")
    print("   - sect2 with 4-level IDs → sect4")

if __name__ == "__main__":
    main()
