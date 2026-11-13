# Metadata export pipeline: MC2 model/KG → external standards

## Context

Goal: data enters the MC2 database in the MC2 model's shape and is stored in
the knowledge graph. From there it is converted and packaged into other
standards on demand. Ingestion is **out of scope** for this plan.

This plan covers:
- the **attribute-mapping layer** in the KG, for the four export targets
  C2M2, GEO, dbGaP and CRDC;
- the **value crosswalks** those targets need;
- **one reference exporter**.

ISA and NAMO are not export targets here. They are covered as reference
models in `plans/standards_alignment_review.md`.

### What exists today

- **Value-level harmonization.** `harmonize.py` resolves raw CV values to
  ontology IRIs and writes SSSOM to `kg-pipeline/mappings/sssom/`.
- **Ontology crosswalks.** `crosswalk_ontology.py` generated
  NCIT→MONDO/UBERON crosswalks in `kg-pipeline/mappings/crosswalks/`:
  tissue (106 rows), tumorType (173), diseaseType (38) and diseaseStatus (6).
  **Every row is `reviewed=false`.** `link_ontology_crosswalk.py` consumes only
  reviewed rows, so none of these currently reach the graph.
- **Attribute-level mappings.** These exist only as 77 LinkML
  `exact_mappings` (68 `CRDC_CDE`, 8 DUO, 1 MIxS) in
  `schema/mc2_model.linkml.yaml`.
- **An older CRDC map.** `modules/shared/GC_v6.0.4_MC2_11.0.0_map_6-24-25.csv`
  maps MC2 11.0.0 to GC v6.0.4. It is older than both current models.
- **Limited instance data in the KG.** Only portal tables (Dataset, Grant,
  Publication, Tool, EducationalResource, DataCatalog) and **46 File View
  rows** are loaded. Individual, Biospecimen, Model and the Sequencing and
  Imaging levels are **schema only**.

### Crosswalk scoping

Each target's current specification was inventoried field by field on
2026-11-12. Every MC2 attribute named in the drafts was checked against
`mc2.model.csv`, and all of them resolve. The drafts are in
`kg-pipeline/mappings/standards/drafts/{c2m2,geo,dbgap,crdc}.tsv` (see the
README there for the column definitions) and become the Part A seeds:

| Target | Spec read | Fields | exact / close / broad / narrow / none | Submission and validation |
|---|---|---|---|---|
| **C2M2** | `C2M2_datapackage.json` (published-documentation `stable`, the schema `cfde-c2m2` itself loads) | 262 in 59 tables | 8 / 63 / 4 / 4 / 183 | Zipped Frictionless TSV package. `cfde-c2m2 prepare` fills the CV tables from ontology IDs; `cfde-c2m2 validate` runs **locally**. |
| **GEO** | `seq_template.xlsx` (GEO update of 2026-10-28) and the GEO seq and validation pages | 43 | 4 / 26 / 0 / 8 / 5 | One xlsx per sequencing type, with an MD5 sheet, plus FTP upload. A server-side validator runs on upload; there is no offline validator and no API. |

**GEO uses the HTS template for Sequencing, Visium and GeoMx.** For GeoMx:
- each AOI library is a GEO sample row;
- Level 1 FASTQs are the raw files;
- Level 2 DCC files are the processed files (Level 3 count matrices can be
  added);
- AOI annotations from ROI Segment Annotation go in submitter-added sample
  columns.

In the template, the MC2 sequencing-platform CV (77 terms) has
43 exact matches against GEO's 109 instruments, 6 that differ only by the
"Illumina " prefix, and 28 unmatched. The library-strategy CV (43 terms) has
19 exact matches, 1 that differs only in case, and 23 unmatched against
GEO's 50. The template also has a `batch` column (from
`File Batch Identifier`). Fields like disease state, sex and age are
submitter-added sample columns, not fixed template columns.
| **dbGaP** | dbGaP submission guide (updated 2026-07-16) and the 2026-04-07 template package | 39 | 3 / 17 / 0 / 10 / 9 | DS (TSV) and DD (xlsx) pairs uploaded via submit.ncbi. Validation runs server-side and locally with GaPTools (Subject Consent and Sample Mapping only). The SRA spreadsheet follows after the subject and sample files are accepted. |
| **CRDC** | CBIIT/cds-model `13.0.1-GC_Release` (2026-10-07). Checked against the portal's own exports, `GC_Dictionary_All_v13.0.1.json` and `GC_Controlled_Vocabularies` (103 files), both downloaded 2026-11-12. | 291 in 24 nodes (281 properties + 10 relationship keys) | 44 / 101 / 15 / 2 / 129 | One TSV per node, uploaded through the Submission Portal (browser or `crdc-datahub-cli-uploader`). Validation is **server-side only**. |

**The CRDC source of truth is the portal's export, not the GitHub YAML.** The
node and property sets match exactly, and so do the required flags. The
enums do not:
- 20 of the 103 vocabularies differ between the two sources.
- 19 have no enum at all in the YAML.
- The export adds the standard "Not Reported" / "Unknown" / "Not Applicable"
  missingness values, plus newer terms.
The exporter and the CRDC value crosswalks should read the exported
dictionary and vocabularies, pinned to a version.

Most "none" rows in C2M2 and CRDC belong to tables MC2 doesn't cover: gene,
protein, phenotype, radiology, proteomics and nanotech. These stay empty.

**About 33 attributes feed three or all four targets.** Of 177 MC2 attributes
used across all targets:
- 11 feed all four: Filename, File Format, File Data Checksum Value,
  Biospecimen_id, Biospecimen Anatomic Site, Sex, Species, Disease Type,
  Primary Diagnosis, Study Name and Study Description.
- 22 more feed three, almost all of them on Individual and Biospecimen.

So the mapping and value-crosswalk work should start with this shared set,
not one target at a time.

**Every target except file-level C2M2 needs Individual and Biospecimen
instance data, which the KG does not hold.** GEO also needs Sequencing
Level 1-3. CRDC also needs Sequencing and Imaging Level 1 and Person View.

#### Value crosswalks needed

Three kinds are needed:
- **ontology ID → ontology ID**, for C2M2;
- **CV string → the target's enum**, for GEO, dbGaP, SRA and CRDC;
- **ontology ID → caDSR permissible-value string**, for CRDC's open
  reference fields.

| Crosswalk | Targets | Size / status |
|---|---|---|
| Species → NCBITaxon / scientific name | all 4 | 32 terms, 6 have NCBITaxon. "Human Patient", "Multispecies" and "Unknown" have no single taxon. |
| Sex → target codes | all 4 | 3 terms. Trivial. CRDC is an identity map. |
| Anatomic site (UBERON) → label / caDSR string | C2M2, GEO, dbGaP, CRDC | A lookup, not a curated CV. For CRDC, `Primary Site` has 246 values and the site fields have 614. |
| `tissue.csv` NCIT → UBERON | C2M2, GEO | **Exists**, 106 rows, all unreviewed. |
| `tumorType` / `diseaseType` NCIT → DOID | C2M2 | Chained through the existing (unreviewed) NCIT→MONDO crosswalks plus MONDO's DOID xrefs. 185 + 46 terms. |
| Sequencing platform → instrument model / platform | GEO, CRDC, SRA (via dbGaP) | 77 terms. For GEO: 43 identical, 13 renamed, 20 with no target. For CRDC `instrument_model`: 76 of 77 match. CRDC `platform` (the vendor) is derived from the instrument model. |
| Library strategy / selection / layout / source molecule | GEO, CRDC, SRA | Strategy has 43 terms: for GEO, 20 identical, 4 mapped and about 19 with no target (GEO rejects WGS/WXS). GEO's molecule field needs source molecule + selection combined. |
| Biospecimen Type (+ Category) → sample type / analyte type / prep method | CRDC, dbGaP, C2M2 | For CRDC `sample_type`, 5 of 61 MC2 terms match and 56 don't. `sample_type_category` is an identity map. dbGaP `ANALYTE_TYPE` needs about 8 terms. C2M2 OBI prep methods need 47 terms, 0 with OBI IDs. |
| `fileFormat.csv` → EDAM | C2M2 | 97 terms, 19 EDAM. (CRDC `file_type` is an identity map: 97 of 97.) |
| `assay.csv` → OBI | C2M2 | 391 terms, 20 OBI, 33 with no ID. `file.assay_type` holds one value; MC2 `Assay` can hold several. |
| Tumor status → IS_TUMOR | dbGaP | 5 terms. |
| CRDC identity enums | CRDC | 26 mapped fields where every MC2 term matches the GC vocabulary export, checked by script. Examples: Sex, Tumor Grade, the TNM stages, morphology (1,152), file type (97), sample type category, preservation method (`embedding_medium`), imaging assay type, and the library source fields. No crosswalk needed. Near-identity: instrument model (76/77), treatment type (37/38), library strategy (41/43), library selection (35/38), disease type (42/46). |
| CRDC partial enums | CRDC | Unmatched MC2 terms per field: `organ_or_tissue` from Tissue, 85 of 114 (17 more differ only in case); `sample_type`, 56/61; `organism_species`, 30/32 (GC allows only Canine, Cell Line, Human, Mouse); `license`, 326/326 (GC allows 4 CC licenses); `tissue_fixative`, 13/17. |
| NCIt / UBERON → caDSR strings | CRDC | Open reference fields with a long tail. Primary Diagnosis has 801 CDS values and Therapeutic Agent has 4,475. |

#### Gaps in the MC2 model that block required target fields

| Gap | Blocks | Note |
|---|---|---|
| **No consent-group concept** | dbGaP `CONSENT` (required). CRDC `consent_group` (conditional). | DUO codes exist only at the study and file level. Consent groups could be derived as "one integer per distinct DUO set of a subject's files", but DUO→GRU/HMB/DS-X loses detail. This needs a model decision. |
| No race / ethnicity on Individual | C2M2 `subject_race` (only if that table is populated). dbGaP and CRDC (optional). | Also raised in the standards review. |
| `NGS Library Layout`: the description says "one of Paired-end or Single", but the values are `Paired-end, Single-indexed` | GEO, SRA | "Single-indexed" is **inherited from CRDC**. GC 13.0.1 `library_layout` has it too and has no single-end value. So CRDC is an identity map. GEO and SRA need single/paired, which should come from `Read Indicator`. The MC2 description is what's inaccurate. |
| No `study_external_url` / `study_access` | CRDC (required) | Both can be filled from config or derived per study. |
| No extract protocol | GEO (required) | Same gap as "Protocol Link" in the standards review. |
| Checksum coverage | C2M2 (md5/sha256 required), CRDC/dbGaP upload manifests (MD5) | Real-data coverage of `File Data Checksum Value` is unknown. |

## Approach

### Part A: Attribute-mapping layer (all four targets)

1. **Create one SSSOM file per target from the scoping drafts in
   `mappings/standards/drafts/`**, at
   `kg-pipeline/mappings/standards/{c2m2,geo,dbgap,crdc}.sssom.tsv`.
   - Columns: `subject_id`, the MC2 slot CURIE from `mc2_model.ttl`;
     `predicate_id`, mapped exact→`skos:exactMatch`, close→`closeMatch`,
     broad and narrow→`broadMatch`/`narrowMatch` (MC2 perspective), and
     none→`sssom:NoTermFound`; `object_id`, the target field CURIE (see
     Decision 3); `mapping_justification`; `comment`, naming the value
     crosswalk or `none`.
   - Rows for out-of-scope target tables (gene, proteomics, radiology and so
     on) are dropped, not carried as `NoTermFound`.
   - For CRDC, the `CRDC_CDE` tags already on the attributes are kept and
     cross-checked against the target CDE.
2. **New `scripts/link_standard_mappings.py`** writes
   `data/rdf/standard_mappings.ttl` with one SKOS triple per mapped row.
   - It follows the pattern of `link_ontology_crosswalk.py`.
   - A new `link-standard-mappings` Make target runs it, and that target is
     added to `full-kg`.
   - New `queries/examples/standard_mappings.rq` answers "where does MC2
     attribute X go in each target?"

### Part B: Shared value crosswalks

3. **Review the four existing NCIT→MONDO/UBERON crosswalks.** All their rows
   are unreviewed today.
4. **Build only the crosswalks that serve the first exporter** (Decision 1),
   in the shared-first order from the table above: species, sex, anatomic
   site, sequencing platform and library fields, and biospecimen type.
   - Output goes to `kg-pipeline/mappings/crosswalks/<cv>_to_<target>.sssom.tsv`.
   - They are generated with `crosswalk_ontology.py`'s `reviewed` flag
     pattern, and only reviewed rows are used.
   - Crosswalks that a target can't use yet are not built.

### Part C: Reference exporter

5. **New `scripts/export_<target>.py`.** It runs SPARQL over the merged graph,
   applies the Part A mapping file and the Part B crosswalks, and writes the
   target's native format to `data/export/<target>/`.
   - Values that can't be mapped go to an `unmapped_<target>.csv` report and
     are never silently dropped.
   - A new `export-<target>` Make target runs it.
6. **Validate with the target's own validator where one runs locally.** For
   C2M2 that is `cfde-c2m2 validate`, which needs approval to add as a
   dependency. CRDC, GEO and dbGaP validate only on the server, so for them
   the exporter checks required fields and enum membership itself, against
   the scoped field inventory.

### Part E: Provenance step layer (PROV-O), derived in the KG

MC2 records experiment **outputs** as template rows linked by keys. The
**steps** between them are implicit: their details sit on whichever row they
produced. Examples are `NGS Library Preparation Kit Name` on Level 1 and
`Software and Version` on Level 2. Part E makes those steps explicit in the
graph, using W3C PROV-O. PROV is already used in `manifest.ttl`. Templates
and submitters are unaffected.

7. **Declare the step edges in `kg-pipeline/mappings/provenance_steps.yaml`.**
   Each edge names an input class, an output class, the joining key, a step
   type, and the MC2 attributes that describe that step. Proposed edges,
   using keys that exist today:

   | Step | Input → output (key) | Step attributes (examples) |
   |---|---|---|
   | Specimen collection | Individual / Model → Biospecimen (`Individual Key`, `Model Key`) | Acquisition Method, Collection Site, Timepoint Type/Offset, Preservation Method/Medium/Temperature |
   | Specimen derivation | Biospecimen → Biospecimen (`Parent Biospecimen Key`) | Embedding Medium, Stain. The step type comes from the new attribute in Decision 7. |
   | AOI selection (GeoMx) | Biospecimen → ROI Segment Annotation (`Biospecimen Key`) | GeoMx Scan name, Tags, Tissue Stain |
   | Library prep + sequencing | Biospecimen / AOI → Sequencing, Visium or GeoMx Level 1 (`Biospecimen Key`, `NanoStringGeoMXROISegmentAnnotation Key`) | NGS Library Preparation Kit *, Library Strategy/Selection/Layout, Sequencing Platform |
   | Imaging acquisition | Biospecimen → Imaging Level 1 | Image Platform Model, Objective, Protocol Link |
   | Computational processing | Level N → Level N+1 (`…LevelN Key`) | Software and Version, Workflow Type/Version/Link/Parameters, Genomic Reference |

8. **New `scripts/build_provenance.py`** writes `data/rdf/provenance.ttl`,
   following the pattern of `link_scdm.py`. For each joined pair of rows it
   creates one step node:
   - It is typed `prov:Activity`, plus an OBI planned-process class per step
     type (the class IRIs still need an OLS check).
   - It links `prov:used` to the input and `prov:wasGeneratedBy` from the
     output.
   - The step attributes go on the step node. They are also left on the row
     that produced them, so existing queries keep working.
   - The step IRI is deterministic: `{output IRI}/activity/{step type}`.
   - Only PROV and OBI types are asserted, never governanceDUO-owned types
     (the D9 principle).

   Steps that pool or split are handled naturally. A Level 3 file with
   several Level 2 keys gets one step with several `prov:used` links.
   A new `provenance` Make target runs the script, inside the
   access-controlled assay KG chain.
9. **Missing intermediate steps degrade gracefully.** No material nodes are
   invented. If nothing records a section between a biopsy and a Level 1
   file, the graph has one step from the biopsy to Level 1, typed with the
   generic planned-process class.

**Depends on Part D (Decision 2).** File View, the only assay class loaded
today, has a `Biospecimen Key` and nothing else to chain to, so without
Individual, Biospecimen and Level 1-3 instance data there are no edges to
derive.

**How Part E helps exports.** GEO's PROTOCOLS section (extract, library
construction, data processing steps, genome build) and SRA's experiment
record both describe steps. With step nodes, each of these comes from one
query instead of being assembled from attributes on different rows.

#### Handling sample-preparation and AOI-selection steps

A **"derived from" link already exists**: `Parent Biospecimen Key`.
Combined with the existing `Biospecimen Type` values for intermediate stages
("Slides", "FFPE Scrolls", "Analyte", "Total RNA" and others), it can already
represent block → section → extract chains as Biospecimen rows. What's
missing is **how** each child was derived. Part E would type that step as
generic. Three pieces would fix it, and only the second is a model change:

- **Guidance, not schema.** Document in the Biospecimen docs that each
  physically distinct stage used downstream (block, section or slide,
  dissociated cells, extract) gets its own Biospecimen row, chained by
  `Parent Biospecimen Key`.
- **One optional attribute on the child, `Biospecimen Derivation Method`.**
  It records how the row was produced from its parent: sectioning,
  macro- or microdissection, dissociation, nucleic acid extraction,
  aliquoting, cell sorting. It would use a small CV bound to OBI
  planned-process terms. This becomes the step type in Part E. A matching
  `Biospecimen Derivation Protocol Link` would close the same protocol gap
  as GEO's required extract protocol. Process parameters such as section
  thickness are added only when a consumer needs them.
- **AOI selection needs nothing new.** The ROI Segment Annotation row is the
  AOI, its `Biospecimen Key` points to the slide, the template implies the
  step type, and its parameters (Tags, Tissue Stain, Scan name) already
  exist.

## Decisions needed before implementing

1. **The first reference exporter.**
   - **C2M2:** the only target exportable from today's KG (file level only),
     and the only one with a local validator. The catch is that CFDE's
     willingness to accept non-Common-Fund submissions is unconfirmed.
   - **CRDC:** the strongest existing overlap. It has 44 exact matches,
     26 enums that need no value mapping (checked against the GC
     vocabulary export), the existing CDE tags and the prior GC map.
     It is the most likely real destination for MC2 data. It requires
     Decision 2, and its validation is server-side only.
   - **My recommendation: CRDC**, if real submissions are expected. Otherwise
     C2M2 as a low-risk proof of the architecture.
2. **Extract Individual and Biospecimen instance data into the KG.**
   Every target except file-level C2M2 needs it. This means extending
   `extract_mc2_assay_metadata.py`, which is currently File View only, to
   these classes in the access-controlled assay KG. This adds scope.
   Proposal: add it to this plan as Part D, ahead of Part C.
3. **IRIs for target fields.** Use the target's own namespace where one exists
   (CRDC properties carry caDSR CDE IDs, which can serve as `object_id` where
   bound). Otherwise use the placeholder
   `https://w3id.org/mc2-center/standards/<target>/<table>.<field>`.
4. **Consent groups.** Should MC2 model them (a model change), or should the
   dbGaP exporter derive them from DUO sets? dbGaP can't be exported without
   one or the other.
5. **Pin the CRDC source.** Commit the GC dictionary and vocabulary exports
   to `kg-pipeline/mappings/standards/source/crdc/v13.0.1/` so the crosswalks
   and the exporter are reproducible. This would be a new folder of
   third-party files.
6. **Part E scope.** Should the provenance layer be in this plan or a
   separate one? It serves exports, but it is also its own initiative, and
   the `plans/` convention is one file per initiative. Whichever you choose,
   it is sequenced after Part D.
7. **`Biospecimen Derivation Method` (and the protocol link).** Do you want
   these new optional Biospecimen attributes? This is a model change, so it
   would go through the model-change plan that comes out of
   `standards_alignment_review.md`, not this plan.

## Verification

- `make test` passes, with new tests for:
  - `link_standard_mappings.py`: SSSOM → triples, and `NoTermFound` rows
    produce no `skos` triple.
  - `export_<target>.py`: run against a fixture graph in `test/fixtures/`
    with no live Synapse, checking output headers and tables, required-field
    checks, and the unmapped report.
- Part E:
  - Tests on a fixture chain (Individual → Biospecimen → child Biospecimen →
    Level 1 → 2 → 3) check that each edge produces exactly one
    `prov:Activity` with the right `prov:used` and `prov:wasGeneratedBy`
    links.
  - A pooled Level 3 file produces one step with several inputs.
  - Step IRIs are stable across reruns.
  - A new example query, `queries/examples/provenance.rq` ("all data derived
    from biospecimen X"), returns the full chain.
- A test checks that every `subject_id` in the `mappings/standards/` files
  resolves to a slot in `mc2_model.ttl`.
- `make full-kg && make validate` still pass, and
  `queries/examples/standard_mappings.rq` returns rows for all four targets.
- `make export-<target>` against the live graph produces output that passes
  the local validator (C2M2) or the exporter's own required-field and enum
  checks (CRDC). Unmapped-value counts are recorded in the Implementation
  Report.
- The orchestrator reviews each subagent diff against this plan, and an
  independent pre-PR review runs before `gh pr create`.

## Process

Store this plan at plans/metadata_export_pipeline.md for review before
implementing. After implementing, append an Implementation Report below this
line.
