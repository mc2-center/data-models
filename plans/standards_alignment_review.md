# C2M2, ISA and NAMO as reference models for MC2: gaps and definitions

## Context

This review asks whether three external standards can **fill gaps in the MC2
model** or **help define existing MC2 attributes more precisely**. It is a
different question from exporting MC2 data to them; export is covered in
`plans/metadata_export_pipeline.md`.

Each standard was read from its own spec or repository on 2026-11-12:

- **C2M2**: the nih-cfde/c2m2 spec README.
- **ISA**: isa-specs.readthedocs.io (model, ISA-JSON and ISA-Tab pages) and the
  ISA-tools/isa-api docs.
- **NAMO**: monarch-initiative/namo, `src/namo/schema/namo.yaml`.

The MC2 side was checked against `mc2.model.csv` and the CV CSVs. Every MC2
description and Valid Values list quoted below was re-checked in the CSV
directly. Ontology IDs that are *proposed* below have not been looked up yet.
Each one needs an OLS pass (`ols-term-annotator`) before use.

### Short answer

| Standard | What it offers MC2 | Main contributions |
|---|---|---|
| **C2M2** | Ontology bindings that are already settled for file and sample fields | Bind MC2 CVs to EDAM, OBI, UBERON and NCBITaxon. Add `File Analysis Type`. Tighten the checksum, compression and URL definitions. |
| **ISA** | A clear line between what describes a *sample* and what describes a *process* | Add protocol links for every assay family. Add a shared time-unit CV bound to UO. Reword process attributes. Optionally split Assay into what was measured vs. the technology used. |
| **NAMO** | A checklist of what to capture for experimental models. Its value sets are thin and mostly have no ontology IDs. | Turn `Model Type` into a CV. Add cell source, authentication and passage, and 3D-culture descriptors. Clean up `Model Source` and `Model Method`. |

None of the three standards suggests restructuring MC2. Most of the value is
in **binding existing CVs to standard ontologies** and **clarifying about 15
attribute descriptions**. There are also a small number of new attributes,
most of them in the Model module.

---

## 1. Gaps: concepts MC2 lacks

Ranked by value. "Source" is the standard that surfaced the gap.

| # | Gap | Source | Evidence in MC2 | Proposed addition |
|---|---|---|---|---|
| 1 | **Model Type has no controlled values** | NAMO, C2M2 `subject.granularity` | `Model Type` is required. Its description is "The general label used to identify the model type." and Valid Values is empty. `Model Method` is also empty. | A Model Type CV whose categories come from NAMO's class hierarchy: 2D cell line, primary culture, iPSC-derived, spheroid, organoid, scaffold/hydrogel/bioprinted 3D culture, co-culture, organ-on-chip, tissue-on-chip, in silico, animal model. **MC2 has to add values NAMO lacks:** PDX, cell-line xenograft, allograft/syngeneic, GEMM and PDX-derived organoid. `Model Graft Source` already assumes these exist. Anchor every value to NCIT, CLO or EFO, not to `namo:` IRIs, because NAMO has no releases. |
| 2 | **No analysis or operation type for derived files** | C2M2 `analysis_type` (OBI) | `File Level` is "The processing level the file can be mapped to". `Software and Version` names a tool, not what the tool did. Nothing records alignment, peak calling, segmentation, and so on. | Add an optional `File Analysis Type`, with a small CV bound to EDAM `operation:` or OBI. |
| 3 | **No protocol link for Sequencing, Visium or GeoMx** | ISA Protocol and Process | Only `Image Protocol Link` exists (protocols.io or DOI). It is the only attribute in the model containing "Protocol". | Add a `Protocol Link` to the Level 1 classes of the Sequencing, Visium and GeoMx families, using the `Image Protocol Link` pattern. A separate Protocol class is not needed. |
| 4 | **Time-unit attributes are free text** | ISA Unit as OntologyAnnotation | `Biospecimen Age at Collection Unit`, `Model Age Unit` and `File Longitudinal Time Elapsed Unit` all have empty Valid Values. The imaging length units are already bound to UO. | Add one shared time-unit CV bound to UO (minute, hour, day, week, month, year) and use it for all three attributes. |
| 5 | **Cell-line provenance and QC** | NAMO `cell_source`, `authentication_method`, `passage_range` | The Model module has none of these. `Model Source` packs origin information into free text. | New attributes: `Model Cell Source` (primary, iPSC-derived, ESC-derived, immortalized line), `Model Authentication Method` (STR profiling, mycoplasma testing, species verification) and `Model Passage Number`. Record the passage actually used, not NAMO's recommended range. |
| 6 | **3D and co-culture descriptors** | NAMO `three_d_architecture`, `matrix_composition`, `culture_system`, `coculture_configuration` | None of these exist. | Add `Model Culture System` (Matrigel dome, suspension, air-liquid interface, transwell) and `Model Matrix Composition`. Add co-culture configuration only if MC2 groups submit co-cultures. Skip NAMO's cell-ratio structure, which does not fit a flat CSV. |
| 7 | **No race or ethnicity on Individual** | C2M2 `subject.race`/`ethnicity` | The `Individual` DependsOn list has `Sex` and `Individual Gender` but neither race nor ethnicity. | Raised here as a finding. dbGaP and CRDC also expect these fields; see the export plan. |
| 8 | **Compression format is not named** | C2M2 `compression_format` (EDAM) | `File Data Compression Status` takes only "Unknown, Compressed, Uncompressed". | Add an optional EDAM-bound `File Compression Format`, such as gzip or bzip2. |
| 9 | **No study-level experimental factor** | ISA Factor | Nothing states which variable a study was designed to compare. `Biospecimen Timepoint Type`, `Treatment Type` and `File Longitudinal Group` come closest. | Optional `Study Experimental Factor`. Worth adding only if the portal wants filtering by study design. |

**Considered and not recommended:**
- **C2M2:** negative disease assertions ("disease ruled out"). `Biospecimen Tumor Status` covers the normal and control cases.
- **C2M2:** archive bundle membership.
- **C2M2:** uncompressed file size. Clarifying the `File Data Size` description is enough.
- **NAMO:** complexity level, biological organization level, and its PBPK, QSAR and validation classes.
- **ISA:** a full process graph, Material types, and performer/date fields.

## 2. Existing attributes that can be defined better

| MC2 attribute | Current description / values | Reference counterpart | Suggested change |
|---|---|---|---|
| **Tissue** | "Tissue type(s) associated with the dataset, file, or publication." `tissue.csv`: 113 of 114 terms use NCIT, 0 use UBERON. | C2M2 `anatomy` = UBERON | Add UBERON IDs to the CV. A generated NCIT→UBERON crosswalk already exists at `kg-pipeline/mappings/crosswalks/tissue_ncit_to_uberon.sssom.tsv` (106 rows). All rows are currently `reviewed=false`, so this is a review-and-promote task, not new mapping work. `Primary Site` and `Biospecimen Anatomic Site` already use UBERON. |
| **File Format** | "The format of the file described by this entry." `fileFormat.csv`: 75 NCIT, 19 EDAM. | C2M2 `file_format` = EDAM `format:` | Make EDAM the preferred ID and add EDAM IDs where they exist. |
| **Assay** | "The assay the dataset, file, or publication is representative of." `assay.csv`: 391 terms using NCIT, EFO, CHMO and PMID IDs; 33 have no ID. | C2M2 `assay_type` = OBI. ISA `measurementType` + `technologyType`. | Add OBI IDs where they exist. One CV currently covers both what is measured and the technology used (for example "3' RNA-seq" and "3D Bioprinting"). A separate technology-type attribute would make `Assay`, `NGS Library Strategy` and `Image Assay Type` easier to relate. This is a larger change, so treat it as a decision, not a fix. |
| **Species** | `dataset_species.csv`: most terms use NCIT; 6 use NCBITaxon. | C2M2 `ncbi_taxonomy` | Add NCBITaxon IDs, which would match `Biospecimen Taxonomy ID`. |
| **File Data Category** | "A broad classification of the contents of a data file…" | C2M2 `data_type` = EDAM `data:` | Add an optional EDAM `data:` ID to the CV. |
| **Biospecimen Type** | "The type of biospecimen". The values mix material categories ("Analyte", "Blood Buffy Coat") with tumor-event states ("Additional - New Primary", "Additional Metastatic"). | ISA Material Type, C2M2 `sample_prep_method` | Rewrite the description to say this is the kind of material collected, and how it differs from `Biospecimen Composition`. The mixed values come from GDC sample types, so splitting them out would be a model change. |
| **Biospecimen preservation, embedding and fixative CVs** | Example: "Text term that represents the method used to preserve the sample." | C2M2 `sample_prep_method` = OBI planned process | Add OBI IDs. Say in the descriptions that these terms describe how the sample was prepared. |
| **File Data Checksum Type** | Values: `md5sum, sha1, sha256`. | C2M2 allows only `md5` and `sha256` | Rename `md5sum` to `md5` (the algorithm, not the tool), and decide whether to keep `sha1`. Both changes break existing submissions. |
| **File Url** | "The url of where the file is stored." | C2M2 `persistent_id`, which forbids bare download URLs | Say whether this is a storage location or a stable resolver URI. |
| **NGS Library Layout** | "…one of Paired-end or Single." Values: `Paired-end, Single-indexed`. | ISA library-prep parameter | **The description doesn't match the values.** "Single-indexed" is a barcoding term, not a layout. MC2 inherited it from CRDC: GC 13.0.1 `library_layout` has it too and has no single-end value. Keep the value for CRDC compatibility, and fix the description. |
| **Workflow Type / Version / Parameter Description, Software and Version** | "Type of computational workflow used to generate the file." | ISA process parameters | Make the descriptions say they describe the step that produced this file, not the file's contents. |
| **Biospecimen Timepoint Type / Offset** | "Label to identify an event associated with the collection…" | ISA Factor Value or collection parameter | State that it describes the sampling design, not the sample itself. |
| **Model Source** | "The reference organism from which the model was derived… a specific Biospecimen Key, Model Key, mouse type, cell line, or other reference." | NAMO `cell_source` | This field carries several kinds of value. Move the origin category to the new `Model Cell Source` (gap 5) and keep `Model Source` for the RRID or reference key. Changes existing tables. |
| **Model Method** | "The term that describes the general method used to create the model." | NAMO `differentiation_method`, `culture_system` | Narrow it to how the model was derived or established, for example directed differentiation, xenograft passage or genetic engineering. Add a CV. |
| **Dataset Design / File Design** | "The overall design of the dataset." / "The overall design of the file." | ISA study design descriptor | The definitions only restate the attribute names. Bind them to EFO or OBI study-design terms, or at least add examples. |
| **Individual Age at Diagnosis** | "Age at the time the individual was diagnosed, expressed in years." | C2M2 `age_at_enrollment` | This is **not** the same concept as C2M2's, so no change is needed. The difference is noted here so nobody maps one to the other later. |

## 3. How each standard should be used

- **C2M2: reference for ontology bindings.** Its required vocabularies (EDAM,
  OBI, UBERON, NCBITaxon, DOID) are a good target set for MC2's CV
  `Ontology Identifier` columns. Binding to them improves the KG and all five
  export targets at the same time.
- **ISA: reference for definition wording.** Use its distinction between a
  sample's characteristics, a process's parameters, and a study's factors when
  rewriting descriptions. Don't adopt its process-graph structure.
- **NAMO: reference for what the Model module should capture.** Use it to
  decide which Model attributes to add. Anchor the resulting values to NCIT,
  CLO or EFO, and keep `namo:` IRIs only as `skos:closeMatch` notes until NAMO
  has a tagged release.

## Decisions for you

1. Which items in Section 1 should go into a model-change plan? Items 1, 4
   and 5 are the clearest wins.
2. Should `Model Type` be a closed CV, or open with suggested values?
3. Do you want the breaking changes: renaming or dropping checksum values,
   splitting `Model Source`, splitting Assay into measurement and technology?
4. Should the `NGS Library Layout` description be fixed? Its value comes
   from CRDC and should stay.
5. Should race and ethnicity be added to Individual? This touches
   consent and de-identification policy.

## Process

This is a review, not an implementation plan. Model changes that come out of
these decisions get their own plan file before implementation.
