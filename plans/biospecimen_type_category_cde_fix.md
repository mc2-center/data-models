# Fix Biospecimen Type Category: register its CV, correct CDE drift

## Context

A repo-wide review (prompted by a kg-pipeline bug fix — see
`plans/mondo_uberon_federation_promotion.md`'s sibling audit work) surfaced
two unregistered CVs. This plan covers `Biospecimen Type Category`.

`modules/biospecimen/annotationProperty.csv`'s `Biospecimen Type Category`
attribute (backed by `CRDC_CDE:12445832`) had a hardcoded 19-value `Valid
Values` list and no `modules/mapping.yaml` entry, so it could never be
maintained from a CV file the normal way. A curated sibling CV,
`modules/biospecimen/biospecimenCategory.csv`, existed but was unregistered
and, on inspection, covered only 11 of the 19 values plus one value
(`Analyte`) that didn't belong.

Fetched CDE 12445832's real record directly from caDSR (via
`~/.claude/skills/cadsr-cde-match/scripts/cde_match.py`'s
`fetch_cde_record()` — a deterministic lookup by known id, not a text
search) to get ground truth rather than trust the model's own prior notes.
Confirmed: the CDE's 19 real permissible values are Blood, Ascites, Bone
Marrow, Cells, Stool, Body Fluid or Substance, Sputum, Urine, Tissue, Mouth
Rinse, Not Reported, Unknown, Xenograft, Skin, Saliva, RNA, DNA, Central
Nervous System, and Cell Line. `Analyte` is not one of them.

The attribute's own (now-replaced) Description carried a speculative note
about a "sibling attribute" called `Biospecimen Analyte Type` being
"applicable when Type Category = Analyte" - grepped the entire repo and
confirmed no such attribute exists anywhere in the model. `Analyte` is
instead a real value of the separate, more granular `Biospecimen Type`
attribute (which matches GDC's own `sample_type` CDE, a different field
from `sample_type_category`/CDE 12445832). The CV's own `Analyte` row cited
`CDS v5.0.4/Sample-sample_type` as its source - the wrong CDS field for an
attribute backed by CDE 12445832 - which is almost certainly how it ended
up in the wrong CV.

Per user direction: keep `Not Reported`/`Unknown` (real, CDE-backed,
commonly-needed sentinels) in the CV; the other 8 currently-hardcoded
values not yet in the CV (`Body Fluid or Substance`, `Xenograft`, `Skin`,
`Saliva`, `RNA`, `DNA`, `Central Nervous System`, `Cell Line`) are left for
separate handling, not added here.

## Approach

1. `modules/biospecimen/biospecimenCategory.csv`: removed the `Analyte` row
   (not a real CDE 12445832 value); added `Not Reported` (`NCIT:C43234`)
   and `Unknown` (`NCIT:C17998`) - both verified against OLS and matched to
   this model's own pre-existing, near-universal convention for these two
   sentinels (used identically across 20+ other CVs in this repo, confirmed
   via grep before adopting).
2. `modules/biospecimen/annotationProperty.csv`: rewrote `Biospecimen Type
   Category`'s Description to a short, consumer-facing statement of what
   the field means and where to look for finer-grained classification -
   dropped the verification narrative/date/"open question" language
   entirely per standing guidance (see
   [[feedback_no_process_narration_in_model]]) that this kind of
   process/historical context belongs in a plan doc (this one), not the
   model itself.
3. `modules/mapping.yaml`: registered `Biospecimen Type Category` ->
   `biospecimen/biospecimenCategory.csv`.
4. Regenerated in order: `update_valid_values.py`, `make collate`
   (`mc2.model.csv`, `all_valid_values.csv`), `create_json_from_model.py
   Biospecimen FileView` (the only two data types whose JSON schema
   actually reference this attribute - confirmed via a full `make
   generate-json` run touching only those two files).

## Verification

- `modules/biospecimen/annotationProperty.csv`'s `Valid Values` for
  `Biospecimen Type Category` is now `Ascites, Blood, Bone Marrow, Cells,
  Fluids, Mouth Rinse, Sputum, Stool, Tissue, Urine, Not Reported, Unknown`
  (12 values, matching the 12-row CV exactly) - confirmed via
  `update_valid_values.py`'s own output.
- `mc2.model.csv` and `all_valid_values.csv` regenerated via `make collate`,
  diffed clean (only the expected `biospecimenCategory` rows added/changed).
- `json_schemas/Biospecimen.json` and `json_schemas/FileView.json`
  regenerated - both `BiospecimenTypeCategory` enums now read `['Ascites',
  'Blood', 'BoneMarrow', 'Cells', 'Fluids', 'MouthRinse', 'NotReported',
  'Sputum', 'Stool', 'Tissue', 'Unknown', 'Urine']`, `Analyte` gone. A full
  `make generate-json` across all ~30 data types confirmed no other schema
  file changed.
- `mc2.model.jsonld` regeneration (`make convert`) run to keep the JSON-LD
  deliverable in sync - see this plan's Implementation Report for the
  result.

## Follow-up (resolved in a later pass, same day)

The items below were originally left open, then closed once the user
established a hard standing rule
(`~/.claude` memory `feedback_cde_alignment_is_mandatory`): any CDE/CRDC_CDE-
mapped attribute's CV must fully match the CDE's real permissible-value
list, full stop - "captured elsewhere" did not mean "acceptable to leave
incomplete."

- **`Fluids` renamed to `Body Fluid or Substance`, code corrected.** Checking
  `NCIT:C204466` (the code `Fluids` carried) against OLS showed it actually
  resolves to "Body Fluid **Specimen**" (the specimen-instance sense) - not
  a match for the CDE's real permissible value, which is the
  material-*category* sense, `NCIT:C13236` ("Body Fluid or **Substance**").
  Renamed the row to the CDE's exact literal string and corrected the code.
- **The other 8 CDE-real values added**: `Cell Line` (`NCIT:C16403`),
  `Central Nervous System` (`NCIT:C12438`) - both fresh OLS lookups, exact
  label matches - and `Xenograft` (`NCIT:C156443`, reused from
  `biospecimen/specimenComp.csv`/`pathology.csv`'s existing convention for
  the same concept), `Skin` (`NCIT:C12470`, reused from `shared/tissue.csv`),
  `Saliva` (`NCIT:C13275`), `RNA` (`NCIT:C198568`), `DNA` (`NCIT:C449`, all
  three reused from `biospecimen/specimenType.csv`'s existing curation of
  the same terms at the more granular `Biospecimen Type` level). The CV is
  now 19/19 rows, exact parity with CDE 12445832's real permissible-value
  list - verified programmatically (see Implementation Report addendum).
- **Still genuinely unresolved, not a completeness gap**: which of
  `RNA`/`DNA`/`Cells` an `Analyte`-typed `Biospecimen Type` value should
  roll up to at the `Biospecimen Type Category` level - the caDSR CDE
  record itself doesn't provide cross-CDE value crosswalks, so this needs
  the actual CDS/GDC data dictionary's own documented relationship (if one
  exists), not a guess. This is a *semantic mapping* question between two
  already-complete CVs, not a missing-value gap.

## Process

Store this plan at `plans/biospecimen_type_category_cde_fix.md` for review.
Implementation Report follows below.

## Implementation Report

Implemented as above. `modules/biospecimen/biospecimenCategory.csv`:
`Analyte` row removed, `Not Reported`/`Unknown` rows added (12 rows total).
`modules/biospecimen/annotationProperty.csv`: Description rewritten,
`Valid Values` regenerated. `modules/mapping.yaml`: new `biospecimen:`
entry added. `mc2.model.csv`, `all_valid_values.csv`,
`json_schemas/Biospecimen.json`, `json_schemas/FileView.json`, and
`mc2.model.jsonld` all regenerated via the documented `make` targets - no
manual edits to any generated artifact. All verification in the section
above passed.

### Addendum: full CDE-parity follow-up

Implemented the "Follow-up" section above in a second pass the same day.
Verified programmatically:

```
CV count: 19
CDE count: 19
Missing from CV: set()
Extra in CV (not in CDE): set()
```

Regenerated `mc2.model.csv`/`all_valid_values.csv` (`make collate`),
`json_schemas/Biospecimen.json`/`FileView.json`
(`create_json_from_model.py`, confirmed via a full `make generate-json` run
that no other schema changed), `mc2.model.jsonld`
(`convert_model_to_jsonld.py`), and kg-pipeline's own
`schema/mc2_model.linkml.yaml`/`mc2_model.ttl`
(`make mc2-model-linkml && make schema`). kg-pipeline's 97-test suite
passes unchanged.
