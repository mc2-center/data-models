# Legacy orphaned CV files: superseded, removed

## Context

While auditing controlled-vocabulary quality (ontology grounding, CDE
compliance, complete descriptions — see
`reports/valid_value_descriptions_report.md` and
`plans/crdc_cde_integration.md`'s Round 13), four CV files turned out to be
dead weight:

- `modules/shared/therapeuticAgent.csv` (4,475 rows)
- `modules/shared/primaryDiagnosisCDS.csv` (800 rows)
- `modules/shared/primaryDiseaseSite.csv` (246 rows)
- `modules/shared/tissueOrganOriginCDS.csv` (614 rows)

None is referenced by `modules/mapping.yaml`, so none backs any live
attribute's Valid Values — confirmed via `grep`/direct inspection, not
assumed.

## Why they're dead, not just incomplete

An earlier turn this session assumed the first three were *staged*
NCI-Thesaurus-coded CV replacements, sitting ready to be wired in for the
Therapeutic Agent/Primary Diagnosis/Primary Site attributes per
`plans/crdc_cde_integration.md`'s "Existing attributes to re-align
controlled vocabularies on" section. That assumption was checked and found
wrong:

- `git log --diff-filter=A` shows all three (plus `tissueOrganOriginCDS.csv`)
  were added in commit `b3ff791`, "Model refactor and expansion" — dated
  **October 2024**, well before `plans/crdc_cde_integration.md` existed.
- None of the four filenames appears anywhere in
  `plans/crdc_cde_integration.md`'s ~1,830 lines (`grep` confirmed zero
  hits) — the plan's proposed CV replacement was never actually tied to
  these specific files.
- The real resolution that plan settled on for Therapeutic Agent and
  Primary Diagnosis was **not** a fixed NCIt-coded picklist at all — both
  attributes (`modules/shared/annotationProperty.csv`) are now open,
  reference-validated free-text fields ("NCI Thesaurus concept name --
  reference-validated, not a fixed list"), each carrying its real
  `CRDC_CDE:` tag directly. A fixed picklist CV was never adopted, so
  `therapeuticAgent.csv`/`primaryDiagnosisCDS.csv` were never activated —
  they simply predate and were superseded by this design decision.
- `tissueOrganOriginCDS.csv` was already known-orphaned: its
  `mapping.yaml` entry was explicitly removed when `Biospecimen Site of
  Resection or Biopsy` was converted to a UBERON pattern-validated field
  (see `plans/crdc_cde_integration.md`'s Implementation Report, Phase 1).
- `primaryDiseaseSite.csv` was never referenced by name anywhere in the
  CDE integration plan either; no attribute currently needs a fixed
  anatomic-site picklist (Site of Origin and Known Metastasis Sites are
  both open UBERON-coded fields, not closed lists).

## Resolution

Per explicit user decision (2026-09-08): delete all four files. Nothing in
`modules/mapping.yaml`, `scripts/`, `docs/`, or `kg-pipeline/` references
them (verified via repo-wide grep before deletion) — `git log`/history
preserves them if ever needed again, so this is a safe, low-risk cleanup
rather than a loss of information.
