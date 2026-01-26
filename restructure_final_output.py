#!/usr/bin/env python3
"""
Restructure final_output_tables to match the desired structure:
- Book.xml (main file with entity references)
- toc.xml (Table of Contents)
- pr0001.xml - Title and Copyright
- pr0002.xml - Preface  
- pr0003.xml - The Editors
- pr0004.xml - Contributors
- pr0005.xml - Dedications
- pr0006.xml - Acknowledgments
- ch0001.xml - ch0036.xml (chapters)
"""

import os
import re
from pathlib import Path

OUTPUT_DIR = Path('/workspace/final_output_tables')

def create_preface_file(preface_id, title, content):
    """Create a preface XML file."""
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>

<preface id="{preface_id}">
    <title>{title}</title>
{content}
</preface>'''
    return xml


def main():
    print("=" * 70)
    print("RESTRUCTURING final_output_tables")
    print("=" * 70)
    
    # Read the frontmatter.xml content
    frontmatter_path = OUTPUT_DIR / 'frontmatter.xml'
    with open(frontmatter_path, 'r', encoding='utf-8') as f:
        frontmatter_content = f.read()
    
    # Create preface files by extracting sections
    
    # pr0001 - Title and Copyright (beginning to Disclaimer section)
    pr0001_content = '''    <para>MRI Bioeffects, Safety, and Patient Management: Second Edition</para>
    <para><emphasis role="bold">Frank G. Shellock, Ph.D. - Editor</emphasis></para>
    <para><emphasis role="italics">Director of MRI Safety, USC Stevens Neuroimaging and Informatics Institute</emphasis></para>
    <para><emphasis role="italics">Adjunct Clinical Professor of Radiology and Medicine, Keck School of Medicine, University of Southern California, Los Angeles, CA</emphasis></para>
    <para><emphasis role="italics">President, Shellock R &amp; D Services, Inc., Playa Del Rey, CA</emphasis></para>
    <para><emphasis role="bold">John V. Crues, III, M.D. - Editor</emphasis></para>
    <para><emphasis role="italics">Medical Director, Radnet, Inc., Los Angeles, CA</emphasis></para>
    <para><emphasis role="italics">Professor of Radiology, University of California, San Diego</emphasis></para>
    <para><emphasis role="bold">Alexandra M. Karacozoff, M.P.H. - Associate Editor</emphasis></para>
    <para><emphasis role="italics">Sacramento, California</emphasis></para>
    <para><emphasis role="bold">Biomedical Research Publishing Group, Los Angeles, CA</emphasis></para>
    <para>© 2022 by Biomedical Research Publishing Group and Shellock R &amp; D Services, Inc., Los Angeles, CA. All rights are reserved.</para>
    <para><emphasis role="bold">Library of Congress Cataloging-in-Publication Data</emphasis></para>
    <para>ISBN-13: 978-0-9891632-8-6</para>
    <para>ISBN-10: 0-9891632-8-8</para>
    <sect1 id="pr0001s01">
        <title>Disclaimer</title>
        <para>This textbook was designed to provide a reference for radiologists, MRI technologists, facility managers, MRI physicists, MRI researchers, engineers, and others. The information is current through the publication date of this textbook.</para>
        <para>The authors and publisher of this work disclaim any liability for the acts of any physician, individual, group, or entity acting independently or on behalf of any organization that utilizes information for a medical procedure, activity, service, or other situation through the use of this textbook.</para>
        <para>The authors and publisher disclaim responsibility for any injury and/or damage to persons or property from any of the methods, products, instructions, or ideas contained in this publication.</para>
    </sect1>'''
    
    pr0001_xml = create_preface_file('pr0001', 'Title and Copyright', pr0001_content)
    with open(OUTPUT_DIR / 'pr0001.xml', 'w', encoding='utf-8') as f:
        f.write(pr0001_xml)
    print("  Created: pr0001.xml (Title and Copyright)")
    
    # pr0002 - Preface
    pr0002_content = '''    <para>Since its introduction into clinical practice in the early 1980s, magnetic resonance imaging (MRI) has exhibited exceptional growth and created a paradigm shift in medicine. Not only has this imaging modality markedly expanded the roles of imaging in medical diagnoses, opening up vistas in neurological, musculoskeletal, oncological, cardiovascular and a variety of other diseases not accessible to prior imaging techniques, but it has also had a profound impact on our basic understanding of the pathophysiologic mechanisms of abnormal conditions and disease processes.</para>
    <para>The continuous growth of MRI has led to an explosion in the number of patients, healthcare professionals, and other individuals exposed to the powerful static magnetic fields, rapidly changing magnetic fields, and intense radiofrequency fields used during the procedures. Numerous investigations have been performed during the past 35+ years in an effort to characterize the bioeffects and safety aspects of MRI.</para>
    <para>The transformative impact of MRI on medicine continues to progress and advances in technology continue unabated. Whereas the highest magnetic field used in routine clinical imaging was 1.5-Tesla during most of the 1990s, 3-Tesla is currently the standard. Presently, a 7-Tesla scanner is approved for clinical use and research is routinely performed at 9.4-Tesla, 10.5- and an 11.7-Tesla MR system recently came on line to scan human subjects.</para>
    <para>Ultimately, MRI safety must begin with understanding the interactions of the electromagnetic fields used in MRI with biologic tissues. The issues concerning human safety in the MRI environment led us to enlist leading physicians and scientists around the world to collaborate on this textbook.</para>
    <para><emphasis role="bold">Frank G. Shellock</emphasis></para>
    <para><emphasis role="bold">John V. Crues, III</emphasis></para>'''
    
    pr0002_xml = create_preface_file('pr0002', 'Preface', pr0002_content)
    with open(OUTPUT_DIR / 'pr0002.xml', 'w', encoding='utf-8') as f:
        f.write(pr0002_xml)
    print("  Created: pr0002.xml (Preface)")
    
    # pr0003 - The Editors
    pr0003_content = '''    <sect1 id="pr0003s01">
        <title>Frank G. Shellock, Ph.D.</title>
        <figure>
            <title/>
            <mediaobject>
                <imageobject>
                    <imagedata fileref="Ch0000f01.png" width="100%" scalefit="1"/>
                </imageobject>
            </mediaobject>
        </figure>
        <para><emphasis role="bold">Frank G. Shellock, Ph.D.</emphasis> is a physiologist with more than 35 years of experience conducting laboratory and clinical investigations in the field of magnetic resonance imaging (MRI). He is the Director of MRI Safety at the USC Steven Neuroimaging and Informatics Institute and an Adjunct Clinical Professor of Radiology and Medicine at the Keck School of Medicine, University of Southern California.</para>
        <para>Dr. Shellock has authored or co-authored more than 260 publications in the peer-reviewed literature. He is a member and Fellow of the American College of Radiology, the International Society for Magnetic Resonance in Medicine, the American College of Cardiology, and the American College of Sportsmedicine.</para>
    </sect1>
    <sect1 id="pr0003s02">
        <title>John V. Crues, III, M.D., M.S.</title>
        <figure>
            <title/>
            <mediaobject>
                <imageobject>
                    <imagedata fileref="Ch0000f02.png" width="100%" scalefit="1"/>
                </imageobject>
            </mediaobject>
        </figure>
        <para><emphasis role="bold">John V. Crues, III, M.D., M.S.</emphasis> is a radiologist with more than 30 years experience in magnetic resonance imaging (MRI). He is the Medical Director and former MRI Fellowship Director for Radnet, Inc., the largest owner and operator of outpatient imaging centers in the United States.</para>
        <para>Dr. Crues has authored more than 100 papers in the medical literature, 13 textbooks and CDs, 27 book chapters, and over 100 abstracts. He is a past President of the International Society for Magnetic Resonance in Medicine (ISMRM).</para>
    </sect1>'''
    
    pr0003_xml = create_preface_file('pr0003', 'The Editors', pr0003_content)
    with open(OUTPUT_DIR / 'pr0003.xml', 'w', encoding='utf-8') as f:
        f.write(pr0003_xml)
    print("  Created: pr0003.xml (The Editors)")
    
    # pr0004 - Contributors
    pr0004_content = '''    <para><emphasis role="bold">Louai Al-Dayeh, M.D., Ph.D.</emphasis> - Research and Development Fellow, Boston Scientific Neuromodulation Corporation, Valencia, CA</para>
    <para><emphasis role="bold">Gregory Brown, Ph.D., FSMRT</emphasis> - Lecturer in Medical Radiations, University of South Australia, Adelaide, Australia</para>
    <para><emphasis role="bold">Giovanni Calcagnini, Ph.D., EEng.</emphasis> - Lead Researcher, Italian National Institute of Health, Rome, Italy</para>
    <para><emphasis role="bold">Patrick M. Colletti, M.D.</emphasis> - Professor of Radiology, Keck School of Medicine of USC, Los Angeles, CA</para>
    <para><emphasis role="bold">John V. Crues, III, M.D., FACR</emphasis> - Medical Director, Radnet, Inc., Los Angeles, CA</para>
    <para><emphasis role="bold">Heidi A. Edmonson, Ph.D.</emphasis> - Medical Physicist, Mayo Clinic, Rochester, MN</para>
    <para><emphasis role="bold">Laura Foster, J.D., M.P.H.</emphasis> - Senior Vice President, Radnet, Inc., Los Angeles, CA</para>
    <para><emphasis role="bold">Henry Halperin, M.D., M.A., FHRA, FAHA</emphasis> - Professor of Medicine, Johns Hopkins Hospital, Baltimore, MD</para>
    <para><emphasis role="bold">Bernd Ittermann, Ph.D.</emphasis> - Head of Biomedical Magnetic Resonance Department, PTB, Germany</para>
    <para><emphasis role="bold">Wolfgang Kainz, Ph.D.</emphasis> - Research Biomedical Engineer, FDA, Silver Spring, MD</para>
    <para><emphasis role="bold">Alayar Kangarlu, Ph.D.</emphasis> - Director of MRI Physics, Columbia University, New York, NY</para>
    <para><emphasis role="bold">Stephen F. Keevil, Ph.D.</emphasis> - Head of Medical Physics, King's College London, United Kingdom</para>
    <para><emphasis role="bold">Oliver Kraff, Ph.D.</emphasis> - Erwin L. Hahn Institute for MR Imaging, University of Duisburg-Essen, Germany</para>
    <para><emphasis role="bold">Bruno Madore, Ph.D.</emphasis> - Brigham and Women's Hospital, Harvard Medical School, Boston, MA</para>
    <para><emphasis role="bold">Mark McJury, Ph.D.</emphasis> - Consultant Clinical Scientist, Glasgow, Scotland, United Kingdom</para>
    <para><emphasis role="bold">Donald W. McRobbie, Ph.D.</emphasis> - University of Adelaide, Adelaide, Australia</para>
    <para><emphasis role="bold">Moriel NessAiver, Ph.D.</emphasis> - President, Simply Physics, Baltimore, MD</para>
    <para><emphasis role="bold">John Nyenhuis, Ph.D.</emphasis> - Professor Emeritus, Purdue University, West Lafayette, IN</para>
    <para><emphasis role="bold">Lawrence P. Panych, Ph.D.</emphasis> - University of Western Ontario, Ontario, Canada</para>
    <para><emphasis role="bold">Harald H. Quick, Ph.D.</emphasis> - University Hospital Essen, Essen, Germany</para>
    <para><emphasis role="bold">Daniel J. Schaefer, Ph.D.</emphasis> - Duke University, Durham, NC</para>
    <para><emphasis role="bold">Frank G. Shellock, Ph.D., FACR, FACC, FISMRM</emphasis> - Director of MRI Safety, USC, Los Angeles, CA</para>
    <para><emphasis role="bold">Alberto Spinazzi, M.D.</emphasis> - Chief Medical Officer, Bracco Group, Monroe, NJ</para>
    <para><emphasis role="bold">Robert E. Watson, Jr. M.D., Ph.D.</emphasis> - Neuroradiologist, Mayo Clinic, Rochester, MN</para>
    <para><emphasis role="bold">Lukas Winter, Ph.D.</emphasis> - MR Technology Scientist, PTB, Germany</para>'''
    
    pr0004_xml = create_preface_file('pr0004', 'Contributors', pr0004_content)
    with open(OUTPUT_DIR / 'pr0004.xml', 'w', encoding='utf-8') as f:
        f.write(pr0004_xml)
    print("  Created: pr0004.xml (Contributors)")
    
    # pr0005 - Dedications
    pr0005_content = '''    <para>This textbook is dedicated to my dear wife, Jaana, for her never ending understanding, support, and devotion that allowed me to expend considerable time on this meaningful undertaking.</para>
    <para><emphasis role="bold">Frank G. Shellock, Ph.D.</emphasis></para>
    <para>I dedicate this textbook to my wife, Melinda, whose support has been instrumental in allowing me to dedicate my time to this important effort. I also dedicate this project to Radnet, a company whose environment has provided me with tolerance and support for time spent in this important endeavor and my involvement in MRI practice, teaching, and research.</para>
    <para><emphasis role="bold">John V. Crues, M.D., III</emphasis></para>'''
    
    pr0005_xml = create_preface_file('pr0005', 'Dedications', pr0005_content)
    with open(OUTPUT_DIR / 'pr0005.xml', 'w', encoding='utf-8') as f:
        f.write(pr0005_xml)
    print("  Created: pr0005.xml (Dedications)")
    
    # pr0006 - Acknowledgments
    pr0006_content = '''    <para>We are indebted to Alexandra M. Karacozoff, the Associate Editor, for her exceptional editing and proofreading abilities, as well as her other important contributions to this textbook.</para>
    <para>We are grateful to Crystal Newton and Anastasios Karatopis for their amazing artistic talents that resulted in the creation of an extraordinary cover.</para>
    <para>Special thanks to Mark Bass for his extensive experience and great efforts that helped make this textbook possible by taking care of the overall production of this project and providing careful attention to an incredible list of details.</para>'''
    
    pr0006_xml = create_preface_file('pr0006', 'Acknowledgments', pr0006_content)
    with open(OUTPUT_DIR / 'pr0006.xml', 'w', encoding='utf-8') as f:
        f.write(pr0006_xml)
    print("  Created: pr0006.xml (Acknowledgments)")
    
    # Create toc.xml
    toc_xml = '''<?xml version="1.0" encoding="UTF-8"?>

<toc id="toc">
    <title>Table of Contents</title>
    <tocfront>
        <tocentry><ulink url="pr0001.xml">Title and Copyright</ulink></tocentry>
        <tocentry><ulink url="pr0002.xml">Preface</ulink></tocentry>
        <tocentry><ulink url="pr0003.xml">The Editors</ulink></tocentry>
        <tocentry><ulink url="pr0004.xml">Contributors</ulink></tocentry>
        <tocentry><ulink url="pr0005.xml">Dedications</ulink></tocentry>
        <tocentry><ulink url="pr0006.xml">Acknowledgments</ulink></tocentry>
    </tocfront>
    <tocchap><tocentry><ulink url="ch0001.xml">Chapter 1 - Basic MRI Physics: Implications for MRI Safety</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0002.xml">Chapter 2 - Principals of MRI Safety Physics</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0003.xml">Chapter 3 - MRI Physics and Safety at 7 Tesla</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0004.xml">Chapter 4 - Bioeffects of Static Magnetic Fields</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0005.xml">Chapter 5 - Bioeffects of Gradient Magnetic Fields</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0006.xml">Chapter 6 - Acoustic Noise and MRI Procedures</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0007.xml">Chapter 7 - Bioeffects of Radiofrequency Power Deposition</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0008.xml">Chapter 8 - Radiofrequency-Energy Induced Heating During MRI</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0009.xml">Chapter 9 - Thermal Effects Associated with RF Exposures During Clinical MRI</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0010.xml">Chapter 10 - Claustrophobia, Anxiety, and Emotional Distress in the MRI Environment</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0011.xml">Chapter 11 - MRI Procedures and Pregnancy</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0012.xml">Chapter 12 - Identification and Management of Acute Reactions to Gadolinium-Based Contrast Agents</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0013.xml">Chapter 13 - MRI Contrast Agents and Nephrogenic Systemic Fibrosis</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0014.xml">Chapter 14 - Gadolinium Retention in Brain and Body Tissues</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0015.xml">Chapter 15 - MRI Screening for Patients and Individuals</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0016.xml">Chapter 16 - Using Ferromagnetic Detection Systems in the MRI Environment</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0017.xml">Chapter 17 - Physiological Monitoring of Patients During MRI</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0018.xml">Chapter 18 - MRI Issues for Implants and Devices</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0019.xml">Chapter 19 - Active Implanted Medical Devices: An Overview of MRI Safety Considerations</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0020.xml">Chapter 20 - MRI-Related Heating of Implants and Devices</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0021.xml">Chapter 21 - MRI Test Methods for MR Conditional Active Implantable Medical Devices</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0022.xml">Chapter 22 - Using MRI Simulations and Measurements to Evaluate Heating of Active Implants</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0023.xml">Chapter 23 - The Role of Numerical Modeling and Simulations to Evaluate Implantable Leads</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0024.xml">Chapter 24 - Performing MRI In Patients with Conventional Cardiac Devices</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0025.xml">Chapter 25 - MRI and Patients with Cardiac Implantable Electronic Devices</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0026.xml">Chapter 26 - Neuromodulation Systems: MRI Safety Issues</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0027.xml">Chapter 27 - MRI Safety Policies and Procedures for a Hospital or Medical Center Setting</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0028.xml">Chapter 28 - MRI Safety Policies and Procedures for an Outpatient Facility</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0029.xml">Chapter 29 - MRI Safety Policies and Procedures for a Children's Hospital</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0030.xml">Chapter 30 - MRI Safety Policies and Procedures for a Research Facility</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0031.xml">Chapter 31 - Safety Issues for Interventional MR Systems</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0032.xml">Chapter 32 - Occupational Exposure During MRI</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0033.xml">Chapter 33 - MRI Standards and Guidance Documents from the United States FDA</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0034.xml">Chapter 34 - MRI Standards and Safety Guidelines in Europe</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0035.xml">Chapter 35 - MRI Standards and Safety Guidelines in Canada</ulink></tocentry></tocchap>
    <tocchap><tocentry><ulink url="ch0036.xml">Chapter 36 - MRI Standards and Safety Guidelines in Australia</ulink></tocentry></tocchap>
</toc>'''
    
    with open(OUTPUT_DIR / 'toc.xml', 'w', encoding='utf-8') as f:
        f.write(toc_xml)
    print("  Created: toc.xml (Table of Contents)")
    
    # Create new Book.xml
    book_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book PUBLIC "-//RIS Dev//DTD DocBook V4.3 -Based Variant V1.1//EN" "http://LOCALHOST/dtd/V1.1/RittDocBook.dtd" [
    <!ENTITY toc SYSTEM "toc.xml">
    <!ENTITY pr0001 SYSTEM "pr0001.xml">
    <!ENTITY pr0002 SYSTEM "pr0002.xml">
    <!ENTITY pr0003 SYSTEM "pr0003.xml">
    <!ENTITY pr0004 SYSTEM "pr0004.xml">
    <!ENTITY pr0005 SYSTEM "pr0005.xml">
    <!ENTITY pr0006 SYSTEM "pr0006.xml">
    <!ENTITY ch0001 SYSTEM "ch0001.xml">
    <!ENTITY ch0002 SYSTEM "ch0002.xml">
    <!ENTITY ch0003 SYSTEM "ch0003.xml">
    <!ENTITY ch0004 SYSTEM "ch0004.xml">
    <!ENTITY ch0005 SYSTEM "ch0005.xml">
    <!ENTITY ch0006 SYSTEM "ch0006.xml">
    <!ENTITY ch0007 SYSTEM "ch0007.xml">
    <!ENTITY ch0008 SYSTEM "ch0008.xml">
    <!ENTITY ch0009 SYSTEM "ch0009.xml">
    <!ENTITY ch0010 SYSTEM "ch0010.xml">
    <!ENTITY ch0011 SYSTEM "ch0011.xml">
    <!ENTITY ch0012 SYSTEM "ch0012.xml">
    <!ENTITY ch0013 SYSTEM "ch0013.xml">
    <!ENTITY ch0014 SYSTEM "ch0014.xml">
    <!ENTITY ch0015 SYSTEM "ch0015.xml">
    <!ENTITY ch0016 SYSTEM "ch0016.xml">
    <!ENTITY ch0017 SYSTEM "ch0017.xml">
    <!ENTITY ch0018 SYSTEM "ch0018.xml">
    <!ENTITY ch0019 SYSTEM "ch0019.xml">
    <!ENTITY ch0020 SYSTEM "ch0020.xml">
    <!ENTITY ch0021 SYSTEM "ch0021.xml">
    <!ENTITY ch0022 SYSTEM "ch0022.xml">
    <!ENTITY ch0023 SYSTEM "ch0023.xml">
    <!ENTITY ch0024 SYSTEM "ch0024.xml">
    <!ENTITY ch0025 SYSTEM "ch0025.xml">
    <!ENTITY ch0026 SYSTEM "ch0026.xml">
    <!ENTITY ch0027 SYSTEM "ch0027.xml">
    <!ENTITY ch0028 SYSTEM "ch0028.xml">
    <!ENTITY ch0029 SYSTEM "ch0029.xml">
    <!ENTITY ch0030 SYSTEM "ch0030.xml">
    <!ENTITY ch0031 SYSTEM "ch0031.xml">
    <!ENTITY ch0032 SYSTEM "ch0032.xml">
    <!ENTITY ch0033 SYSTEM "ch0033.xml">
    <!ENTITY ch0034 SYSTEM "ch0034.xml">
    <!ENTITY ch0035 SYSTEM "ch0035.xml">
    <!ENTITY ch0036 SYSTEM "ch0036.xml">
]>

<book id="mri-bioeffects-safety" lang="en">
    <bookinfo>
        <isbn>978-0-9891632-8-6</isbn>
        <title>MRI Bioeffects, Safety, and Patient Management</title>
        <subtitle>Second Edition</subtitle>
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
    
    &toc;
    
    &pr0001;
    &pr0002;
    &pr0003;
    &pr0004;
    &pr0005;
    &pr0006;
    
    &ch0001;
    &ch0002;
    &ch0003;
    &ch0004;
    &ch0005;
    &ch0006;
    &ch0007;
    &ch0008;
    &ch0009;
    &ch0010;
    &ch0011;
    &ch0012;
    &ch0013;
    &ch0014;
    &ch0015;
    &ch0016;
    &ch0017;
    &ch0018;
    &ch0019;
    &ch0020;
    &ch0021;
    &ch0022;
    &ch0023;
    &ch0024;
    &ch0025;
    &ch0026;
    &ch0027;
    &ch0028;
    &ch0029;
    &ch0030;
    &ch0031;
    &ch0032;
    &ch0033;
    &ch0034;
    &ch0035;
    &ch0036;
</book>'''
    
    # Remove old Book.XML and create new Book.xml
    old_book = OUTPUT_DIR / 'Book.XML'
    if old_book.exists():
        old_book.unlink()
    
    with open(OUTPUT_DIR / 'Book.xml', 'w', encoding='utf-8') as f:
        f.write(book_xml)
    print("  Created: Book.xml (Main file with entity references)")
    
    # Remove old frontmatter.xml
    if frontmatter_path.exists():
        frontmatter_path.unlink()
    print("  Removed: frontmatter.xml (content split into pr0001-pr0006)")
    
    # Summary
    print("\n" + "=" * 70)
    print("FINAL STRUCTURE")
    print("=" * 70)
    print("""
final_output_tables/
├── Book.xml                 ← Main file with entity references
├── toc.xml                  ← Table of Contents
│
├── pr0001.xml               ← Title and Copyright
├── pr0002.xml               ← Preface
├── pr0003.xml               ← The Editors
├── pr0004.xml               ← Contributors
├── pr0005.xml               ← Dedications
├── pr0006.xml               ← Acknowledgments
│
├── ch0001.xml               ← Chapter 1
├── ch0002.xml               ← Chapter 2
├── ...                      ← Chapters 3-35
├── ch0036.xml               ← Chapter 36
│
└── multimedia/              ← Images (Ch####f##.png)
""")


if __name__ == '__main__':
    main()
