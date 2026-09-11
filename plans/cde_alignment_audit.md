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
value space. Most CRDC_CDE-tagged enumerated fields (15+) were already
exact matches - no action needed. `Treatment Type`, `NGS Sequencing
Platform`, `File Data Checksum Type`, and `Biospecimen Stain` were
confirmed as genuine, safe, additive gaps and already fixed (see git log -
commits `9a83080`/`53376ec`).

The remaining findings needed a human call, since several are structural
mismatches (wrong CDE tagged, two attributes sharing one CDE incorrectly,
or a CV that's broader than its CDE) rather than simple missing-value
gaps. Presented a side-by-side (attribute / backing CV / CDE id / CDE name
/ value counts) for review; the user annotated each finding directly in
this file with `[REVIEW: ...]` directives, reproduced and turned into
concrete steps below. All ground truth below (CDE permissible values, and
which existing CV rows already carry a reusable ontology code) was
re-verified directly - `fetch_cde_record()` for every CDE id, direct file
reads for current CV content - not taken from the earlier forks' summaries.

## Approach

### 1. `Assay` / `DSP Dataset Assay` - wrong CDE, split off a new attribute

Both share one CV (`shared/assay.csv`, 391 rows) and are both tagged
`CRDC_CDE:12373576` ("Research Activity Experimental Method Type", only 9
broad values: `RNA Sequencing`, `Radiology`, `DNA Sequencing`,
`Methylation Analysis`, `LC-MS/MS`, `Pathology`,
`Multigene Expression Assay`, `Immunofluorescence`,
`Quantitative Immunofluorescence`). Directive: keep the 391-value CV as-is
for both attributes, but move this CDE onto a **new** attribute,
`File Assay Category`, and remove the CDE tag from `Assay`/`DSP Dataset
Assay` entirely.

Steps:
1. Remove `CRDC_CDE:12373576` from `Assay`'s `Properties`
   (`modules/shared/annotationProperty.csv`) and from `DSP Dataset Assay`'s
   `Properties` (`modules/sharingPlans/annotationProperty.csv`). No other
   change to either attribute or to `shared/assay.csv`.
2. Create a new CV, `modules/shared/fileAssayCategory.csv`, with the CDE's
   9 real values. Two already have an established, reusable NCIT code in
   `shared/assay.csv` itself - reuse rather than re-derive: `RNA Sequencing`
   -> `NCIT:C124261`, `DNA Sequencing` -> `NCIT:C153598`. The other 7
   (`Radiology`, `Methylation Analysis`, `LC-MS/MS`, `Pathology`,
   `Multigene Expression Assay`, `Immunofluorescence`,
   `Quantitative Immunofluorescence`) need a fresh OLS lookup each at
   implementation time, same method used throughout this session.
3. Add `File Assay Category` to `modules/mapping.yaml` (new `shared:` entry
   pointing at the new CV) and to `modules/shared/annotationProperty.csv`
   as a new attribute definition (`Properties: CRDC_CDE:12373576`).
4. **"Update file-based data models to include new attribute"** - resolved:
   confirmed each per-level module does NOT inherit shared file attributes
   through any indirection - every processing-level "component" row
   (`Imaging Level 1`, `Sequencing Level 1`, etc.) lists every one of its
   attributes, shared or level-specific, inline in its own `DependsOn`
   column. Used `File Format`'s own presence (a sibling shared file
   attribute, defined once in `modules/file/annotationProperty.csv` like
   `File Assay Category` will be) as the definitive marker for "which
   modules carry the generic file-shared attributes": confirmed by grep
   for a literal `, File Format,` DependsOn member (not just an incidental
   substring hit - excluded `dataset`/`sharingPlans`/`tool`, whose own
   attributes merely contain the substring "File Format" in an unrelated
   name). Real hit list, 19 modules total - add `File Assay Category` to
   each one's top component row's `DependsOn`, immediately alongside where
   `File Format` already sits in that same list:
   `file` (the `File View` row itself), `geomxImaging`, `geomxLevel1`,
   `geomxLevel2`, `geomxLevel3`, `imagingLevel1`, `imagingLevel2`,
   `imagingLevel3Image`, `imagingLevel3Segments`, `imagingLevel4`,
   `sequencingLevel1`, `sequencingLevel2`, `sequencingLevel3`,
   `sequencingRNALevel1`, `visiumRNAAux`, `visiumRNALevel1`,
   `visiumRNALevel2`, `visiumRNALevel3`, `visiumRNALevel4`.
   (`imagingChannel`/`geomxRoi` and others do NOT carry `File Format` today
   and are correctly excluded - they're sub-components, not their own file
   record.)

### 2. `Image Assay Type` / `GeoMx DSP Assay Type` - confirmed distinct, one is a real match

Directive: these are legitimately separate attributes (GeoMx is
platform-specific); if `Image Assay Type` aligns with the currently-tagged
CDE, replace its CV.

Verified: `CDE:7789196` ("Assay Type", 23 values:
`GeoMX-DSP, CODEX, MIBI, IMC, mIF, mIHC, t-CyCIF, ExSeq, MERFISH, CyCIF,
Not Applicable, ELISA, CyTOF, ctdDNA, ATAC-Seq, NULISA, RNA-Seq, WES,
TCR-Seq, scRNA-Seq, H and E, IHC, Olink PEA`) matches **12 of `Image Assay
Type`'s current 14 values** (`imagingLevel1/imageAssay.csv`) exactly or
near-exactly (`H&E` vs `H and E`). Only `MxIF` and `SABER` aren't in the
CDE. `GeoMx DSP Assay Type`'s current 4 values (`RNA nCounter`,
`Protein nCounter`, `Protein NGS`, `RNA NGS`) don't appear in this CDE at
all - confirms it was tagged in error there.

Steps:
1. `GeoMx DSP Assay Type` (`geomxLevel1/assayType.csv`): remove
   `CDE:7789196` from its `Properties`. Leave its 4 current values
   untouched (no replacement CDE identified or requested).
2. `Image Assay Type` (`imagingLevel1/imageAssay.csv`): tag `Properties`
   with `CDE:7789196`, then replace the CV content with the CDE's 23 real
   values. Reuse the 12 already-current, already-coded rows directly.
   Add the 11 new ones (`ELISA`, `CyTOF`, `ctdDNA`, `ATAC-Seq`, `NULISA`,
   `RNA-Seq`, `WES`, `TCR-Seq`, `scRNA-Seq`, `Olink PEA`, and rename
   current `H&E` to the CDE's literal `H and E`) with fresh OLS lookups.
   Confirmed: **drop `MxIF` and `SABER`** (neither is a real CDE value) -
   full replace, 23/23 exact parity, no extras kept.

### 3. `Biospecimen Embedding Medium` - no replacement CDE found

Directive: find the right CDE, prefer a CRDC_CDE.

Already searched: the current tag, `CDE:8037927` ("Biospecimen Collection
Medium Type", 5 values - liquid cell-culture media), is confirmed wrong for
an *embedding* medium (current CV holds real embedding compounds: paraffin
wax, resin, agar, etc.). Queried the live caDSR `cdeMatch` API directly
(`PV` and `VM` match types, three name variants: "Embedding Medium",
"Tissue Embedding Medium", "Specimen Embedding Medium Type", with and
without the current 10 valid values as context) - **zero candidate CDEs
returned in any query**. No CRDC_CDE (or any CDE) appears to be indexed for
this concept.

Steps:
1. Remove the incorrect `CDE:8037927` tag from `Biospecimen Embedding
   Medium`'s `Properties` (`modules/biospecimen/annotationProperty.csv`).
   Leave the CV (`embeddingMedium.csv`) untouched - it's not CDE-backed
   drift, it's a real, independently-curated vocabulary.
2. Document in this file (done, above) that a CDE search was performed and
   came up empty, so a future pass doesn't repeat the same dead-end search.
   No further action unless a real CDE turns up some other way (e.g. a
   future caDSR release, or a manual browse of the CDE Browser UI, which
   the automated API search doesn't fully replicate).

### 4. `Biospecimen Preservation Method` / `Preservation Medium`

Directive: clear the Method/Medium cross-contamination and align Method
with its real CDE; confirm Medium is aligned with its own CDE too.

- **`Preservation Medium`** (`fixative.csv`, `CRDC_CDE:16323957`,
  "Specimen Preservation Procedure Medium Type"): confirmed **already
  exact, 17/17** - no action needed.
- **`Preservation Method`** (`preservation.csv`, `CRDC_CDE:8028962`,
  "Specimen Preservation Procedure Type", 14 real values: `Fresh`,
  `Fresh Dissociated`, `Fresh Dissociated and Single Cell Sorted`,
  `Fresh Dissociated and Single Cell Sorted into Plates`, `Cryopreserved`,
  `Frozen`, `Snap Frozen`, `Not Applicable`, `Not Reported`, `Unknown`,
  `Cytospin Slide`, `Refrigerated Vacuum Chamber`, `Refrigerated`,
  `Fixation`): confirmed contaminated - current 20 rows include medium-type
  values lifted from `fixative.csv` (`OCT`, `Formalin fixed paraffin
  embedded - FFPE`, `Methacarn fixed paraffin embedded - MFPE`,
  `Liquid Nitrogen`, the buffered/unbuffered formalin variants) that don't
  belong to this CDE at all.

Steps for `Preservation Method`:
1. Replace `preservation.csv`'s content with exactly the CDE's 14 values.
2. Reuse existing codes directly (already present in the current,
   contaminated file, just under slightly different casing/wording -
   confirmed real NCIT terms, not guesses): `Fresh` -> `NCIT:C84517`,
   `Cryopreserved` -> `NCIT:C16475`, `Snap Frozen` -> `NCIT:C63521`,
   `Frozen` -> `NCIT:C158417`, `Not Reported` -> `NCIT:C43234`, `Unknown`
   -> `NCIT:C17998` (fix casing from current lowercase `unknown`),
   `Fresh Dissociated` -> `NCIT:C185404`,
   `Fresh Dissociated and Single Cell Sorted` -> `NCIT:C185405`,
   `Fresh Dissociated and Single Cell Sorted into Plates` -> `NCIT:C185406`
   (renaming from the current, slightly different value strings).
3. Fresh OLS lookups needed for the remaining 5: `Not Applicable`
   (likely reuses the same `NCIT:C48660` already established elsewhere in
   this repo, e.g. `specimenComp.csv` - verify, don't assume), `Cytospin
   Slide`, `Refrigerated Vacuum Chamber`, `Refrigerated`, `Fixation`.
4. Drop the remaining contaminated rows entirely (the cryopreservation
   sub-variants, the FFPE/MFPE/formalin/OCT/Liquid Nitrogen/Negative 80 Deg
   C rows) - none are real values of this CDE.

### 5. `Biospecimen Composition` - replace with exact CDE match

Directive: losing values is fine if the CDE is a good match - replace.

`CRDC_CDE:12922545` ("Tumor Classification Category") has 11 real values:
`Unknown, Not Reported, Metastatic, Primary, Not Applicable, Xenograft,
Synchronous Primary, Recurrent, Progression, Prior Primary, Premalignant`.
**All 11 already have an established, correct NCIT code in the current
file** (`specimenComp.csv`) - zero new OLS lookups needed, just casing
fixes and drops.

Steps:
1. Fix casing on 2 rows: `Not applicable` -> `Not Applicable`
   (`NCIT:C48660`, unchanged), `Not reported` -> `Not Reported`
   (`NCIT:C43234`, unchanged).
2. Keep the other 9 CDE-matching rows exactly as they are (`Metastatic`,
   `Primary`, `Xenograft`, `Synchronous Primary`, `Recurrent`,
   `Progression`, `Prior Primary`, `Premalignant`, `Unknown`) - already
   correctly coded.
3. Drop the 13 rows that aren't real CDE values: `Additional Primary`,
   `Atypia or hyperplasia`, `Local recurrence`, `Normal`, `Normal adjacent`,
   `Normal distant`, `NOS`, `Premalignant - in situ`, `Tissue`,
   `Tumor post-adjuvant therapy`, `Tumor post-neoadjuvant therapy`,
   `Tumor post-therapy`,
   `Tumor specimen from de novo untreated malignancy of the bladder`.
4. Result: `specimenComp.csv` goes from 24 rows to exactly 11, full parity.

### 6. `File Format` / `Dataset File Formats` - split into two CVs

Directive: `File Format` carries the real, active `CRDC_CDE:11416926` tag
(confirmed: `File Format`'s `Properties` has both `CDE:11416926,
CRDC_CDE:11416926`; `Dataset File Formats`'s `Properties` has only the
legacy `CDE:11416926`, no CRDC_CDE). They currently share one CV
(`shared/dataset_file_format.csv`, 81 rows) via two `mapping.yaml` entries.
Split: `Dataset File Formats` keeps this CV unchanged (still used for CCKP
curation); `File Format` gets its own CV aligned to the CDE's 97 real
values.

`CRDC_CDE:11416926` ("Data File Format Type") has 97 values - a full
diff/reconciliation (not blind union) is needed since ~15-20 of the
current 81 values are case/naming variants of real CDE values rather than
true gaps (e.g. `JPG` vs CDE's `JPEG`, `TAR Format` vs `TAR`, `MATLAB
script` vs `MATLAB Script`) - captured in the earlier audit fork's report,
not re-derived here.

Steps:
1. Create `modules/shared/fileFormat.csv` (new CV, distinct file).
2. Populate with the CDE's 97 real values. For each, check whether a
   same-or-near-same-named row already exists in `dataset_file_format.csv`
   to reuse its existing Ontology Identifier (most format codes there are
   already NCIT/EDAM-coded) - a rename-and-reuse pass, not blank slate.
   Do the per-value reconciliation table (missing vs. rename-candidate vs.
   genuinely-new) as a first implementation sub-step before writing rows,
   given the size.
3. Update `modules/mapping.yaml`: `File Format` -> `shared/fileFormat.csv`
   (new); `Dataset File Formats` stays -> `shared/dataset_file_format.csv`
   (unchanged).
4. `modules/file/annotationProperty.csv`'s `File Format` row keeps its
   `CDE:11416926, CRDC_CDE:11416926` tags (now genuinely backed).
   `modules/dataset/annotationProperty.csv`'s `Dataset File Formats` row -
   resolved (directive: keep the tag only if it's a good fit, otherwise
   discard): computed the actual overlap between its current 81 values and
   the CDE's 97 real values - only **39/81 (48%) case-insensitive exact
   matches**. The other 42 (`COOL`, `cloupe`, `rcc`, `H5AD`, `SF`, `PKL`,
   `BPM`, `CDS`, `DCC`, `SRA`, ...) are largely genomics/single-cell/CCKP-
   specific formats with no CDE equivalent at all, not naming variants of
   real CDE values - a materially different, broader vocabulary than the
   CDE represents, not "the same CV, just not yet reconciled." **Verdict:
   discard the legacy `CDE:11416926` tag** on `Dataset File Formats` - keep
   its 81-value CV completely unchanged, just remove the now-misleading
   CDE reference from `Properties`.

### 7. `NGS Library Strategy` - align, additive

Directive: align with the CDE as long as it's a good match.

`CRDC_CDE:6273393` ("Molecular Analysis Library Sequencing Technique
Type") has 41 real values; current `libraryStrategy.csv` has 39, missing 4
real values (`scRNA-Seq`, `mRNA-Seq`, `Bulk RNA-Seq`, `scDNA-Seq`) and
carrying 2 values (`RNA-Seq`, `DNA-Seq`) not literally in the CDE's list
that may be intended as broader stand-ins for some of the missing precise
terms.

Steps:
1. Add the 4 missing values with fresh OLS lookups.
2. Keep `RNA-Seq`/`DNA-Seq` as-is (additive-only, same treatment as
   `Treatment Type`'s `Control` and `NGS Sequencing Platform`'s `Complete
   Genomics` - legitimate extras, not replaced) unless told otherwise; no
   directive here said to trim, unlike `Sex`/`Composition`.
3. Result: 43 rows (41 real + 2 legitimate extras), full CDE coverage.

### 8. `Sex` - align, trim to exact CDE match (approved)

Directive confirmed: proceed with the removal as described. `CRDC_CDE:7572817`
("Person Sex at Birth Category") has exactly 3 real values: `Male`,
`Female`, `Unknown`. Current `shared/biologicalSex.csv` has 9 - the 3 real
ones plus 6 inclusive/demographic extras (`Decline to answer`, `Don't
know`, `Intersex`, `None of these describe me`, `Prefer not to answer`,
`X`).

Steps:
1. Confirm `Male`/`Female`/`Unknown` already have correct, reusable codes
   in the current file (expected, given this CV's maturity) - reuse, no
   new lookups.
2. Remove the 6 non-CDE rows.
3. Result: `biologicalSex.csv` goes from 9 rows to exactly 3.

### 9. `Biospecimen Composition` extras - approved (see #5 above, same removal)

### 10. Category D - fetch retries and unverifiable CDE

On retry (this pass), 3 of the 4 previously-failed fetches actually
resolved fine:
- `Study Description` (`CDE:03444002`) -> "Study Research Identification
  Text", genuinely 0 permissible values (free text) - correctly untagged
  as an enum, no action.
- `Study Deidentification Method Type` (`CDE:14576319`) -> "Data File
  Deidentification Method Type", 4 values - resolved; **not yet diffed
  against current `deIdMethod.csv` content** in this pass, needs a normal
  diff pass like the others above before closing.
- `Study_id` (`CDE:12960571`) -> resolves, but to **"Study Pediatric
  Identifier"**, 98 values - a real CDE, but a poor semantic fit for a
  generic `Study_id` primary key. Directive: try to find a replacement,
  otherwise remove. Searched the live `cdeMatch` API (`VM` match type, 4
  name variants: "Study Identifier", "Study ID", "Unique Study
  Identifier", "Research Study Identifier") - **zero candidates returned
  for any variant**. Root cause: `Study_id` has no permissible values (it's
  a free-text/pattern primary key, `^syn\d+$`-shaped in practice), and the
  `cdeMatch` API's `PV`/`VM` match types are fundamentally built to match
  *enumerated* fields against CDEs by their value lists - there's no
  value-list signal here to match on, so the tool doesn't apply well
  regardless of query wording. **Verdict: remove `CDE:12960571`** from
  `Study_id`'s `Properties` (`modules/study/annotationProperty.csv`,
  keeping `primary_key`) - no replacement found via available tooling. A
  manual caDSR CDE Browser text search might still turn something up but
  is outside what this pass automates.

Directive for the one still-unresolvable id: **remove if not verifiable**.
- `DSP Data Use Codes` (`CDE:0002001`): still returns "No data returned"
  on retry - the id does not resolve in caDSR. Remove this `Properties`
  tag from `DSP Data Use Codes`
  (`modules/sharingPlans/annotationProperty.csv`). No other change - this
  field is DUO-coded, a separate registry from caDSR CDEs, and its actual
  values are unaffected.

## Verification (for every step above)

- Re-fetch each touched CDE fresh via `fetch_cde_record()` and do an exact
  set-diff against the resulting CV content before considering any item
  closed - same discipline as the 4 already-fixed items, not a one-time
  check against this document's cached counts.
- `make collate` (`mc2.model.csv`/`all_valid_values.csv`), a full `make
  generate-json` run (not just the data types expected to change - confirm
  nothing else moves), `convert_model_to_jsonld.py`, and kg-pipeline's
  `make mc2-model-linkml && make schema` + `make test` (97/97) after every
  batch of changes, matching the pattern from the first 4 fixes.
- New CVs (`fileAssayCategory.csv`, `fileFormat.csv`) need a
  `modules/mapping.yaml` entry before `update_valid_values.py` will ever
  populate their attribute's `Valid Values` - don't forget this step, it
  was the root cause of the original `Biospecimen Type Category` gap.

## Process

Store this plan at `plans/cde_alignment_audit.md`. All sub-questions
raised during review are now resolved (File Assay Category propagates to
19 named modules; `Image Assay Type` drops `MxIF`/`SABER`; `Dataset File
Formats`' legacy CDE tag is discarded, 48% overlap confirmed not a good
fit; `Study_id`'s CDE is removed, no replacement found via `cdeMatch`).
Every section above is ready to implement as written. Append an
Implementation Report below this line once work begins.

## Implementation Report

Implemented all 10 sections as written, including the 4 answers to the
open sub-questions (File Assay Category propagates to all 19 named
modules; `Image Assay Type` drops `MxIF`/`SABER`; `Dataset File Formats`'
legacy tag discarded; `Study_id`'s CDE removed, no replacement found).

**Section 1 (`Assay`/`DSP Dataset Assay` → `File Assay Category`):**
`CRDC_CDE:12373576` removed from both `Assay` and `DSP Dataset Assay`
(their 391-value CVs untouched). New CV `modules/shared/fileAssayCategory.csv`
(9 rows, all coded - 2 reused from `shared/assay.csv`, 7 fresh OLS
lookups), registered in `mapping.yaml`, new attribute added to
`shared/annotationProperty.csv`. Propagated to all 19 modules confirmed
via the `File Format`-presence grep (`file`, `geomxImaging`,
`geomxLevel1-3`, `imagingLevel1-4`+`imagingLevel3Image`+`imagingLevel3Segments`,
`sequencingLevel1-3`, `sequencingRNALevel1`, `visiumRNAAux`,
`visiumRNALevel1-4`) - each got `File Assay Category` inserted immediately
after `File Format` in its component row's `DependsOn`.

**Section 2 (`Image Assay Type`/`GeoMx DSP Assay Type`):** `GeoMx DSP Assay
Type`'s wrong `CDE:7789196` tag removed, its 4 values untouched.
`Image Assay Type` re-tagged with `CDE:7789196` and its CV fully replaced -
12 kept (including a literal-value rename, `H&E`→`H and E`, and a
label-correction, `MxIF`→`mIF`, both reusing their existing NCIT codes
since the concept was already right), 10 new rows added via fresh OLS
lookups (`NULISA` has no defensible ontology match, documented). 23/23
exact parity.

**Section 3 (`Biospecimen Embedding Medium`):** wrong `CDE:8037927` tag
removed; CV untouched (no replacement CDE exists per the earlier
`cdeMatch` search).

**Section 4 (`Preservation Method`/`Medium`):** `Preservation Medium`
confirmed unchanged (already 17/17). `Preservation Method`'s CV fully
replaced with the 14 real values - 9 reused existing codes (renamed from
contaminated-but-coded rows), 5 fresh OLS lookups. 14/14 exact parity.

**Section 5 (`Biospecimen Composition`):** CV trimmed from 24 to 11 rows,
2 case fixes, all codes reused from the pre-existing file - zero new
lookups needed, as predicted. 11/11 exact parity.

**Section 6 (`File Format`/`Dataset File Formats` split):** `Dataset File
Formats` kept unchanged (81 values, CV file untouched) with its legacy
`CDE:11416926` tag discarded (confirmed 48% overlap, not a good fit,
per the pre-implementation analysis). New CV
`modules/shared/fileFormat.csv` (97 rows) built via programmatic
reconciliation: 50 values reused existing codes from
`dataset_file_format.csv`/`tool_format.csv` by exact-match lookup, 47
required fresh OLS searches (45 resolved to real NCIT/EDAM codes - many
to a dedicated `NCIT:C19xxxx`-`C22xxxx` "X Format" series that appears to
already back this same CDE's vocabulary elsewhere in NCIT; `im3`/`BAS`
have no defensible match, documented). `mapping.yaml` updated: `File
Format` → `fileFormat.csv` (new), `Dataset File Formats` stays →
`dataset_file_format.csv` (unchanged). 97/97 exact parity on `File Format`.

**Section 7 (`NGS Library Strategy`):** added the 4 missing values
(`mRNA-Seq`, `Bulk RNA-Seq`, `scRNA-Seq`, `scDNA-Seq`) via fresh OLS
lookups; kept `RNA-Seq`/`DNA-Seq` as legitimate extras per the plan. 43
rows total (41 real + 2 extras).

**Section 8 (`Sex`):** trimmed from 9 to 3 rows (`Female`/`Male`/`Unknown`),
all codes reused, zero new lookups. 3/3 exact parity.

**Section 10 (fetch retries/unverifiable):** `Study Deidentification
Method Type` confirmed already 4/4 exact on retry, untouched.
`Study_id`'s `CDE:12960571` removed (`primary_key` kept). `DSP Data Use
Codes`' unresolvable `CDE:0002001` removed (DUO values untouched).

**Verification:**
- Every touched CV verified for exact set-parity against a freshly
  re-fetched CDE record before moving to the next section (not trusting
  the plan document's cached counts) - all 8 CDE-backed CVs confirmed
  exact (9/9, 23/23, 14/14, 11/11, 97/97, 43-row NGS Library Strategy with
  2 documented extras, 3/3 Sex, plus the untouched-and-reconfirmed
  Preservation Medium 17/17).
- `update_valid_values.py` and `make collate` regenerated
  `mc2.model.csv`/`all_valid_values.csv` cleanly across all 35 touched
  files plus the 2 new CVs.
- Full `make generate-json` regenerated 22 `json_schemas/*.json` files
  (all 19 `File Assay Category`-propagation targets plus `Biospecimen`,
  `Individual`, `Model`; spot-checked `SequencingLevel1.json` - correct
  9-value `FileAssayCategory` enum). `convert_model_to_jsonld.py` produced
  a valid `mc2.model.jsonld` (graph grew 5317→5361 nodes).
- kg-pipeline: `make mc2-model-linkml` regenerated
  `schema/mc2_model.linkml.yaml` (568 slots, 142 enums, 0 warnings from
  the LinkML generator itself). `make schema` regenerated
  `schema/mc2_model.ttl` (53,560 triples) and `schema/cckp_portal.ttl`
  (1,173 triples); `validate_graph.py --parse-only` parsed both cleanly.
  `make test` - 97/97 passed, no regressions.
- `git status` confirms the touched-file set matches the plan exactly:
  35 modified `modules/**/*.csv` + `mapping.yaml`, 2 new CVs
  (`fileAssayCategory.csv`, `fileFormat.csv`), the 4 collated/derived
  root files, 22 `json_schemas/*.json`, and 5 kg-pipeline schema
  artifacts - nothing unexpected, `.vscode/` remains untracked and
  unrelated.
