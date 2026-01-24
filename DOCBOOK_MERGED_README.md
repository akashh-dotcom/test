# DocBook Merged Chapters - Documentation

## ISBN: 9780989163286
**Book Title:** MRI Bioeffects, Safety, and Patient Management (Second Edition)

---

## Overview

This package contains **all 36 chapters merged into a single chapter file**, maintaining all content, references, and multimedia links.

---

## File Structure

### Total Files in Package
- **1** Master book file: `book.9780989163286.xml`
- **1** Merged chapter file: `chapter.9780989163286.merged.xml` (contains all 36 chapters)
- **6** Preface files (front matter)
- **1** Multimedia directory with all images
- **Total: 9 files/directories**

---

## Files Included

### 1. Master Book File
**File:** `book.9780989163286.xml`
**Purpose:** DocBook master file with ENTITY declarations

### 2. Merged Chapter File
**File:** `chapter.9780989163286.merged.xml`
**Size:** 2.4 MB
**Content:** All 36 chapters combined in sequential order
**Structure:**
```xml
<chapter id="merged-chapters" label="Main Content">
  <title>MRI Bioeffects, Safety, and Patient Management</title>

  <sect1 id="ch0001s0000">
    <!-- Chapter 1 content -->
  </sect1>

  <sect1 id="ch0002s0000">
    <!-- Chapter 2 content -->
  </sect1>

  ...

  <sect1 id="ch0036s0000">
    <!-- Chapter 36 content -->
  </sect1>
</chapter>
```

### 3. Preface Files (Front Matter)
Same as DocBook proper structure:
- `preface.9780989163286.pr0001.xml` - Title and Copyright
- `preface.9780989163286.pr0002.xml` - Preface
- `preface.9780989163286.pr0003.xml` - The Editors
- `preface.9780989163286.pr0004.xml` - Contributors
- `preface.9780989163286.pr0005.xml` - Dedications
- `preface.9780989163286.pr0006.xml` - Acknowledgments

### 4. Multimedia Directory
**Directory:** `multimedia/`
**Content:** All images referenced in chapters (Ch0001f01.jpg, Ch0002f01.jpg, etc.)

---

## Book.XML Structure

The master book file references the merged chapter:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.2//EN"
  "http://www.oasis-open.org/docbook/xml/4.2/docbookx.dtd" [
<!ENTITY pr0001 SYSTEM "preface.9780989163286.pr0001.xml">
<!ENTITY pr0002 SYSTEM "preface.9780989163286.pr0002.xml">
<!ENTITY pr0003 SYSTEM "preface.9780989163286.pr0003.xml">
<!ENTITY pr0004 SYSTEM "preface.9780989163286.pr0004.xml">
<!ENTITY pr0005 SYSTEM "preface.9780989163286.pr0005.xml">
<!ENTITY pr0006 SYSTEM "preface.9780989163286.pr0006.xml">
<!ENTITY merged-chapters SYSTEM "chapter.9780989163286.merged.xml">
]>
<book id="mri-bioeffects-safety" lang="en">
  <title>MRI Bioeffects, Safety, and Patient Management</title>
  <subtitle>Second Edition</subtitle>
  <bookinfo>
    <isbn>9780989163286</isbn>
    ...
  </bookinfo>

  <!-- Prefaces -->
  &pr0001;
  &pr0002;
  &pr0003;
  &pr0004;
  &pr0005;
  &pr0006;

  <!-- All chapters merged -->
  &merged-chapters;
</book>
```

---

## Chapters Included in Merged File

All 36 chapters are included in sequential order:

| Sect1 ID | Chapter # | Title |
|----------|-----------|-------|
| ch0001s0000 | 1 | Basic MRI Physics: Implications for MRI Safety |
| ch0002s0000 | 2 | Principles of MRI Safety Physics |
| ch0003s0000 | 3 | MRI Physics and Safety at 7 Tesla |
| ch0004s0000 | 4 | Bioeffects of Static Magnetic Fields |
| ch0005s0000 | 5 | Bioeffects of Gradient Magnetic Fields |
| ch0006s0000 | 6 | Acoustic Noise Associated With MRI Procedures |
| ch0007s0000 | 7 | Bioeffects of Radiofrequency Power Deposition |
| ch0008s0000 | 8 | Radiofrequency-Energy Induced Heating During MRI |
| ch0009s0000 | 9 | Thermal Effects Associated with RF Exposures |
| ch0010s0000 | 10 | Claustrophobia, Anxiety, and Emotional Distress |
| ch0011s0000 | 11 | MRI Procedures and Pregnancy |
| ch0012s0000 | 12 | Identification and Management of Acute Reactions |
| ch0013s0000 | 13 | MRI Contrast Agents and Nephrogenic Systemic Fibrosis |
| ch0014s0000 | 14 | Gadolinium Retention in Brain and Body Tissues |
| ch0015s0000 | 15 | MRI Screening for Patients and Individuals |
| ch0016s0000 | 16 | Using Ferromagnetic Detection Systems |
| ch0017s0000 | 17 | Physiological Monitoring of Patients During MRI |
| ch0018s0000 | 18 | MRI-Related Issues for Implants and Devices |
| ch0019s0000 | 19 | Active Implanted Medical Devices |
| ch0020s0000 | 20 | MRI-Related Heating of Implants and Devices |
| ch0021s0000 | 21 | MRI Test Methods for MR Conditional Devices |
| ch0022s0000 | 22 | Using MRI Simulations and Measurements |
| ch0023s0000 | 23 | The Role of Numerical Modeling and Simulations |
| ch0024s0000 | 24 | Performing MRI in Patients with Conventional Cardiac Devices |
| ch0025s0000 | 25 | MRI and Patients with Cardiac Implantable Electronic Devices |
| ch0026s0000 | 26 | MRI Safety Issues for Neuromodulation Systems |
| ch0027s0000 | 27 | MRI Safety Policies and Procedures for a Hospital |
| ch0028s0000 | 28 | MRI Safety Policies and Procedures for an Outpatient Facility |
| ch0029s0000 | 29 | MRI Safety Policies and Procedures for a Children's Hospital |
| ch0030s0000 | 30 | MRI Safety Policies and Procedures for a Research Facility |
| ch0031s0000 | 31 | Safety Issues for Interventional MR Systems |
| ch0032s0000 | 32 | Occupational Exposure During MRI |
| ch0033s0000 | 33 | MRI Safety and Screening Training Programs |
| ch0034s0000 | 34 | MRI Facilities, Inspections, and Accreditation |
| ch0035s0000 | 35 | MRI Safety Standards and Guidelines in the United States |
| ch0036s0000 | 36 | MRI Safety Standards and Guidelines in Australia |

---

## Key Features

### ✅ All Content Preserved
- All 36 chapters merged sequentially
- No content deleted or modified
- All text, formatting, tables, figures, and lists intact
- All bibliographies and references preserved

### ✅ All References Maintained
- Original chapter IDs preserved (ch0001s0000, ch0002s0000, etc.)
- All internal section IDs maintained (sect2, sect3, sect4, sect5)
- All cross-references between chapters work correctly
- All figure and table references intact

### ✅ All Multimedia Links Working
- All image references maintained (e.g., `multimedia/Ch0002f01.jpg`)
- Complete multimedia directory included
- No broken links

### ✅ Proper XML Structure
- Valid DocBook XML 4.2 DTD structure
- Proper nesting: chapter → sect1 → sect2 → sect3 → sect4 → sect5
- All emphasis, lists, tables, figures properly formatted
- Well-formed XML throughout

---

## Advantages of Merged Structure

1. **Single File Access**: All chapter content in one file for easy reading/processing
2. **Simplified Distribution**: Only 1 chapter file instead of 36 separate files
3. **Cross-Chapter Navigation**: All chapters accessible without file switching
4. **Maintained Organization**: Each chapter still identifiable by its sect1 ID
5. **Reference Integrity**: All internal references still work correctly

---

## Comparison with Split Structure

| Feature | Split (36 files) | Merged (1 file) |
|---------|------------------|-----------------|
| Chapter files | 36 separate files | 1 combined file |
| File size per chapter | ~50-100 KB each | 2.4 MB total |
| Chapter IDs | ch0001s0000 - ch0036s0000 | Same IDs preserved |
| Cross-references | Work across files | Work within file |
| Distribution | 36+ files to manage | 8 files total |
| Processing | Requires entity resolution | Direct access |

---

## Usage

### To Use This Package:

1. **Extract** `9780989163286_DOCBOOK_MERGED.zip`
2. **Master file** is `book.9780989163286.xml`
3. **Main content** in `chapter.9780989163286.merged.xml`
4. **Process** with DocBook toolchain (xsltproc, Apache FOP, etc.)
5. **Multimedia** references point to `multimedia/` directory

### To Access Specific Chapters:

Since all chapters are in one file, you can:
- Navigate by sect1 ID (e.g., find `ch0015s0000` for Chapter 15)
- Use XPath queries to extract specific chapters
- Process the entire merged file as a single document

---

## Output Package

**File:** `9780989163286_DOCBOOK_MERGED.zip`
**Size:** 22.8 MB
**Location:** `/home/user/test/`

**Contents:**
- book.9780989163286.xml (1.4 KB)
- chapter.9780989163286.merged.xml (2.4 MB)
- preface.9780989163286.pr0001.xml through pr0006.xml
- multimedia/ directory (all images)

---

## Technical Details

- **XML Version:** 1.0
- **Encoding:** UTF-8
- **DTD:** DocBook XML V4.2
- **Public ID:** `-//OASIS//DTD DocBook XML V4.2//EN`
- **System ID:** `http://www.oasis-open.org/docbook/xml/4.2/docbookx.dtd`

---

## Validation

The merged file maintains:
- ✅ Valid DocBook XML 4.2 structure
- ✅ All original chapter IDs
- ✅ All section hierarchy (sect1-sect5)
- ✅ All multimedia references
- ✅ All cross-references
- ✅ All formatting and content

---

**Generated:** 2026-01-24
**ISBN:** 9780989163286
**Publisher:** Biomedical Research Publishing Group
**Edition:** Second Edition (2022)
**Total Chapters:** 36 (all merged)
**Total Content:** Complete with no losses
