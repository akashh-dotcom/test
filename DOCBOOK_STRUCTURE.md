# DocBook Proper Structure - Complete Documentation

## ISBN: 9780989163286
**Book Title:** MRI Bioeffects, Safety, and Patient Management (Second Edition)

---

## File Structure Overview

This package follows the **DocBook XML 4.2 DTD** standard with ISBN-based naming conventions.

### Total Files
- **1** Master book file: `book.9780989163286.xml`
- **6** Preface files (front matter)
- **36** Chapter files (main content)
- **1** Multimedia directory with all images
- **Total: 44 files**

---

## Naming Conventions

### 1. Book File
**Pattern:** `book.{ISBN}.xml`
**Example:** `book.9780989163286.xml`
**Purpose:** Master file containing all ENTITY declarations and book structure

### 2. Preface Files (Front Matter)
**Pattern:** `preface.{ISBN}.pr####.xml`
**ID Format:** `<preface id="pr####">`

| File | ID | Title |
|------|-----|-------|
| preface.9780989163286.pr0001.xml | pr0001 | Title and Copyright |
| preface.9780989163286.pr0002.xml | pr0002 | Preface |
| preface.9780989163286.pr0003.xml | pr0003 | The Editors |
| preface.9780989163286.pr0004.xml | pr0004 | Contributors |
| preface.9780989163286.pr0005.xml | pr0005 | Dedications |
| preface.9780989163286.pr0006.xml | pr0006 | Acknowledgments |

### 3. Chapter Files
**Pattern:** `sect1.{ISBN}.ch####s0000.xml`
**ID Format:** `<sect1 id="ch####s0000">`
**Note:** The `s0000` suffix indicates this is the main chapter file (section 0)

All 36 chapters follow this pattern:
- `sect1.9780989163286.ch0001s0000.xml` → Chapter 1
- `sect1.9780989163286.ch0002s0000.xml` → Chapter 2
- ...
- `sect1.9780989163286.ch0036s0000.xml` → Chapter 36

---

## The CARDINAL RULE

**CRITICAL:** For any file with root ID `{ROOT_ID}`, ALL internal structural IDs MUST be prefixed with `{ROOT_ID}`

### Example for Chapter 1 (root ID: ch0001s0000)

```
ch0001s0000                          ← sect1 (file root)
├── ch0001s0000s01                   ← sect2 #1
│   ├── ch0001s0000s01s01            ← sect3 #1
│   │   ├── ch0001s0000s01s01s01     ← sect4 #1
│   │   │   └── ch0001s0000s01s01s01s01  ← sect5 #1
│   │   └── ch0001s0000s01s01fg0001  ← figure #1
│   └── ch0001s0000s01s02            ← sect3 #2
└── ch0001s0000s02                   ← sect2 #2
```

### ID Length Reference

| Element | Pattern | Example | Length |
|---------|---------|---------|---------|
| Root (chapter) | ch####s#### | ch0001s0000 | 11 chars |
| sect2 | {root}s## | ch0001s0000s01 | 14 chars |
| sect3 | {sect2}s## | ch0001s0000s01s01 | 17 chars |
| sect4 | {sect3}s## | ch0001s0000s01s01s01 | 20 chars |
| sect5 | {sect4}s## | ch0001s0000s01s01s01s01 | 23 chars |
| figure | {parent}fg#### | ch0001s0000s01fg0001 | 18+ chars |
| table | {parent}ta#### | ch0001s0000s01ta0001 | 18+ chars |

---

## Book.XML Structure

The master `book.9780989163286.xml` file contains:

### 1. DOCTYPE Declaration with ENTITY References
```xml
<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.2//EN"
  "http://www.oasis-open.org/docbook/xml/4.2/docbookx.dtd" [
<!ENTITY pr0001 SYSTEM "preface.9780989163286.pr0001.xml">
<!ENTITY pr0002 SYSTEM "preface.9780989163286.pr0002.xml">
...
<!ENTITY pr0006 SYSTEM "preface.9780989163286.pr0006.xml">
<!ENTITY ch0001s0000 SYSTEM "sect1.9780989163286.ch0001s0000.xml">
<!ENTITY ch0002s0000 SYSTEM "sect1.9780989163286.ch0002s0000.xml">
...
<!ENTITY ch0036s0000 SYSTEM "sect1.9780989163286.ch0036s0000.xml">
]>
```

### 2. Book Metadata
```xml
<book id="mri-bioeffects-safety" lang="en">
  <title>MRI Bioeffects, Safety, and Patient Management</title>
  <subtitle>Second Edition</subtitle>
  <bookinfo>
    <isbn>9780989163286</isbn>
    <authorgroup>
      <author>
        <firstname>Frank G.</firstname>
        <surname>Shellock</surname>
      </author>
      <author>
        <firstname>John V.</firstname>
        <surname>Crues</surname>
        <lineage>III</lineage>
      </author>
    </authorgroup>
    <publisher>
      <publishername>Biomedical Research Publishing Group</publishername>
    </publisher>
    <pubdate>2022</pubdate>
    <edition>Second Edition</edition>
    <copyright>
      <year>2022</year>
      <holder>Biomedical Research Publishing Group and Shellock R &amp; D Services, Inc.</holder>
    </copyright>
  </bookinfo>
```

### 3. Content References
```xml
  &pr0001;
  &pr0002;
  &pr0003;
  &pr0004;
  &pr0005;
  &pr0006;
  &ch0001s0000;
  &ch0002s0000;
  ...
  &ch0036s0000;
</book>
```

---

## Chapter Titles

| File | Chapter # | Title |
|------|-----------|-------|
| sect1.9780989163286.ch0001s0000.xml | 1 | Basic MRI Physics: Implications for MRI Safety |
| sect1.9780989163286.ch0002s0000.xml | 2 | Principles of MRI Safety Physics |
| sect1.9780989163286.ch0003s0000.xml | 3 | MRI Physics and Safety at 7 Tesla |
| sect1.9780989163286.ch0004s0000.xml | 4 | Bioeffects of Static Magnetic Fields |
| sect1.9780989163286.ch0005s0000.xml | 5 | Bioeffects of Gradient Magnetic Fields |
| sect1.9780989163286.ch0006s0000.xml | 6 | Acoustic Noise Associated With MRI Procedures |
| sect1.9780989163286.ch0007s0000.xml | 7 | Bioeffects of Radiofrequency Power Deposition |
| sect1.9780989163286.ch0008s0000.xml | 8 | Radiofrequency-Energy Induced Heating During MRI |
| sect1.9780989163286.ch0009s0000.xml | 9 | Thermal Effects Associated with RF Exposures |
| sect1.9780989163286.ch0010s0000.xml | 10 | Claustrophobia, Anxiety, and Emotional Distress |
| sect1.9780989163286.ch0011s0000.xml | 11 | MRI Procedures and Pregnancy |
| sect1.9780989163286.ch0012s0000.xml | 12 | Identification and Management of Acute Reactions to Gadolinium-Based Contrast Agents |
| sect1.9780989163286.ch0013s0000.xml | 13 | MRI Contrast Agents and Nephrogenic Systemic Fibrosis |
| sect1.9780989163286.ch0014s0000.xml | 14 | Gadolinium Retention in Brain and Body Tissues |
| sect1.9780989163286.ch0015s0000.xml | 15 | MRI Screening for Patients and Individuals |
| sect1.9780989163286.ch0016s0000.xml | 16 | Using Ferromagnetic Detection Systems |
| sect1.9780989163286.ch0017s0000.xml | 17 | Physiological Monitoring of Patients During MRI |
| sect1.9780989163286.ch0018s0000.xml | 18 | MRI-Related Issues for Implants and Devices |
| sect1.9780989163286.ch0019s0000.xml | 19 | Active Implanted Medical Devices |
| sect1.9780989163286.ch0020s0000.xml | 20 | MRI-Related Heating of Implants and Devices |
| sect1.9780989163286.ch0021s0000.xml | 21 | MRI Test Methods for MR Conditional Active Implantable Medical Devices |
| sect1.9780989163286.ch0022s0000.xml | 22 | Using MRI Simulations and Measurements |
| sect1.9780989163286.ch0023s0000.xml | 23 | The Role of Numerical Modeling and Simulations |
| sect1.9780989163286.ch0024s0000.xml | 24 | Performing MRI in Patients with Conventional Cardiac Devices |
| sect1.9780989163286.ch0025s0000.xml | 25 | MRI and Patients with Cardiac Implantable Electronic Devices |
| sect1.9780989163286.ch0026s0000.xml | 26 | MRI Safety Issues for Neuromodulation Systems |
| sect1.9780989163286.ch0027s0000.xml | 27 | MRI Safety Policies and Procedures for a Hospital |
| sect1.9780989163286.ch0028s0000.xml | 28 | MRI Safety Policies and Procedures for an Outpatient Facility |
| sect1.9780989163286.ch0029s0000.xml | 29 | MRI Safety Policies and Procedures for a Children's Hospital |
| sect1.9780989163286.ch0030s0000.xml | 30 | MRI Safety Policies and Procedures for a Research Facility |
| sect1.9780989163286.ch0031s0000.xml | 31 | Safety Issues for Interventional MR Systems |
| sect1.9780989163286.ch0032s0000.xml | 32 | Occupational Exposure During MRI |
| sect1.9780989163286.ch0033s0000.xml | 33 | MRI Safety and Screening Training Programs |
| sect1.9780989163286.ch0034s0000.xml | 34 | MRI Facilities, Inspections, and Accreditation |
| sect1.9780989163286.ch0035s0000.xml | 35 | MRI Safety Standards and Guidelines in the United States |
| sect1.9780989163286.ch0036s0000.xml | 36 | MRI Safety Standards and Guidelines in Australia |

---

## Key Features Preserved

### ✅ All Content Preserved
- No content deleted or modified
- All text, formatting, and structure maintained exactly as in source
- All bibliographies, figures, tables, and lists intact

### ✅ Multimedia References
- All image references maintained (e.g., `multimedia/Ch0002f01.jpg`)
- Complete multimedia directory with all images
- No broken links - all fileref attributes point to correct files

### ✅ XML Structure
- Proper DocBook XML 4.2 DTD compliance
- Correct element nesting and hierarchy
- All emphasis, lists, tables, figures properly formatted

### ✅ ID Consistency (CARDINAL RULE)
- All internal IDs follow the prefix rule
- sect2, sect3, sect4, sect5 IDs properly prefixed with parent IDs
- Figure and table IDs follow same convention
- No ID conflicts or duplicates

---

## Validation Rules

### Filename ↔ Root ID Match
**RULE:** Filename fragment MUST equal root element ID

✅ **CORRECT:**
- File: `sect1.9780989163286.ch0011s0000.xml`
- Root: `<sect1 id="ch0011s0000">`

❌ **WRONG:**
- File: `sect1.9780989163286.ch0011s0000.xml`
- Root: `<sect1 id="ch0011">`

### ID Hierarchy Validation
All IDs must follow the hierarchical prefix pattern:
- Root determines all child IDs
- Each level adds suffix to parent ID
- No ID can exist without proper parent prefix

---

## Output Package

**File:** `9780989163286_DOCBOOK_PROPER.zip` (23 MB)
**Location:** `/home/user/test/`
**Contents:**
- book.9780989163286.xml
- 6 preface files (pr0001-pr0006)
- 36 chapter files (ch0001s0000-ch0036s0000)
- multimedia/ directory

---

## Processing Summary

### Source
- Original ZIP: `9780989163286_FINAL_RITTDOC.zip`
- 11 source XML files with mixed chapter content
- Identified duplicates and merged chapters

### Transformation Steps
1. ✅ Split front matter into 6 individual preface files
2. ✅ Extracted all 36 chapters from source files
3. ✅ Removed duplicate chapters (ch004, ch006, ch011)
4. ✅ Converted chapter elements to sect1 elements
5. ✅ Updated all IDs to follow CARDINAL RULE prefix convention
6. ✅ Applied ISBN-based naming to all files
7. ✅ Created master book.{ISBN}.xml with proper ENTITY declarations
8. ✅ Copied all multimedia files
9. ✅ Validated structure and IDs

### Standards Compliance
- ✅ DocBook XML 4.2 DTD
- ✅ ISBN-based file naming
- ✅ CARDINAL RULE for ID prefixing
- ✅ Proper ENTITY declarations
- ✅ Correct sect1/sect2/sect3/sect4/sect5 nesting

---

## Usage

To use this DocBook package:

1. Extract `9780989163286_DOCBOOK_PROPER.zip`
2. The master file is `book.9780989163286.xml`
3. All ENTITY references will resolve to individual files
4. Process with any DocBook-compatible toolchain (e.g., xsltproc, Apache FOP, etc.)
5. All multimedia references point to `multimedia/` directory

---

## Technical Notes

- **XML Version:** 1.0
- **Encoding:** UTF-8
- **DTD:** DocBook XML V4.2
- **Public ID:** `-//OASIS//DTD DocBook XML V4.2//EN`
- **System ID:** `http://www.oasis-open.org/docbook/xml/4.2/docbookx.dtd`

---

**Generated:** 2026-01-24
**ISBN:** 9780989163286
**Publisher:** Biomedical Research Publishing Group
**Edition:** Second Edition (2022)
