# Knowledge graph design doc

## Context

governanceDUO has one page that explains its whole knowledge graph:
`docs/graph-design.md` (~750 lines, in MkDocs). It covers what the graph is for,
where it sits in Sage Brain, its layers, the model, identifiers and namespaces,
how it is built and validated, how to query it, how it relates to
sagebrain-model, and what is operational today. data-models has no page like it.
Everything about `kg-pipeline/` is split across three places:

- `kg-pipeline/README.md` (378 lines): a command reference and directory layout.
  It is not on the MkDocs site.
- `plans/kg_pipeline_architecture_decisions.md` (527 lines): design rationale,
  v1 limitations, Schema.org alignment, MONDO/UBERON promotion, sagebrain-model
  interop, the MC2 assay-metadata KG, and live-data verification.
- ~8 initiative plans: `scdm_alignment.md`, `datacatalog_kg_integration.md`,
  `kg_pipeline_sagebrain_alignment.md`, `cckp_schema_class_alignment.md`,
  `cckp_shacl_shape_gaps.md`, `mondo_uberon_federation_promotion.md`,
  `cckp_copilot_sparql_graph_followups.md` and `kg_pipeline_readme_fixes.md`.

The MkDocs nav (`nav.yml`) covers only the data model. It has no
knowledge-graph section.

## Approach

1. Add `docs/knowledge-graph.md`, titled "CCKP knowledge graph design". Use the
   same section structure as governanceDUO's `graph-design.md`, adapted to this
   repo's graph:
   1. What the graph is for, and what it deliberately doesn't do.
   2. Where it sits: a mermaid diagram of Synapse portal tables, the MC2 model
      and CVs, kg-pipeline, the Synapse distribution folder, the SageBrain S3
      bucket and Neptune, sagebrain-model, and the SCDM and ontology crosswalks.
   3. The layers, as a table: schema (mc2_model and cckp_portal TBox), portal
      instances, ontology-IRI harmonization, Biolink dual typing, DataCatalog,
      SCDM and ontology-crosswalk federation, the MC2 assay-metadata KG
      (access-controlled), and the manifest.
   4. The model: LinkML schemas, class alignment (Schema.org/Biolink), the
      "Key not Ref" foreign-key convention, and a worked Turtle example taken
      from real pipeline output.
   5. Identifiers and namespaces: `mint_iri()`, Synapse-canonical IRIs vs the
      w3id placeholder namespace, and the prefix table.
   6. How it is built: a stage-by-stage mermaid diagram, SSSOM mappings, the
      suggest-mappings stage, SHACL validation, `queries/*.rq` checks, tests,
      and the publish paths.
   7. Using the graph: example SPARQL taken from `queries/examples/`.
   8. Relationship to sagebrain-model, including the D9 principle (never
      assert governanceDUO-owned types; join only on shared `syn:` IRIs).
   9. What's operational today, as a status table.
   10. Where to look next.
2. Make every factual claim trace to a file, Makefile target or function in
   the repo. Where a source is stale, the code wins.
3. Add a nav entry in `nav.yml`.
4. Follow the no-process-narration rule: write the page for users and link to
   `plans/` for history, rather than retelling it.

## Verification

- Spot-check every file path, Make target, script name and IRI in the page
  against the tree (for example with `grep` or `ls`).
- Check that the SPARQL examples parse with rdflib and that they return rows
  against `data/rdf/` output where it exists.
- `mkdocs build --strict`, or plain `mkdocs build` if strict mode fails because
  of warnings that were already there. Mermaid rendering depends on
  `pymdownx.superfences` custom fences. Check whether that is configured, and
  add the fence config if it isn't.
- Before accepting the page, the orchestrator reviews the diff against this
  plan.

## Process

Store this plan at plans/kg_design_doc.md for review before implementing.
After implementing, append an Implementation Report below this line.

## Implementation Report (2026-09-24)

Implemented per the Approach, with no departures from its 10-section
structure. Read governanceDUO's `docs/graph-design.md` in full (read-only,
no edits there) and matched its tone/structure: numbered `## N.` sections,
mermaid flowcharts, a layer table, a namespace table, a worked Turtle
example, SPARQL examples, a "What's operational today" status table, and a
"Where to look next" table.

**Files changed:**
- `docs/knowledge-graph.md` (new, 632 lines) — title "# CCKP knowledge graph
  design". Sections: 1 What the graph is for (incl. what it deliberately
  doesn't do), 2 Where it sits (mermaid), 3 The layers (table), 4 The model
  (LinkML schemas, schema.org/Biolink class alignment, the "Key"-vs-"Ref"
  foreign-key distinction, a worked Turtle example), 5 Identifiers and
  namespaces (`mint_iri()`, namespace table), 6 How the graph is built
  (mermaid, harmonization/SSSOM, suggest-mappings/crosswalks, validation,
  tests, publish paths), 7 Using the graph (3 SPARQL examples from
  `queries/examples/`), 8 Relationship to sagebrain-model and governanceDUO
  (incl. the D9 principle), 9 What's operational today (status table), and
  "Where to look next" (table).
- `nav.yml` — added `Knowledge Graph: knowledge-graph.md` as a top-level
  entry between `Data Models` and `Standard Terms`. Checked
  `scripts/hooks.py`'s `on_files()` first: it loads `nav.yml` wholesale into
  `config["nav"]` and only *overwrites* the `"Standard Terms"` key
  afterward (to splice in the auto-generated per-model valid-values pages)
  — every other top-level key, including the new one, passes through
  unmodified and in the same (Python dict / PyYAML, insertion-ordered)
  position.
- `mkdocs.yml` — `pymdownx.superfences` had no `custom_fences` entry for
  mermaid (it was a bare list item), so nothing would have rendered the two
  diagrams. Added the standard Material config (`custom_fences: - name:
  mermaid, class: mermaid, format:
  !!python/name:pymdownx.superfences.fence_code_format`). No other
  `mkdocs.yml` change.

**Verification run (all commands actually executed, not summarized from
memory):**

- SPARQL parse check — every file in `kg-pipeline/queries/*.rq` and
  `kg-pipeline/queries/examples/*.rq` (15 files total) parsed cleanly with
  `rdflib.plugins.sparql.prepareQuery` (via `kg-pipeline/.venv`, rdflib
  7.6.0).
- SPARQL run check — ran `kg-pipeline/scripts/run_query.py queries/examples
  data/rdf/cckp_kg_full.ttl` (the real, already-built 340,786-triple graph):
  all 6 example queries returned real rows —
  `datasets_by_tumor_type` 175, `information_content_entities_by_source_class`
  341, `measurement_technique_without_resolved_assay` 6,
  `open_source_tools_by_operation` 1, `program_output_rollup` 26,
  `publications_for_datasets` 394. Also ran
  `scripts/validate_graph.py --queries queries data/rdf/cckp_kg_full.ttl`:
  9/9 sanity checks (the pass/fail `queries/*.rq` files) passed.
- `mkdocs build` — mkdocs itself was present globally but
  `mkdocs-material`/`mkdocs-table-reader-plugin` were not, so per the spec I
  created a scratch venv at `/private/tmp/claude-504/mkdocs-venv` and
  installed `mkdocs`, `mkdocs-material`, `mkdocs-table-reader-plugin`,
  `pandas`, `PyYAML` there (global env untouched beyond that).
  - `mkdocs build --strict` failed, but not because of anything in this
    change: `scripts/hooks.py`'s `on_pre_build()` hit a hard
    `pandas.errors.ParserError` reading two **pre-existing** CV CSVs —
    `modules/biospecimen/stainType.csv` (row "In situ hybridization") and
    `modules/shared/fileAssayCategory.csv` (rows "LC-MS/MS" and
    "Quantitative Immunofluorescence") — each has a `Description` cell with
    an unescaped, unquoted internal comma, so the row tokenizes into more
    fields than the header declares. Confirmed unrelated to this task:
    `git status --short` before/after showed only `mkdocs.yml`, `nav.yml`,
    and the new `docs/knowledge-graph.md` touched; the same
    `pandas.read_csv()` call fails identically on these two files in
    isolation, with or without any of this change's edits.
  - Since I couldn't fix pre-existing model CSV data as part of a docs-only
    task without exceeding this task's scope, I verified the actual
    deliverable (nav entry, mermaid rendering, the new page itself) in an
    **isolated scratch copy** instead: `rsync`'d the repo (minus `.git`,
    `kg-pipeline/.venv`, `kg-pipeline/data`) to
    `/private/tmp/claude-504/docs-build-check`, quoted the three offending
    CSV cells there only, and ran `mkdocs build`/`mkdocs build --strict`
    from that copy. **The real working tree's two CSV files were never
    modified** — this was purely a disposable side-channel check.
  - In the scratch copy, `--strict` still failed, but only on 123
    pre-existing warnings (broken `../valid_values/shared.md#attribute-*`
    anchors and missing `legacy-docs/assets/*` images) — none mention
    `knowledge-graph.md`. Plain `mkdocs build` (no `--strict`) succeeded
    with exit code 0 and built `site/knowledge-graph/index.html`: `<h1
    id="cckp-knowledge-graph-design">CCKP knowledge graph design`, 2
    rendered `class="mermaid"` blocks (matching the page's two diagrams),
    and the `Knowledge Graph` nav entry present in the site sidebar. No
    output at all mentioned `knowledge-graph.md`.

**Discrepancies between source docs/plans and the current code (code
followed, per the Hard rules; not narrated in the page itself):**

- `kg-pipeline/README.md`/`plans/kg_pipeline_architecture_decisions.md`
  describe the consortium→SCDM Program crosswalk as shipping
  `reviewed=false` until a human curates it ("currently mints 0 Program
  nodes by design"). As of this branch's current
  `mappings/crosswalks/consortium_to_scdm_program.tsv`, all 11 rows are
  actually `reviewed=true`, and `data/rdf/scdm_links.ttl` really does carry
  11 `sagecdm:Program` nodes and their `consortiumRef` edges — the human
  curation pass already happened and the docs weren't updated. The page
  states the current (`reviewed=true`, live) status, not the stale
  "0 by design" description.
- `plans/kg_pipeline_architecture_decisions.md`'s "Verified against live
  data" section cites a prior run of **331 Tools** and a merged graph of
  **431,744 triples**. The current `kg-pipeline/data_sources.yaml` records
  **349 Tools**, and parsing the current `data/rdf/cckp_kg.ttl`/
  `cckp_kg_full.ttl` with rdflib gives **304,990** / **340,786** triples
  respectively — a smaller live graph than the plan's snapshot, presumably
  from portal data changing between runs. The page's "What's operational
  today" table cites the current, re-verified numbers.
- `mc2_model.linkml.yaml` carries no `cckp_join` annotations at all
  (grepped directly — confirmed absent), so the "Key not Ref" section
  states precisely that MC2-model "Key" fields reached through that schema
  (e.g. `File View`'s `Biospecimen Key`) come through `build_triples.py` as
  plain literals unless a stage resolves them itself (which
  `link_sagebrain.py` does, by grouping on the literal value) — this isn't
  a discrepancy against any doc, just a fact I verified in code rather than
  assumed, since no existing doc stated it explicitly.

**Not independently verified:** SHACL validation
(`scripts/validate_graph.py --shacl schema/cckp_portal.shacl.ttl
data/rdf/cckp_kg_full.ttl`) was not re-run against the full ~340K-triple
graph for this pass (the spec's verification list required the SPARQL
parse/run checks and the `mkdocs build`, not a fresh SHACL run) — section 9
of the page cites it as "operational, run in `make validate`/`make
full-kg`" based on the code path and the existing SHACL fixtures under
`kg-pipeline/test/fixtures/`, not a live re-run for this page.
`data/rdf/scdm_links.ttl`'s Organization/Program counts (90/11) were
confirmed by grepping the actual committed Turtle file, not by re-running
`make link-scdm`.

The two malformed CV CSVs found above
(`modules/biospecimen/stainType.csv`, `modules/shared/fileAssayCategory.csv`)
were left unmodified in the real repository, as flagged to the requester —
fixing model data is outside this task's scope, but they currently block
any `mkdocs build` (strict or plain) run directly against this repo's
working tree.

**Orchestrator review (2026-09-24):** Spot-checked the page against the code:
`mint_iri()`, the crosswalk `reviewed` status (11 `sagecdm:Program` nodes in
`scdm_links.ttl`), every referenced path, and every Make target all hold. Four
fixes were made after review:
- The worked example claimed "Pending Annotation" resolved through a
  blank-value convention. In fact, it is a file-format CV term mapped to
  `NCIT:C53470`.
- `scripts/graph_iris.py` is attributed to governanceDUO only.
- The "Data Models" link pointed to the *Model* data-type page and now
  points to the home page.
- Removed the "verified for this page" narration.

**Follow-up fixes (2026-09-24):**
- **Malformed vocabulary CSVs.** Three unquoted Description cells were
  quoted: `modules/biospecimen/stainType.csv` ("In situ hybridization") and
  `modules/shared/fileAssayCategory.csv` ("LC-MS/MS" and "Quantitative
  Immunofluorescence"). The stray comma had shifted "In situ
  hybridization"'s Source value (`CRDC_CDE:8120269`) into Nonpreferred
  Terms, and `all_valid_values.csv` carried that shift. It is corrected now.
- **"Pending Annotation" aliases.** `NCIT:C53470` is "Pending", so the
  mapping is correct. The problem was the "LA" and "Limited Access" aliases
  in `tissue.csv`, `assay.csv` and `tumorType.csv`. They would have mapped
  a genuine "Limited Access" value to "Pending". No portal table uses
  either string as a vocabulary value (the only matches are in abstract
  prose), so the aliases were removed. `assay.csv` keeps "Pending
  annotation".
- **Stale crosswalk status.** Comments in `kg-pipeline/Makefile` and
  `kg-pipeline/README.md` now say that all 11 consortium→SCDM Program rows
  are `reviewed=true`. The live-data counts in
  `plans/kg_pipeline_architecture_decisions.md` were updated to the
  2026-09-24 run. Historical plans such as `scdm_alignment.md` were left
  unchanged.
- **Verification.**
  - `mkdocs build` against the real tree exits 0, with no warnings about
    `knowledge-graph.md`. The hook's generated files were removed
    afterward.
  - `update_valid_values.py` and `make collate` ran cleanly. The only
    output change is in `all_valid_values.csv`, as described above.
  - kg-pipeline `pytest` passes: 156 tests.
