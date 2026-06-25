# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Data models and controlled vocabularies for the [Cancer Complexity Knowledge Portal](https://cancercomplexity.synapse.org/) (CCKP). The model is maintained as CSV files in domain-specific `modules/`, collated into `mc2.model.csv`, and converted to JSON-LD for use by the Sage Bionetworks [schematicpy](https://pypi.org/project/schematicpy/) framework and the [Data Curator App](https://dca.app.sagebionetworks.org/).

## Commands

```bash
# Install dependencies (Python 3.10+)
pip install -r requirements.txt

# Full build: update valid values in all modules → collate → generate JSON Schemas
make all

# Steps individually:
python update_valid_values.py   # reads modules/mapping.yaml, rewrites annotationProperty.csv Valid Values columns
make collate                    # concatenates all modules/*/annotationProperty.csv → mc2.model.csv
make convert                    # schematic schema convert mc2.model.csv → mc2.model.jsonld
make generate-json              # python create_json_from_model.py <data types> → json_schemas/

# Generate JSON schemas for specific data types only
python create_json_from_model.py Biospecimen Study Dataset

# QC model build
make qc

# Docs dev server
mkdocs serve   # http://localhost:8000
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

### PR requirements
PRs to main must have exactly one semantic label: `major`, `minor`, `patch`, or `non-release`. The `pr-check.yml` workflow enforces this.

### CI workflows (`.github/workflows/`)
| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `build-jsonld.yml` | PR to main (module changes) | `make all` to validate collation + schema conversion |
| `build-docs.yml` | Push to main | Builds MkDocs site → GitHub Pages |
| `pr-check.yml` | PR events | Validates semantic label |
| `google-sheet-sync.yml` | Scheduled/manual | Syncs RFC Google Sheets to a CSV branch |
| `create-release.yml` | Manual trigger | Creates GitHub release with version bump |
