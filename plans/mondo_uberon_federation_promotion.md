# Promote reviewed MONDO/UBERON crosswalk rows into a linked graph output

## Context

Reviewed `SageBrain RDF Knowledge Graph Construction` (draft doc, Sage
Bionetworks' NF-OSI-derived KG pipeline architecture reference, not checked
into this repo) against `kg-pipeline/`'s ontology-alignment code. Its
"Suggested Ontologies for Cross-Portal Alignment" table names **MONDO** for
Disease/phenotype and **UBERON** for Anatomy/tissue as the recommended
cross-portal anchors — explicitly caveated as unratified suggestions
("These are suggestions. We have not formally agreed upon this alignment
across portals"), consistent with the doc's own design principle to "delay
expensive harmonization or ontology alignment work until there is clear
cross-portal agreement or governance."

This pipeline already anchors `tumorType`/`diseaseType`/`diseaseStatus`/
`tissue` in **NCIT** (matching what the MC2 model's own CV CSVs are curated
against — this is correct and shouldn't change) and separately produces
**supplementary** NCIT→MONDO/UBERON crosswalks via
`scripts/crosswalk_ontology.py`, explicitly for future sagebrain-model
federation, never consumed by `harmonize.py` or the main graph build. Per
that script's own docstring: "This script does NOT change how kg-pipeline
harmonizes its own data... it produces a *supplementary* crosswalk... a
crosswalk hit is never written back... automatically."

Checked current coverage of these crosswalk files (all committed, all
reviewed=none-tracked today):

| File | Rows | Target-ontology hits |
|---|---|---|
| `mappings/crosswalks/tumorType_ncit_to_mondo.sssom.tsv` | 174 | 174 MONDO (100%) |
| `mappings/crosswalks/diseaseType_ncit_to_mondo.sssom.tsv` | 38 | 38 MONDO (100%) |
| `mappings/crosswalks/diseaseStatus_ncit_to_mondo.sssom.tsv` | 6 | 6 MONDO (100%) |
| `mappings/crosswalks/tissue_ncit_to_uberon.sssom.tsv` | 113 | 105 UBERON + 1 CL (94%) |

Coverage is already essentially complete, but every row is still only a
proposal — `crosswalk_ontology.py`'s output has no per-row
confirmed/reviewed marker at all today (unlike the SCDM crosswalk stage,
which already solved exactly this "generated but needs human sign-off before
it's trusted" problem: `mappings/crosswalks/consortium_to_scdm_program.tsv`
ships a `reviewed` column defaulting to `"false"`, and
`scripts/link_scdm.py:108` explicitly skips any row where
`(row.get("reviewed") or "").strip().lower() != "true"`). This plan reuses
that exact, already-proven pattern rather than inventing a new one.

Given the PDF calls out disease-focus and tissue-based landscape/coverage
queries as priority cross-portal competency questions, and the crosswalk
data is already near-complete, promoting **reviewed** rows into an actual
graph output (additive, alongside the existing NCIT triples — never
replacing them) is now a low-risk, well-grounded next step, gated on human
review rather than automatic trust.

## Approach

1. **Add a `reviewed` column to `scripts/crosswalk_ontology.py`'s TSV
   writer**, defaulting every row to `"false"` on generation — mirroring
   `scripts/crosswalk_scdm.py`'s exact column name and `"false"` string
   value (not a boolean type, matching existing SSSOM-adjacent TSV
   convention). Re-running `make crosswalk-ontology` must not silently
   flip existing human-reviewed rows back to unreviewed — follow
   `crosswalk_scdm.py`'s own merge-not-overwrite handling if it has one,
   or document why a clean regenerate is safe here (crosswalk rows are
   keyed on stable CV `Attribute` labels, not row order).

2. **Human review step (outside this plan's automation):** a person
   reviews each of the 4 files' rows against the source NCIT term and sets
   `reviewed` to `"true"` for confirmed matches — given the 94-100%
   automated-match rate already found, this is plausibly a fast pass, not a
   from-scratch curation effort, but it is explicitly out of scope for an
   agent to bulk-flip without review.

3. **New script `scripts/link_ontology_crosswalk.py`**, structured like
   `scripts/link_scdm.py`:
   - Load `data/rdf/cckp_kg.ttl` (the already-built instance graph from
     `make triples`).
   - For each of the 4 crosswalk files, filter to `reviewed == "true"` rows
     only (exact pattern from `link_scdm.py:108`).
   - For every subject with an existing `cckp:tumorTypeTerm` /
     `cckp:diseaseTypeTerm` / `cckp:diseaseStatusTerm` / `cckp:tissueTerm`
     edge whose NCIT object matches a reviewed crosswalk row's source CURIE,
     emit an additional edge — `cckp:tumorTypeMondoTerm` /
     `cckp:diseaseTypeMondoTerm` / `cckp:diseaseStatusMondoTerm` /
     `cckp:tissueUberonTerm` — to the crosswalk's target MONDO/UBERON IRI.
     Additive only: the original NCIT triple is untouched.
   - Write output to its own file, `data/rdf/ontology_crosswalk_links.ttl`
     — a new, separate provenance file, following the convention the README
     already documents for `scdm_links.ttl`/`DataCatalog.ttl` ("same subject
     IRIs, different trust tier/upstream source, combine by simple
     triple-set union — no join logic needed").

4. **New Makefile target `make link-ontology-crosswalk`**, and fold its
   output into `full-kg`'s union alongside `link-scdm` (matching how
   `combined-kg`/`full-kg` already union multiple stage outputs into their
   own separate merged file, never mutating `cckp_kg.ttl` in place).

5. **Documentation**: add this stage to `kg-pipeline/README.md`'s
   "Additional pipeline stages" list, the "Running" command table, the
   "Consuming the graph" table, and the "Directory layout" section — matching
   the existing entries for the DataCatalog and SCDM stages exactly in
   structure. Add a short section to
   `plans/kg_pipeline_architecture_decisions.md` documenting this as a
   deliberate, gated promotion of the previously-review-only MONDO/UBERON
   crosswalks (cross-reference this plan file).

6. **Tests**: `test/test_link_ontology_crosswalk.py`, fixture-based like
   `test/test_link_scdm.py` — a small fixture `cckp_kg`-shaped graph plus a
   handful of fixture crosswalk rows (some `reviewed=true`, some `false`,
   confirming unreviewed rows are correctly skipped and reviewed rows
   correctly resolve).

## Verification

- `make test` passes, including the new `test_link_ontology_crosswalk.py`.
- Run `make crosswalk-ontology` to regenerate the 4 crosswalk files with the
  new `reviewed` column (all `"false"` until a human reviews them) —
  confirm no existing MONDO/UBERON hits are lost or altered, only the new
  column added.
- After manually flipping a representative sample (or all, given the
  coverage already found) of rows to `reviewed=true`, run
  `make triples && make link-ontology-crosswalk` against real/dev data and
  spot-check: a `Dataset` already resolving `cckp:tumorTypeTerm` →
  `NCIT:C3510` should also resolve `cckp:tumorTypeMondoTerm` → a real MONDO
  CURIE in `data/rdf/ontology_crosswalk_links.ttl`.
- `make validate` (SHACL + coverage regression gate) still passes — this
  stage doesn't touch `harmonize.py`, CV files, or the coverage baseline at
  all, so no regression is expected there.
- Confirm `make full-kg` still produces a single unioned graph when this
  new file is added to its inputs, the same way it already does for
  `scdm_links.ttl`.

## Process

Store this plan at `plans/mondo_uberon_federation_promotion.md` for review
before implementing. After implementing, append an Implementation Report
below this line — what was actually done, any deviations from the Approach
section, and verification results.

## Implementation Report

Implemented with two scope-narrowing deviations found during
implementation (both documented below and in
`plans/kg_pipeline_architecture_decisions.md`'s new "MONDO/UBERON crosswalk
promotion" section), everything else as planned.

**Step 1:** Added a `reviewed` column (default `"false"`) to
`scripts/crosswalk_ontology.py`'s `write_sssom()`, via a new
`load_existing_reviewed()` that reads any previously-written file at the
same path and carries forward existing `reviewed` values keyed on
`subject_id` (the source NCIT CURIE - stable across re-runs, unlike row
order). Applied the same column to the 4 already-committed crosswalk files
directly (`tumorType`/`diseaseType`/`diseaseStatus_ncit_to_mondo.sssom.tsv`,
`tissue_ncit_to_uberon.sssom.tsv`) rather than re-running live OLS4 queries
via `make crosswalk-ontology` - avoids depending on live network access and
non-reproducible OLS index drift for a purely mechanical column addition;
every row defaults to `reviewed=false`, identical to what a regen would
produce. Added `test/test_crosswalk_ontology.py` (3 tests) covering the
default-false and preserve-on-rerun behavior, including a mixed case (one
previously-reviewed row + one newly-added row on the same rerun).

**Step 2 deviation:** the plan called for `link_ontology_crosswalk.py` to
load the *built* `data/rdf/cckp_kg.ttl` graph and match against its existing
`cckp:{field}Term` edges. Implemented instead by reading the harmonized CSVs
directly (`data/harmonized/{Class}_harmonized.csv`'s `{field}_ontology_iri`
cell) and reusing `build_triples.py`'s own `mint_id`/`mint_iri`/
`expand_curie_or_url`/`load_prefixes` - this is the same pattern
`scripts/link_scdm.py` already uses (it never touches `cckp_kg.ttl` either),
so this is a correction toward the codebase's actual established
convention, not a new one. Simpler and avoids re-parsing the multi-hundred-
thousand-triple built graph just to look up a value already available in
the harmonized CSV.

**Step 2 scope-narrowing (real, surfaced, not silent):** only `tumorType`
and `tissue` are wired up in `FIELD_CROSSWALKS`/`FIELD_CLASSES`, not all 4
crosswalk files the plan's Context section listed. "Disease Type"/"Last
Known Disease Status" (backing `diseaseType`/`diseaseStatus_ncit_to_mondo`)
turned out, on checking `schema/cckp_portal.linkml.yaml` and
`modules/mapping.yaml` directly, to be MC2 individual/biospecimen-level
attributes with no corresponding field on any of the 5 CCKP portal classes
- and not extracted by the mc2-assay stage either. There is no
`cckp:diseaseTypeTerm`/`diseaseStatusTerm` edge anywhere in this pipeline's
output for a MONDO edge to attach to. `scripts/link_ontology_crosswalk.py`'s
module docstring and its run output ("Not yet consumable...") say this
explicitly; the two crosswalk files stay committed, `reviewed` column and
all, for whenever a future stage extracts those fields.

**Steps 3-5:** `scripts/link_ontology_crosswalk.py` implemented per the
(corrected) design above. `make link-ontology-crosswalk` target added,
folded into `full-kg` (chained via two `scripts/merge_ttl.py` calls,
`base==out` on the second, which is safe since `merge_ttl.py` fully parses
before serializing). `test/test_link_ontology_crosswalk.py` (5 tests)
covers: reviewed-only filtering, additive-not-replacing behavior (asserts
`cckp:tumorTypeTerm` is never touched), and a full
`build_ontology_crosswalk_links()` end-to-end run producing both a MONDO
and a UBERON edge. `kg-pipeline/README.md` updated in all 4 places the plan
named (Running table, Consuming-the-graph table, Additional-pipeline-stages
list, Directory-layout section) plus the `mappings/crosswalks/` description
updated to explain the `reviewed` gate and the diseaseType/diseaseStatus
non-consumption. `plans/kg_pipeline_architecture_decisions.md` got a full
new section rather than "a short section" as originally scoped, since the
CL-prefix gap and the scope-narrowing finding below were worth preserving
in full.

**Also found, left as-is (out of scope for this plan):** one row in
`tissue_ncit_to_uberon.sssom.tsv` (`Peripheral Blood Mononuclear Cell`)
resolved to `CL:2000001` rather than a UBERON term - `crosswalk_ontology.py`
returns the best available OLS hit even outside its nominal target
ontology. `schema/mc2_model.linkml.yaml`'s `prefixes:` block has no `CL:`
entry, so `expand_curie_or_url()` can't expand it and this one row is
silently (by that function's own existing, documented design) skipped even
if flipped to `reviewed=true`. Not fixed here - adding a `CL:` prefix to the
MC2 model's central prefix registry is a bigger-surface change than this
plan's scope.

**Verification results:**
- `make test` - all 94 tests pass (86 pre-existing + 8 new:
  5 in `test_link_ontology_crosswalk.py`, 3 in `test_crosswalk_ontology.py`).
- `make link-ontology-crosswalk` against the real, live `data/harmonized/`
  tree with every crosswalk row at its shipped `reviewed=false` default
  produces exactly 0 triples, as expected.
- Manually flipped 5 rows each in `tumorType_ncit_to_mondo.sssom.tsv`/
  `tissue_ncit_to_uberon.sssom.tsv` to `reviewed=true` and re-ran against
  real data: 161 real triples (133 `tumorTypeMondoTerm` edges/129 rows, 28
  `tissueUberonTerm` edges/27 rows), spot-checked resolving to real MONDO/
  UBERON IRIs on real minted Dataset/Publication subject IRIs. Reverted the
  crosswalk files back to `reviewed=false` afterward via a saved backup
  (`git diff` confirmed only the intended `reviewed`-column addition
  remained, not the temporary flip).
- Did not run `make validate`'s SHACL/coverage checks specifically for this
  change - this stage doesn't touch `harmonize.py`, any CV file, or the
  coverage baseline, so no regression is expected there; not re-verified
  live in this session beyond the `make test` suite and the manual
  `link-ontology-crosswalk` run above.
