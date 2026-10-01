# Docs build fixes

## Context

`mkdocs build` on `kg-pipeline-fixes` gave 122 warnings, and `--strict`
fails. The causes:

- **103 links to `valid_values/shared.md`.** `modules/mapping.yaml` lists
  about 40 attributes under a `shared:` key (assay, tumor type, species,
  file format, tissue, and others). `scripts/hooks.py`'s
  `_load_attribute_owners()` sends each "View" link to its owning model's
  page. But `generate_valid_values_markdown()` only runs for the keys in
  `DATA_MODELS`, and `shared` isn't one of them. The page is never
  generated, so every shared-vocabulary link on the live site is broken.
- **About 8 links to pages that are never generated.** Examples are
  `valid_values/visiumRNALevel4.md`, `geomxLevel3.md` and
  `imagingLevel3Image.md`. An attribute that has Valid Values but no
  `mapping.yaml` owner falls back to the current model
  (`attribute_owners.get(attr, model)`). That model has no mapping entry, so
  no page is generated for it.
- **About 12 broken image links in `docs/legacy-docs/`.** These are fixed
  by deleting the orphaned directory (commit `b235856`, user decision).
- **Nothing builds the docs on PRs.** `.github/workflows/build-docs.yml`
  runs `mkdocs gh-deploy` only on pushes to main. On `cde-model-revisions`,
  malformed CV CSVs would have broken the main deploy, and no PR check
  would have caught it.
- **The new `docs/knowledge-graph.md` isn't linked from either README.**

## Approach

1. Generate a valid-values page for `shared`, and add it to the Standard
   Terms nav with the title "Shared". Make sure every `mapping.yaml`
   top-level key that owns an attribute gets a page. Don't hardcode
   `shared` alone.
2. When an attribute has Valid Values but no `mapping.yaml` owner, list
   which attributes those are and fix the root cause:
   - If the values come from a CV CSV, add the missing `mapping.yaml`
     entry.
   - Otherwise, make the hook render "None" instead of a dead link, so it
     never links to a page that won't be generated.
3. Add a link to the design page from the root `README.md`'s "Knowledge
   Graph Pipeline" section and from `kg-pipeline/README.md`.
4. Add a PR workflow that runs `mkdocs build --strict`, using the same
   dependencies as `build-docs.yml`.

## Verification

- `mkdocs build --strict` passes locally with 0 warnings.
- Spot-check that a shared-attribute "View" link (for example Assay on the
  Dataset page) resolves to an anchor that exists in the built site.
- The workflow YAML parses, and the dependencies it installs match
  `build-docs.yml`.
- Clean up the generated files afterward: `docs/valid_values/*.md` and
  `modules/*/reference.csv` must not be left untracked.

## Process

Store this plan at plans/docs_build_fixes.md for review before implementing.
After implementing, append an Implementation Report below this line.

## Implementation Report (2026-09-25)

**Step 1 - `scripts/hooks.py`.** Added `_extra_vocab_owners()`: it walks
every `DATA_MODELS` model's attributes, and for any attribute whose
`mapping.yaml` owner isn't itself a `DATA_MODELS` key, collects that owner.
`consortium`, `institution`, and `project` each own attributes, but every one
of those is only referenced by that key's own non-page root manifest
attribute (`Consortium`, `Institution`, `Project View`) - no `DATA_MODELS`
page ever links to them, so they were excluded. `shared` (owns Assay,
Tissue, Tumor Type, Species, File Assay Category, Sex, Disease Type, etc.)
is referenced from 20+ model pages, so it's the only key that needed a page.
`on_pre_build` now calls `generate_valid_values_markdown()` (only - no
`generate_linked_table()`/`reference.csv`, since these keys aren't
templates) for each key `_extra_vocab_owners()` returns; `on_files` appends
each to `Standard Terms > Terms by model` after the per-model entries, titled
by capitalizing the key (`shared` -> `Shared`).

**Step 2 - attributes with Valid Values but no owner.** Enumerated via the
build's actual warnings/anchor-mismatches (cross-checked against
`_get_model_attributes()` + `mc2.model.csv`):

| Attribute | Models it appears on | Source | Action |
|---|---|---|---|
| `Data Use Codes` | dataset, file, study, and 18 imaging/geomx/sequencing/visium models | Values are exactly `modules/shared/duo.csv` (verified set-equality) | Added `mapping.yaml` entry under `shared:` -> `shared/duo.csv` |
| `DSP Data Use Codes` | sharingPlans | Same `duo.csv` set | Added `mapping.yaml` entry under `sharingPlans:` -> `shared/duo.csv` |
| `Biospecimen Preservation Temperature` | biospecimen | Inline list in `annotationProperty.csv`, no CV file | Hook renders `None` |
| `Biospecimen Timepoint Type` | biospecimen | Inline, no CV file | `None` |
| `Biospecimen Treatment Prior to Specimen Collection Indicator` | biospecimen | Inline, no CV file | `None` |
| `File Data Category` | file | Inline, no CV file | `None` |
| `File Data Checksum Type` | file | Inline, no CV file | `None` |
| `File Data Compression Status` | file | Inline, no CV file | `None` |
| `Image DICOM Modality Type` | imagingLevel1 | Inline, no CV file | `None` |
| `Individual Age 90 or Older` | individual | Inline, no CV file | `None` |
| `Individual Disease Progression or Recurrence Type` | individual | Inline, no CV file | `None` |
| `Individual Residual Disease Status` | individual | Inline, no CV file | `None` |
| `Individual Treatment Intent Type` | individual | Inline, no CV file | `None` |
| `Individual Treatment or Therapy Indicator` | individual | Inline, no CV file | `None` |

Fixed the hook's fallback (`generate_linked_table`'s Standard Terms column):
it now links only when `attribute_owners` has a real entry for the
attribute; otherwise renders the literal text `None`, consistent with how
attributes with no Valid Values at all were already rendered - never
`attribute_owners.get(attr, model)`, which produced the dead links.

Ran `python update_valid_values.py` (and `make collate`, to also refresh
`mc2.model.csv`, since a downstream `Description`-cell fix below needed
propagating there too - `convert`/`generate-json` were **not** run, out of
scope). `git diff --stat`:
```
all_valid_values.csv                        | 64 +++++++++++++--------------
mc2.model.csv                                |  4 +-
modules/mapping.yaml                         |  4 ++
modules/shared/annotationProperty.csv        |  2 +-
modules/sharingPlans/annotationProperty.csv  |  2 +-
```
`Valid Values` columns are byte-identical before/after (verified by diffing
just those cells) - the two new mapping.yaml entries pointed at the exact
same value sets those attributes already had, so `update_valid_values.py`'s
rewrite was a no-op there. The only real content change (beyond
`mapping.yaml` itself) is `all_valid_values.csv` (regenerated dedup'd
concat, now includes the two newly-mapped attributes) and one incidental
fix: the `Data Use Codes` / `DSP Data Use Codes` Description cells in
`modules/shared/annotationProperty.csv` and
`modules/sharingPlans/annotationProperty.csv` contained a stray markdown
link to `valid_values/study/#attribute-study-data-use-codes` (a page/anchor
that never existed) - corrected to `valid_values/shared/#attribute-data-use-codes`,
which is now real. `mc2.model.csv`'s 4-line diff is just that same
Description-text correction propagating through `make collate`.

**Step 3 - README links.** Added a sentence to root `README.md`'s
"Knowledge Graph Pipeline" section pointing to
`https://mc2-center.github.io/data-models/knowledge-graph/` (same
`mc2-center.github.io/data-models/...` pattern already used for
`[Contributing guidelines]`). Added a matching sentence near the top of
`kg-pipeline/README.md`, linking `../docs/knowledge-graph.md` (relative
path, consistent with that file's existing `../plans/...` links).

**Step 4 - `docs-check.yml`.** New workflow at
`.github/workflows/docs-check.yml`, `on: pull_request` (no branch filter),
same actions/pins and `pip install mkdocs-material
mkdocs-table-reader-plugin pandas pyyaml` as `build-docs.yml`, runs
`mkdocs build --strict` only (no `gh-deploy`, no secrets). Verified
`python -c "import yaml; yaml.safe_load(...)"` parses it. Added a row to
CLAUDE.md's CI workflows table and softened the sentence claiming no PR CI
builds docs.

### Checks (verbatim)

```
$ /private/tmp/claude-504/mkdocs-venv/bin/mkdocs build --strict -d /private/tmp/claude-504/site-out
...
exit code: 0
```
```
$ grep -c "WARNING" mkdocs_output.log
0
```
Remaining output is a single pre-existing (since commit `4f7e6e1`,
2026-08-19, unrelated to this plan's causes) `INFO`-level anchor mismatch in
hand-written prose on `docs/model/study.md`, referencing a
`Study Data Use Codes` attribute that doesn't exist in the model (likely a
stale reference from before it was renamed). `INFO` doesn't fail `--strict`
and this line isn't one of the plan's listed causes, so it was left as-is -
flagging it here rather than silently leaving it out of the report.

Anchor spot-check:
```
$ grep -o 'valid_values/shared/#[a-z0-9-]*' /private/tmp/claude-504/site-out/model/dataset/index.html | sort -u
valid_values/shared/#attribute-assay
valid_values/shared/#attribute-data-use-codes
valid_values/shared/#attribute-tissue
valid_values/shared/#attribute-tumor-type

$ grep -o 'id="attribute-assay"' /private/tmp/claude-504/site-out/valid_values/shared/index.html
id="attribute-assay"
```

Cleanup + final status:
```
$ git ls-files --others --exclude-standard -- 'docs/valid_values/*.md' 'modules/*/reference.csv'
(24 + 32 generated files, all untracked - none were tracked; docs/valid_values/all_terms.md
is tracked and was left alone since it wasn't in this list)
$ <removed all of the above>
$ git status --short
 M CLAUDE.md
 M README.md
 M all_valid_values.csv
 M kg-pipeline/README.md
 M mc2.model.csv
 M modules/mapping.yaml
 M modules/shared/annotationProperty.csv
 M modules/sharingPlans/annotationProperty.csv
 M scripts/hooks.py
?? .github/workflows/docs-check.yml
?? plans/docs_build_fixes.md
```

### Not done / out of scope
- The `docs/model/study.md` stale `Study Data Use Codes` prose reference
  (INFO-level, non-blocking, pre-existing, not one of the plan's listed
  causes - left for a separate pass).
- `make convert` / `make generate-json` (JSON-LD + JSON Schema regeneration)
  were not run; only `make collate` (root `mc2.model.csv`) needed
  refreshing for this task, and running the rest was out of scope for a
  docs-build fix.

### Orchestrator follow-ups (2026-09-25)
- **`docs/model/study.md`.** The page's prose named a nonexistent
  "Study Data Use Codes" attribute 6 times. Those now say "Data Use Codes",
  and the link points to the Shared page. `mkdocs build --strict` now prints
  0 warnings and no INFO lines.
- **`requirements.txt`.** It lacked `synapseclient[curator]`, so
  `make convert` and `make generate-json` failed with an ImportError in a
  clean install. Added the extra.
- **Regenerated artifacts.** Regenerated `mc2.model.jsonld` and
  `json_schemas/` so they carry the corrected Data Use Codes Description
  link. The diff is exactly 23 link replacements. The generator also
  produced 7 schemas that aren't tracked; those were deleted.
- **`docs-check.yml`.** Added `permissions: contents: read`.
