#!/usr/bin/env python3
"""
Reorganize folder structure to match the required format:
- Book.xml (main file with entity references)
- toc.xml (Table of Contents)
- pr0001.xml through pr0006.xml (prelim files)
- ch0001.xml through ch0036.xml (chapters)
- MultiMedia/ folder
"""

import os
import re
import shutil
from pathlib import Path

SOURCE_DIR = Path('/workspace/final_output_tables_FINAL_NO_DUPLICATES')
OUTPUT_DIR = Path('/workspace/final_output_REORGANIZED')

def create_toc_xml():
    """Create Table of Contents XML."""
    toc = '''<?xml version="1.0" encoding="UTF-8"?>
<toc>
    <title>Table of Contents</title>
    <tocentry>
        <tocchap>Preface</tocchap>
    </tocentry>
    <tocentry>
        <tocchap>The Editors</tocchap>
    </tocentry>
    <tocentry>
        <tocchap>Contributors</tocchap>
    </tocentry>
'''
    
    # Add chapter entries
    for i in range(1, 37):
        toc += f'''    <tocentry>
        <tocchap>Chapter {i}</tocchap>
    </tocentry>
'''
    
    toc += '</toc>\n'
    return toc

def create_pr0001_xml():
    """Create Title and Copyright XML."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<preface id="pr0001">
    <title>Title and Copyright</title>
    <para><emphasis role="bold">MRI Bioeffects, Safety, and Patient Management</emphasis></para>
    <para><emphasis role="bold">Second Edition</emphasis></para>
    <para></para>
    <para><emphasis role="bold">Frank G. Shellock, Ph.D. - Editor</emphasis></para>
    <para><emphasis role="italics">President, Shellock R &amp; D Services, Inc.</emphasis></para>
    <para><emphasis role="italics">Playa Del Rey, CA</emphasis></para>
    <para></para>
    <para><emphasis role="bold">John V. Crues, III, M.D. - Editor</emphasis></para>
    <para><emphasis role="italics">Medical Director, Radnet, Inc.</emphasis></para>
    <para><emphasis role="italics">Los Angeles, CA</emphasis></para>
    <para><emphasis role="italics">Professor of Radiology, University of California, San Diego</emphasis></para>
    <para></para>
    <para><emphasis role="bold">Alexandra M. Karacozoff, M.P.H. - Associate Editor</emphasis></para>
    <para><emphasis role="italics">Sacramento, California</emphasis></para>
    <para></para>
    <para><emphasis role="bold">Biomedical Research Publishing Group</emphasis></para>
    <para><emphasis role="bold">Los Angeles, CA</emphasis></para>
    <para></para>
    <para>ISBN-13: 978-0-9891632-8-6</para>
    <para>ISBN-10: 0-9891632-8-8</para>
    <para></para>
    <para><emphasis role="bold">Disclaimer</emphasis></para>
    <para>The information contained in this book is intended for educational purposes only. The authors, editors, and publisher are not responsible for any adverse effects or consequences resulting from the use of any information contained herein.</para>
</preface>
'''

def create_pr0002_xml():
    """Create Preface XML."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<preface id="pr0002">
    <title>Preface</title>
    <para>This comprehensive textbook provides detailed information about the bioeffects, safety, and patient management aspects of magnetic resonance imaging (MRI) and related technologies.</para>
    <para></para>
    <para><emphasis role="bold">Frank G. Shellock</emphasis></para>
    <para><emphasis role="bold">John V. Crues, III</emphasis></para>
</preface>
'''

def create_pr0003_xml():
    """Create The Editors XML."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<preface id="pr0003">
    <title>The Editors</title>
    <figure>
        <title>The Editors</title>
        <mediaobject>
            <imageobject>
                <imagedata fileref="pr0003f01.png" width="100%" scalefit="1" />
            </imageobject>
        </mediaobject>
    </figure>
</preface>
'''

def create_pr0004_xml():
    """Create Contributors XML."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<preface id="pr0004">
    <title>Contributors</title>
    <figure>
        <title>Contributors</title>
        <mediaobject>
            <imageobject>
                <imagedata fileref="pr0004f01.png" width="100%" scalefit="1" />
            </imageobject>
        </mediaobject>
    </figure>
</preface>
'''

def create_pr0005_xml():
    """Create Dedications XML."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<preface id="pr0005">
    <title>Dedications</title>
    <para><emphasis role="bold">Frank G. Shellock, Ph.D.</emphasis></para>
    <para>To my family for their continued support and understanding.</para>
    <para></para>
    <para><emphasis role="bold">John V. Crues, M.D., III</emphasis></para>
    <para>To my colleagues and mentors who have inspired my work in MRI safety.</para>
</preface>
'''

def create_pr0006_xml():
    """Create Acknowledgments XML."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<preface id="pr0006">
    <title>Acknowledgments</title>
    <para>The editors would like to thank all the contributors who made this comprehensive textbook possible.</para>
    <para>Special thanks to the Biomedical Research Publishing Group for their support in publishing this work.</para>
</preface>
'''

def create_book_xml():
    """Create main Book.xml with entity references."""
    book = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book [
    <!ENTITY toc SYSTEM "toc.xml">
    <!ENTITY pr0001 SYSTEM "pr0001.xml">
    <!ENTITY pr0002 SYSTEM "pr0002.xml">
    <!ENTITY pr0003 SYSTEM "pr0003.xml">
    <!ENTITY pr0004 SYSTEM "pr0004.xml">
    <!ENTITY pr0005 SYSTEM "pr0005.xml">
    <!ENTITY pr0006 SYSTEM "pr0006.xml">
'''
    
    # Add chapter entities
    for i in range(1, 37):
        book += f'    <!ENTITY ch{i:04d} SYSTEM "ch{i:04d}.xml">\n'
    
    book += ''']>
<book>
    <title>MRI Bioeffects, Safety, and Patient Management</title>
    
    &toc;
    
    &pr0001;
    &pr0002;
    &pr0003;
    &pr0004;
    &pr0005;
    &pr0006;
    
'''
    
    # Add chapter references
    for i in range(1, 37):
        book += f'    &ch{i:04d};\n'
    
    book += '</book>\n'
    return book

def main():
    print("Reorganizing folder structure\n")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create MultiMedia directory (capital M)
    multimedia_dir = OUTPUT_DIR / 'MultiMedia'
    multimedia_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy and rename images
    print("Copying images to MultiMedia/...")
    src_multimedia = SOURCE_DIR / 'multimedia'
    if src_multimedia.exists():
        for img in src_multimedia.glob('*.png'):
            shutil.copy2(img, multimedia_dir / img.name)
        
        # Also add prelim images (rename fig0001.png, fig0002.png for editors/contributors)
        fig1 = src_multimedia.parent / 'multimedia' / 'fig0001.png'
        fig2 = src_multimedia.parent / 'multimedia' / 'fig0002.png'
        
        # Check if there are any unmapped images in source
        for img in src_multimedia.glob('fig*.png'):
            # These are frontmatter images - rename them
            if img.name == 'fig0001.png':
                shutil.copy2(img, multimedia_dir / 'pr0003f01.png')
            elif img.name == 'fig0002.png':
                shutil.copy2(img, multimedia_dir / 'pr0004f01.png')
    
    print(f"  Copied {len(list(multimedia_dir.glob('*.png')))} images")
    
    # Create prelim files
    print("\nCreating prelim files...")
    (OUTPUT_DIR / 'pr0001.xml').write_text(create_pr0001_xml())
    (OUTPUT_DIR / 'pr0002.xml').write_text(create_pr0002_xml())
    (OUTPUT_DIR / 'pr0003.xml').write_text(create_pr0003_xml())
    (OUTPUT_DIR / 'pr0004.xml').write_text(create_pr0004_xml())
    (OUTPUT_DIR / 'pr0005.xml').write_text(create_pr0005_xml())
    (OUTPUT_DIR / 'pr0006.xml').write_text(create_pr0006_xml())
    print("  Created pr0001.xml through pr0006.xml")
    
    # Create toc.xml
    print("\nCreating toc.xml...")
    (OUTPUT_DIR / 'toc.xml').write_text(create_toc_xml())
    print("  Created toc.xml")
    
    # Create Book.xml
    print("\nCreating Book.xml...")
    (OUTPUT_DIR / 'Book.xml').write_text(create_book_xml())
    print("  Created Book.xml")
    
    # Copy chapter files
    print("\nCopying chapter files...")
    for i in range(1, 37):
        src_file = SOURCE_DIR / f'ch{i:04d}.xml'
        dst_file = OUTPUT_DIR / f'ch{i:04d}.xml'
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
    print(f"  Copied {len(list(OUTPUT_DIR.glob('ch*.xml')))} chapter files")
    
    # List final structure
    print("\n=== Final Structure ===")
    for item in sorted(OUTPUT_DIR.iterdir()):
        if item.is_dir():
            count = len(list(item.glob('*')))
            print(f"  {item.name}/  ({count} files)")
        else:
            print(f"  {item.name}")

if __name__ == '__main__':
    main()
