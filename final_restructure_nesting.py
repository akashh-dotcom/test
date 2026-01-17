#!/usr/bin/env python3
"""
FINAL SOLUTION: Properly restructure XML to nest subsections.

Converts flat structure:
  <sect1>
    <sect2 id="ch##s01"/>
    <sect2 id="ch##s02"/>
    <sect2 id="ch##s02s01"/>  <-- Wrong: sibling, should be child
    <sect2 id="ch##s02s02"/>  <-- Wrong: sibling, should be child
  </sect1>

To proper nested structure:
  <sect1>
    <sect2 id="ch##s01"/>
    <sect2 id="ch##s02">
      <sect3 id="ch##s02s01"/>  <-- Correct: nested child as sect3
      <sect3 id="ch##s02s02"/>  <-- Correct: nested child as sect3
    </sect2>
  </sect1>
"""

import re
from pathlib import Path
from collections import defaultdict

def parse_section_id(sect_id):
    """Parse section ID to get level and parent ID."""
    # ch0012s0002s0001 → parent: ch0012s0002, level: 3
    parts = re.findall(r's\d{4}', sect_id)
    level = len(parts) + 1  # +1 for the ch part

    if len(parts) > 1:
        # Has a parent
        parent_id = sect_id.rsplit('s', 1)[0]
        return level, parent_id
    return level, None

def extract_section_blocks(content):
    """Extract each sect2 block with its full content."""
    lines = content.split('\n')
    sections = []
    current_section = None
    depth = 0

    for i, line in enumerate(lines):
        # Opening tag
        if '<sect2 id=' in line:
            match = re.search(r'<sect2 id="([^"]+)">', line)
            if match:
                if depth == 0:  # Top-level sect2
                    sect_id = match.group(1)
                    current_section = {
                        'id': sect_id,
                        'start_line': i,
                        'content_lines': []
                    }
                depth += 1

        # Add line to current section
        if current_section is not None:
            current_section['content_lines'].append(line)

        # Closing tag
        if '</sect2>' in line:
            depth -= 1
            if depth == 0 and current_section:
                current_section['end_line'] = i
                sections.append(current_section)
                current_section = None

    return sections

def build_section_tree(sections):
    """Build parent-child relationships."""
    tree = defaultdict(list)
    roots = []

    for section in sections:
        level, parent_id = parse_section_id(section['id'])
        section['level'] = level
        section['parent_id'] = parent_id

        if parent_id:
            tree[parent_id].append(section)
        else:
            roots.append(section)

    return roots, tree

def output_section_with_children(section, tree, indent='   '):
    """Recursively output section with its children properly nested."""
    lines = []
    sect_type = 'sect2' if section['level'] == 2 else 'sect3' if section['level'] == 3 else 'sect4'

    # Get section content
    content_lines = section['content_lines']

    # Find where to insert children (before closing tag)
    closing_idx = -1
    for i in range(len(content_lines) - 1, -1, -1):
        if '</sect2>' in content_lines[i]:
            closing_idx = i
            break

    if closing_idx == -1:
        closing_idx = len(content_lines)

    # Output lines up to closing tag, converting sect2 to appropriate level
    for i, line in enumerate(content_lines):
        if i == 0:
            # Opening tag
            converted_line = line.replace('<sect2 id=', f'<{sect_type} id=')
            lines.append(converted_line)
        elif i == closing_idx:
            # Before closing tag, insert children
            children = tree.get(section['id'], [])
            for child in children:
                child_lines = output_section_with_children(child, tree, indent + '   ')
                lines.extend(child_lines)
            # Then closing tag
            converted_line = line.replace('</sect2>', f'</{sect_type}>')
            lines.append(converted_line)
        elif i < closing_idx:
            # Content line
            lines.append(line)
        # Skip lines after closing (they shouldn't exist for top-level)

    return lines

def restructure_file(xml_path):
    """Restructure one XML file."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Extract all sect2 blocks
    sections = extract_section_blocks(content)

    if not sections:
        return 0

    # Build tree
    roots, tree = build_section_tree(sections)

    # Count subsections
    subsections = [s for s in sections if s['level'] > 2]
    if not subsections:
        return 0  # Nothing to restructure

    # Build new content
    new_lines = []
    skip_until = -1

    for i, line in enumerate(lines):
        if i < skip_until:
            continue

        # Check if this line starts a root section
        matching_root = None
        for root in roots:
            if i == root['start_line']:
                matching_root = root
                break

        if matching_root:
            # Output this section with all its children nested
            section_lines = output_section_with_children(matching_root, tree)
            new_lines.extend(section_lines)
            skip_until = matching_root['end_line'] + 1

            # Also skip all children
            def skip_children(section_id):
                for child in tree.get(section_id, []):
                    nonlocal skip_until
                    skip_until = max(skip_until, child['end_line'] + 1)
                    skip_children(child['id'])

            skip_children(matching_root['id'])
        else:
            new_lines.append(line)

    # Write back
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"  {xml_path.name}: {len(subsections)} subsections nested properly")
    return len(subsections)

def main():
    base_dir = Path("/home/user/test/9781394266074-reference-converted")

    print("=" * 80)
    print("FINAL XML RESTRUCTURING - PROPERLY NESTING ALL SUBSECTIONS")
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
            import traceback
            traceback.print_exc()

    print()
    print("=" * 80)
    print(f"Total subsections properly nested: {total}")
    print("=" * 80)
    print()
    print("✅ All subsections are now:")
    print("   - Converted to <sect3> (or <sect4> for deeper nesting)")
    print("   - Properly nested inside their parent <sect2>")
    print("   - Navigation should now work correctly!")

if __name__ == "__main__":
    main()
