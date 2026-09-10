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
