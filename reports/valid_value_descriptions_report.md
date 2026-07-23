# Controlled Vocabulary Description & Ontology Backfill Report

This report tracks every valid-value term whose `Description` and/or
`Ontology Identifier`/`Ontology Url`/`NCIt Code` was populated by this pass,
separate from any `*_decisions.json` worklist format used by prior OLS
annotation work. It is a running log, updated as each batch of CV files is
processed across multiple turns.

## Scope

**Explicitly excluded** (per user instruction + follow-up scoping):
- `shared/therapeuticAgent.csv` (4,475 terms — explicitly out of scope)
- Administrative/identifier lists with no real ontology equivalent:
  `grant/grant_number.csv`, `grant/grant_type.csv`,
  `institution/institution_alias.csv`, `institution/institution_name.csv`,
  `institution/institution_location_state.csv`,
  `consortium/consortium_name.csv`, `consortium/consortium_funding_agency.csv`,
  `theme/theme_name.csv`, `shared/sourceGeography.csv`,
  `shared/studyLicense.csv`, `shared/dataPermission.csv`, `shared/dataTier.csv`,
  `shared/boolean.csv`,
  `tool/tool_accessibility.csv`, `tool/tool_cost.csv`,
  `tool/tool_documentation_type.csv`, `tool/tool_download_type.csv`,
  `tool/tool_license.csv`, `tool/tool_link_type.csv`,
  `tool/tool_operating_system.csv`, `tool/tool_type.csv`,
  `tool/entity_role.csv`, `tool/entity_type.csv`,
  `person/chair_roles.csv`, `person/consent_for_portal_display.csv`,
  `person/portal_display.csv`, `person/working_group_participation.csv`,
  `project/project_type.csv`

  **Judgment call flagged for review:** `tool/tool_format.csv`,
  `tool/tool_data.csv`, `tool/tool_operation.csv`, `tool/tool_topic.csv`, and
  `tool/tool_language.csv` were kept **in scope** despite living in the same
  "tool" module as several excluded files, because they describe genuine
  bioinformatics/software concepts with real ontology coverage (EDAM
  ontology's Operation/Topic/Data/Format branches), not MC2-specific
  identifiers. Say the word if you'd rather these were excluded too.

**In scope:** 65 files, ~4,850 missing descriptions (see per-batch tables
below for the authoritative per-file list).

## Ontology selection

NCIT is the default first choice (it's the most comprehensive single
ontology for cancer/clinical vocabulary and is what's already used
throughout this model), but it is not the only valid source. Other
ontologies are used when they fit better, e.g.: BAO (BioAssay Ontology) for
antibody roles/assay methods, OBI (Ontology for Biomedical Investigations)
and FBBI (biological imaging methods) for assay/imaging techniques, EDAM
for bioinformatics data/format/operation/topic concepts, DUO (Data Use
Ontology) for data-use codes. `Ontology Identifier` records whichever
ontology's CURIE actually matched (e.g. `BAO:0002643`, not just NCIT); `NCIt
Code` is only populated when the match is specifically from NCIT.

## Confidence rubric

- **High** — Direct OLS match: the term's label (or an unambiguous synonym)
  matches an OLS class, and its definition is used directly or lightly
  adapted.
- **Medium** — Partial/conceptual OLS match: a related or broader/narrower
  OLS class was found and its definition adapted to fit this specific term,
  or the match required some interpretive judgment.
- **Low** — No usable OLS match found; description written by inference from
  similar terms in the same list or general domain knowledge, not grounded
  in any specific ontology record.

## Log

<!-- Entries appended per batch below. Columns: File | Term | Description source | Ontology match | Confidence -->

### Batch 1a (manually processed before switching to Agent delegation)

| File | Term | Description source | Ontology match | Confidence |
|---|---|---|---|---|
| file/eventType.csv | Enrollment | OLS: NCIT "Enrollment" | NCIT:C37948 | Medium |
| imagingLevel3Segments/objectClass.csv | Spot | Inferred from imaging/spatial-omics domain usage; no OLS match found | None | Low |
| imagingLevel4/summaryStat.csv | Not Specified | Inferred, matches sibling "Not Reported"/"Not Specified" boilerplate pattern; no OLS match found | None | Low |
| individual/metStage.csv | cM0 (i+) | OLS: NCIT "cM0 (i+) TNM Finding" (exact match) | NCIT:C95956 | High |
| individual/recurrence.csv | Not Allowed to Collect | OLS: NCIT "Not Allowed To Collect" (exact match) | NCIT:C141478 | High |
| shared/treatmentOutcome.csv | No Response | OLS: NCIT "No Response to Treatment" | NCIT:C162704 | High |
| biospecimen/preservation.csv | Negative 80 Deg C | Inferred, analogous to sibling "Liquid Nitrogen" entry pattern; no OLS match found | None | Low |
| biospecimen/preservation.csv | Methacarn fixed paraffin embedded - MFPE | Inferred, analogous to sibling "Formalin fixed paraffin embedded - FFPE" entry; no OLS match found | None | Medium |
| biospecimen/specimenComp.csv | Normal distant | Inferred, directly analogous to sibling "Normal adjacent" entry's definition | None | Medium |
| biospecimen/specimenComp.csv | Tumor specimen from de novo untreated malignancy of the bladder | Inferred from the term's own wording; no OLS match found | None | Low |
| imagingChannel/abRole.csv | Primary | OLS: BAO (BioAssay Ontology) "primary antibody" (exact match) | BAO:0002643 | High |
| imagingChannel/abRole.csv | Secondary | OLS: BAO "secondary antibody" (exact match) | BAO:0002644 | High |
| publication/publication_accessibility.csv | Open Access | Inferred, standard definition; no OLS match found | None | Low |
| publication/publication_accessibility.csv | Restricted Access | Inferred, standard definition; no OLS match found | None | Low |
| shared/biologicalSex.csv | None of these describe me | Inferred, analogous to sibling "Decline to answer"/"Prefer not to answer" entries | None | Medium |
| shared/biologicalSex.csv | X | Inferred from common usage; no OLS match found | None | Low |
| shared/tumorGrade.csv | Intermediate Grade | Inferred, directly analogous to sibling "High Grade"/G1-G4 entries in same file | None | Medium |
| shared/tumorGrade.csv | Low Grade | Inferred, directly analogous to sibling entries in same file | None | Medium |
| visiumRNALevel1/spatialReads.csv | cDNA | OLS: NCIT "cDNA" (exact match) | NCIT:C324 | High |
| visiumRNALevel1/spatialReads.csv | Spatial Barcode and UMI | Inferred from standard 10x Genomics spatial sequencing terminology; no OLS match found | None | Medium |
| biospecimen/acquisitionMethod.csv | Not specified | Inferred, matches sibling boilerplate pattern; no OLS match found | None | Low |
| biospecimen/acquisitionMethod.csv | Other | Reused from sibling "Other" rows elsewhere in the model (same NCIT code already used consistently across many files) | NCIT:C17649 | High |
| biospecimen/acquisitionMethod.csv | Re-excision | OLS: NCIT "Re-Excision" (exact match) | NCIT:C48600 | High |
| biospecimen/fixative.csv | Diimidoester | OLS: NCIT "Diimidoester" (exact match) | NCIT:C185112 | High |
| biospecimen/fixative.csv | Methacarn | Inferred from known histology/chemistry domain knowledge, analogous to sibling "Carnoy's Solution" entry; no OLS match found | None | Medium |
| biospecimen/fixative.csv | Poloxamer | Inferred from known chemistry domain knowledge; no OLS match found | None | Low |

### Batch 1b - shared/duo.csv (24 terms)

Not an OLS-matching task: the `Attribute` value for each row already *is* a
DUO ontology ID (e.g. `DUO:0000042`), so Ontology Identifier/Url were filled
in mechanically (`http://purl.obolibrary.org/obo/DUO_<number>`). All 24
`DUO:xxxx` rows — High confidence (the ID is definitionally correct, not a
similarity match). The 7 `DUOPlus1`-`DUOPlus7` rows are MC2-specific
governance extensions with no real DUO backing and remain unmapped (None).

### Wave 1 — Agent: sequencing small files (3 files)

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| sequencingLevel3/matrixType.csv | Raw Counts | The unprocessed matrix of read or fragment counts per feature (e.g., gene or transcript) per cell or sample, prior to any normalization, scaling, or batch correction. | EDAM:data_3917 | Medium | OLS found EDAM "Count matrix"; definition adapted. |
| sequencingLevel3/matrixType.csv | Normalized Counts | A matrix of feature counts adjusted (e.g. for sequencing depth or library size) to enable comparison across cells/samples. | None | Medium | No unambiguous OLS match; inferred from standard genomics domain knowledge. |
| sequencingLevel3/matrixType.csv | Scaled Counts | A matrix of counts further transformed (e.g. centered/scaled to unit variance) after normalization, typically used as input for dimensionality reduction or clustering. | None | Medium | No OLS match; inferred from standard scRNA-seq analysis conventions. |
| sequencingLevel3/matrixType.csv | Batch Corrected Counts | A matrix of counts adjusted to remove technical variation between sequencing batches/runs while preserving biological signal. | None | Medium | No OLS match; inferred from standard batch-effect-correction domain knowledge. |
| sequencingLevel1/readIndicator.csv | R1 | The read direction identified as number 1 in a paired-end nucleotide sequencing reaction. | NCIT:C172301 | High | Exact NCIT "Read Pair 1" match. |
| sequencingLevel1/readIndicator.csv | R2 | The read direction identified as number 2 in a paired-end nucleotide sequencing reaction. | NCIT:C172302 | High | Exact NCIT "Read Pair 2" match. |
| sequencingLevel1/readIndicator.csv | R1&R2 | Indicates that both Read 1 and Read 2, the forward and reverse reads of a paired-end sequencing reaction, are represented or applicable. | None | Medium | No OLS class for combined value; analogized from R1/R2 sibling rows. |
| sequencingLevel1/readIndicator.csv | I1 | The first index read in a sequencing run, used to identify the sample-specific barcode (e.g. i7 index) for demultiplexing pooled libraries. | None | Medium | No direct OLS match; standard Illumina/NGS domain knowledge. |
| sequencingLevel1/librarySourceMaterial.csv | Bulk Cells | A biospecimen consisting of multiple cells intended to be analyzed as a pool. | NCIT:C178223 | High | Exact NCIT "Bulk Cell Specimen" match (sibling of already-mapped Single-cells/Single-nuclei). |
| sequencingLevel1/librarySourceMaterial.csv | Bulk Tissue | A biospecimen either derived from a whole tissue specimen or tissue section, which may consist of heterogeneous cells or tissues. | NCIT:C178225 | High | Exact NCIT "Bulk Tissue Specimen" match. |
| sequencingLevel1/librarySourceMaterial.csv | Bulk Nuclei | A biospecimen consisting of multiple nuclei intended to be analyzed as a pool. | NCIT:C178224 | High | Exact NCIT "Bulk Nucleus Specimen" match. |

### Wave 1 — Agent: shared clinical small files (4 files)

**⚠ Data-quality bug found (not fixed here, out of scope):** `modules/individual/lymphStage.csv`
is mapped in `mapping.yaml` to the **Individual Tumor Lymph Node Stage** attribute, but its actual
row content is a duplicate of `biospecimen/specimenComp.csv`'s Biospecimen-Composition
tumor-tissue-type vocabulary (Additional Primary, Normal distant, Tissue, Tumor specimen from de
novo untreated malignancy of the bladder, etc.) — not real AJCC N0/N1/N2/N3/NX lymph-node stage
codes. The agent annotated the file's *actual* content as found (matching the equivalent
`specimenComp.csv` terms) rather than guessing real N-stage descriptions for a mismatched file.
Flagging here for a separate follow-up fix (attribute needs either the correct valid-value source
file or a corrected `mapping.yaml` entry).

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| shared/deIdMethod.csv | Manual | Of or related to the hands; reference to a method, process, task, or activity being done by hand (as opposed to being performed with the assistance of automation or other supportive means). | NCIT:C63513 | High | Exact label match "Manual" in NCIT. |
| shared/deIdMethod.csv | Semiautomatic | Of or related to a method or process performed using a combination of manual and automatic means. | NCIT:C172484 | High | Matches NCIT "Semi-Automatic", unambiguous spelling variant. |
| shared/deIdMethod.csv | Automatic | Operating with minimal human intervention; independent of external control. | NCIT:C70669 | High | Exact label match. |
| shared/deIdMethod.csv | Not Applicable | Determination of a value is not relevant in the current context. | NCIT:C48660 | High | Exact label match, consistent with same code used elsewhere in the model. |
| study/indexDate.csv | Diagnosis Date | The date on which a diagnosis of disease was made. | NCIT:C164339 | High | Matches NCIT "Date of Diagnosis", same concept reordered. |
| study/indexDate.csv | Enrollment Date | The date a subject is formally enrolled in a study. | NCIT:C222473 | Medium | Closest match is NCIT "Study Subject Enrolled Date"; label not identical but same concept. |
| study/indexDate.csv | Collection Date | The date on which the sample or data was collected. | NCIT:C81286 | High | Exact label match. |
| study/indexDate.csv | Birth Date | The calendar date on which a person was born. | NCIT:C68615 | High | Exact label match. |
| shared/diseaseStatus.csv | Biochemical evidence of disease without structural correlate | An indication that biochemical markers of a disease are present but morphological markers are absent. | NCIT:C165197 | High | Exact label match. |
| shared/diseaseStatus.csv | With Tumor | There is evidence of a tumor in an individual. | NCIT:C156849 | High | Exact label match; complementary code to existing "Tumor Free" (C156848) row. |
| shared/diseaseStatus.csv | Not Allowed To Collect | An indication that specifies that a collection event was not permitted. | NCIT:C141478 | High | Exact label match. |
| shared/diseaseStatus.csv | Distant Metastasis | The presence of cancer cells that have spread from the primary tumor site and been detected at a distal anatomic site. | NCIT:C18206 | Medium | Label matches exactly but NCIT class models the biological process rather than a disease-status finding; definition adapted to status context. |
| shared/diseaseStatus.csv | Regional Disease | A disease or condition that extends beyond the site of origin and spreads into adjacent tissues and regional lymph nodes. | NCIT:C41844 | High | Exact label match, same "Disease Extent by Site or System" family as existing "Localized Disease" row. |
| individual/lymphStage.csv | Additional Primary | A biospecimen derived from a new, independent primary tumor arising in a patient who has a history of a prior, unrelated primary cancer. | None | Low | No OLS match found for this GDC/TCGA tumor_tissue_type value; inferred from term wording and sibling rows. See data-quality note above. |
| individual/lymphStage.csv | Normal distant | A specimen comprised of morphologically normal tissue collected from a site distant from the tumor in an experimental subject. | None | Medium | No direct OLS hit; adapted from sibling row "Normal adjacent" (NCIT:C164032) definition pattern. See data-quality note above. |
| individual/lymphStage.csv | Tissue | A biospecimen consisting of similarly specialized cells and intercellular matrix, used here to denote a tissue sample not otherwise classified by tumor status. | NCIT:C12801 | Medium | Exact label match but NCIT class defines the generic anatomical concept; description adapted to this enum's tumor-status catch-all usage. See data-quality note above. |
| individual/lymphStage.csv | Tumor specimen from de novo untreated malignancy of the bladder | A tumor tissue specimen derived from a newly diagnosed, treatment-naive primary malignancy of the bladder that has not received prior therapy. | None | Low | No OLS match found; inferred purely from the term's own wording. See data-quality note above. |

### Wave 1 — Agent: education medium files (2 files)

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| education/ed_accessibility.csv | Alternative Text | A text alternative provided for non-text content (such as images), allowing assistive technologies like screen readers to convey the content's meaning to users who cannot see it. | None | Medium | Self-explanatory W3C/WCAG accessibility term; no matching OLS class found. |
| education/ed_accessibility.csv | Audio Description | An additional narration track that describes important visual information in video content (actions, scenes, on-screen text) for users who are blind or have low vision. | None | Medium | No matching OLS class; standard accessibility terminology. |
| education/ed_accessibility.csv | Braille | Indicates the resource, or a version of it, is available in Braille, a tactile writing system that enables reading by touch for people who are blind or have low vision. | None | Medium | OLS hits were clinical/geographic, not the accessibility-format concept. |
| education/ed_accessibility.csv | Captions | A synchronized, on-screen text display of spoken dialogue and other audio content within a video, providing an optional transcript of the audio for viewers who are deaf or hard of hearing. | NCIT:C185118 | Medium | Adapted from NCIT "Closed Captioning", closest related OLS class. |
| education/ed_accessibility.csv | ChemML | An XML-based markup format (analogous to Chemical Markup Language) used to encode chemical formulas and notation in an accessible, machine-readable form for assistive technologies. | EDAM:format_4023 | Medium | EDAM "cml" is the closest real ontology analog; exact term "ChemML" not found. |
| education/ed_accessibility.csv | Described Math | A text-based or audio description of mathematical notation and expressions, provided as an alternative to visual math formulas for users who use screen readers or other assistive technology. | None | Medium | No matching OLS class; plain-meaning description. |
| education/ed_accessibility.csv | Display Transformability | Indicates that the resource's visual presentation (e.g., text size, color, spacing, layout) can be modified or resized by the user without loss of content or functionality, supporting users with low vision or reading disabilities. | None | Medium | No relevant OLS class found; standard WCAG concept. |
| education/ed_accessibility.csv | Haptic | Indicates that the resource provides touch-based (haptic) feedback, such as vibration, force, or tactile cues, as an alternative or supplement to visual or auditory information. | MESH:D000089862 | Medium | Adapted from MeSH "Haptic Technology". |
| education/ed_accessibility.csv | High Contrast | Indicates that a high-contrast display option (e.g., strongly differentiated foreground/background colors) is available to improve readability for users with low vision. | None | Medium | Top OLS hit was a biological organism-color-pattern quality, domain mismatch. |
| education/ed_accessibility.csv | Large Print | Indicates that the resource, or a version of it, is available in a large-print format with enlarged text to improve readability for users with low vision. | None | Medium | Closest OLS hit had no definition text and a clinical-labeling context. |
| education/ed_accessibility.csv | Latex | Indicates that mathematical or scientific content is encoded using LaTeX, a document preparation and markup system, allowing accessible rendering of complex notation. | SWO:3000025 | Medium | SWO "tex" class describes the LaTeX document format. |
| education/ed_accessibility.csv | Long Description | A detailed textual description provided for complex non-text content (such as charts, graphs, or images) that cannot be adequately conveyed through brief alternative text alone. | None | Medium | OLS search returned zero results; plain W3C accessibility meaning. |
| education/ed_accessibility.csv | MathML | An XML-based markup language for describing mathematical notation and expressions, capturing both structure and content to enable accessible rendering of formulas in web documents. | NCIT:C71609 | High | NCIT "Mathematical Markup Language" is an exact conceptual match. |
| education/ed_accessibility.csv | Nemeth Braille | A specialized Braille code used to represent mathematical and scientific notation, enabling readers who are blind or have low vision to access complex math content. | None | Medium | OLS search returned zero results; established meaning of the Nemeth Braille code. |
| education/ed_accessibility.csv | Sign Language | A system of hand gestures, facial expressions, and body movements used for communication, provided here as a video-based interpretation of content for users who are deaf or hard of hearing. | NCIT:C51278 | High | Exact label match with a directly usable definition. |
| education/ed_accessibility.csv | Structural Navigation | Indicates that the resource is structured with navigational markup (such as headings, landmarks, or lists) that allows assistive technology users to move efficiently between sections of content. | None | Medium | OLS search returned zero results; standard WCAG accessibility concept. |
| education/ed_accessibility.csv | Tactile Graphics | Raised or textured versions of images, diagrams, or graphics that can be explored by touch, enabling users who are blind or have low vision to perceive visual information. | None | Medium | OLS search returned zero relevant hits. |
| education/ed_accessibility.csv | Text Transcript | A full text version of the spoken and relevant non-speech audio content of a media resource, allowing users to read the content instead of, or in addition to, listening to it. | None | Medium | No matching OLS class found among top hits. |
| education/ed_activity_type.csv | Activity/Lab | A hands-on exercise or laboratory-based activity in which learners actively perform tasks, experiments, or procedures to apply and reinforce concepts. | None | Medium | Top OLS hits were unrelated SNOMED occupational-ability findings. |
| education/ed_activity_type.csv | Assessment | A resource used to evaluate learner understanding or performance, such as a quiz, test, or other measurement of academic achievement. | MESH:D004521 | Medium | Adapted from MeSH "Educational Measurement". |
| education/ed_activity_type.csv | Case Study | A detailed, narrative-based educational resource examining a specific real-world example, scenario, or problem to illustrate concepts or promote analytical and critical-thinking skills. | None | Medium | NCIT "Case Study" label-exact but clinical-trial-specific definition; domain mismatch rejected. |
| education/ed_activity_type.csv | Data Set | A structured collection of related data records provided as an educational resource for analysis, exploration, or hands-on learning exercises. | NCIT:C47824 | High | Exact label match, generic directly usable definition. |
| education/ed_activity_type.csv | Diagram/Illustration | A visual representation, such as a diagram, chart, or illustration, used to depict concepts, structures, or processes for instructional purposes. | EVORAO:Image | Medium | EVORAO "Image" class explicitly covers "pictures, diagrams, or illustrations". |
| education/ed_activity_type.csv | Full Course | A complete, self-contained sequence of instructional materials and activities covering a full subject or curriculum, typically spanning a full academic term. | None | Medium | No relevant OLS class found. |
| education/ed_activity_type.csv | Game | An interactive, rule-based activity designed to engage learners and teach or reinforce concepts through play. | None | Medium | No relevant OLS class found. |
| education/ed_activity_type.csv | Homework/Assignment | Work or tasks assigned to learners for completion outside of the primary instructional setting, used to reinforce or extend learning. | NCIT:C89269 | High | NCIT "Homework" is a direct match with a usable definition. |
| education/ed_activity_type.csv | Interactive | A resource that requires active learner participation or response, such as a clickable simulation, interactive exercise, or dynamic multimedia element. | None | Medium | OLS search returned only unrelated protein-interaction database entries. |
| education/ed_activity_type.csv | Lecture | A recorded or transcribed instructional talk delivered to an audience or class, typically used to present or explain subject matter. | MESH:D019531 | High | Exact label match with a directly usable definition. |
| education/ed_activity_type.csv | Lecture Notes | Written notes, outlines, or summaries prepared for or derived from a lecture, used to supplement or review instructional content. | MESH:D019528 | High | MeSH "Lecture Note" (singular) is an unambiguous match. |
| education/ed_activity_type.csv | Lesson | A single, discrete unit of instruction focused on a specific topic or set of learning objectives. | None | Medium | No relevant OLS class found. |
| education/ed_activity_type.csv | Lesson Plan | A structured outline prepared by an instructor detailing the objectives, activities, materials, and assessment methods for a lesson. | None | Medium | No relevant OLS class found. |
| education/ed_activity_type.csv | Module | A self-contained segment of instructional content covering a specific topic, often combined with other modules to form a larger course or curriculum. | None | Medium | OLS search returned zero results. |
| education/ed_activity_type.csv | Primary Source | An original document, artifact, or firsthand record (such as a letter, dataset, or historical artifact) created at the time of the event or phenomenon under study, used as direct evidence for learning or research. | None | Medium | NCIT "Source Document Verification" domain-mismatched (clinical-trial data verification). |
| education/ed_activity_type.csv | Reading | A text-based resource, such as an article, excerpt, or book chapter, assigned for learners to read as part of instructional content. | None | Medium | OLS search returned zero relevant hits. |
| education/ed_activity_type.csv | Simulation | An interactive model or representation of a real-world process, system, or scenario that allows learners to explore and experiment in a controlled, simulated environment. | None | Medium | No relevant OLS class found. |
| education/ed_activity_type.csv | Student Guide | A resource providing learners with instructions, guidance, or supplementary information to support their use of a course or activity. | None | Medium | No relevant OLS class found. |
| education/ed_activity_type.csv | Syllabus | A document describing the material, structure, objectives, and requirements covered in a course. | schema:Syllabus | High | Schema.org "Syllabus" is an exact label match under LearningResource. |
| education/ed_activity_type.csv | Teaching/Learning Strategy | An instructional method, technique, or procedure used by educators to facilitate teaching or by learners to facilitate learning of new material. | OCCO:00000030 | Medium | OCCO "learning strategies" closely matches the concept. |
| education/ed_activity_type.csv | Textbook | A book intended for use in the study of a specific subject, providing a systematic presentation of its principles and essential knowledge. | MESH:D022923 | High | Exact label match with a directly usable definition. |
| education/ed_activity_type.csv | Unit of Study | A cohesive set of lessons or learning materials organized around a specific topic or theme, typically spanning several class sessions. | None | Medium | No relevant OLS class found. |

### Wave 1 — Agent: biospecimen/file small files (2 files)

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| biospecimen/embeddingMedium.csv | Carbowax | A trade name for polyethylene glycol (PEG), a water-soluble, wax-like polymer historically used as an embedding medium for light microscopy that allows sections to be stained without prior dewaxing. | NCIT:C762 | Medium | OLS surfaced PEG entries (Carbowax is PEG's trade name) but with no definition text, so description was written from general chemistry knowledge. |
| biospecimen/embeddingMedium.csv | Epoxy Resin (Araldite) | A class of thermosetting polymer resins (e.g., Araldite) formed by curing epoxide monomers with a hardener; used as a hard, transparent embedding medium for ultrathin sectioning in transmission electron microscopy. | None | Low | No generic "epoxy resin" NCIT class exists; top hits were narrow, unrelated carcinogenic epoxide compounds that would misrepresent the term. |
| biospecimen/embeddingMedium.csv | Agar embedding | Use of agar, a gelatinous polysaccharide extracted from red algae, as a supporting medium to consolidate small, fragmented, or friable tissue specimens prior to histological processing and sectioning. | MESH:D000362 | Medium | No usable NCIT hit for generic "Agar"; MeSH definition adapted to the histology embedding context. |
| biospecimen/embeddingMedium.csv | Celloidin media | A purified nitrocellulose (collodion) solution in ether and alcohol; historically used as an embedding medium for sectioning large, hard, or heterogeneous specimens (e.g., whole organs, decalcified bone) that are poorly suited to paraffin embedding. | MESH:D003101 | Medium | No NCIT match; "Celloidin" matched MeSH "Collodion" (a synonymous form), adapted to embedding-medium context. |
| biospecimen/embeddingMedium.csv | Gelatin | A translucent, colorless, water-soluble protein derived from collagen; used as an embedding medium for cryosectioning and to orient or support small, friable tissue specimens. | NCIT:C65802 | Medium | Exact label match but OLS entry had no definition text, so description was written independently. |
| biospecimen/embeddingMedium.csv | Other | Different than the one(s) previously specified or mentioned. | NCIT:C17649 | High | Exact label+definition match; established repo-wide mapping for "Other". |
| biospecimen/embeddingMedium.csv | None | No person or thing, nobody, not any. | NCIT:C41132 | High | Exact label+definition match, consistent with sibling "Unknown" row's general-qualifier style. |
| file/processLevel.csv | Level 1 | (existing description, unchanged) | NCIT:C142663 | Medium | NCIT "Raw Data" is a reasonable broader match for this pipeline-stage concept, though no exact ontology equivalent exists. |
| file/processLevel.csv | Level 2 | (existing description, unchanged) | None | Low | Only candidate, NCIT "Processed Data", is too broad/non-distinguishing to apply meaningfully — skipped per "don't force a weak match." |
| file/processLevel.csv | Level 3 | (existing description, unchanged) | None | Low | Same reasoning as Level 2. |
| file/processLevel.csv | Level 4 | (existing description, unchanged) | None | Low | Same reasoning as Level 2/3. |
| file/processLevel.csv | Auxiliary | (existing description, unchanged) | None | Low | No relevant OLS class; candidates were unrelated clinical-study/protein concepts. |
| file/processLevel.csv | Not Applicable | (existing description, unchanged) | NCIT:C48660 | High | Exact label+definition match, standard NCIT missing-value-reason qualifier. |
| file/processLevel.csv | Metadata | (existing description, unchanged) | NCIT:C52095 | High | Exact label+definition match, directly consistent with the row's existing description. |

### Wave 1 — Agent: education small files (3 files)

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| education/ed_hazard.csv | Flashing | Indicates the educational resource contains flashing or strobing visual effects that may pose a seizure risk for photosensitive users. | None | Medium | No OLS match relevant to the accessibility-hazard sense; inferred from term + "Resource Access Hazard" parent context (schema.org/EPUB vocabulary). |
| education/ed_hazard.csv | Motion | Indicates the educational resource contains motion effects (e.g., panning, zooming, or animated movement) that may cause discomfort or disorientation for motion-sensitive users. | None | Medium | NCIT "Motion" definition too generic/physical, would misrepresent the accessibility-hazard meaning. |
| education/ed_hazard.csv | Simulation | Indicates the educational resource contains simulated or virtual environments that may pose a hazard for users sensitive to simulated motion or visual effects. | None | Medium | Only unrelated EDAM/HP/MeSH hits found. |
| education/ed_hazard.csv | Sound | Indicates the educational resource contains audio content, including unexpected or startling sounds, that may pose a hazard for users with sound sensitivities. | None | Medium | Only unrelated MeSH/SNOMED hits found. |
| education/ed_intended_use.csv | Curriculum/Instruction | A structured course of study or instructional material intended for use in classroom teaching or curriculum-based instruction. | MESH:D003479 | Medium | MeSH "Curriculum" is a partial/related match, adapted since the term also covers "Instruction." |
| education/ed_intended_use.csv | Assessment | The process of evaluating or measuring the value, significance, or extent of a learner's knowledge, skills, or performance. | NCIT:C25217 | High | Exact label match; definition lightly adapted to educational context. |
| education/ed_intended_use.csv | Professional Development | Resources intended to support ongoing training, skill-building, or continuing education for professionals in a given field. | None | Medium | No usable OLS match found. |
| education/ed_intended_use.csv | Other | Different than the one(s) previously specified or mentioned. | NCIT:C17649 | High | Confirmed via OLS fetch; matches existing repo precedent for "Other". |
| education/ed_primary_audience.csv | Student | A person who is enrolled in an educational institution. | NCIT:C75561 | High | Exact label match, verbatim definition. |
| education/ed_primary_audience.csv | Teacher | One who instructs or educates others. | NCIT:C102873 | High | Exact label match, verbatim definition. |
| education/ed_primary_audience.csv | Administrator | An individual responsible for the operational, managerial, or administrative oversight of an educational institution or program. | SNOMED:84914008 | Medium | SNOMED "School administrator" is an unambiguous synonym but returned no definition text. |
| education/ed_primary_audience.csv | Parent | A mother or a father; an immediate progenitor. | NCIT:C42709 | High | Exact label match, verbatim definition. |
| education/ed_primary_audience.csv | Professor | A courtesy title for a teacher of the highest academic rank in a college or university. | NCIT:C69170 | High | Exact label match, verbatim definition. |
| education/ed_primary_audience.csv | General Audience | The broad general public, without restriction to a specific educational role, age group, or professional background. | None | Medium | No usable OLS match; self-evident from context. |
| education/ed_primary_audience.csv | Other | Different than the one(s) previously specified or mentioned. | NCIT:C17649 | High | Same NCIT:C17649 concept as other "Other" rows. |
| education/ed_level.csv | Preschool | An educational institution for children that precedes kindergarten. | NCIT:C147937 | High | Exact label match, verbatim definition. |
| education/ed_level.csv | Lower Primary | The earlier years of primary (elementary) education, typically encompassing the first few grades of primary school. | None | Medium | No OLS hit; inferred by analogy to sibling "Upper Primary"/"Preschool"/"High School" rows. |
| education/ed_level.csv | Upper Primary | The later years of primary (elementary) education, typically encompassing the grades preceding the transition to middle or secondary school. | None | Medium | Same reasoning as Lower Primary. |
| education/ed_level.csv | Middle School | The educational level between primary/elementary school and high school, typically covering grades 6 through 8. | None | Medium | SNOMED/NCIT hits not a clean fit; description self-evident from context. |
| education/ed_level.csv | High School | A secondary school that usually includes grades 9 through 12. | NCIT:C89278 | High | Exact label match, verbatim definition. |
| education/ed_level.csv | Community College / Lower Division | A two-year postsecondary institution offering associate degrees and lower-division (freshman and sophomore level) undergraduate coursework. | SNOMED:224870001 | Medium | SNOMED "Community college" matches part of the compound term but no definition text and doesn't cover "Lower Division." |
| education/ed_level.csv | College / Upper Division | A four-year postsecondary institution, or the upper-division (junior and senior level) undergraduate coursework within one. | None | Medium | No clean single-concept OLS match; inferred by analogy. |
| education/ed_level.csv | Graduate / Profession | Studies beyond the bachelor's degree at an institution having graduate or professional programs, undertaken to prepare for entrance into a specific field or to obtain a higher degree. | MESH:D004500 | Medium | MeSH "Education, Graduate" covers the "Graduate" half; adapted to also cover "/ Profession." |
| education/ed_level.csv | Career / Technical | Educational programs focused on career-specific or technical/vocational skills that prepare students for direct entry into a trade or occupation. | None | Medium | OLS hits were specific teacher-occupation classes, not the education-level concept itself. |
| education/ed_level.csv | Adult Education | Educational programs and instructional resources designed for adult learners pursuing education outside the traditional K-12 or college-age system. | SNOMED:161125007 | Medium | SNOMED exact label match but no definition text returned. |
| education/ed_primary_format.csv | Audio | A file representing sound recordings or audio tracks. | EVORAO:Audio | High | Exact label match, directly usable OLS definition. |
| education/ed_primary_format.csv | Braille/BNF | Content formatted in Braille or Braille-ready format (BRF) for tactile reading by individuals who are blind or have low vision. | None | Medium | No relevant OLS hits. |
| education/ed_primary_format.csv | Downloadable docs | Documents (e.g., PDF, Word) provided as downloadable files for offline viewing or use. | None | Low | Zero OLS search results returned; best-effort inference from term wording alone. |
| education/ed_primary_format.csv | eBook | A digital book formatted for reading on an e-reader, tablet, computer, or other electronic device. | None | Low | Zero OLS search results returned. |
| education/ed_primary_format.csv | Graphics/Photos | Static visual content, such as illustrations, diagrams, or photographs. | None | Medium | Only unrelated clinical SNOMED hits found. |
| education/ed_primary_format.csv | Interactive | Content that requires or invites active user engagement, such as simulations, games, or interactive multimedia exercises. | None | Medium | No clean single-concept OLS match. |
| education/ed_primary_format.csv | Mobile | A computer program or software application designed to run on a mobile device such as a phone or tablet. | GSSO:003578 | Medium | GSSO "mobile application" is a related/adapted match. |
| education/ed_primary_format.csv | Text/HTML | Content delivered as plain text or as HTML web pages viewable in a web browser. | None | Medium | NCIT "HTML Browser" describes a viewer program, not the content format itself. |
| education/ed_primary_format.csv | Video | The storing or preserving of video images to be displayed later. | NCIT:C91063 | Medium | NCIT "Video Recording" describes the process rather than the format/genre; adapted. |
| education/ed_primary_format.csv | Other | Different than the one(s) previously specified or mentioned. | NCIT:C17649 | High | Same NCIT:C17649 concept, confirmed via OLS fetch. |

### Wave 1 — Agent: imaging/geomx small files (4 files)

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| geomxLevel1/assayType.csv | RNA nCounter | GeoMx Digital Spatial Profiler (DSP) readout method in which oligonucleotide barcodes released from RNA probes hybridized within selected regions of interest are quantified using the NanoString nCounter digital barcode counting platform, without amplification or sequencing. | NCIT:C198498 | Medium | Related OLS class "NanoString nCounter Analysis System" found, adapted to the RNA-panel/GeoMx context. |
| geomxLevel1/assayType.csv | Protein nCounter | GeoMx Digital Spatial Profiler (DSP) readout method in which oligonucleotide barcodes released from antibody-conjugated protein probes bound within selected regions of interest are quantified using the NanoString nCounter digital barcode counting platform. | NCIT:C198498 | Medium | Same nCounter platform match, adapted to protein-panel context. |
| geomxLevel1/assayType.csv | Protein NGS | GeoMx Digital Spatial Profiler (DSP) readout method in which oligonucleotide barcodes released from antibody-conjugated protein probes bound within selected regions of interest are quantified by next-generation sequencing rather than the nCounter platform, enabling higher-plex protein readouts. | None | Medium | No OLS hit; inferred by analogy to sibling nCounter rows and GeoMx-NGS domain knowledge. |
| geomxLevel1/assayType.csv | RNA NGS | GeoMx Digital Spatial Profiler (DSP) readout method in which oligonucleotide barcodes released from RNA probes hybridized within selected regions of interest are quantified by next-generation sequencing rather than the nCounter platform, enabling whole-transcriptome or higher-plex RNA readouts. | None | Medium | No OLS hit; inferred by analogy to sibling rows. |
| imagingLevel3Segments/segmentType.csv | Mask | A segmentation output represented as a binary or labeled raster image in which pixels belonging to a segmented object (e.g., a cell or nucleus) are assigned a non-zero/class value and background pixels are assigned zero. | None | Low | OLS matches were neuroimaging-specific; description written from domain knowledge. |
| imagingLevel3Segments/segmentType.csv | Outline | A segmentation output represented as the boundary contour line surrounding a segmented object, as opposed to a filled area (mask) or a single coordinate (point). | None | Low | No OLS match found; inferred by analogy to sibling rows. |
| imagingLevel3Segments/segmentType.csv | Polygon | A segmentation output in which an object's spatial extent is represented as a closed polygon defined by an ordered sequence of vertex coordinates. | NCIT:C85402 | Medium | NCIT "Imaging Region of Interest" definition explicitly covers polygon ROI representation; adapted. |
| imagingLevel3Segments/segmentType.csv | Probability Map | A segmentation output in which each pixel is assigned a continuous value representing the estimated probability that it belongs to a given object class, typically produced by a probabilistic or machine-learning-based segmentation algorithm rather than a binary mask. | None | Low | No OLS match found; standard image-analysis domain knowledge. |
| imagingLevel3Segments/segmentType.csv | Point | A segmentation output in which an object or region of interest is represented by a single coordinate (point) rather than an outline, polygon, or mask. | NCIT:C85402 | Medium | Same NCIT ROI class explicitly mentions point ROI; adapted. |
| imagingLevel2/immersion.csv | Air | An imaging immersion condition in which no liquid or oil medium is used between the objective lens and the specimen or coverslip; the objective is separated from the sample only by air. | BAO:0150017 | Medium | Exact label match ("air interface objective lens") in BioAssay Ontology but no definition text to adapt verbatim. |
| imagingLevel2/immersion.csv | Oil | An imaging immersion condition in which a specialized oil with a refractive index matched to glass is applied between the objective lens and the specimen or coverslip to increase numerical aperture and resolution. | BAO:0150019 | Medium | Exact label match ("oil immersion lens") in BAO, no definition text available. |
| imagingLevel2/immersion.csv | Water | An imaging immersion condition in which water is applied between the objective lens and the specimen or coverslip, commonly used with water-immersion objectives for live-cell or aqueous-sample imaging. | BAO:0150020 | Medium | Exact label match ("water immersion lens") in BAO, no definition text available. |
| imagingLevel2/immersion.csv | Other | An imaging immersion medium other than air, oil, water, glycerol, or a multi-immersion configuration. | None | Low | Catch-all value; no OLS match applicable. |
| imagingLevel2/immersion.csv | Multi | An imaging immersion condition using a multi-immersion objective lens compatible with more than one immersion medium (e.g., air, water, oil, or glycerol), allowing the same lens to be used across different sample preparations. | None | Medium | No OLS match; established multi-immersion-objective domain knowledge. |
| imagingLevel2/immersion.csv | Glycerol | An imaging immersion condition in which glycerol, a triol with a refractive index intermediate between water and oil, is applied between the objective lens and the specimen; glycerol-immersion objectives are often used for tissue-clearing or deep-imaging applications. | CHEBI:17754 | Medium | Exact chemical match in ChEBI; chemical definition adapted to describe imaging-immersion usage. |
| imagingLevel1/imageAssay.csv | CODEX | CO-Detection by indEXing (CODEX): a highly multiplexed cytometric imaging approach used to create multiplexed datasets from a single tissue staining reaction. CODEX iteratively visualizes antibody binding events using DNA barcodes, fluorescent dNTP analogs, and an in situ polymerization-based indexing procedure. | NCIT:C181931 | High | Exact label/definition match. |
| imagingLevel1/imageAssay.csv | CyCIF | Cyclic Immunofluorescence (CyCIF): a method for highly multiplexed immunofluorescent imaging of cells using an iterative, cycling process in which images of expressed fluorescently-tagged proteins, fluorescent dyes, or fluorescently-tagged antibodies are serially collected from the same sample and assembled into a high-dimensional representation of the spatial relationships between targets of interest. | NCIT:C210700 | High | Exact abbreviation/definition match. |
| imagingLevel1/imageAssay.csv | ExSeq | ExSeq (Expansion Sequencing): a spatial transcriptomics assay that involves physically expanding specimens with polymer- and hydrogel-based systems followed by in situ sequencing. | EFO:0700006 | High | Exact label match, definition used verbatim. |
| imagingLevel1/imageAssay.csv | GeoMX-DSP | GeoMx Digital Spatial Profiler (DSP): a method to profile RNA or protein from tissue sections that combines spatial and molecular profiling by generating a whole-tissue image at single-cell resolution alongside digital profiling data from photocleavable-oligonucleotide-barcoded probes imaged from selected regions of interest. | NCIT:C181933 | High | Near-exact label match, definition usable. |
| imagingLevel1/imageAssay.csv | H&E | Hematoxylin and Eosin (H&E) staining: a routine histological staining method using two dyes, hematoxylin, which stains cell nuclei a dark purplish color, and eosin, which stains cytoplasm and connective tissue an orangish-pink color. | NCIT:C23011 | High | Exact match, definition lightly adapted. |
| imagingLevel1/imageAssay.csv | IHC | Immunohistochemistry (IHC): a diagnostic or research technique in which an antibody is used to link a cellular antigen specifically to a stain that can be visualized with a microscope. | NCIT:C51944 | High | Exact abbreviation match, definition usable. |
| imagingLevel1/imageAssay.csv | IMC | Imaging Mass Cytometry (IMC): a method that combines laser ablation of tissue specimens with secondary ion mass spectrometry to image antibodies tagged with isotopically pure elemental metal reporters, allowing in situ characterization of the specimen while preserving its tissue architecture and cellular morphology. | NCIT:C182027 | High | Exact label/definition match. |
| imagingLevel1/imageAssay.csv | MERFISH | Multiplexed Error-Robust Fluorescence In Situ Hybridization (MERFISH): an image-based approach to single-cell transcriptomics in which RNAs are identified via a combinatorial labeling approach that encodes RNA species with error-robust barcodes, followed by sequential rounds of single-molecule FISH to read out the barcodes. | NCIT:C210697 | High | Exact label/definition match. |
| imagingLevel1/imageAssay.csv | MIBI | Multiplexed Ion Beam Imaging (MIBI): a method for multiplexed immunohistochemistry that uses secondary ion mass spectrometry to image antibodies tagged with isotopically pure elemental metal reporters, capable of analyzing up to 100 targets simultaneously over a five-log dynamic range. | NCIT:C181930 | High | Exact abbreviation/definition match. |
| imagingLevel1/imageAssay.csv | mIHC | Multiplexed Immunohistochemistry (mIHC): a method that enables simultaneous detection of multiple biomarkers on a single tissue section using immunohistochemistry techniques. | NCIT:C181927 | High | Exact abbreviation/definition match. |
| imagingLevel1/imageAssay.csv | MxIF | Multiplexed Immunofluorescence (MxIF): a method that enables simultaneous detection of multiple biomarkers on a single tissue section using immunofluorescence techniques. | NCIT:C181928 | High | Exact abbreviation/definition match. |
| imagingLevel1/imageAssay.csv | Not Applicable | Indicates that determination of a value is not relevant in the current context. | NCIT:C48660 | High | Exact label/definition match. |
| imagingLevel1/imageAssay.csv | SABER | Signal Amplification By Exchange Reaction (SABER): a DNA-based in situ hybridization method that uses a primer exchange reaction to generate long, concatemeric single-stranded DNA amplification tails on oligonucleotide probes, enabling programmable, multiplexed signal amplification for imaging RNA, DNA, or protein targets without enzymatic or antibody-based amplification. | None | Medium | No OLS match found in any queried ontology; description from established SABER-FISH domain knowledge. |
| imagingLevel1/imageAssay.csv | t-CyCIF | Tissue-based Cyclic Immunofluorescence (t-CyCIF): a multiplex immunofluorescence imaging assay that uses iterative cycles of antibody staining, fluorescence imaging, and fluorophore inactivation to enable highly multiplexed spatial detection and quantification of protein targets within the same tissue specimen while preserving tissue architecture and cellular context. | EFO:0023019 | High | Exact label match, definition used verbatim. |

### Wave 1 — Agent: visium small files (4 files)

Note: `modules/visiumRNALevel3/visiumFileType.csv` contains two duplicate term rows ("json scale
factors" and "probe dataset csv" each appear twice) — both occurrences were filled identically.

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| visiumRNALevel1/slideVersion.csv | V1 | 10x Genomics Visium Spatial Gene Expression slide, version 1 (the original, manually placed Visium slide format), with capture areas measuring 6.5mm x 6.5mm containing 4,992 spatially barcoded spots each. | EFO:0022857 | High | Exact OLS label match "Visium Spatial Gene Expression V1" with directly usable definition. |
| visiumRNALevel1/slideVersion.csv | V2 | 10x Genomics Visium slide, version 2, compatible with the Visium CytAssist instrument for automated tissue transfer from a standard glass slide; available with capture areas of 6.5mm x 6.5mm or 11mm x 11mm. | EFO:0022858 | Medium | OLS hit names the whole CytAssist V2 assay rather than just the slide. |
| visiumRNALevel1/slideVersion.csv | V3 | A later generation of the 10x Genomics Visium slide, succeeding versions 1 and 2 in this model's slide-version series; 10x Genomics has not published a distinct 'V3' Visium slide specification in public ontology sources. | None | Low | No OLS hit found; generic inference by analogy to sibling rows. |
| visiumRNALevel1/slideVersion.csv | V4 | The most recent generation of the 10x Genomics Visium slide referenced in this model, succeeding versions 1 through 3; 10x Genomics has not published a distinct 'V4' Visium slide specification in public ontology sources. | None | Low | No OLS hit found; generic inference by analogy to sibling rows. |
| visiumRNALevel1/captureArea.csv | A / B / C / D | Capture area [A/B/C/D], one of four positions on this 10x Genomics Visium slide format; each capture area contains a grid of spatially barcoded spots used to capture mRNA from a mounted tissue section. | None | Medium | No OLS match for single letters (too ambiguous to search); Visium slide layout is well-established domain knowledge. |
| visiumRNALevel1/captureArea.csv | A1 / B1 / C1 / D1 | Capture area [A1/B1/C1/D1], one of the four standard positions on a 10x Genomics Visium slide; each capture area contains a grid of spatially barcoded spots used to capture mRNA from a mounted tissue section. | None | Medium | Standard Visium slide labeling is well-established domain knowledge; no OLS match. |
| visiumRNALevel1/spatialLibrary.csv | Smart-seq2 | Switching mechanism at the 5' end of RNA templates (SMART)-based library construction method; Smart-seq2 transcriptome libraries have improved detection, coverage, and accuracy compared to the original Smart-seq method, and are generated with off-the-shelf reagents at lower cost. | EFO:0008931 | High | Exact OLS label match with directly usable definition. |
| visiumRNALevel1/spatialLibrary.csv | Smart-SeqV4 | Single-cell RNA-seq library construction method using SMART chemistry to generate high-quality cDNA from ultra-low amounts of total RNA or directly from intact cells (<1,000 cells); improves on Smart-seq2 via LNA technology and an optimized template-switching oligo. | EFO:0700016 | High | Exact OLS label match ("Smart-seq v4") with directly usable definition. |
| visiumRNALevel1/spatialLibrary.csv | 10xV1.0 | First version (v1) of the 10x Genomics droplet-based single-cell 3' library construction chemistry, in which barcoded gel beads and cells are co-encapsulated in nanoliter droplets for parallel barcoding of transcripts. | EFO:0009901 | Medium | OLS term "10x 3' v1" is a strong analog but not an exact label match. |
| visiumRNALevel1/spatialLibrary.csv | 10xV1.1 | Minor revision (v1.1) of the first-generation 10x Genomics single-cell 3' library construction chemistry; specific chemistry differences from v1.0 are not documented in public ontology sources. | None | Low | No "v1.1" term found in OLS (only v1 exists); generic inference. |
| visiumRNALevel1/spatialLibrary.csv | 10xV2 | Second version (v2) of the 10x Genomics droplet-based single-cell 3' library construction chemistry, in which the poly(dT) sequence is part of the gel bead oligo (along with the cell barcode and UMI) and the template-switch oligo is supplied in the RT primer. | EFO:0009899 | Medium | OLS term "10x 3' v2" is a strong analog, not exact label match. |
| visiumRNALevel1/spatialLibrary.csv | 10xV3 | Third version (v3) of the 10x Genomics droplet-based single-cell 3' library construction chemistry. | EFO:0009922 | Medium | OLS term "10x 3' v3" is a strong analog, not exact label match. |
| visiumRNALevel1/spatialLibrary.csv | 10xV3.1 | Minor revision (v3.1) of the third-generation 10x Genomics single-cell 3' library construction chemistry. | EFO:0022980 | Medium | OLS term "10x 3' v3.1" is a strong analog, not exact label match. |
| visiumRNALevel1/spatialLibrary.csv | Drop-seq | Droplet microfluidics-based method for parallel analysis of mRNA transcripts from thousands of individual cells, in which each cell is co-encapsulated with a barcoded bead in a nanoliter droplet. | EFO:0008722 | High | Exact OLS label match with directly usable definition. |
| visiumRNALevel1/spatialLibrary.csv | inDropsV2 | Second version (v2) of the inDrop (indexing droplets) single-cell RNA-seq library construction method, a droplet microfluidic platform that uses hydrogel beads to deliver barcoded primers to individual cells. | None | Medium | Only a generic unversioned "inDrop" OLS term exists; no v2-specific match found. |
| visiumRNALevel1/spatialLibrary.csv | inDropsV3 | Third version (v3) of the inDrop (indexing droplets) single-cell RNA-seq library construction method. | None | Medium | Same reasoning as inDropsV2. |
| visiumRNALevel1/spatialLibrary.csv | TruDrop | Droplet-based microfluidic single-cell library construction platform based on inDrop that incorporates dual indexing to detect index hopping, using standard Illumina sequencing primers for high-throughput sequencing. | EFO:0700010 | High | Exact OLS label match with directly usable definition. |
| visiumRNALevel1/spatialLibrary.csv | Nextera XT | Illumina library preparation kit that uses tagmentation (simultaneous enzymatic fragmentation and adapter tagging) to construct sequencing-ready libraries from very low quantities of input DNA/cDNA; commonly used as a downstream library-prep step following methods such as Smart-seq2. | None | Medium | No OLS match found; well-established domain knowledge used instead. |
| visiumRNALevel3/visiumFileType.csv | reference png / reference jpg | PNG/JPEG image of the tissue section supplied as the Space Ranger alignment reference image, used to register the capture-area spot grid to the tissue for spatial gene expression analysis. | None | Medium | Compound term (content+format); format matched OLS but not the full compound term. |
| visiumRNALevel3/visiumFileType.csv | json scale factors | JSON file output by Space Ranger (scalefactors_json.json) that records the scaling factors needed to relate spot positions to the full-resolution, high-resolution, and low-resolution tissue images. | None | Medium | Compound term; JSON format matched generically but not the full compound term. |
| visiumRNALevel3/visiumFileType.csv | probe dataset csv | CSV file listing the probe set used in a probe-based (e.g., FFPE) Visium assay, including probe IDs and the genes they target. | None | Medium | No specific OLS match for "probe set/dataset"; domain knowledge of Space Ranger outputs. |
| visiumRNALevel3/visiumFileType.csv | qc result html | HTML quality-control report summarizing metrics from Space Ranger processing of a Visium sample, such as sequencing, alignment, and spatial coverage statistics. | EDAM:data_3914 | Medium | OLS "Quality control report" matches the "qc result" semantic content; format portion not covered. |
| visiumRNALevel3/visiumFileType.csv | filtered mex / unfiltered mex | [Un]filtered feature-barcode expression matrix in Market Exchange (MEX) sparse-matrix format, containing [only spots Space Ranger called as tissue-covered / all spots regardless of tissue coverage] on a Visium sample. | NCIT:C184778 | Medium | "mex" matches NCIT "MEX Format" exactly; "filtered"/"unfiltered" qualifier is domain knowledge. |
| visiumRNALevel3/visiumFileType.csv | tissue_positions | Space Ranger output file (tissue_positions.csv/.parquet) that maps each spot barcode to its row/column array coordinates and pixel coordinates on the full-resolution tissue image, and indicates whether the spot overlaps tissue. | None | Medium | No OLS match found; well-established Space Ranger output file, domain knowledge. |
| visiumRNALevel3/visiumFileType.csv | barcodes | Space Ranger output file (barcodes.tsv) listing the spot barcode sequences corresponding to the columns of the feature-barcode expression matrix. | None | Medium | No OLS match found; standard Space Ranger output, domain knowledge. |
| visiumRNALevel3/visiumFileType.csv | features | Space Ranger output file (features.tsv) listing the gene/feature IDs and names corresponding to the rows of the feature-barcode expression matrix. | None | Medium | No usable OLS match found; standard Space Ranger output, domain knowledge. |
| visiumRNALevel3/visiumFileType.csv | fiducial image png / fiducial image jpg | PNG/JPEG image showing the fiducial frame (alignment markers) printed on the Visium slide, used by Space Ranger/Loupe Browser to register the capture area to the tissue image. | None | Medium | MeSH "Fiducial Markers" describes the general concept, not this specific file; kept blank. |
| visiumRNALevel3/visiumFileType.csv | detected image png / detected jpg | PNG/JPEG image output by Space Ranger showing the tissue area and spots detected during the tissue-detection step, overlaid on the slide image. | None | Medium | No OLS match found; domain knowledge of Space Ranger pipeline. |
| visiumRNALevel3/visiumFileType.csv | high res image | High-resolution tissue microscopy image (tissue_hires_image.png) bundled in Space Ranger spatial output, used for detailed visualization of the tissue section with the overlaid spot grid. | None | Medium | No specific OLS match; domain knowledge of Space Ranger output naming. |
| visiumRNALevel3/visiumFileType.csv | low res image | Low-resolution, downsampled tissue microscopy image (tissue_lowres_image.png) bundled in Space Ranger spatial output, used for lightweight visualization of the tissue section with the overlaid spot grid. | None | Medium | Same reasoning as high res image. |

### Wave 2 — Agent: shared dataset_species / treatmentType / diseaseType (75 rows)

| File | Term | Description source | Ontology | Confidence |
|---|---|---|---|---|
| shared/dataset_species.csv | 29 species terms (African Bush Elephant, Armadillo, Asian Elephant, Boar, Cat, Chicken, Cow, Dog, E. coli, Guinea Pig, Horse, Human, Human Patient, Human Cell Line, Mouse, Multispecies, Not Applicable, Opossum, Rabbit, Rat, Rhesus monkey, Sheep, Trichoplax adhaerens, Unknown, Unspecified, Worm, Fruit Fly, Zebrafish) | Mostly direct NCIT label matches; a few via NCBITaxon (taxon ID only, no OLS definition), FOODON, FBcv, MeSH | NCIT/NCBITaxon/FOODON/MeSH/FBcv | Mostly High, several Medium |
| shared/treatmentType.csv | 30 cancer treatment modality terms (radiation/chemo/surgical/cellular therapy types) | Direct NCIT label matches throughout | NCIT | Mostly High, a few Medium |
| shared/diseaseType.csv | 16 ICD-O-3 morphology category terms (Basal Cell Neoplasms, Blood Vessel Tumors, etc.) | Mix of direct/related NCIT and SNOMED matches; 5 rows (Ductal and Lobular Neoplasms, Granular Cell Tumors and Alveolar Soft Part Sarcomas, Miscellaneous Bone Tumors, Miscellaneous Tumors, Transitional Cell Papillomas and Carcinomas) had no usable OLS match — described from ICD-O-3 domain knowledge | NCIT/SNOMED/None | Mix of High/Medium/Low |

Full per-term detail available in the agent transcripts; summarized here per project convention of table-per-batch. All applied per "apply all, flag confidence" decision.

### Wave 2 — Agent: tumorType.csv (8 rows)

| File | Term | Description | Ontology | Confidence | Justification |
|---|---|---|---|---|---|
| shared/tumorType.csv | Acute Promyelocytic Leukemia | An acute myeloid leukemia characterized by the predominance of abnormal promyelocytes, most often driven by translocations involving the retinoic acid receptor-alpha (RARA) gene. Over 95% of cases show t(15;17)(q24.1;q21.2), fusing PML and RARA. | NCIT (NCIt Code=C208352 only; pre-existing ICD-O-3 code in Ontology Identifier preserved) | High | Exact OLS label match; existing ICD-O-3 code preserved, only blank NCIt Code cell filled. |
| shared/tumorType.csv | Gastroesophageal Adenocarcinoma | A malignant epithelial neoplasm composed of glandular cells arising at or near the esophagus/stomach junction; encompasses distal esophageal, GEJ, and gastric cardia adenocarcinomas. | DOID:0080375 | Medium | Exact DOID label match; NCIT only has narrower "GEJ Adenocarcinoma". |
| shared/tumorType.csv | Myoepithelioma | A tumor composed predominantly of myoepithelial cells; usually benign, though malignant myoepithelial carcinoma also occurs. | None (pre-existing ICD-O-3 code in Ontology Identifier preserved) | High | MeSH exact match used for description; NCIT only has site/behavior-specific subtypes, so not recorded as NCIt Code. |
| shared/tumorType.csv | Pan-cancer | A term describing analyses/datasets/studies spanning multiple cancer types together rather than a single cancer type, to identify shared or distinguishing features across cancers. | None | Low | No usable OLS match; written from domain knowledge (e.g. TCGA Pan-Cancer Atlas). |
| shared/tumorType.csv | Pending Annotation | An administrative placeholder indicating a tumor/cancer type has not yet been curated or assigned; awaiting manual annotation review. | None | Low | Internal curation-status term, not an ontology concept. |
| shared/tumorType.csv | Uterine Adenosarcoma | A primary malignant neoplasm of the uterine corpus with a sarcomatous mesenchymal component combined with a benign glandular epithelial component; generally low-grade, can recur locally. | NCIT:C6336 | High | Direct match to NCIT "Uterine Corpus Adenosarcoma". |
| shared/tumorType.csv | Not-Applicable | Determination of a value is not relevant in the current context. | NCIT:C48660 (NCIt Code only) | High | Mirrors sibling "Not Applicable" row using same code/description. |
| shared/tumorType.csv | Plexiform Neurofibroma | An elongated, multinodular neurofibroma involving multiple trunks of a nerve plexus or multiple fascicles of a large nerve; some resemble a "bag of worms". | NCIT:C3797 | High | Exact label match; row already had NCIt Code=C3797 pre-populated, confirming the match. |

Note: this file has an internal convention where `Ontology Url` is never populated and `Ontology Identifier` holds bare ICD-O-3 codes (paired with Source=ICD-O-3) rather than CURIEs — pre-existing curated values were left untouched, only blank cells filled.

### Wave 2 — Agent: education/sequencing small files (ed_topic.csv 37 rows, librarySelection.csv 3 rows, libraryStrategy.csv 2 rows)

37 `education/ed_topic.csv` rows filled — mostly direct NCIT matches (Biology, Genetics, Chemistry, Physics, Metastasis, Immunotherapy, etc.), several MeSH/EDAM/schema.org matches (Diversity/Equity/Inclusion, Epigenetics, Statistics and Probability, Patient Advocacy), and about a dozen Low-confidence domain-knowledge descriptions with no ontology match (Computational Model Development, Mechano-genetics, Mechano-resistance, Outreach, Platform Development, etc.). Two rows (Training Material, Systems Biology) already had ontology mappings pre-populated — only Description was added to match.

`sequencingLevel1/librarySelection.csv`: rRNA Depletion (GENEPIO:0101020, High), miRNA Size Fractionation (NCIT:C163991, Medium), Affinity Enrichment (NCIT:C163987, Medium).

`sequencingLevel1/libraryStrategy.csv`: scMultiome (NCIT:C205123, High), Synthetic-Long-Read (NCIT:C204827, High).

### Wave 2 — Agent: seqPlatform.csv (52 rows)

All 52 blank rows filled — sequencing instrument/platform names, overwhelmingly matched via GENEPIO (genomic epidemiology platform ontology) and EFO with High confidence (Illumina HiSeq/NextSeq/NovaSeq/MiSeq series, PacBio, Ion Torrent, Oxford Nanopore MinION/GridION/PromethION, AB Genetic Analyzer/SOLiD series, 454 GS series). Three Low-confidence rows had no ontology match: `454 GS FLX+`, `Illumina NextSeq 2500` (flagged by the agent as likely a data-entry conflation of NextSeq 500/550 with HiSeq 2500 — not a real commercial platform name), and `Other`.

### Wave 2 — Agent: biospecimen specimenType.csv (61 rows) + shared/tissue.csv (3 rows)

61 `specimenType.csv` rows filled — mostly direct NCIT matches from the GDC/TCGA biospecimen-type series (Blood Derived Cancer variants, FFPE Scrolls, Xenograft Tissue variants, Cell Line, DNA/RNA/Total RNA, Whole Blood, etc.), several UBERON/BTO/MONDO/EMAPA/SIO matches, and about a dozen Low-confidence rows with no usable OLS match (Additional - New Primary, Blood Derived Normal, Bone Marrow Normal, Lymphoid Normal, Primary/Recurrent Blood Derived Cancer variants, Primary Tumor, Recurrent Tumor, Repli-G X DNA, Solid Tissue Normal).

`shared/tissue.csv`: Caecum and Cardia already had pre-existing Ontology Identifier values (UBERON and ICD-O-3 topography code respectively) — only Description was added to match, existing mappings left untouched. Pending Annotation — administrative placeholder, no ontology match (Low).

### Wave 2 — Agent: tool_language.csv (67 rows)

All 67 blank rows filled — programming/software language names. High/Medium-confidence matches mostly via SWO (Software Ontology, e.g. Python, MATLAB, Java, C/C++/C#, Perl, Ruby, Fortran, PostScript, Racket) plus a few NCIT (HTML, SQL) and EDAM (CWL, Nextflow) matches. About half the rows (AWK, Bash, Go, R, Julia, Lisp, Lua, Scala, Scheme, Shell, TeX, VHDL, Verilog, WDL, XAML, and others) had no usable OLS match and were described from general software-engineering domain knowledge (Low confidence).

### Wave 2 — Agent: dataset_file_format.csv (81 rows)

All 81 blank rows filled — file/data format names. High/Medium-confidence matches mostly via NCIT and EDAM (FASTA, FASTQ, BAM, VCF, JSON, TIFF, HDF5, GTF/GFF3, maf, TSV, XML, ZIP, etc.). About 20 rows (COOL, DCC, DS_Store, FCS, FIG, FREQ, GCG, GCTx, LIF, MAP, ROUT, RPROJ, SGI, STAT, TDF, cloupe, SF, BPM, CLS, SCN, SVS, and administrative placeholders Unspecified/Pending Annotation) had no usable OLS match and were described from bioinformatics/software domain knowledge (Low confidence).

**Note:** the agent assigned to `tool_language.csv` observed that CRLF, not bare `\n`, is this repo's actual native line-ending convention for individual CV term CSVs (verified separately against pre-session git history) — the earlier "normalize to `\n`" instruction given to every agent this session was based on a mistaken premise. Per user decision, the whole repo was subsequently standardized to bare `\n` in a dedicated cleanup commit (see `8c5a746`) with a new `.gitattributes` rule to enforce it going forward, so this file (and all others) now consistently use `\n`.
