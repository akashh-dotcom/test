#!/usr/bin/env python3
"""
Properly nest sections in XML files:
1. Convert sect2 with 3-level IDs to sect3
2. Move them inside their parent sect2
3. Handle 4-level IDs as sect4 inside sect3
"""

import re
from pathlib import Path

def extract_sections(content):
    """Extract all sect2 elements with their positions."""
    sections = []
    pattern = r'(<sect2 id="([^"]+)">.*?</sect2>)'

    # Find all sect2 elements
    pos = 0
    depth = 0
    current_section = None
    start_pos = None

    for line_no, line in enumerate(content.split('\n')):
        if '<sect2 id=' in line:
            match = re.search(r'<sect2 id="([^"]+)">', line)
            if match:
                if depth == 0:
                    start_pos = line_no
                    sect_id = match.group(1)
                    current_section = {'id': sect_id, 'start': line_no, 'lines': []}
                depth += 1

        if current_section:
            current_section['lines'].append(line)

        if '</sect2>' in line:
            depth -= 1
            if depth == 0 and current_section:
                current_section['end'] = line_no
                sections.append(current_section)
                current_section = None

    return sections

def get_id_level(sect_id):
    """Get nesting level from ID."""
    parts = sect_id.replace('ch', '').split('s')
    return len(parts)

def get_parent_id(sect_id):
    """Get parent ID for a section."""
    parts = sect_id.split('s')
    if len(parts) > 2:  # Has a parent
        return 's'.join(parts[:-1])
    return None

def restructure_file(xml_path):
    """Restructure a single XML file."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Extract all sect2 sections
    sections = extract_sections(content)

    # Group sections by level
    level_2 = [s for s in sections if get_id_level(s['id']) == 2]
    level_3 = [s for s in sections if get_id_level(s['id']) == 3]
    level_4 = [s for s in sections if get_id_level(s['id']) == 4]

    if not level_3 and not level_4:
        return 0  # Nothing to fix

    # Build new content
    new_lines = []
    skip_until = -1

    for i, line in enumerate(lines):
        if i < skip_until:
            continue

        # Check if this line starts a level-2 section
        level_2_match = None
        for sect in level_2:
            if i == sect['start']:
                level_2_match = sect
                break

        if level_2_match:
            # Output this level-2 section
            # But before closing it, insert any level-3 children

            # Find children
            children_3 = [s for s in level_3 if get_parent_id(s['id']) == level_2_match['id']]

            # Output level-2 section lines, but stop before </sect2>
            section_lines = lines[level_2_match['start']:level_2_match['end']]

            # Find the closing tag position
            closing_pos = -1
            for j, sline in enumerate(section_lines):
                if '</sect2>' in sline and j > 0:  # Not the first line
                    closing_pos = j
                    break

            if closing_pos == -1:
                closing_pos = len(section_lines) - 1

            # Output lines up to (but not including) closing tag
            for j in range(closing_pos):
                new_lines.append(section_lines[j])

            # Insert children as sect3
            for child in children_3:
                # Convert sect2 to sect3 in child lines
                child_lines = lines[child['start']:child['end']+1]
                for cline in child_lines:
                    # Convert tags
                    cline = cline.replace('<sect2 id=', '<sect3 id=')
                    cline = cline.replace('</sect2>', '</sect3>')
                    new_lines.append(cline)

            # Now add the closing tag
            new_lines.append(section_lines[closing_pos])

            # Skip the original level-2 section
            skip_until = level_2_match['end'] + 1

            # Also skip the children (they're now inserted)
            for child in children_3:
                if child['start'] > skip_until:
                    skip_until = max(skip_until, child['end'] + 1)

        else:
            # Check if this is a level-3 section that should be skipped
            # (because it was already inserted above)
            is_level_3 = False
            for sect in level_3:
                if i == sect['start']:
                    # Check if it has been nested
                    parent_id = get_parent_id(sect['id'])
                    parent = next((s for s in level_2 if s['id'] == parent_id), None)
                    if parent:
                        is_level_3 = True
                        skip_until = sect['end'] + 1
                        break

            if not is_level_3:
                new_lines.append(line)

    # Write back
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"  {xml_path.name}: Nested {len(level_3)} sect3 elements")
    return len(level_3)

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("=" * 80)
    print("PROPERLY NESTING SUBSECTIONS IN XML FILES")
    print("=" * 80)
    print()

    xml_files = sorted(base_dir.glob("sect1.*.xml"))
    total = 0

    for xml_file in xml_files:
        try:
            count = restructure_file(xml_file)
            total += count
        except Exception as e:
            print(f"  ERROR in {xml_file.name}: {e}")

    print()
    print("=" * 80)
    print(f"Total sections properly nested: {total}")
    print("=" * 80)

if __name__ == "__main__":
    main()
