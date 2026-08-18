# CCKP Knowledge-Graph Pipeline

Builds a queryable RDF knowledge graph for the Cancer Complexity Knowledge
Portal (CCKP): a LinkML schema for the portal's own tables, an RDF/Turtle
representation of both that schema and the MC2 Center data model (this
repo), and a pipeline that extracts real CCKP data from Synapse and
materializes it as triples with real ontology IRI mappings (NCIT, MONDO,
EFO, OBI, ...) sourced from this repo's controlled-vocabulary CSVs.

Modeled after [nf-osi/kg-pipeline](https://github.com/nf-osi/kg-pipeline)'s
stage structure (extract → harmonize → map-to-RDF → validate) and its
never-silently-drop-a-value discipline, but built on LinkML instead of a
hand-authored OWL ontology + RML/Java, since LinkML is what this task asked
for and this repo already has LinkML tooling (originally the `csv-to-linkml`
Claude Code skill; a copy is vendored into `scripts/vendor/` - see below) that
knows how to read its ontology mappings. See "Design decisions" below for
the full list of deliberate departures from the nf-osi reference.

## Architecture

```
Stage 0 (occasional)                    Stage 1 (hand-authored once)
mc2.model.csv + mapping.yaml            cckp_portal.linkml.yaml
      │ scripts/vendor/csv_to_linkml.py       │ imports mc2_model.linkml.yaml
      │ + scripts/resolve_prefixes.py         │ for shared enums (assay, tumorType,
      ▼                                       │ species, tissue, license, etc.)
schema/mc2_model.linkml.yaml                  ▼
      │ `make schema` (linkml generate owl)   schema/cckp_portal.ttl
      ▼
schema/mc2_model.ttl  ◄── committed, both are the "RDF turtle representation" deliverables

Stage 2: Extract              Stage 3: Harmonize                 Stage 4: Map to RDF
Synapse tables                data/raw/*.csv                     data/harmonized/*.csv
(synapseclient,                 │ look up each vocab value          │ rdflib: mint IRIs,
 5 View tables)   ──────────►   │ against MC2 CV CSV (via           │ emit literal + ontology-
      │                         │ mapping.yaml), emit               │ IRI edge per row,
      ▼                         │ <field>_ontology_iri + reports    │ FK columns → object props
data/raw/<table>.csv  ────────► data/harmonized/<table>.csv ─────►  data/rdf/<table>.ttl
                                 + mappings/sssom/<field>.sssom.tsv        │
                                                                            ▼
                                                        data/rdf/cckp_kg.ttl (merged:
                                                        mc2_model.ttl + cckp_portal.ttl
                                                        + all per-table instance triples)
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Stage 2 (extract) needs Synapse credentials: set `SYNAPSE_AUTH_TOKEN`, or
have a cached `synapseclient` login (`~/.synapseConfig` /
`syn.login()`'d before). All 5 in-scope tables are public.

## Running

```bash
make schema      # regenerate schema/*.ttl from schema/*.linkml.yaml
make extract      # pull the 5 CCKP tables from Synapse -> data/raw/
make harmonize    # resolve controlled-vocabulary values -> data/harmonized/
make triples      # build RDF -> data/rdf/<Table>.ttl + data/rdf/cckp_kg.ttl
make validate     # parse-check the schema turtle + report harmonization coverage
make all          # schema + extract + harmonize + triples + validate
make test         # pytest test/ (fixture-based, no live Synapse access needed)
```

To regenerate `schema/mc2_model.linkml.yaml` after `modules/` changes
upstream (not part of `make schema` - see "Design decisions"):

```bash
make mc2-model-linkml
```

This uses `scripts/vendor/csv_to_linkml.py`, a vendored copy of the
`csv-to-linkml` Claude Code skill's converter (stdlib-only, no extra
dependencies) - reproducible from a clean clone, no Claude Code skill
installation required.

## Verified against live data

Last run against the real portal pulled **1141 Datasets, 4773
Publications, 331 Tools, 160 Grants, 10 EducationalResources** and produced
a merged graph of **402,092 triples** in `data/rdf/cckp_kg.ttl` (not
committed - see `data/` in `.gitignore`). Example resolved queries:

- `Dataset -[tumorTypeTerm]-> NCIT:C3510` (Cutaneous Melanoma) for a real
  dataset row.
- `Dataset -[grantNumberRef]-> Grant` cross-entity joins resolve correctly
  for all 1141 datasets that have a grant number matching a real Grant row.

## v1 scope and known limitations

- **Person/PersonView is out of scope.** The `cckp-search` skill's own docs
  flag its backing table ID as unconfirmed and note a consent/portal-display
  gate that would need separate handling - a documented follow-up, not an
  oversight.
- **Publication/Tool/EducationalResource have no declared LinkML
  `identifier` slot.** No confirmed-live unique row-ID column exists for
  these tables (verified against the live Synapse table schema, not
  assumed). `scripts/build_triples.py`'s `mint_id()` uses a documented
  fallback chain per class (e.g. Publication: `pubMedId`, else a hash of
  title+doi) - see the schema file's per-slot comments and
  `FALLBACK_ID_FIELD` in `build_triples.py`.
- **Field cardinality (scalar vs. list) was verified against the live
  Synapse table schema** (`synapseclient.Synapse.getTableColumns`), not
  guessed from the MC2 model or naming conventions - several fields
  surprised in both directions (e.g. `Dataset.grantNumber`/`consortium`/
  `dataType` are list-valued despite having no MC2-model array analog;
  `Publication.authors`/`keywords` and `Tool.license`/`toolEntityType` are
  scalar despite reading as list-like). If the live table schema changes,
  re-verify `schema/cckp_portal.linkml.yaml`'s `multivalued` flags rather
  than trusting the header comment as a lasting truth.
- **Real, pre-existing gaps in the MC2 model's own ontology curation are
  surfaced, not hidden.** `make harmonize` produces two distinct reports:
  - `data/harmonized/unmapped_terms.csv` - a CCKP value didn't match any
    term in its mapped MC2 controlled-vocabulary CSV. Some of these CVs
    (`grant_number.csv`, `publication_accessibility.csv`,
    `theme_name.csv`, `consortium_name.csv`, `tool_operation.csv`,
    `tool_license.csv`, and others) currently have **zero** populated
    `Ontology Identifier` values at all - every value against them will be
    "unresolved" until that curation work happens (candidate follow-up for
    the `ols-term-annotator`/`cadsr-cde-match` skills already in this repo's
    toolkit).
  - `data/harmonized/malformed_cv_terms.csv` - a CV row's own `Ontology
    Identifier` isn't a valid CURIE and its `Ontology Url` isn't a valid
    URL (e.g. `modules/shared/tissue.csv` stores bare ICD-O-3 topography
    codes like `C15.2`, and one `modules/shared/tumorType.csv` row stores a
    bare ICD-O-3 morphology code `9835/3`). These are treated as "no
    ontology mapping" rather than emitted as a fake IRI. Worth a follow-up
    similar to this repo's prior CDE/ontology mismatch reviews.
- **`linkml generate owl` logs "Ambiguous attribute" warnings** for field
  names reused verbatim across multiple CCKP classes (e.g. `grantNumber` on
  Dataset/Publication/Tool/EducationalResource). Each is a `class`-scoped
  LinkML `attribute`, not a shared top-level `slot`, so this is expected
  and non-blocking - fixable later by promoting shared-name fields to
  top-level `slots:` with `slot_usage:` overrides per class, not needed for
  correct RDF output today.

## Design decisions (departures from nf-osi/kg-pipeline)

nf-osi/kg-pipeline uses Dagster + RML/RMLMapper (Java) + a hand-authored
OWL ontology, at NF-portal scale (~400K-row Files table). This pipeline
instead uses:

- **LinkML**, not a hand-authored ontology - the user's explicit ask, and
  this repo already has `csv-to-linkml`/`ols-term-annotator` Claude Code
  skills built around it (the former is vendored into `scripts/vendor/` so
  this pipeline doesn't depend on a skill installation - see below).
- **Plain Python + rdflib**, not RML/Java, for triple-building - CCKP is
  ~5 tables/~6.4K rows total, rdflib is already an (unused) repo
  dependency, and this avoids a JVM toolchain for a portal this size.
- **A Makefile + Python CLI scripts**, not Dagster - matches this repo's
  existing `make all`/`make collate` idiom; nf-osi's own architecture doc
  explicitly endorses a Makefile as a valid orchestrator at smaller scale.
- **The MC2 model's own controlled-vocabulary CSVs as the harmonization
  source of truth**, not new hand-authored SSSOM files - `mappings/sssom/*.tsv`
  is still produced (standard format, reviewable, portable to other
  tooling) but as a *byproduct* of joining against `modules/mapping.yaml` +
  the CV CSVs, not the primary curation artifact.

## Directory layout

```
kg-pipeline/
  README.md
  Makefile
  requirements.txt           - isolated from the repo root's requirements.txt;
                                linkml pulls a large, independently-versioned
                                dependency tree (Sphinx, SPARQLWrapper, a newer
                                pydantic, ...) that would conflict with the
                                root env's pins.
  data_sources.yaml          - Synapse table synIds + last-pulled row count/timestamp
  schema/
    mc2_model.linkml.yaml    - generated via `make mc2-model-linkml` + resolve_prefixes.py
    mc2_model.ttl             - generated via `make schema`
    mc2_model_prefixes_report.md
    cckp_portal.linkml.yaml  - hand-authored; imports mc2_model.linkml.yaml
    cckp_portal.ttl           - generated via `make schema`
  mappings/sssom/*.sssom.tsv - harmonization crosswalks (generated, committed)
  scripts/
    vendor/csv_to_linkml.py   - vendored csv-to-linkml skill converter (Stage 0)
    resolve_prefixes.py       - Stage 0 fixup (see script docstring)
    extract_cckp_tables.py    - Stage 2
    harmonize.py               - Stage 3
    build_triples.py           - Stage 4
    validate_graph.py          - Stage 5
  data/                        - gitignored: raw/, harmonized/, rdf/
  test/
    fixtures/*.csv             - small hand-made sample rows, one per in-scope table
    conftest.py, test_*.py     - pytest suite (24 tests, no live Synapse access needed)
```
