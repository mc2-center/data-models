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
hand-authored OWL ontology + RML/Java. See
[`plans/kg_pipeline_architecture_decisions.md`](../plans/kg_pipeline_architecture_decisions.md)
for the full design rationale, including why LinkML/rdflib/Makefile were
chosen over nf-osi's Dagster + RML/Java stack.

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
      │                         │ mapping.yaml), emit               │ IRI edge per row + a
      ▼                         │ <field>_ontology_iri + reports    │ resolvable external IRI
data/raw/<table>.csv  ────────► data/harmonized/<table>.csv ─────►  for any doi/pubMedId value,
                                 + mappings/sssom/<field>.sssom.tsv  FK columns → object props
                                        │                                    │
                                        ▼                                    ▼
                          Stage 3.5: Suggest mappings          data/rdf/<table>.ttl
                          (human-review only, never auto-              │
                          applied - see below)                         ▼
                          data/harmonized/unmapped_terms.csv  data/rdf/cckp_kg.ttl (merged:
                                  │                            mc2_model.ttl + cckp_portal.ttl
                                  ▼                             + all per-table instance triples)
                          data/harmonized/mapping_suggestions.csv
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
make schema               # regenerate schema/*.ttl from schema/*.linkml.yaml
make extract               # pull the 5 CCKP tables from Synapse -> data/raw/
make harmonize             # resolve controlled-vocabulary values -> data/harmonized/
make suggest-mappings      # propose candidate mappings for unmapped_terms.csv -> mapping_suggestions.csv
make crosswalk-ontology    # propose NCIT/BTO -> MONDO/UBERON crosswalks for sagebrain-model federation
make sagecdm-schema        # regenerate schema/sagecdm.ttl from schema/vendor/sagecdm/*.yaml
make crosswalk-scdm        # institution/consortium -> SCDM Organization/Program crosswalks
make triples               # build RDF -> data/rdf/<Table>.ttl + data/rdf/cckp_kg.ttl
make link-scdm             # link the CCKP graph to SCDM Organization/Program/Person -> data/rdf/scdm_links.ttl
make extract-datacatalog   # pull Data Catalog annotations from native Synapse Dataset entities -> data/raw/
make harmonize-datacatalog # resolve Data Catalog controlled-vocabulary values -> data/harmonized/datacatalog/
make triples-datacatalog   # build RDF -> data/rdf/DataCatalog.ttl (merges onto existing cckp:Dataset subjects)
make merge-datacatalog     # fold DataCatalog.ttl into cckp_kg.ttl IN PLACE (dropped by the next `make triples`)
make combined-kg           # triples + triples-datacatalog, merged into their own data/rdf/cckp_kg_with_datacatalog.ttl
make full-kg               # combined-kg + link-scdm, merged into data/rdf/cckp_kg_full.ttl (the fullest graph)
make validate              # parse-check the schema turtle + coverage report + regression gate + SHACL shapes
make update-coverage-baseline  # after intentionally curating a CV or accepting a new gap
make publish-portal-kg     # upload data/raw|harmonized|rdf -> the public portal Synapse staging location
make all                   # schema + extract + harmonize + triples + validate
make test                  # pytest test/ (fixture-based, no live Synapse access needed)

# Access-controlled MC2 assay-metadata KG (biospecimen/individual/model/sequencing/imaging) -
# separate stage, never part of `make all`; see "Additional pipeline stages" below
make extract-mc2-assay     # walk Dataset entities -> data/mc2_assay/raw/"File View.csv"
make harmonize-mc2-assay   # -> data/mc2_assay/harmonized/
make triples-mc2-assay     # -> data/mc2_assay/rdf/mc2_assay_kg.ttl
make link-sagebrain        # -> data/mc2_assay/rdf/sagebrain_links.ttl
make publish-mc2-assay     # upload raw/harmonized/rdf -> the restricted Synapse staging location
```

To regenerate `schema/mc2_model.linkml.yaml` after `modules/` changes
upstream (not part of `make schema`):

```bash
make mc2-model-linkml
```

This uses `scripts/vendor/csv_to_linkml.py`, a vendored copy of the
`csv-to-linkml` Claude Code skill's converter (stdlib-only, no extra
dependencies) - reproducible from a clean clone, no Claude Code skill
installation required.

**`make suggest-mappings` picks its external registry per-CV automatically**
(`scripts/suggest_mappings.py`'s `choose_registry()`), driven by whatever
CURIE prefix a CV's own existing `Ontology Identifier` values already use
most (`ROR:...` → the ROR API, `SPDX:...` → SPDX's own license-list-data,
anything else → EBI OLS4). If you hit a CV backed by some other non-OLS
registry, add one `<registry>_search()` function and one entry to
`PREFIX_TO_REGISTRY` there - don't hand-roll a separate one-off script the
way SPDX mappings used to be done. A prefix confirmed not to be in OLS
(`NON_OLS_PREFIXES`) but still missing a registered backend prints a
warning instead of silently returning nothing.

## Consuming the graph

`data/rdf/` isn't one file - it's several, some independent and some layered
on top of each other. Which one to load depends on what you need:

| I want... | Load | Built by |
|---|---|---|
| Just one entity type (e.g. only Datasets) | `Dataset.ttl` (or `Publication`/`Tool`/`Grant`/`EducationalResource.ttl`) | `make triples` |
| The 5 CCKP portal tables as one graph, nothing else | `cckp_kg.ttl` | `make triples` |
| ...plus native Synapse Dataset-entity annotations (`measurementTechnique`, `license`, `creator`, ...) | `cckp_kg_with_datacatalog.ttl` | `make combined-kg` |
| ...plus SCDM Organization/Program federation links | `cckp_kg_full.ttl` | `make full-kg` |
| Only the SCDM federation layer itself, to reason about separately | `scdm_links.ttl` | `make link-scdm` |
| The schema alone (classes/properties, no instance data) | `schema/mc2_model.ttl` + `schema/cckp_portal.ttl` | `make schema` |

**Why so many files instead of one.** Some of this is genuine subsetting
(`cckp_kg.ttl` is just the 5 class files concatenated - nothing new
asserted). Some is deliberate provenance separation: `DataCatalog.ttl` and
`scdm_links.ttl` both reuse the *same* subject IRIs as `cckp_kg.ttl` (a
`Dataset`/`Grant`/etc. is the same node in every file), so they combine by
simple triple-set union - no join logic needed - but each stays its own file
by default because it's a different trust tier (DataCatalog: same subjects,
different upstream source, not yet broadly verified; scdm_links: this
pipeline's own derived/provisional read of SCDM, not an authoritative SCDM
data source). `combined-kg`/`full-kg` exist so you don't have to do that
union yourself if you just want everything: they rebuild their inputs fresh
and merge them into their own separate output file, rather than mutating
`cckp_kg.ttl` in place (that in-place mutation is what `merge-datacatalog`
still does, for backward compatibility - but it's silently undone by the
next plain `make triples`, which is exactly the staleness trap
`combined-kg`/`full-kg` avoid).

**Loading more than one file together** (e.g. in a triple store, or via
`rdflib.Graph().parse(...)` called once per file) unions them automatically,
same as the Makefile targets do internally - there's no separate "connect
these" step required once the files are in front of you, only when you're
deciding which ones to combine and why.

```python
import rdflib
g = rdflib.Graph()
g.parse("data/rdf/cckp_kg.ttl", format="turtle")
g.parse("data/rdf/scdm_links.ttl", format="turtle")   # now one connected graph
```

`data/mc2_assay/rdf/` (biospecimen/individual/model/sequencing/imaging) is a
separate domain entirely - different subject IRIs, access-controlled source
data - and isn't connected to anything above; see "Additional pipeline
stages" below for what it is and how to build it.

## Additional pipeline stages

Beyond the core extract → harmonize → map-to-RDF → validate flow above,
this pipeline has three optional stages, each with its own `make` targets
(shown in "Running" above) and its own design-rationale doc:

- **Data Catalog** (native Synapse Dataset-entity annotations - `license`,
  `measurementTechnique`, `accessType`, ...): merges a second metadata
  facet onto the same `cckp:Dataset` subjects `make triples` already
  builds. See
  [`plans/datacatalog_kg_integration.md`](../plans/datacatalog_kg_integration.md).
- **SCDM (Sage Common Data Model) interop**: links `Grant`/`Dataset`/
  `Publication`/`Tool` institution and consortium values to cross-portal
  `sagecdm:Organization`/`Program`/`Person` entities. See
  [`plans/scdm_alignment.md`](../plans/scdm_alignment.md).
- **MC2 assay-metadata KG** (biospecimen/individual/model/sequencing/
  imaging): a separate, access-controlled stage linking MC2's
  assay/subject-level modules into
  [sagebrain-model](https://github.com/Sage-Bionetworks/sagebrain-model)'s
  classes - the layer that actually overlaps with sagebrain's
  biological-entity focus. Every artifact lives under the isolated,
  `.gitignore`d `data/mc2_assay/` tree (never `data/`), since per-file
  Synapse annotations here can require login, unlike the public CCKP
  portal tables the rest of this pipeline builds. See
  [`plans/kg_pipeline_architecture_decisions.md`](../plans/kg_pipeline_architecture_decisions.md)
  for the full sagebrain-model interoperability design and live-data
  discovery findings behind this stage.

For this pipeline's documented v1 scope, known limitations, and the last
verified live-data run (triple counts, example resolved queries), also see
[`plans/kg_pipeline_architecture_decisions.md`](../plans/kg_pipeline_architecture_decisions.md).

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
    cckp_portal.linkml.yaml  - hand-authored; imports mc2_model.linkml.yaml.
                                Each of the 5 classes carries a class-level
                                schema.org mapping (`exact_mappings`/
                                `close_mappings` - Dataset/Publication/Tool/
                                Grant -> schema:Dataset/ScholarlyArticle/
                                SoftwareApplication/MonetaryGrant exactly,
                                EducationalResource -> schema:LearningResource
                                as a close match only) - a cheap Layer-1
                                schema-level alignment, same schema.org
                                vocabulary the Data Catalog stage already
                                asserts real predicates in (see
                                `plans/cckp_schema_class_alignment.md`).
    cckp_portal.ttl           - generated via `make schema`
    cckp_portal.shacl.ttl    - hand-authored instance-level SHACL shapes (see
                                "Additional pipeline stages" above)
    vendor/sagecdm/*.yaml    - vendored, pinned SageCommonDataModel LinkML
                                source + VENDORED.md (see "Additional
                                pipeline stages" above)
    sagecdm.ttl               - generated via `make sagecdm-schema`
  mappings/sssom/*.sssom.tsv - harmonization crosswalks (generated, committed)
  mappings/crosswalks/*.sssom.tsv - supplementary MONDO/UBERON federation
                                crosswalks (generated, committed, human-review
                                only - never consumed by harmonize.py)
  mappings/crosswalks/institution_to_scdm_organization.tsv - deterministic,
                                no review needed (see "Additional pipeline
                                stages" above)
  mappings/crosswalks/consortium_to_scdm_program.tsv - generated, committed,
                                human-review required before use (ships
                                reviewed: false)
  mappings/confirmed_unmappable.tsv - human-curated (table, field, value, reason)
                                registry backing build_triples.py's tier-3
                                provisional placeholder IRIs
  mappings/coverage_baseline.json - coverage-gate ratchet (generated, committed -
                                unlike data/harmonized/*, which is gitignored)
  scripts/
    vendor/csv_to_linkml.py   - vendored csv-to-linkml skill converter (Stage 0)
    resolve_prefixes.py       - Stage 0 fixup (see script docstring)
    extract_cckp_tables.py    - Stage 2
    harmonize.py               - Stage 3
    suggest_mappings.py         - Stage 3.5 (human-review candidate mappings)
    crosswalk_ontology.py       - MONDO/UBERON federation crosswalks (human-review)
    build_triples.py           - Stage 4
    validate_graph.py          - Stage 5 (+ SHACL validation)
    extract_mc2_assay_metadata.py - MC2 assay-metadata KG: Synapse Dataset-entity
                                discovery + File View extraction (live Synapse
                                credentials required - not used by `make all`)
    link_sagebrain.py            - MC2 assay-metadata KG: sagebrain property links
    crosswalk_scdm.py            - institution/consortium -> SCDM crosswalks (make crosswalk-scdm)
    link_scdm.py                  - SCDM Organization/Program/Person links (make link-scdm)
    extract_datacatalog.py        - Data Catalog: native Dataset-entity annotations (make extract-datacatalog)
    build_datacatalog_triples.py  - Data Catalog: merges onto the existing cckp:Dataset subject (make triples-datacatalog)
    merge_datacatalog.py           - folds data/rdf/DataCatalog.ttl into cckp_kg.ttl (make merge-datacatalog)
    publish_kg.py                 - Synapse publish for both pipelines (--profile portal|mc2-assay)
  data/                        - gitignored: raw/, harmonized/, rdf/ (rdf/ includes
                                scdm_links.ttl once `make link-scdm` has been run,
                                DataCatalog.ttl once `make triples-datacatalog` has)
  data/harmonized/datacatalog/ - Data Catalog's own harmonize --out-dir, kept
                                separate from data/harmonized/'s own
                                unmapped_terms.csv (see "Additional pipeline
                                stages" above)
  data/mc2_assay/              - gitignored (access-controlled - see
                                "Additional pipeline stages" above): raw/, harmonized/, rdf/
  test/
    fixtures/*.csv, shacl_*.ttl - small hand-made sample rows/graphs
    conftest.py, test_*.py     - pytest suite (no live Synapse access needed,
                                except test_mc2_assay_file_view.py's fixture-only
                                tests, which also need none - live calls are
                                exercised only by running the scripts directly)
```
