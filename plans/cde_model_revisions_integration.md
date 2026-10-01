# Integrate `cde-model-revisions` (PR #262) into the live model + curation pipeline

## Context

`main` hasn't moved since 2026-08-19 (`64eb67b`, the exact merge-base with
`cde-model-revisions`) — PR #262 is the only open PR against it, already
labeled `major`. Compared `main` against `cde-model-revisions` directly
(`git diff`/`git show` on both refs) and checked the one external repo
confirmed to consume this model's column names against live Synapse tables,
[`mc2-center/mc2-center-dcc`](https://github.com/mc2-center/mc2-center-dcc)
("Data coordination resources for CCKP"), by cloning it read-only and
grepping for the specific names/values this branch changes.

The changes aren't a pile of independent edits — they're two coherent
patterns plus one infrastructure migration:

1. **Attribute consolidation**: ~70 per-entity-prefixed duplicate attributes
   (`Biospecimen Sex`/`Individual Sex`/`Model Sex`, `Dataset Grant Number`/
   `Publication Grant Number`/`Tool Grant Number`/`Resource Grant Number`,
   `Dataset Assay`/`File Assay`/`Publication Assay`, `Study License`/
   `Tool License`/`Resource License`, `Grant Investigator`/`Project
   Investigator`/`Study Investigator`, etc.) collapsed into single shared
   attributes (`Sex`, `grantNumber`, `Assay`, `License`, `Investigator`),
   defined once in `modules/shared/` and reused via `DependsOn` (this repo's
   established "Key not Ref" pattern).
2. **CV-to-reference-validation shift**: several fields (`Therapeutic Agent`,
   `Primary Site`, `Primary Diagnosis`, `Known Metastasis Sites`,
   `Anatomic Site`, `Biospecimen Site of Resection or Biopsy`, `File
   Longitudinal Event Type`) moved from a closed `shared/*.csv` picklist to
   free-text NCIt/UBERON reference validation or a regex pattern
   (`^UBERON:\d+$`); the backing CV files (`shared/anatomicSite.csv`,
   `shared/primaryDiseaseSite.csv`, `shared/primaryDiagnosisCDS.csv`,
   `shared/therapeuticAgent.csv`, `shared/tissueOrganOriginCDS.csv`,
   `file/eventType.csv`) were deleted outright, not renamed.
3. **Curator migration**: `schematicpy` dropped from `requirements.txt`;
   `mc2.model.jsonld`/`json_schemas/*.json` generation now goes through
   `synapseclient.extensions.curator` instead of the `schematic` CLI.

Both patterns land on real, live-consumed columns and values — this is not
a cosmetic rename. One instance of exactly this failure mode **already
happened once, inside this branch's own development**: `consortium_name.csv`
was deleted in favor of `consortium_id.csv`, and `kg-pipeline`'s own
`crosswalk_scdm.py` broke because it still pointed at the deleted file
(fixed in `191c8f1`, "fix broken consortium crosswalk, point at
consortium_id.csv"). That's direct, observed evidence this class of change
breaks a downstream consumer that isn't updated in lockstep — the question
for `mc2-center-dcc` (and any other undiscovered consumer) is whether the
same thing is about to happen again, just not caught yet because nothing
exercises that path in this repo's own test suite.

## Approach

### A. Resource model changes (Dataset/Study/Publication/Grant/Tool/EducationalResource/DataCatalog)

1. **`grantNumber` consolidation** (`Dataset/Publication/Tool/Resource Grant
   Number` → shared `grantNumber`): Valid Values list went from populated to
   **empty** — it's now a free-text/join-key field, not a CV. Confirm this
   is intentional (it matches `kg-pipeline`'s own `cckp_join:
   "Grant.grantNumber"` design) and not an accidental drop of validation.
2. **`Assay` consolidation** (`Dataset/File/Publication Assay` → shared
   `Assay`): Valid Values list grew (9,434→9,590 chars) — net-additive,
   lower risk, but diff the actual value sets (not just lengths) to confirm
   nothing existing was dropped in the merge.
3. **`License` consolidation** (`Study/Tool/Resource License` → shared
   `License`): sizes diverge a lot per entity (e.g. `Study License` was 102
   chars, the new shared `License` is 3,474) — confirm every value any of
   the three source CVs used to allow is still present in the merged list.
4. **`Investigator` consolidation** (`Grant/Project/Study Investigator` →
   shared `Investigator`) — feeds `kg-pipeline`'s SCDM Person-minting
   (`link_scdm.py`); already covered on the kg-pipeline side, but confirm
   `mc2-center-dcc`'s `portal_tables/create_grant_projects.py` (below) is
   updated too.
5. **Consortium**: `consortium_name.csv` deleted, `consortium_id.csv` added.
   Already caused one internal break (see Context). Grep the rest of this
   repo and confirm nothing else references the deleted file by name.
6. **Institution**: `institution_id.csv` added alongside the existing
   (reformatted) `institution_name.csv`/`institution_alias.csv` — additive,
   not a deletion, lower risk than consortium's file removal, but confirm
   nothing assumed the old row ordering/content of the two reformatted files.
7. **DataCatalog** (new module): additive only, populated from native
   Synapse Dataset-entity annotations rather than curator-submitted
   manifests, per `kg-pipeline/README.md`'s own description. Confirmed
   `dca_config/dca-template-config.json` is untouched by this PR and has no
   `DataCatalog` entry — consistent, no action needed there for this class.
8. **`dca_config/dca-template-config.json` sanity pass**: this file is
   hand-maintained, not regenerated by any build step, and this PR doesn't
   touch it. None of its `schema_name` entries match a renamed/removed
   class from this PR's `json_schemas/` changes (checked against the
   `10xVisium*` renames and `ImagingChannel`'s removal below) — but do an
   explicit manual read-through before merge, since nothing will flag this
   file if it silently drifts.

### B. Assay model changes (Biospecimen/Individual/Model/File-level + Sequencing/Imaging/GeoMx/Visium)

1. **`Sex` consolidation** (`Biospecimen/Individual/Model Sex` → shared
   `Sex`): Valid Values list **shrank** (114→21 chars) — a narrowing, not an
   expansion. This is the highest-priority item to audit: pull the live
   Synapse Biospecimen/Individual/Model tables and check for any existing
   `Sex` annotation value that isn't in the new, smaller list.
2. **Biospecimen collection-method enum reformatting**: not just re-casing —
   some values changed concept, not just spelling (`"Blooddraw"`→
   `"BloodDraw"`, `"Fineneedleaspirate"`→`"Aspiration"`,
   `"Coreneedlebiopsy"`→`"BoneMarrowAspiration"`, `"ForcepsBiopsy"`→
   `"NeedleBiopsy"`). `json_schemas/Biospecimen.json` shrank from 8,145 to
   395 lines reflecting this. **Audit the live Biospecimen Synapse table for
   every value in this CV against the new list before merge** — this is the
   single most concrete "a previously-valid annotation could now fail
   validation" finding in the whole diff.
3. **CV-to-reference-validation shift** (see Context, pattern 2): confirm
   this is a deliberate, reviewed design decision (it reads as one — the new
   descriptions explicitly say "reference-validated, not a fixed list") and
   not an inadvertent side effect of the consolidation. It loosens
   validation (any UBERON-shaped string now passes vs. a closed list before)
   rather than tightening it, so the breakage risk here is low, but it's a
   real reduction in curation-time enforcement worth an explicit sign-off
   from whoever owns curation QA.
4. **`File Assay Category` split out of `Assay`/`DSP Dataset Assay`**
   (CRDC_CDE 12373576): a structural split of a previously-merged concept on
   a class (`File`) used by both portal Dataset rows and the MC2 assay File
   View — confirm `kg-pipeline`'s `File View` harmonization (already
   updated per its own history) and any DCC-side File-level annotation
   script agree on which field now holds which value.
5. Per PR #262's own body: Image Assay Type/GeoMx DSP Assay Type CDE
   conflict resolved, Biospecimen Preservation Method/Composition/Embedding
   Medium/File Format/NGS Library Strategy/Sex brought to CDE parity, Tool
   Entity Role un-mapped, Tumor Grade reformatted, legacy CDE tags removed
   (`Study_id`, `DSP Data Use Codes`) — each already individually reviewed
   per-attribute during the CDE alignment rounds; no further action beyond
   the general template/live-data checks below.
6. **18 `templates/*.csv` files** got header renames tracking the
   consolidations above (`Biospecimen.csv`, `Individual.csv`, `Model.csv`,
   and several NanoString/Visium templates). Anyone with an in-progress
   local copy of an old template mid-curation will have a header mismatch —
   worth a heads-up to active curators ahead of merge, not just a code fix.

### C. Infrastructure / code changes

1. **Curator migration**: `requirements.txt` drops `schematicpy` entirely;
   `convert_model_to_jsonld.py` now calls
   `synapseclient.extensions.curator.generate_jsonld` directly; root
   `Makefile`'s `convert` target updated to match. Separately, **`make all`
   itself changes shape**: on `main`, `all: collate generate-json` — it
   never actually regenerated `mc2.model.jsonld`. On `cde-model-revisions`,
   `all: collate convert generate-json` adds `convert` back in. This is a
   real behavior change to the top-level build target, independent of the
   schematicpy swap, and should be called out explicitly in the PR/release
   notes (anyone who ran `make all` on main and assumed `mc2.model.jsonld`
   was current was wrong; that's now fixed).
2. **`mc2-center-dcc` still depends on `schematic` directly** in 5 of its
   own files (`portal_tables/union_qc.py`, `utils/csv_to_ttl.py`,
   `annotations/upload-workflow.sh`, `annotations/upload-manifests.py`,
   `curator_tools/create_file_based_metadata_task.py`) for manifest
   validation/upload against this repo's generated schema. Data-models
   dropping its own `schematicpy` dependency doesn't remove DCC's, but the
   curator-generated `mc2.model.jsonld`'s shape must still be something
   `schematic`'s validator can consume — **verify DCC's schematic-based
   validate/upload path against a curator-generated `mc2.model.jsonld`
   before merge**, not just against schematicpy's old output shape.
3. `qc_model/mc2_qc.model.csv` + `.jsonld` (346,288 lines) and `make qc`
   removed. Confirmed non-functional before this branch touched it (called
   the already-broken `schematic schema convert` CLI) — this is removing a
   capability that didn't work, not introducing a regression.
4. **`json_schemas/` regeneration side effects**: 5 files renamed
   (`VisiumAuxiliaryFiles*`→`10xVisiumAuxiliaryFiles*`, matching the
   Makefile's own `DATA` list naming) — cosmetic. `ImagingChannel.json`
   deleted with no replacement — confirmed the underlying `Imaging Channel`
   model class is unchanged and still `IsTemplate: True` on both branches,
   and confirmed `ImagingChannel` was never in the Makefile's `DATA`
   generation list on *either* branch, so this reads as stale-file cleanup,
   not a new gap. Decision needed: add it to `DATA` if a standalone template
   is actually wanted, or leave it out deliberately (and say so, so the next
   person doesn't wonder). `Dataset.json` (vs. `DatasetView.json`) is
   unchanged/stale on both branches — pre-existing, unrelated to this PR,
   flagged only so it isn't mistaken for a new issue.
5. **`kg-pipeline/`**: new, self-contained subsystem (own venv,
   requirements.txt, Makefile, test suite) building an RDF knowledge graph
   from this model plus live Synapse data. Additive and isolated from the
   root build — `make all` at the repo root never touches it — so low
   direct risk to the curation pipeline itself. It has no CI coverage yet
   (confirmed no `.github/workflows/*` runs its build or tests), which is a
   real operational gap for a subsystem this size, independent of this
   integration.
6. `docs/model/dataCatalog.md` + `scripts/hooks.py` changes — additive,
   auto-deployed by the existing `build-docs.yml` on push to main, no manual
   step needed.
7. Pre-existing, not introduced by this branch: `build-jsonld.yml` (which
   used to run `make all` on every PR) was already removed from `main`
   before this branch started. No CI currently validates `make all` or
   `kg-pipeline` on PRs — worth deciding, given the scale of this PR, whether
   to restore some form of "does the model still build" CI gate as part of
   landing it, rather than relying entirely on local verification.

### D. `mc2-center-dcc` coordination (cross-repo check)

Cloned `mc2-center/mc2-center-dcc` read-only and grepped it for the specific
names/values this branch changes. Findings:

- **Real, concrete coupling confirmed**: 9+ files hardcode the exact
  per-entity attribute names being consolidated — most centrally
  `annotations/attribute_dictionary.py`'s `ATTRIBUTE_DICT`/`PUBLICATION_DICT`
  (`"Publication Assay": "assay"`, `"Dataset Assay": "assay"`,
  `"Publication Grant Number": "grantNumber"`, ...), plus
  `portal_tables/sync_publications.py`, `portal_tables/create_grant_projects.py`
  (reads `grant["Grant Investigator"]`), `utils/check_publications_status.py`,
  `utils/table_to_annotations.py`, `utils/merge_and_correct_manifests.py`,
  `annotations/processing-splits.py` (also hardcodes `"Tool License"`), and
  `annotations/edit_legacy_annotations.py`/`annotations/split_manifest_grants.py`.
  These need updating in lockstep with this PR, the same way
  `crosswalk_scdm.py` needed updating here.
- **No matches** for the changed CV enum strings (old Biospecimen values),
  the renamed/removed `json_schemas` filenames, or `qc_model`/`make qc` —
  those specific risk categories are clear on the DCC side.
- **CI timing**: `sync-to-portal.yml` (DCC's main portal-table sync) is
  `workflow_dispatch`-only — no unattended cron risk right after merge, but
  whoever next runs it manually needs DCC's scripts updated first.
  `update-theme-graphs.yml` and `publications-status-check.yml` **do** run
  on a monthly cron (`0 0 1 * *`) — real risk of unattended breakage on the
  1st of the month following this merge if DCC isn't updated first.
- DCC does not vendor/pin/submodule this repo's generated files directly (no
  `.gitmodules`, no committed copy of `mc2.model.jsonld`/`json_schemas/`) —
  it consumes column *names* via its own sync scripts against live Synapse
  tables, which is exactly why the renames matter and a file-content diff
  alone wouldn't have caught this.
- DCC also has its own `utils/csv_to_ttl.py`/`build_ttl_graphs.sh`/
  `build_ttl_templates.sh` TTL-building tooling, independent of
  `kg-pipeline`. Didn't read these files' contents — worth a follow-up to
  confirm whether this is legacy/superseded by `kg-pipeline` or serves a
  genuinely different purpose (e.g. per-manifest TTL for Synapse JSON-schema
  binding, per the neighboring `utils/synapse_json_schema_bind.py`), since
  duplicate-but-diverging TTL tooling across two repos is its own
  maintenance risk regardless of this PR.

## Out of scope for this pass (flagged as follow-ups, not acted on)

- Actually auditing the live Synapse Biospecimen/Individual/Model/Sex tables
  against the new Valid Values lists (items B.1/B.2 above) — needs Synapse
  read access to the real production tables and sign-off from whoever owns
  curation QA; this plan identifies exactly what to check, not the check
  itself.
- Opening/updating PRs against `mc2-center-dcc` for the hardcoded
  attribute-name dictionary and sync scripts (item D above) — that's a
  separate repo with its own review process; this plan only identifies what
  needs to change there.
- Reading `mc2-center-dcc`'s `csv_to_ttl.py`/`build_ttl_*.sh` to determine
  overlap with `kg-pipeline` — noted as a follow-up, not resolved here.
- Deciding whether to restore a `make all`/`kg-pipeline` CI gate (item C.7)
  — a repo-policy call, not made here.
- Any actual `git merge`/`git rebase` mechanics for landing PR #262 — main
  hasn't moved since the merge-base, so this is a clean fast-forward
  whenever the above is cleared; no git-level conflict work is needed.

## Verification

- Live-data audits (Sex, Biospecimen collection-method values) return zero
  violations against the new Valid Values lists, or every violation found is
  triaged (re-annotate vs. add as a recognized legacy value) before merge.
- `mc2-center-dcc`'s `attribute_dictionary.py` and the sync/annotation
  scripts listed in D are updated to the new shared attribute names, and a
  dry run of `sync-to-portal.yml` (or the equivalent scripts run locally
  against a test table) succeeds against the new schema shape.
- DCC's `schematic`-based validate/upload path (item C.2) successfully
  validates a manifest against a curator-generated `mc2.model.jsonld` from
  this branch.
- `make all` (root) and `make schema && make test` (kg-pipeline) both run
  clean from a fresh clone of `cde-model-revisions` post-merge.
- `dca_config/dca-template-config.json` manually reviewed and confirmed to
  need no changes (or updated if it does).
- PR #262's `major` label stands (no new evidence found here that changes
  that assessment).

## Process

- Store this plan at `plans/cde_model_revisions_integration.md` for review
  before acting on it.
- After executing the coordination/audit steps above (in this conversation
  or a future one), append an Implementation Report below this line
  documenting what was actually found/fixed and any deviations from this
  plan.
