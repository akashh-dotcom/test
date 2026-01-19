#!/usr/bin/env python3
"""
Deep Content Verification: PDF vs ZIP
Checks for missing content between PDF and ZIP source files
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import subprocess

class ContentVerifier:
    def __init__(self, pdf_path, zip_extract_dir, pdf_text_file):
        self.pdf_path = pdf_path
        self.zip_dir = zip_extract_dir
        self.pdf_text_file = pdf_text_file
        self.issues = []
        self.warnings = []
        self.info = []

    def extract_pdf_metadata(self):
        """Extract PDF metadata"""
        try:
            result = subprocess.run(['pdfinfo', self.pdf_path],
                                  capture_output=True, text=True)
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            return info
        except:
            return {}

    def extract_xml_text(self, xml_file):
        """Extract all text content from XML file"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Get all text from all elements
            text_parts = []
            for elem in root.iter():
                if elem.text:
                    text_parts.append(elem.text.strip())
                if elem.tail:
                    text_parts.append(elem.tail.strip())

            return ' '.join(text_parts)
        except Exception as e:
            return f"Error: {e}"

    def get_xml_sections(self, xml_file):
        """Get section structure from XML"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            sections = []
            for elem in root.iter():
                if 'sect' in elem.tag or elem.tag == 'title':
                    title_elem = elem.find('.//title')
                    if title_elem is not None and title_elem.text:
                        sections.append({
                            'tag': elem.tag,
                            'id': elem.get('id', 'no-id'),
                            'title': title_elem.text.strip()
                        })
                    elif elem.tag == 'title' and elem.text:
                        sections.append({
                            'tag': 'title',
                            'id': elem.get('id', 'no-id'),
                            'title': elem.text.strip()
                        })
            return sections
        except Exception as e:
            return []

    def get_image_references_from_xml(self, xml_file):
        """Extract all image references from XML"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            images = []
            for elem in root.iter():
                if 'imagedata' in elem.tag:
                    fileref = elem.get('fileref')
                    if fileref:
                        images.append(fileref)
            return images
        except Exception as e:
            return []

    def count_pdf_images(self):
        """Count images in PDF"""
        try:
            result = subprocess.run(['pdfimages', '-list', self.pdf_path],
                                  capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            # Subtract header lines
            if len(lines) > 2:
                return len(lines) - 2
            return 0
        except:
            return None

    def analyze_pdf_pages(self):
        """Analyze PDF page content"""
        with open(self.pdf_text_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # Try to identify chapters
        chapter_pattern = r'Chapter\s+(\d+)'
        chapters = re.findall(chapter_pattern, text, re.IGNORECASE)

        # Count pages with form feed character
        pages = text.count('\f') + 1

        return {
            'total_pages': pages,
            'chapters_found': len(set(chapters)),
            'chapter_numbers': sorted(set(chapters), key=lambda x: int(x) if x.isdigit() else 0),
            'text_length': len(text),
            'word_count': len(text.split())
        }

    def verify_content(self):
        """Main verification function"""
        print("="*80)
        print("DEEP CONTENT VERIFICATION REPORT")
        print("="*80)

        # PDF Analysis
        print("\n📄 PDF ANALYSIS")
        print("-" * 80)
        pdf_info = self.extract_pdf_metadata()
        pdf_pages = int(pdf_info.get('Pages', 0))
        print(f"Total Pages: {pdf_pages}")
        print(f"Title: {pdf_info.get('Title', 'N/A')}")
        print(f"Author: {pdf_info.get('Author', 'N/A')}")

        pdf_analysis = self.analyze_pdf_pages()
        print(f"Text Pages Detected: {pdf_analysis['total_pages']}")
        print(f"Chapters Found in PDF: {pdf_analysis['chapters_found']}")
        if pdf_analysis['chapter_numbers']:
            print(f"Chapter Numbers: {', '.join(pdf_analysis['chapter_numbers'][:20])}")
        print(f"Total Words: {pdf_analysis['word_count']:,}")

        pdf_images = self.count_pdf_images()
        if pdf_images is not None:
            print(f"Images in PDF: {pdf_images}")

        # ZIP Analysis
        print("\n📦 ZIP CONTENT ANALYSIS")
        print("-" * 80)

        xml_files = list(Path(self.zip_dir).rglob('*.xml'))
        print(f"XML Files Found: {len(xml_files)}")
        for xf in xml_files:
            print(f"  - {xf.name}")

        # Analyze main chapter XML
        main_xml = Path(self.zip_dir) / 'ch0001.xml'
        if main_xml.exists():
            xml_text = self.extract_xml_text(main_xml)
            xml_word_count = len(xml_text.split())
            print(f"\nch0001.xml Content:")
            print(f"  Word Count: {xml_word_count:,}")
            print(f"  Character Count: {len(xml_text):,}")

            sections = self.get_xml_sections(main_xml)
            print(f"  Sections Found: {len(sections)}")

            # Show first few sections
            print("\n  Section Titles (First 10):")
            for i, sect in enumerate(sections[:10], 1):
                print(f"    {i}. [{sect['tag']}] {sect['title'][:60]}")

            # Get image references
            images = self.get_image_references_from_xml(main_xml)
            print(f"\n  Image References in XML: {len(images)}")

        # Check Book.XML
        book_xml = Path(self.zip_dir) / 'Book.XML'
        if book_xml.exists():
            with open(book_xml, 'r') as f:
                book_content = f.read()

            # Count chapter references
            chapter_refs = re.findall(r'<!ENTITY\s+(ch\d+)', book_content)
            print(f"\nBook.XML Analysis:")
            print(f"  Chapter References: {len(chapter_refs)}")
            if chapter_refs:
                print(f"  Chapters: {', '.join(chapter_refs)}")

        # Image Files
        image_files = list(Path(self.zip_dir).rglob('*.jpg')) + \
                     list(Path(self.zip_dir).rglob('*.png'))
        print(f"\n  Image Files in ZIP: {len(image_files)}")

        # COMPARISON & ISSUES
        print("\n" + "="*80)
        print("🔍 VERIFICATION RESULTS")
        print("="*80)

        # Check 1: Page Count Comparison
        print("\n1. PAGE COUNT VERIFICATION")
        print(f"   PDF Pages: {pdf_pages}")
        print(f"   Expected from ZIP: ~{pdf_analysis['total_pages']} (based on text)")

        if pdf_pages > 100 and len(xml_files) == 1:
            self.issues.append(
                f"CRITICAL: PDF has {pdf_pages} pages but ZIP only contains 1 XML chapter file"
            )
            print(f"   ❌ ISSUE: PDF has {pdf_pages} pages but ZIP only has 1 chapter XML")

        # Check 2: Content Coverage
        print("\n2. CONTENT COVERAGE")
        pdf_words = pdf_analysis['word_count']
        xml_words = xml_word_count if main_xml.exists() else 0

        coverage = (xml_words / pdf_words * 100) if pdf_words > 0 else 0
        print(f"   PDF Word Count: {pdf_words:,}")
        print(f"   ZIP Word Count: {xml_words:,}")
        print(f"   Coverage: {coverage:.1f}%")

        if coverage < 50:
            self.issues.append(
                f"CRITICAL: ZIP content only covers {coverage:.1f}% of PDF content"
            )
            print(f"   ❌ ISSUE: ZIP contains only {coverage:.1f}% of PDF content")
        elif coverage < 90:
            self.warnings.append(
                f"WARNING: ZIP content covers {coverage:.1f}% of PDF content"
            )
            print(f"   ⚠️  WARNING: Potential missing content ({100-coverage:.1f}% gap)")
        else:
            print(f"   ✅ Content coverage is good")

        # Check 3: Chapter Verification
        print("\n3. CHAPTER VERIFICATION")
        pdf_chapters = pdf_analysis['chapters_found']
        zip_chapters = len(chapter_refs) if book_xml.exists() else 0

        print(f"   Chapters in PDF: {pdf_chapters}")
        print(f"   Chapters in ZIP: {zip_chapters}")

        if pdf_chapters > zip_chapters:
            missing = pdf_chapters - zip_chapters
            self.issues.append(
                f"CRITICAL: {missing} chapters appear to be missing from ZIP"
            )
            print(f"   ❌ ISSUE: {missing} chapters missing from ZIP")
        else:
            print(f"   ✅ Chapter count matches or ZIP has more")

        # Check 4: Image Verification
        print("\n4. IMAGE VERIFICATION")
        zip_images = len(image_files)
        print(f"   Images in ZIP: {zip_images}")
        if pdf_images:
            print(f"   Images in PDF: {pdf_images}")
            if abs(zip_images - pdf_images) > 50:
                self.warnings.append(
                    f"WARNING: Image count mismatch (ZIP: {zip_images}, PDF: {pdf_images})"
                )
                print(f"   ⚠️  WARNING: Significant image count difference")
            else:
                print(f"   ✅ Image counts are similar")

        # Check 5: Specific Content Verification
        print("\n5. SPECIFIC CONTENT CHECKS")

        # Check if preface exists in both
        with open(self.pdf_text_file, 'r', encoding='utf-8', errors='ignore') as f:
            pdf_text = f.read()

        xml_text_lower = xml_text.lower() if main_xml.exists() else ""
        pdf_text_lower = pdf_text.lower()

        # Check for key sections
        key_sections = [
            'preface',
            'introduction',
            'bioeffects',
            'safety',
            'magnetic resonance imaging'
        ]

        for section in key_sections:
            in_pdf = section in pdf_text_lower
            in_xml = section in xml_text_lower

            if in_pdf and not in_xml:
                self.warnings.append(f"Section '{section}' found in PDF but not in ZIP XML")
                print(f"   ⚠️  '{section}' in PDF but not in ZIP")
            elif in_pdf and in_xml:
                print(f"   ✅ '{section}' found in both")

        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)

        if self.issues:
            print(f"\n❌ CRITICAL ISSUES FOUND: {len(self.issues)}")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        if not self.issues and not self.warnings:
            print("\n✅ No major issues found - content appears complete")

        # Final Verdict
        print("\n" + "="*80)
        print("VERDICT")
        print("="*80)

        if len(self.issues) > 0:
            print("\n❌ INCOMPLETE: The ZIP file does NOT contain the complete book content.")
            print("   The ZIP appears to be a PARTIAL export or SAMPLE of the full PDF.")
            print(f"   Estimated missing content: ~{100-coverage:.0f}% of the book")
            print(f"   Missing: ~{pdf_pages - (pdf_pages * coverage / 100):.0f} pages worth of content")
        elif len(self.warnings) > 0:
            print("\n⚠️  PARTIAL: The ZIP file may be missing some content.")
            print("   Review the warnings above for details.")
        else:
            print("\n✅ COMPLETE: The ZIP file appears to contain complete source content.")

        print("="*80)

        return {
            'issues': self.issues,
            'warnings': self.warnings,
            'pdf_pages': pdf_pages,
            'pdf_words': pdf_words,
            'xml_words': xml_words,
            'coverage': coverage
        }

def main():
    pdf_file = "9780989163286.pdf"
    zip_extract = "temp_extract"
    pdf_text = "pdf_extracted.txt"

    verifier = ContentVerifier(pdf_file, zip_extract, pdf_text)
    results = verifier.verify_content()

    # Save report
    report_file = "content_verification_report.txt"
    print(f"\n✅ Full report saved to: {report_file}")

    return results

if __name__ == "__main__":
    main()
