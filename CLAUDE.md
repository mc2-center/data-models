# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Data models and controlled vocabularies for the [Cancer Complexity Knowledge Portal](https://cancercomplexity.synapse.org/) (CCKP). The model is maintained as CSV files in domain-specific `modules/`, collated into `mc2.model.csv`, and converted to JSON-LD/JSON Schema via `synapseclient.extensions.curator` (the actively-maintained successor to [schematicpy](https://pypi.org/project/schematicpy/), which Sage Bionetworks has announced will be retired by end of 2026) for use by the [Data Curator App](https://dca.app.sagebionetworks.org/).

A second subsystem, `kg-pipeline/`, converts this model (plus live CCKP portal data pulled from Synapse) into an RDF knowledge graph - its own LinkML schema, an extract → harmonize → map-to-RDF → validate build, and publish paths to Synapse and (optionally) a SageBrain Neptune S3 bucket. It has its own README, Makefile, and Python environment - see "kg-pipeline (knowledge graph)" under Architecture below.

## Commands

```bash
# Install dependencies (Python 3.10+)
pip install -r requirements.txt

# Full build: update valid values in all modules → collate → generate JSON Schemas
make all

# Steps individually:
python update_valid_values.py   # reads modules/mapping.yaml, rewrites annotationProperty.csv Valid Values columns
make collate                    # concatenates all modules/*/annotationProperty.csv → mc2.model.csv
make convert                    # python convert_model_to_jsonld.py → mc2.model.jsonld
make generate-json              # python create_json_from_model.py <data types> → json_schemas/

# Generate JSON schemas for specific data types only
python create_json_from_model.py Biospecimen Study Dataset

# Docs dev server
mkdocs serve   # http://localhost:8000
```

```bash
# kg-pipeline: separate venv + requirements.txt (isolated from the root
# install above - linkml pulls a large, independently-versioned dependency
# tree). Run from kg-pipeline/.
cd kg-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

make schema               # regenerate schema/*.ttl from schema/*.linkml.yaml
make all                  # schema + extract (needs Synapse credentials) + harmonize + triples + validate
make full-kg              # combined-kg + SCDM/ontology-crosswalk federation -> data/rdf/cckp_kg_full.ttl
make deploy-kg            # upload cckp_kg_full.ttl + manifest.ttl -> its Synapse distribution folder
make upload-sagebrain-s3  # local equivalent of nf-osi/kg-pipeline's Neptune S3 upload (needs SAGEBRAIN_BUCKET + aws CLI)
make test                 # pytest test/ - no live Synapse access needed
```

## Architecture

### The module + collation pattern

Each domain lives in `modules/<domain>/`:
- `annotationProperty.csv` — attribute definitions for that domain (type, description, valid values, validation rules)
- One CSV per controlled vocabulary (e.g., `specimenType.csv`, `fixative.csv`) — the actual enumerated terms

`modules/mapping.yaml` is the central registry: it maps each attribute name to the CV CSV that provides its valid values. `update_valid_values.py` reads this file and rewrites the `Valid Values` column in each `annotationProperty.csv`.

`make collate` then concatenates all `annotationProperty.csv` files into `mc2.model.csv` (the header comes from the consortium module, body from all others via `tail -n +2`).

### CSV conventions
- All columns read/written as `dtype=str` — `TRUE`/`FALSE` must not become `True`/`False`
- No NaN — use empty strings (`keep_default_na=False`)
- Index on `Attribute` column when updating via pandas

### kg-pipeline (knowledge graph)

`kg-pipeline/` is a separate, self-contained pipeline (own `README.md`, `Makefile`, `requirements.txt`, `test/`) that builds an RDF knowledge graph from this model plus live CCKP portal data:

- **Stage 0**: this repo's `mc2.model.csv` → `schema/mc2_model.linkml.yaml` (via a vendored `csv-to-linkml` converter) → `schema/mc2_model.ttl` (OWL/Turtle)
- **Stages 2-4**: pull the 5 CCKP portal Synapse tables → resolve controlled-vocabulary values against this model's CVs (real ontology IRIs: NCIT, MONDO, EFO, OBI, ...) → mint RDF instance triples, dual-typed `cckp:{Class}` and (where Biolink has a matching class) `biolink:{Class}`
- **Stage 5**: SHACL shape validation + `queries/*.rq` sanity checks
- **Stage 6**: `manifest.ttl` - a small PROV/VOID statement about the build (git commit, timestamp, where the graph was published), used as a lightweight trigger file by a downstream Neptune auto-loader instead of polling the much larger merged graph
- Optional stages: Data Catalog annotations, SCDM (Sage Common Data Model) federation, MC2 assay-metadata KG (access-controlled, linked into `sagebrain-model`)
- Publish paths: Synapse (`make publish-portal-kg`, `make deploy-kg`) and a local-runnable SageBrain Neptune S3 upload (`make upload-sagebrain-s3`, needs `SAGEBRAIN_BUCKET` + the `aws` CLI - no CI/OIDC; `--dry-run` mirrors the upload locally without either)

Instance IRIs use Synapse's own canonical form (`https://www.synapse.org/Synapse:synNNN...`) for any row with a real Synapse entity id, rather than minting a second identifier - see `mint_iri()` in `scripts/build_triples.py`. Everything else keeps the placeholder `w3id.org/mc2-center/cckp-portal/data/{Class}/{id}` namespace.

See `kg-pipeline/README.md` for the full command reference, directory layout, and design rationale (also `plans/kg_pipeline_architecture_decisions.md`).

### PR requirements
PRs to main must have exactly one semantic label: `major`, `minor`, `patch`, or `non-release`. The `pr-check.yml` workflow enforces this.

### CI workflows (`.github/workflows/`)
| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `build-docs.yml` | Push to main | Builds MkDocs site → GitHub Pages |
| `docs-check.yml` | PR events | Runs `mkdocs build --strict` (no deploy) |
| `pr-check.yml` | PR events | Validates semantic label |
| `google-sheet-sync.yml` | Scheduled/manual | Syncs RFC Google Sheets to a CSV branch |
| `create-release.yml` | Manual trigger | Creates GitHub release with version bump |

No CI currently validates `make all` (root model) or `kg-pipeline/`'s build/tests on PRs (the old `build-jsonld.yml` was removed as obsolete; nothing replaced it) - run them locally before pushing model or kg-pipeline changes. `docs-check.yml` covers the docs site build itself.
