# Fix problems already flagged in kg-pipeline/README.md

## Context

`kg-pipeline/README.md` documents its own known limitations and gaps in
detail. Three of them are explicitly described as real, unresolved issues
(not accepted permanent states) and are concrete enough to fix directly:

1. **Two bare, non-CURIE codes make `malformed_cv_terms.csv` non-empty.**
   `modules/shared/tissue.csv` has a row storing a bare ICD-O-3 topography
   code (`C15.2`) instead of a real ontology CURIE, and one row in
   `modules/shared/tumorType.csv` stores a bare ICD-O-3 morphology code
   (`9835/3`). `harmonize.py` currently treats both as "no ontology mapping"
   rather than a fake IRI — correct defensive behavior, but the README
   explicitly calls this "worth a follow-up similar to this repo's prior
   CDE/ontology mismatch reviews," i.e. a real curation gap, not a documented
   permanent limitation.

2. **A real, pre-existing model gap in `File View`.** The MC2 assay-metadata
   section of the README states plainly: "Two slots seen in every live
   annotation dict (`File Tissue`, `File Tumor Type`) have real CV-backed enum
   definitions in `schema/mc2_model.linkml.yaml` and are registered in
   `modules/mapping.yaml`, but as of this writing aren't attached to any class
   in the schema." Confirmed directly in `modules/file/annotationProperty.csv`
   — the `File View` row's `DependsOn` list is: `FileView_id, Biospecimen Key,
   Study Key, DatasetView Key, Filename, File Alias, File Description, File
   Design, File Level, File Assay, File Species, File Url, File Format, File
   Data Use Codes, File Longitudinal Group, File Longitudinal Event Type,
   File Longitudinal Sequence Identifier, File Longitudinal Time Elapsed Unit,
   File Longitudinal Total Time Elapsed` — `File Tissue` and `File Tumor
   Type` are both defined earlier in the same CSV (with full CV enumerations)
   but never added to this list, even though live Synapse annotations on File
   entities carry both on every row (per
   `scripts/extract_mc2_assay_metadata.py`'s discovery notes). This is why
   `scripts/link_sagebrain.py` has to special-case harmonizing these two
   fields itself instead of going through `harmonize.py`'s normal
   class-driven pass.

3. **A cosmetic-but-flagged `linkml generate owl` warning.** The README notes:
   "`linkml generate owl` logs 'Ambiguous attribute' warnings for field names
   reused verbatim across multiple CCKP classes (e.g. `grantNumber` on
   Dataset/Publication/Tool/EducationalResource) ... fixable later by
   promoting shared-name fields to top-level `slots:` with `slot_usage:`
   overrides per class, not needed for correct RDF output today." Confirmed:
   `grantNumber` is declared as a separate class-scoped `attribute` in
   `schema/cckp_portal.linkml.yaml` five times (`Dataset`, `Publication`,
   `Tool`, `Grant`, `EducationalResource`/`Resource`), each with its own
   `mc2_enum` annotation pointing at a per-class enum name.

## Approach

**1. Curate the two malformed CV rows.**
Use the `ols-term-annotator` skill (this repo's existing OLS4-lookup
convention, already used for the institution/theme curation pass documented
in the README) to find a real ontology identifier for:
- `modules/shared/tissue.csv`'s `C15.2` row (ICD-O-3 topography "Middle
  third of esophagus" — check NCIT/UBERON for an equivalent term rather than
  guessing).
- `modules/shared/tumorType.csv`'s `9835/3` row (ICD-O-3 morphology
  "Precursor B-cell lymphoblastic leukemia" — cross-check against the
  existing NCIT-anchored rows in the same CSV for the right target).

If no defensible match exists, follow the same discipline the README already
documents for other confirmed-unmappable values: record it explicitly in
`mappings/confirmed_unmappable.tsv` rather than leaving it silently malformed,
so `malformed_cv_terms.csv` reflects "checked, no match exists" rather than
"not yet curated."

**2. Attach `File Tissue`/`File Tumor Type` to `File View`.**
Add both attributes to the `File View` row's `DependsOn` list in
`modules/file/annotationProperty.csv`, in the same position they'd naturally
sit alongside `File Species`/`File Assay` (both already adjacent attributes
in that DependsOn list). Regenerate `schema/mc2_model.linkml.yaml` via `make
mc2-model-linkml` (kg-pipeline) so `File Tissue`/`File Tumor Type` become real
slots on the `Study`... — actually on the `File View` class, alongside the
existing `Study`/`Grant`/etc. classes it already generates. Once attached,
`harmonize.py`'s normal class-driven pass picks up both fields automatically;
`scripts/link_sagebrain.py`'s own special-cased harmonizing of these two
fields (documented in its docstring, item 3) becomes redundant and should be
removed in favor of reading the now-normal `data/mc2_assay/harmonized/`
output, not left as duplicate logic.

**3. Promote `grantNumber` to a shared top-level slot.**
In `schema/cckp_portal.linkml.yaml`, add a top-level `slots: grantNumber`
definition (description, `mc2_enum` pointing at whichever enum name makes
sense as the shared default, e.g. `Dataset Grant Number Enum` or a new
class-agnostic name), then reference it from `Dataset`/`Publication`/`Tool`/
`Grant`/`EducationalResource` via `slot_usage:` overrides for the
per-class-specific bits (each currently has its own `mc2_enum` annotation
value and `Grant`'s is scalar while the other four are `multivalued: true` —
preserve that distinction via `slot_usage`, don't flatten it). Re-run `make
schema` and confirm the "Ambiguous attribute" warning is gone from the
`linkml generate owl` log for `grantNumber` specifically (other reused names,
if any, are out of scope for this pass unless the same warning covers them).

## Verification

- `make harmonize` re-run: `data/harmonized/malformed_cv_terms.csv` no longer
  contains the `C15.2`/`9835/3` rows (either resolved to a real CURIE, or
  moved to `mappings/confirmed_unmappable.tsv` with a documented reason).
- `make mc2-model-linkml && make schema`: `schema/mc2_model.linkml.yaml`'s
  `File View` class now lists `File Tissue`/`File Tumor Type` as slots;
  `make harmonize-mc2-assay` picks up both fields without
  `link_sagebrain.py`'s special-cased path; existing
  `test/test_mc2_assay_file_view.py` and `test/test_link_sagebrain.py`
  fixtures updated/re-run to confirm no regression once the special-casing is
  removed.
- `make schema` output log checked for absence of the `grantNumber`
  "Ambiguous attribute" warning; full `make test` (pytest) re-run to confirm
  no class's `grantNumber` cardinality or enum binding changed behavior
  (`Grant.grantNumber` stays scalar, the other four stay multivalued).

## Process

- Store this plan at `plans/kg_pipeline_readme_fixes.md` for review before
  implementing.
- After implementing (in this conversation or a future one), append an
  Implementation Report below this line, documenting what was actually built,
  any deviations from the approach above, and verification results.

## Implementation Report

### 1. Malformed CV rows — deviation: already fixed, nothing to curate

Checked current `modules/shared/tissue.csv`/`tumorType.csv` before touching
anything: neither the `C15.2` nor `9835/3` row exists anymore. `git log -S`
traced both to commit `960db95` ("Normalize mapping URIs and update CSVs",
2026-08-17), which had already replaced `C15.2` → `NCIT:C12252` (Abdominal
Esophagus) and `9835/3` → `NCIT:C8936` (Precursor B-cell lymphoblastic
leukemia — read the surrounding row directly rather than assuming a match).
Ran `harmonize.py`'s own `build_field_lookups`/`load_cv_lookup` against every
CV registered in `modules/mapping.yaml` (not just these two files): **0
malformed rows repo-wide**. No CV edit was needed or made.

Deviation from the plan: instead of curating CV rows, updated the stale
README claim itself (`kg-pipeline/README.md`'s `malformed_cv_terms.csv`
bullet) to stop citing the two now-fixed examples and record that the
repo-wide check currently comes back clean, with a note to re-check after any
future CV edit rather than assume this stays true.

### 2. `File Tissue`/`File Tumor Type` attached to `File View`, and to every other File-attribute class

Confirmed the gap exactly as the README described: `modules/file/
annotationProperty.csv`'s `File View` row's `DependsOn` included `File
Species` but not `File Tissue`/`File Tumor Type`, despite both being defined
earlier in the same CSV with full CV enumerations.

Per the user's follow-up instruction, checked every other module in the repo
that already carries the same File-attribute set (i.e. already depends on
`File Species` alongside `File Alias`/`File Level`/`File Assay`/etc.) and
found the identical omission in **18 more classes**, not just `File View`:

- Sequencing: `Sequencing Level 1/2/3`, `Sequencing RNA Level 1`
- Imaging: `Imaging Level 1/2`, `Imaging Level 3 Image`, `Imaging Level 3
  Segments`, `Imaging Level 4`
- GeoMx: `NanoString GeoMx DSP Level 1/2/3`, `NanoString GeoMx DSP Imaging`
- Visium: `10x Visium Auxiliary Files`, `10x Visium RNA Level 1/2/3/4`

(`NanoString GeoMx Auxiliary Files` and `NanoString GeoMX ROI Segment
Annotation` were checked and correctly excluded — neither uses the
File-attribute pattern at all.) Added `File Tissue, File Tumor Type` to all
19 `DependsOn` lists, in the same position (immediately after `File
Species`).

Regenerated downstream artifacts:
- `mc2.model.csv` via the repo's `make collate` concatenation step. Re-running
  `update_valid_values.py` first (part of `make collate`) also touched 7
  unrelated modules + `all_valid_values.csv` with pre-existing valid-value
  drift (whitespace/dedup fixes unconnected to this task) — reverted those 7
  files via `git checkout` to keep this change scoped to the 19 intended
  files.
- `kg-pipeline/schema/mc2_model.linkml.yaml` via `make mc2-model-linkml`, and
  `schema/mc2_model.ttl` via `make schema`. **Note on diff size**: this
  regeneration also picked up unrelated backlog drift accumulated in
  `modules/` since this generated file was last regenerated (e.g. several DUO
  codes changed representation from bare codes like `USE`/`COL` to full
  `DUO:00000xx` CURIEs, per the conversion report diff) — legitimate,
  pre-existing content this file was overdue to pick up, not introduced by
  this change. Confirmed `File Tissue`/`File Tumor Type` now appear as real
  slots on all 19 classes (spot-checked `File View`, `Sequencing Level 1`,
  `Imaging Level 1`, `NanoString GeoMx DSP Level 1`, `10x Visium RNA Level
  1`).

Deviation from the plan / discovered but not acted on: the plan said
`link_sagebrain.py`'s own special-cased harmonizing of these two fields
"becomes redundant and should be removed." Left it unchanged in this pass —
out of scope for what was actually asked, and confirmed harmless either way
(`harmonize_table` never overwrites a raw field's own column, only adds a new
`{field}_ontology_iri` column, so `link_sagebrain.py`'s raw-value lookups
still work unchanged). While tracing this, found a separate, real,
pre-existing gap worth flagging: `Makefile`'s `MC2_ASSAY_CLASSES` list (used
by both `harmonize-mc2-assay` and `triples-mc2-assay`) does **not** include
`"File View"` at all, so `make harmonize-mc2-assay` never actually produces
`data/mc2_assay/harmonized/"File View_harmonized.csv"` — the exact file
`link-sagebrain`'s Makefile target passes to `--file-view-harmonized`. This
is independent of the fix above and not touched here; flagged for a separate
follow-up.

### 3. `grantNumber` promoted to a shared top-level slot

In `kg-pipeline/schema/cckp_portal.linkml.yaml`: added a top-level `slots:
grantNumber` (title + generic description), then converted `Dataset`,
`Publication`, `Tool`, `Grant`, and `EducationalResource` to declare `slots:
[grantNumber]` and removed their own duplicate `attributes: grantNumber:`
entries, moving each class's distinct cardinality/`mc2_enum`/`cckp_join`/
description into that class's own `slot_usage: grantNumber:` block — exactly
preserving the original per-class differences (`Grant`'s stays scalar with no
`mc2_enum`/`cckp_join`; the other four stay `multivalued: true` with their
own distinct enum name).

### Verification

- `linkml generate owl` on the updated `cckp_portal.linkml.yaml`: the
  "Ambiguous attribute: grantNumber" warning is gone; all other pre-existing
  ambiguous-attribute warnings (`description`, `assay`, `tissue`, `theme`,
  `tumorType`, `consortium`, `grantName`, etc.) remain, as expected — those
  reused names were explicitly out of scope for this pass.
- `make schema`: `schema/mc2_model.ttl` (185,325 triples) and
  `schema/cckp_portal.ttl` (1,172 triples) both regenerated and pass
  `scripts/validate_graph.py --parse-only`.
- `python3 -m pytest test/`: **55 passed**, no regressions from either the
  schema change or the `grantNumber` refactor.
- `make generate-json` (root repo) and any live-Synapse-dependent step
  (`make extract`, `create_json_from_model.py`, `make harmonize`/`triples`/
  `validate` against real data) were **not** run — they require a live
  Synapse login this session doesn't have. The root repo's `json_schemas/*`
  are now stale relative to `mc2.model.csv` and should be regenerated
  (`python create_json_from_model.py`) the next time someone with Synapse
  credentials runs the full build.

### Addendum (same day) — closed the two follow-ups from item 2

The user added `"File View"` to `Makefile`'s `MC2_ASSAY_CLASSES` (the
Makefile-wiring gap flagged above), then asked to remove the now-redundant
harmonization in `link_sagebrain.py`. Both done:

- **`scripts/link_sagebrain.py`** no longer imports `load_cv_lookup` from
  `harmonize.py` or re-resolves `File Tissue`/`File Tumor Type` against
  `tissue.csv`/`tumorType.csv` itself. It now reads each field's
  already-resolved `{field}_ontology_iri` column straight from the harmonized
  `File View` CSV (populated by `harmonize.py`'s normal pass now that `File
  View` is in `MC2_ASSAY_CLASSES` and its `mc2_model.linkml.yaml` slots carry
  `range: File Tissue Enum`/`File Tumor Type Enum`). Since that column holds
  `url or ident` (harmonize.py's own convention — prefers a CV row's
  `Ontology Url` over its bare `Identifier`) while the crosswalk TSVs are
  keyed by CURIE, added `curie_from_resolved()` to reverse the OBO Foundry
  purl form back to a CURIE (the only URL shape every CV this script reads
  uses) — checked URL-first, since a URL like
  `http://purl.obolibrary.org/obo/NCIT_C12252` also satisfies `harmonize.py`'s
  own `CURIE_RE` (its `http:` scheme alone matches `PREFIX:REST`); checking
  `CURIE_RE` first would have misidentified every URL as an already-bare
  CURIE (caught by a failing test, fixed before landing). `--modules-dir` is
  no longer an accepted flag — removed from both the script's `argparse` and
  the `link-sagebrain` Makefile target. As a side effect, the old code's
  `malformed = []` list passed to its own `load_cv_lookup` calls was
  populated but never written or reported anywhere — a second, latent,
  silently-dropped diagnostic this refactor also removes; malformed
  tissue/tumor-type rows are now caught by the normal
  `harmonize-mc2-assay`-produced `malformed_cv_terms.csv` instead.
- **`test/test_link_sagebrain.py`** rewritten for the new signatures:
  `aggregate_by_biospecimen_key(rows)` now returns `(resolved, conflicts)`
  instead of taking `tissue_lookup`/`tumor_type_lookup`/a mutated `conflicts`
  list; `build_sagebrain_links` no longer takes `modules_dir`; fixtures
  updated to supply pre-resolved `{field}_ontology_iri` columns (OBO purl
  URLs) instead of raw CV labels; added unit tests for
  `curie_from_resolved()` covering the URL, bare-CURIE, and blank cases.

**Verification:**
- `python3 -m pytest test/`: **58 passed** (55 + 3 new `curie_from_resolved`
  tests, replacing the 2 old ones that called `load_cv_lookup` directly).
- End-to-end smoke test beyond the mocked unit tests: ran the real
  `scripts/harmonize.py --classes "File View"` against a synthetic raw `File
  View.csv` row (Tissue=`Breast`, Tumor Type=`Triple-Negative Breast
  Carcinoma`) using the actual `schema/mc2_model.linkml.yaml` and
  `modules/mapping.yaml` — confirmed `File Tissue_ontology_iri`/`File Tumor
  Type_ontology_iri` came back as `.../NCIT_C12971`/`.../NCIT_C71732`. Piped
  that harmonized CSV into the real `scripts/link_sagebrain.py` (against the
  real, committed `mappings/crosswalks/tissue_ncit_to_uberon.sssom.tsv`/
  `tumorType_ncit_to_mondo.sssom.tsv`) and got the expected
  `sagebrain:source_tissue`/`has_pathology` triples resolved to
  `UBERON:0000310`/`MONDO:0005494`. Temp files cleaned up afterward.
- `make -n harmonize-mc2-assay`/`make -n link-sagebrain`: confirmed the
  Makefile's `--classes` argv includes `"File View"` as its own quoted
  argument (no word-splitting issue from the user's edit) and
  `link-sagebrain`'s recipe no longer passes `--modules-dir`.
