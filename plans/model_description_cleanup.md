# Model-wide cleanup: remove process/historical narration from model content

## Context

Standing directive (see `~/.claude` memory `feedback_no_process_narration_in_model`,
saved 2026-09-10): the data model's own content (`Description`/`Notes`/other
free-text columns in `modules/*/annotationProperty.csv` and CV CSVs) must stay
user-facing - it should help someone understand, navigate, and consume the
model. Process narration, curation history, and internal-review commentary
belong in `plans/`/reports instead. Caught first on `Biospecimen Type
Category` (see `plans/biospecimen_type_category_cde_fix.md`), then escalated
to a full model-wide sweep by explicit user request.

An audit (fork, 2026-09-10) grepped every `modules/*/annotationProperty.csv`
and every CV CSV referenced from `modules/mapping.yaml` for this pattern.
Verified and extended its findings directly (the audit undercounted the
per-row attribution-stamp pattern - re-swept with a broader regex covering
`"Added by X <date>"`, `"X added <date>"`, and bare `"<initials> <date>"`
stamps) before applying any edit.

## What was changed

**1. Per-row curator-attribution stamps in the `Notes` column - cleared
entirely (zero navigational value; git blame is the right tool for "who
added this and when," not a per-row model field).** 623 rows across 9 files:

| File | Rows cleared |
|---|---|
| `tool/tool_data.csv` | 144 |
| `tool/tool_operation.csv` | 118 |
| `tool/tool_topic.csv` | 114 |
| `tool/tool_format.csv` | 118 (117 stamps + 1 rewritten, see below) |
| `shared/assay.csv` | 92 (+ 13 individually reviewed, see below) |
| `shared/tumorType.csv` | 15 (+ 1 individually reviewed) |
| `shared/tissue.csv` | 8 |
| `tool/tool_language.csv` | 10 (this file's Notes column is lowercase `notes` - a separate, pre-existing header-casing inconsistency, not fixed here) |
| `tool/tool_license.csv` | 1 |

**2. `shared/assay.csv` - 13 rows individually reviewed** (process narration
mixed with a genuinely useful disambiguation fragment, or pure narration):
- `X-Ray Diffraction`, `in vivo tumor growth`, `in silico synthesis`,
  `in vivo PDX viability`, `histology`, `proximity extension assay`: cleared
  entirely (pure "added while aligning modules/dataCatalog... (2026-09-01)"
  narration - already fully documented in
  `plans/datacatalog_kg_integration.md`, no information lost).
- `RNA array`, `shRNA-seq`, `spatial transcriptomics`, `compound screen`,
  `metabolic screening`: shortened to just the useful disambiguation
  fragment (e.g. "Distinct from the more specific DNA Gene-Expression
  Microarray/MicroRNA Expression Array rows in this CV."), dropping the
  attribution/date/"added while aligning" preamble.
- `Clinical Study`, `Survival Analysis`: shortened to the substantive
  alias-rationale, dropping the `"AG 2023-09-22 /"` attribution prefix.

**3. `tool/tool_format.csv` - `DCC` row**: `"OB 1/11/2024, to be used in
GeoMX metadata"` -> `"To be used in GeoMX metadata."` (kept the one useful
fact, dropped the attribution/date).

**4. `shared/tumorType.csv` - `Choriocarcinoma` row**: cleared
`"From ICD-O-3, definition from NCIt"` (Source column already says
`ICD-O-3`; the cross-source composition detail doesn't help someone use the
term).

**5. `dataCatalog/dataCatalog_data_type.csv` - 7 rows cleared**: all were
"Aligned with modules/shared/mc2_iconTag_map_3-4-25.csv label: X" or "no
existing label fits... added as a new category" - crosswalk-decision
narration, already fully documented in `plans/datacatalog_kg_integration.md`.

**6. `biospecimen/pathology.csv` - 9 rows cleared, 1 attribute Description
updated instead.** Every row in this CV carried an identical
`"Not in use as of MC2 data model v8.x.x"` Notes value - redundant 9x over
and tied to a specific model version. Cleared all 9, and added the
underlying fact once, version-independently, to the attribute's own
Description in `biospecimen/annotationProperty.csv`:
`Biospecimen Pathology` -> `"The pathology identifier associated with the
biospecimen. Not currently in use."`

**7. Three attribute Descriptions rewritten to drop embedded
process/decision narration** (in `annotationProperty.csv` files, not CVs):
- `biospecimen/annotationProperty.csv` - `Biospecimen Acquisition Method`:
  dropped "Valid Values replaced with CRDC_CDE:15115495's... the prior
  free-text list's more granular terms... no longer have a direct slot --
  CDE:6626651 remains flagged for follow-up review" - this exact follow-up
  is already tracked in `plans/crdc_cde_integration.md` (lines 267, 566-567,
  1235, 1867). New Description: "Records the method of acquisition or
  source for the specimen under consideration."
- `individual/annotationProperty.csv` - `Individual Year of Birth`: dropped
  "Note: a PHI/de-identification consideration was raised and accepted for
  this field -- see plans/crdc_cde_integration.md" - already tracked there
  (lines 198-201). New Description: "The 4-digit year of the subject's
  birth."
- `biospecimen/annotationProperty.csv` - `Biospecimen Type Category`: see
  `plans/biospecimen_type_category_cde_fix.md` (done in the prior,
  immediately-preceding pass this session).

## Explicitly left alone (reviewed, not process narration)

- `education/ed_language.csv` - every row's Notes documents the *external*
  ISO 639-1 standard's own revision date ("ISO 639-1 2-letter language codes
  updated 1/11/2013"), not this model's edit history. Legitimate.
- All uses of words like "verified"/"investigation"/"curation" inside real
  NCIT/EDAM/DUO term *definitions* (scientific sense, not process
  narration) - e.g. `grant/grant_type.csv`'s R01 definition,
  `tool/tool_topic.csv`'s EDAM "Bioinformatics" definition.
- Example/test fixture files (`grant/exampleColumn.csv`, etc.).

## Not addressed here (flagged for a separate look)

- `shared/GC_v6.0.4_MC2_11.0.0_map_6-24-25.csv` - filename itself embeds a
  date; existence/live-usage status not checked in this pass.
- `modules/governance/*.model.csv` - a different artifact shape entirely
  (full schematic-style columns, not a CV term list); already flagged in an
  earlier, separate audit as possibly orphaned - not re-chased here.
- `tool/tool_language.csv`'s lowercase `notes` header (vs. every other CV's
  `Notes`) - a pre-existing inconsistency noticed in passing, not part of
  this directive's scope.

## Verification

- Every bulk edit done via `csv.reader`/`csv.writer` preserving each file's
  original quoting convention (`QUOTE_ALL` for `pathology.csv`, otherwise
  `QUOTE_MINIMAL`) and encoding (`utf-8-sig` where a BOM was already
  present) - `git diff` on each file confirmed only the `Notes`/`Description`
  cell content changed, no incidental reformatting of untouched rows or
  columns (spot-checked full before/after row pairs, not just cell counts).
- Confirmed `Notes` is never read by `create_json_from_model.py` or
  `convert_model_to_jsonld.py` (`grep -n Notes` on both - zero hits), so
  clearing Notes cells has no effect on any generated JSON
  schema/JSON-LD - only the `Description` rewrites (3 attributes) required
  regenerating downstream artifacts.
- `make collate` regenerated `mc2.model.csv`/`all_valid_values.csv` clean.
- `create_json_from_model.py Biospecimen Individual FileView` regenerated
  the 3 affected schemas; a full `make generate-json` across all ~30 data
  types confirmed no other schema file changed as a result of this pass.
- `python3 convert_model_to_jsonld.py` regenerated `mc2.model.jsonld`
  cleanly (valid JSON, parses).

## Process

Store this plan at `plans/model_description_cleanup.md`. This report itself
stands as the completed record - no further action pending from this pass.
