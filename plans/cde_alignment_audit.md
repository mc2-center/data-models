# Model-wide CDE/CRDC_CDE alignment audit

## Context

Standing rule (see `~/.claude` memory `feedback_cde_alignment_is_mandatory`):
any attribute with a `CDE:`/`CRDC_CDE:` reference in its `Properties` column
must have its controlled vocabulary fully match that CDE's real
permissible-value list from caDSR - established after `Biospecimen Type
Category` was initially left incomplete (see
`plans/biospecimen_type_category_cde_fix.md`).

Ran three parallel audit forks across every `modules/*/annotationProperty.csv`
(115 CDE-referencing rows across 18 files), each fetching real CDE records
via `~/.claude/skills/cadsr-cde-match/scripts/cde_match.py`'s
`fetch_cde_record()` and diffing against the attribute's actual current
value space (CV file, or hardcoded `Valid Values`), prioritizing
`CRDC_CDE:`-mapped rows per a mid-audit steer.

## Findings summary

Most CRDC_CDE-tagged enumerated fields (15+) were already exact matches -
no action needed. Real findings fell into two very different categories:

**A. Genuine missing-value gaps (safe to close by adding real values)** -
fixed in this pass, see below.

**B. Structural mismatches where literal alignment would be actively
harmful** - flagged to the user, NOT fixed here, awaiting direction:
- `Assay` / `DSP Dataset Assay` (`CRDC_CDE:12373576`): CDE has only 9 broad
  categories; the model has 391/~400 curated EFO/OBI-anchored terms.
  Literal alignment would mean deleting ~390 real values.
- `Image Assay Type` / `GeoMx DSP Assay Type` (`CDE:7789196`): both cite the
  same CDE but have completely non-overlapping current value sets, neither
  matching the CDE's real 23-value list.
- `Biospecimen Embedding Medium` (`CDE:8037927`): current values are
  embedding compounds; the CDE's real permissible values are liquid
  cell-culture media - looks like the wrong CDE is tagged entirely.
- `Biospecimen Preservation Method` (`CRDC_CDE:8028962`): several current
  values look like they belong to `Biospecimen Preservation Medium`'s own
  CDE instead (cross-contamination between the two attributes).
- `Biospecimen Composition` (`CRDC_CDE:12922545`): 12 values beyond the
  CDE's real 11, plus case mismatches (`Not applicable` vs `Not Applicable`).
  Unlike the other findings, "fixing" this could mean removing values that
  may be in live use.

**C. Needs more careful reconciliation, not a blind add** (not started):
- `File Format`/`Dataset File Formats` (`CRDC_CDE:11416926`, one CV backing
  two attribute names): real gaps exist but mixed with case/naming variants
  of already-present values (`JPG` vs `JPEG`, `TAR Format` vs `TAR`, etc.) -
  needs a per-value rename-vs-add judgment call.
- `NGS Library Strategy` (`CRDC_CDE:6273393`): missing 4 real values, 2
  current values (`RNA-Seq`, `DNA-Seq`) may be generic stand-ins for some of
  them - ambiguous.
- `License` (legacy `CDE:14902606`): the model's SPDX-based `tool_license.csv`
  already covers all 4 real CDE values, just under SPDX hyphenated naming
  (`CC-BY-4.0` vs `CC BY 4.0`) - a formatting-convention difference, not a
  real gap. Low priority.

**D. Needs retry / low priority**: 3 CDE ids failed to fetch twice
(`Study Description` CDE:03444002, `Study_id` CDE:12960571,
`Study Deidentification Method Type` CDE:14576319) - transient API issue or
malformed ids, unresolved. `DSP Data Use Codes` (CDE:0002001) has a
suspicious id format and returned no data - this field is DUO-based anyway,
likely a non-issue.

**E. Deliberately NOT touched**: `Sex` (`CRDC_CDE:7572817`) has 9 values vs.
the CDE's 3 (`Male`/`Female`/`Unknown`) - the extra inclusive/modern
demographic options are a deliberate broadening, not a gap to shrink.

## Fixes applied in this pass (category A)

- **`Treatment Type`** (`shared/treatmentType.csv`, `CRDC_CDE:14737565`):
  added the 7 missing real values (`Oncolytic Virus Therapy`,
  `Vaccine Therapy`, `Conditioning Therapy`,
  `Immunosuppressive Therapy/GVHD Prophylaxis for Transplant`,
  `Post-Transplant Salvage Therapy`, `Ablation Therapy`, `Targeted Therapy`),
  each with a real NCIT code from a fresh OLS lookup. Now 38/38 (37 real +
  1 legitimate extra, `Control`, a study-design concept - kept, not
  CDE-backed but not a gap either).
- **`NGS Sequencing Platform`** (`sequencingLevel1/seqPlatform.csv`,
  `CRDC_CDE:6352164`): added the 10 missing real values (mostly newer
  Illumina instruments and two legacy methylation arrays / two Affymetrix
  expression arrays / one SNP array), reusing EFO/OBI/NCIT codes via OLS
  lookup. Two values (`Illumina Human Methylation 27`/`450`) had no
  defensible ontology match found in EFO/GENEPIO/OBI - added with a blank
  Ontology Identifier and an explicit "No defensible ontology match found"
  Notes entry, matching this file's own pre-existing precedent
  (`Illumina NextSeq 2500` already carries the same kind of documented gap).
  `Illumina NovaSeq S4` reuses the existing `Illumina NovaSeq 6000` row's
  EFO code (S4 is a flow-cell configuration of the same physical
  instrument, not a distinct one). Now 77/77 (76 real + legitimate extra
  `Complete Genomics`).
- **`File Data Checksum Type`** (`file/annotationProperty.csv`, hardcoded,
  `CRDC_CDE:11475057`): corrected from `SHA-1, SHA-256, SHA-512` (wrong
  casing on two real values, one entirely non-existent value) to the CDE's
  exact literal permissible values: `md5sum, sha1, sha256`.
- **`Biospecimen Stain`** (`biospecimen/annotationProperty.csv`, `CDE:8120269`):
  had zero `Valid Values` despite being `Required: True`. Created a new CV,
  `modules/biospecimen/stainType.csv` (6 rows: `H&E`, `IHC`,
  `In situ hybridization`, `mIHC`, `Other`, `Wright-Giemsa`, each with a
  real NCIT code - `Other` reuses this repo's own established
  `NCIT:C17649` convention), and registered it in `modules/mapping.yaml`.

## Verification

- All 4 fixes verified for exact CDE parity via direct set-diff against a
  freshly-fetched CDE record (not the audit forks' summarized counts).
- `make collate` (`mc2.model.csv`/`all_valid_values.csv`),
  `make generate-json` (full run across all ~30 data types - 10 schema
  files affected: `Biospecimen`, `FileView`, `Individual`, `Model`,
  `10xVisiumRNALevel1`, `NanoStringGeoMxDSPLevel1`/`Level2`,
  `SequencingLevel1`/`Level2`, `SequencingRNALevel1`), and
  `convert_model_to_jsonld.py` all regenerated cleanly (valid JSON/JSON-LD).
- kg-pipeline's own `mc2_model.linkml.yaml`/`mc2_model.ttl` regenerated
  (`make mc2-model-linkml && make schema`); its 97-test suite passes
  unchanged.

## Process

Store this plan at `plans/cde_alignment_audit.md`. Category B/C/D items
remain open - see above for exactly what each needs before it can be
closed. Do not re-run the full 3-fork audit for these remaining items;
resume from this document's findings instead.
