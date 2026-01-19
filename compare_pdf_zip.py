#!/usr/bin/env python3
"""
Comparison Report Generator for PDF and ZIP Files
Compares 9780989163286.pdf with 9780989163286_rittdoc (3).zip
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import subprocess
import json

class PDFZIPComparator:
    def __init__(self, pdf_path, zip_path):
        self.pdf_path = pdf_path
        self.zip_path = zip_path
        self.extract_dir = "temp_extract"
        self.report = {}

    def analyze_pdf(self):
        """Analyze PDF file"""
        print("Analyzing PDF file...")
        pdf_info = {
            'file_name': os.path.basename(self.pdf_path),
            'file_size': os.path.getsize(self.pdf_path),
            'file_size_mb': round(os.path.getsize(self.pdf_path) / (1024*1024), 2)
        }

        # Try to get PDF page count using pdftotext or similar
        try:
            result = subprocess.run(['pdftk', self.pdf_path, 'dump_data'],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'NumberOfPages' in line:
                        pdf_info['page_count'] = int(line.split(':')[1].strip())
        except:
            pass

        # Try alternative method with pdfinfo
        try:
            result = subprocess.run(['pdfinfo', self.pdf_path],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Pages:' in line:
                        pdf_info['page_count'] = int(line.split(':')[1].strip())
                    elif 'Title:' in line:
                        pdf_info['title'] = line.split(':', 1)[1].strip()
                    elif 'Creator:' in line:
                        pdf_info['creator'] = line.split(':', 1)[1].strip()
        except:
            pass

        # Try to extract text from first few pages
        try:
            result = subprocess.run(['pdftotext', '-l', '3', self.pdf_path, '-'],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                pdf_info['sample_text'] = result.stdout[:500]
        except:
            pass

        self.report['pdf'] = pdf_info
        return pdf_info

    def analyze_zip(self):
        """Analyze ZIP file contents"""
        print("Analyzing ZIP file...")
        zip_info = {
            'file_name': os.path.basename(self.zip_path),
            'file_size': os.path.getsize(self.zip_path),
            'file_size_mb': round(os.path.getsize(self.zip_path) / (1024*1024), 2)
        }

        # Analyze ZIP contents
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            zip_info['total_files'] = len(file_list)
            zip_info['file_list'] = file_list[:20]  # First 20 files

        # Analyze extracted contents
        xml_files = list(Path(self.extract_dir).rglob('*.xml'))
        image_files = list(Path(self.extract_dir).rglob('*.jpg')) + \
                     list(Path(self.extract_dir).rglob('*.png'))

        zip_info['xml_files_count'] = len(xml_files)
        zip_info['image_files_count'] = len(image_files)

        # Analyze Book.XML if exists
        book_xml_path = Path(self.extract_dir) / 'Book.XML'
        if book_xml_path.exists():
            try:
                tree = ET.parse(book_xml_path)
                root = tree.getroot()
                zip_info['book_xml_root'] = root.tag
                zip_info['book_xml_children'] = [child.tag for child in root][:10]
            except Exception as e:
                zip_info['book_xml_error'] = str(e)

        # Analyze main chapter XML
        ch_xml_path = Path(self.extract_dir) / 'ch0001.xml'
        if ch_xml_path.exists():
            try:
                with open(ch_xml_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    zip_info['ch0001_size'] = len(content)
                    zip_info['ch0001_sample'] = content[:1000]  # First 1000 chars

                # Try to parse as XML
                tree = ET.parse(ch_xml_path)
                root = tree.getroot()
                zip_info['ch0001_root_tag'] = root.tag

                # Count elements
                all_elements = list(root.iter())
                zip_info['ch0001_element_count'] = len(all_elements)

                # Get unique tags
                tags = set([elem.tag for elem in all_elements])
                zip_info['ch0001_unique_tags'] = list(tags)[:20]

            except Exception as e:
                zip_info['ch0001_error'] = str(e)

        # Get sample image info
        if image_files:
            sample_images = []
            for img in image_files[:10]:
                sample_images.append({
                    'name': img.name,
                    'size': img.stat().st_size,
                    'path': str(img.relative_to(self.extract_dir))
                })
            zip_info['sample_images'] = sample_images

        self.report['zip'] = zip_info
        return zip_info

    def compare_contents(self):
        """Compare PDF and ZIP contents"""
        print("Comparing contents...")
        comparison = {}

        # File size comparison
        pdf_size = self.report['pdf']['file_size']
        zip_size = self.report['zip']['file_size']
        comparison['size_ratio'] = round(pdf_size / zip_size, 2)
        comparison['size_difference_mb'] = round((zip_size - pdf_size) / (1024*1024), 2)

        # Content type comparison
        comparison['pdf_is_rendered'] = True  # PDF is rendered output
        comparison['zip_is_source'] = True    # ZIP contains source XML/images

        comparison['notes'] = [
            f"PDF is {comparison['size_ratio']}x smaller than ZIP",
            f"ZIP contains {self.report['zip']['total_files']} source files",
            f"ZIP includes {self.report['zip']['xml_files_count']} XML files and {self.report['zip']['image_files_count']} images",
            "PDF is the rendered/compiled version of the XML source in ZIP",
            "ZIP contains structured data (XML) and multimedia assets"
        ]

        self.report['comparison'] = comparison
        return comparison

    def generate_report(self):
        """Generate comprehensive comparison report"""
        print("\n" + "="*80)
        print("COMPARISON REPORT: PDF vs ZIP")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # PDF Information
        print("\n📄 PDF FILE ANALYSIS")
        print("-" * 80)
        pdf = self.report.get('pdf', {})
        print(f"File Name:    {pdf.get('file_name', 'N/A')}")
        print(f"File Size:    {pdf.get('file_size_mb', 'N/A')} MB ({pdf.get('file_size', 0):,} bytes)")
        if 'page_count' in pdf:
            print(f"Pages:        {pdf.get('page_count')}")
        if 'title' in pdf:
            print(f"Title:        {pdf.get('title')}")
        if 'creator' in pdf:
            print(f"Creator:      {pdf.get('creator')}")

        # ZIP Information
        print("\n📦 ZIP FILE ANALYSIS")
        print("-" * 80)
        zip_data = self.report.get('zip', {})
        print(f"File Name:         {zip_data.get('file_name', 'N/A')}")
        print(f"File Size:         {zip_data.get('file_size_mb', 'N/A')} MB ({zip_data.get('file_size', 0):,} bytes)")
        print(f"Total Files:       {zip_data.get('total_files', 'N/A')}")
        print(f"XML Files:         {zip_data.get('xml_files_count', 'N/A')}")
        print(f"Image Files:       {zip_data.get('image_files_count', 'N/A')}")

        if 'book_xml_root' in zip_data:
            print(f"\nBook.XML Root:     {zip_data.get('book_xml_root')}")

        if 'ch0001_root_tag' in zip_data:
            print(f"\nch0001.xml Info:")
            print(f"  Root Tag:        {zip_data.get('ch0001_root_tag')}")
            print(f"  Total Elements:  {zip_data.get('ch0001_element_count', 'N/A')}")
            print(f"  File Size:       {zip_data.get('ch0001_size', 0):,} bytes")

        # Comparison
        print("\n🔍 COMPARISON ANALYSIS")
        print("-" * 80)
        comp = self.report.get('comparison', {})
        print(f"Size Ratio:        PDF is {comp.get('size_ratio', 'N/A')}x the size of ZIP")
        print(f"Size Difference:   {abs(comp.get('size_difference_mb', 0))} MB")
        print(f"\nKey Findings:")
        for note in comp.get('notes', []):
            print(f"  • {note}")

        # Content Structure
        print("\n📋 CONTENT STRUCTURE")
        print("-" * 80)
        print("PDF Structure:")
        print("  • Rendered document format")
        print("  • Fixed layout with text and images")
        print("  • Optimized for viewing and printing")
        print("  • Compressed content")

        print("\nZIP Structure:")
        print("  • Source XML files with structured data")
        print("  • Separate multimedia assets (images)")
        print("  • Machine-readable format")
        print("  • Editable and transformable")

        # Sample Content
        if zip_data.get('sample_images'):
            print("\n🖼️  SAMPLE IMAGES IN ZIP (First 10)")
            print("-" * 80)
            for idx, img in enumerate(zip_data['sample_images'], 1):
                print(f"{idx:2d}. {img['path']:50s} {img['size']:>10,} bytes")

        # File Types
        print("\n📂 FILE TYPE BREAKDOWN")
        print("-" * 80)
        if 'ch0001_unique_tags' in zip_data:
            print(f"XML Elements Found: {', '.join(zip_data['ch0001_unique_tags'][:15])}")

        print("\n" + "="*80)
        print("END OF REPORT")
        print("="*80)

        # Save report to file
        report_file = f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            # Redirect stdout to file
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            self.generate_report_content()
            sys.stdout = old_stdout

        print(f"\n✅ Report saved to: {report_file}")

        # Also save JSON version
        json_file = report_file.replace('.txt', '.json')
        with open(json_file, 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"✅ JSON data saved to: {json_file}")

        return report_file

    def generate_report_content(self):
        """Generate report content (for file output)"""
        print("="*80)
        print("COMPARISON REPORT: PDF vs ZIP")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # PDF Information
        print("\nPDF FILE ANALYSIS")
        print("-" * 80)
        pdf = self.report.get('pdf', {})
        for key, value in pdf.items():
            if key != 'sample_text':
                print(f"{key:20s}: {value}")

        # ZIP Information
        print("\nZIP FILE ANALYSIS")
        print("-" * 80)
        zip_data = self.report.get('zip', {})
        for key, value in zip_data.items():
            if key not in ['file_list', 'sample_images', 'ch0001_sample']:
                if isinstance(value, list):
                    print(f"{key:20s}: {len(value)} items")
                else:
                    print(f"{key:20s}: {value}")

        # Comparison
        print("\nCOMPARISON ANALYSIS")
        print("-" * 80)
        comp = self.report.get('comparison', {})
        for key, value in comp.items():
            if key != 'notes':
                print(f"{key:20s}: {value}")

        print("\nKey Findings:")
        for note in comp.get('notes', []):
            print(f"  • {note}")

def main():
    pdf_file = "9780989163286.pdf"
    zip_file = "9780989163286_rittdoc (3).zip"

    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found!")
        return

    if not os.path.exists(zip_file):
        print(f"Error: ZIP file '{zip_file}' not found!")
        return

    comparator = PDFZIPComparator(pdf_file, zip_file)

    # Run analysis
    comparator.analyze_pdf()
    comparator.analyze_zip()
    comparator.compare_contents()

    # Generate report
    comparator.generate_report()

if __name__ == "__main__":
    main()
