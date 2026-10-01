# Implementation Report: data-models CDE alignment (release 14.0.0)

Plan: `mc2-center-dcc/plans/data_models_cde_alignment.md`. Work is on branch `cde-14-alignment`, cut from `origin/cde-model-revisions` (PR #262). Done 2026-09-30, stopped before DM-11's tag.

## Status by item

| Item | Status | Notes |
|---|---|---|
| DM-1 Species enforcement | Done | Cause: curator folds names that differ only in case/spacing into one class label. DataCatalog's `species` (not required) shadowed shared `Species`. The same collision affected `studyId`/`Study_id`, `grantNumber`/`Grant Number`, `contributor`/the Tool Entity Role value `Contributor`, and `license`/`License`. Owner chose to merge where the concepts match: `species` → `Species`, `grantNumber` → `GrantView Key`. `Study_id` values are study codes, not Synapse IDs, so `studyId` → `dataCatalogStudyId`. There is no shared Contributor attribute, so `contributor` → `dataCatalogContributor`. `extract_datacatalog.py` maps the live Synapse keys onto the new names. |
| DM-2 license → License | Done | |
| DM-3 SPDX licenses | Done | `tool/tool_license.csv` moved to `shared/license.csv`; legacy tokens recorded as Nonpreferred Terms; `studyLicense.csv` retired. **Open:** curator to confirm `CC_BY_NC` → `CC-BY-NC-4.0` (the old CV, and a live alias, said 3.0). |
| DM-4 No-grant sentinel | Done | `Grant Number`: `^(CA\d{6}\|Affiliated/Non-Grant Associated)$`. `GrantView Key` left unanchored, `(CA\d{6}\|Affiliated/Non-Grant Associated)`, because it takes comma-separated lists in one string cell. |
| DM-5 ImagingChannel, template flags | Done | `scripts/check_template_list.py` compares `DATA` against `IsTemplate`. `Collection` is excluded (owner decision): it is not a portal table or manifest. The suspected Makefile `all_valid_values.csv` argument bug didn't exist; it was a misread of the terminal output. |
| DM-6 Drop 10x prefix | Done | Stale `json_schemas/10xVisium*.json` removed. |
| DM-7 Enum display labels | Done | `scripts/enum_display_labels.py`, called from `create_json_from_model.py`. Casing comes from each attribute's own CSV Valid Values. A first version took it from the JSON-LD, where values differing only in case share one node. That swapped e.g. `No`/`no` (language code) and `Immunoassay`/`immunoassay` in 11 properties. The JSON-LD fallback is unused in the current model. |
| DM-8 Missing portal schemas | Done | PersonView, ProjectView, Consortium, Institution, Theme. |
| DM-9 Remove DCA | Done | |
| DM-10 consortium_name | Done | The CSV is gone. `consortium_name` remains only as an internal column name in kg-pipeline's SCDM crosswalk (`mappings/crosswalks/consortium_to_scdm_program.tsv`, `crosswalk_scdm.py`, `link_scdm.py`, tests), unrelated to the deleted file. |
| DM-11 Release | Notes drafted (`plans/release_14.0.0_notes.md`) | **Not tagged**, held for the owner. |
| DM-12 Checks | Done | `scripts/check_json_schemas.py`: 0 failures across 38 schemas. `make all`, kg-pipeline `make schema && make test` (186 passed), root `pytest tests` (21 passed), and `mkdocs build --strict` all pass. |
| DM-13 CI gate | Not started | Deferred by plan. |

## Additional changes not in the plan

- `templates/*.csv` still had pre-consolidation headers. Added `scripts/build_templates.py` and a `make templates` target; `make all` now runs it. All 33 templates were regenerated.
- `Makefile` targets marked `.PHONY`, since a `templates/` directory exists.

## Consequences to note downstream

- DataCatalog now requires `Species`, inherited from the shared attribute.
- DataCatalog.json keys are class labels (`StudyKey`, `DataCatalogStudyId`). They can't match the live camelCase annotation keys on Dataset entities, so this schema can't validate those annotations directly. This was already true before this work.
- `results/cde_match/` and `kg-pipeline/scripts/vendor/references/mapping-rules.md` keep the old `10x Visium` names as historical or illustrative records.
