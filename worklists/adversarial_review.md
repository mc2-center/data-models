# Adversarial Review of Ontology Identifier / Ontology Url Mappings

Scope: the 13 modules that currently carry `Ontology Identifier` + `Ontology Url`
columns (`biospecimen`, `individual`, `model`, `imagingChannel`, `imagingLevel1-4`,
`sequencingLevel1-3`, `sequencingRNALevel1`) — 142 populated attribute rows.
Every row traces to a record in `worklists/*_decisions.json` from the earlier
OLS annotation pass. The CSV state matches those decision records exactly (0
drift, 0 missing, 0 extra).

Method: same approach as the caDSR CDE review — pulled the real term record
(label + definition + obsolescence status) live from the EBI OLS4 API for all
86 unique NCIT/OBI IDs used (`GET /ols4/api/ontologies/{ontology}/terms/{iri}`),
compared against each attribute's actual description, and ran fresh OLS
searches (`GET /ols4/api/search?q=...`) to check whether a closer term exists
for every self-flagged "partial" verdict.

## Headline

This process was noticeably higher-quality than the caDSR CDE matcher: it's
semantic (LLM-verified against real definitions), not keyword-scored, and its
59 self-reported "partial" verdicts (out of 142) are mostly honest, correct
admissions of genuine NCIT vocabulary gaps rather than errors. Independent
re-verification found only **5 concrete, fixable mismatches** — all low
severity, none of them the kind of wildly-wrong-domain error the CDE review
turned up.

## Confirmed fixable issues

| Attribute(s) | Current term | Problem | Recommended term |
|---|---|---|---|
| `Biospecimen_id`, `Individual_id`, `Model_id` | NCIT:C166393 "Specimen Identifier" | Every other component's `_id` field (10 of them: ImagingChannel/ImagingLevel1-4/SequencingLevel1-3/SequencingRNALevel1) correctly uses NCIT:C49189 "Primary Key". These three break that convention — "Specimen Identifier" is flatly wrong for `Individual_id`/`Model_id` (neither is a specimen) and inconsistent even for `Biospecimen_id` (every other `_id` is tagged by structural role, not domain). | **NCIT:C49189 "Primary Key"** — for all three, matching the established model-wide pattern |
| `Image Physical Size X/Y/Z` | NCIT:C42578 "Unit of Length" | These hold the actual numeric size *value*; "Unit of Length" is the unit-of-measure classifier, correctly used already on their sibling `_Unit` fields (`Image Physical Size X/Y/Z Unit`). Reusing it on the value fields is a value-vs-unit category error. | **NCIT:C25334 "Length"** ("the linear extent in space from one end of something to the other") |
| `Image Assay Type` | NCIT:C17369 "Imaging Procedure" | C17369 is a broad component-level placeholder reused across 7 different table/schema rows (`Imaging Channel`, `Imaging Level 1-4`, etc.) as a generic "this is imaging" tag — reasonable there, but a much closer term exists for this specific attribute. | **NCIT:C189101 "Assay Type"** ("The type of assay that was utilized") — exact match |
| `NGS Raw Reads` | OBI:0600047 "sequencing assay" | Same placeholder-reuse pattern: OBI:0600047 is correctly used on the three Sequencing Level *component* rows, but `NGS Raw Reads` is a count value ("the number of reads that pass filter..."), not the assay itself. | **NCIT:C164667 "Sequence Read Count"** ("The number of sequencing reaction results that were pooled...") |
| `Individual Recurrence Status` | NCIT:C159899 "Was a New Tumor Event Present After Initial Treatment Question" | This is literally a survey-*question* wrapper class — the original decision's own note already flags it ("Partial because this is a Question class not an attribute class"). | **NCIT:C123621 "Disease Recurrence Indicator"** ("An indication as to whether disease recurrence occurred") — matches the field's Yes/No/Unknown semantics directly |

Four of these five follow the same shape: a broad term correctly used to tag a
*component/table-level row* got reused on a specific *attribute* inside that
component, where a much more precise term already exists in NCIT. Worth
checking for this pattern generally whenever a term is reused 3+ times.

## Checked and confirmed correct (no better alternative exists)

- **`Individual`/`Biospecimen`/`Model Disease Type` → NCIT:C164326 "Concurrent
  Disease Type"** — searched exhaustively; NCIT genuinely has no generic
  "disease/tumor type" property term. Every other hit is either a
  comorbidity-specific concept or a single named disease. The "partial, best
  available" framing is accurate — nothing to swap to.
- The bulk of the remaining 59 "partial" verdicts (`Model Age/Type/Method/
  Source/Acquisition Type/Graft Source`; `Image Objective/Nominal
  Magnification/FOV*/Software/Parameter file/Number of Objects/Features/
  Summary Statistic`; `NGS Library Selection Method/Strategy/Source Molecule/
  Preparation Days from Index`) — spot-verified against real OLS definitions
  and/or fresh searches; each is a genuine NCIT coverage gap with the closest
  available parent term already selected. No action needed.
- All "Number of Days Between Index Date and X" attributes (`Individual Days to
  Last Followup/To Recurrence/to Last Known Disease Status/to Treatment`,
  `Model Days to Treatment`) — exact matches, verified.
- Channel-level antibody/reagent terms (`Antibody Name`→Reagent Name,
  `Vendor`→Manufacturer, `Lot`→Reagent Lot Number, `Catalog Number`,
  `Fluorophore`→Fluorochrome Dye) — reasonable, correctly-scoped generic reuse.

## Worth a second look, lower confidence (not recommending a change)

- **`NGS Aligned Reads` → NCIT:C164052 "Aligned Sequence Read"** — the
  attribute is a count ("these reads can number from the hundreds of thousands
  to tens of millions"), but C164052's definition describes the *alignment
  determination process*, not a count, which is the same value-vs-process
  mismatch as the `NGS Raw Reads` fix above. I didn't find a clearly better
  "aligned read count" NCIT/OBI term on search, though — NCIT:C164667
  "Sequence Read Count" (recommended above for `NGS Raw Reads`) could plausibly
  serve both. Flagging for awareness rather than recommending outright, since
  ontology class definitions are sometimes written loosely even when the class
  is meant to cover both the concept and its instances/counts.

## Documentation-only note (no CSV impact)

The decision note for `Individual` (`worklists/individual_decisions.json`,
correctly recorded as NCIT:C16960 "Patient") cites "NCIT:C29847" in its prose
as the source of that label — but C29847 is actually **"Cresidine"**, an
unrelated aromatic amine compound, not a patient/person term. This looks like
a hallucinated citation in the note text from the original verification pass.
It doesn't affect the model (the ID actually recorded and used, C16960, is
correct) — just worth knowing if that decisions file is ever treated as an
audit trail.
