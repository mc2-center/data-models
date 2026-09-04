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
make schema              # regenerate schema/*.ttl from schema/*.linkml.yaml
make extract              # pull the 5 CCKP tables from Synapse -> data/raw/
make harmonize            # resolve controlled-vocabulary values -> data/harmonized/
make suggest-mappings     # propose candidate mappings for unmapped_terms.csv -> mapping_suggestions.csv
make crosswalk-ontology   # propose NCIT/BTO -> MONDO/UBERON crosswalks for sagebrain-model federation
make sagecdm-schema       # regenerate schema/sagecdm.ttl from schema/vendor/sagecdm/*.yaml
make crosswalk-scdm       # institution/consortium -> SCDM Organization/Program crosswalks
make triples              # build RDF -> data/rdf/<Table>.ttl + data/rdf/cckp_kg.ttl
make link-scdm            # link the CCKP graph to SCDM Organization/Program/Person -> data/rdf/scdm_links.ttl
make extract-datacatalog  # pull Data Catalog annotations from native Synapse Dataset entities -> data/raw/
make harmonize-datacatalog # resolve Data Catalog controlled-vocabulary values -> data/harmonized/datacatalog/
make triples-datacatalog  # build RDF -> data/rdf/DataCatalog.ttl (merges onto existing cckp:Dataset subjects)
make merge-datacatalog    # fold DataCatalog.ttl into cckp_kg.ttl IN PLACE (dropped by the next `make triples`)
make combined-kg          # triples + triples-datacatalog, merged into their own data/rdf/cckp_kg_with_datacatalog.ttl
make full-kg              # combined-kg + link-scdm, merged into data/rdf/cckp_kg_full.ttl (the fullest graph)
make validate             # parse-check the schema turtle + coverage report + regression gate + SHACL shapes
make update-coverage-baseline  # after intentionally curating a CV or accepting a new gap
make publish-portal-kg    # upload data/raw|harmonized|rdf -> the public portal Synapse staging location
make all                  # schema + extract + harmonize + triples + validate
make test                 # pytest test/ (fixture-based, no live Synapse access needed)
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
data source - see "Design decisions"). `combined-kg`/`full-kg` exist so you
don't have to do that union yourself if you just want everything: they
rebuild their inputs fresh and merge them into their own separate output
file, rather than mutating `cckp_kg.ttl` in place (that in-place mutation is
what `merge-datacatalog` still does, for backward compatibility - but it's
silently undone by the next plain `make triples`, which is exactly the
staleness trap `combined-kg`/`full-kg` avoid).

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
data - and isn't connected to anything above; see "Interoperating with
sagebrain-model" below for what it is and how to build it.

## Verified against live data

Last run against the real portal pulled **1141 Datasets, 4773
Publications, 331 Tools, 160 Grants, 10 EducationalResources** and produced
a merged graph of **431,744 triples** in `data/rdf/cckp_kg.ttl` (not
committed - see `data/` in `.gitignore`). Example resolved queries:

- `Dataset -[tumorTypeTerm]-> NCIT:C3510` (Cutaneous Melanoma) for a real
  dataset row.
- `Dataset -[grantNumberRef]-> Grant` cross-entity joins resolve correctly
  for all 1141 datasets that have a grant number matching a real Grant row.
- `Grant -[themeTerm]-> NCIT:C19151` (Metastasis) and `Grant
  -[grantInstitutionTerm]-> ROR:02jzgtq86` (Dana-Farber Cancer Institute),
  from the institution/theme curation described below.
- `Publication -[doiIri]-> https://doi.org/10.1038/...` and `Publication
  -[pubMedIdIri]-> https://pubmed.ncbi.nlm.nih.gov/...` - templated directly
  from the value, no CV curation involved.

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
    term in its mapped MC2 controlled-vocabulary CSV. Splits into three
    situations, not one - see `make suggest-mappings` below.
  - `data/harmonized/malformed_cv_terms.csv` - a CV row's own `Ontology
    Identifier` isn't a valid CURIE and its `Ontology Url` isn't a valid
    URL. These are treated as "no ontology mapping" rather than emitted as
    a fake IRI. Previously flagged here: `modules/shared/tissue.csv` stored
    a bare ICD-O-3 topography code (`C15.2`) and `modules/shared/tumorType.csv`
    stored a bare ICD-O-3 morphology code (`9835/3`) - both have since been
    curated with real NCIT CURIEs (verified 2026-09-01 via `harmonize.py`'s
    own `build_field_lookups` against the full model: 0 malformed rows
    across every CV registered in `modules/mapping.yaml`). Re-run this check
    after any CV edit rather than assuming this file stays empty.
- **`make suggest-mappings` (Stage 3.5) turns `unmapped_terms.csv` into a
  reviewable worklist**, `data/harmonized/mapping_suggestions.csv`. It never
  edits a CV file itself - it only classifies and proposes:
  - `curation_gap` - the raw value already exists as a CV `Attribute` (or
    `Nonpreferred Terms` alias), but that CV row's own `Ontology Identifier`
    is blank. `harmonize.py`'s `load_cv_lookup` skips such rows entirely, so
    a perfectly valid picklist term can never match. This was the single
    largest category before curation - e.g. `publication_accessibility.csv`
    had exactly 2 valid values (`Open Access`, `Restricted Access`), both
    with a blank `Ontology Identifier`, accounting for thousands of
    "unresolved" rows on its own.
  - `possible_typo` - the raw value doesn't exist in the CV, but is a close
    fuzzy match to one that does (e.g. `Mathemtical Modeling` →
    `Mathematical Modeling`, `Genera` → `General`) - raw-data noise, not a
    new concept.
  - `novel_term` - doesn't match anything in the CV. For `curation_gap` and
    `novel_term`, the script queries the EBI OLS4 REST API (biased toward
    whatever ontology prefix(es) that CV already uses) or, for
    institution-name CVs, the ROR affiliation-matching API, and writes every
    candidate CURIE/label/URL to the suggestions file for a human to accept
    or reject by hand-editing the CV's `Ontology Identifier`/`Ontology Url`
    columns.
  - A small set of pure accession-number fields (`grantNumber` on every
    class - see `EXCLUDED_FIELDS` in `scripts/suggest_mappings.py`) is
    skipped without any network call: their backing CV
    (`grant/grant_number.csv`) is a real, curated allowlist of ~155 valid
    grant numbers, but grant numbers have no ontology equivalent to look up
    - these are documented as intentionally unmapped, not a coverage gap.
  - **Curation pass results (2026-08-18):** acting on `suggest-mappings`'
    output plus targeted OLS4/ROR API queries -
    `modules/institution/institution_name.csv` and `institution_alias.csv`
    are now 90/91 populated with ROR identifiers (one bare abbreviation,
    `Lurie`, and one merged/renamed institution, `Indiana University -
    Purdue University Indianapolis`, were left unmapped rather than guessed
    - see each CSV's `Notes` column), and `modules/theme/theme_name.csv` is
    10/18 populated with NCIT/EDAM identifiers for its single-concept values
    (`Metastasis`, `Immunotherapy`, `Evolution`, etc.).
  - **Confirmed, not just assumed, genuinely non-ontology-mappable fields**
    (live NCIT/EDAM/OBI/DUO/ROR queries returned no defensible match, so no
    identifier was invented): `Publication`/`Tool.accessibility` (`Open
    Access`/`Restricted Access` describe a publication/software access
    *policy*, not a biomedical concept), `Tool.cost` (`Free of
    Charge`/`Commercial`), `Tool.license`'s `Not licensed` value (SPDX only
    lists real license identifiers, not an "unlicensed" placeholder),
    most of `Grant.consortium` (two exceptions found and curated: `HTAN` →
    `NCIT:C181842`, `Sage Bionetworks` → `ROR:049ncjx51`) and the remaining 8
    `Grant.theme` values (NCI-internal program/initiative names and
    multi-concept research themes with no single-term equivalent),
    `Grant.grantType` (NIH activity codes like
    `R01`/`U01` - NCIT only has category-level "R-Series"/"U-Series" terms,
    too coarse to stand in for a specific code), and `Publication`/
    `Dataset.tumorType`'s `Pan-Cancer` value (a multi-tumor-type *study
    scope* descriptor, not itself a tumor type). These are legitimately
    different from a "curation gap" - the CV term is real, but no matching
    external vocabulary term exists to point it at.
- **A coverage regression gate, not a fixed threshold.** `make validate`
  compares each non-excluded field's unmapped-value count against a
  checked-in ratchet baseline (`mappings/coverage_baseline.json`) and fails
  if any field's count *grew* - a brand-new CV with unmapped values isn't a
  failure the day it's added, but letting an already-tracked field quietly
  get worse is. Run `make update-coverage-baseline` after intentionally
  curating a CV (to record the improvement) or after knowingly accepting a
  new gap (to move the ratchet forward deliberately, not by accident).
- **DOI and PubMed IDs get a resolvable external IRI with zero CV curation
  needed.** `doi` and `pubMedId`/`publicationId` fields aren't backed by any
  MC2 controlled vocabulary - they're free identifiers - so
  `build_triples.py` templates `cckp:doiIri` → `https://doi.org/...` and
  `cckp:pubMedIdIri` → `https://pubmed.ncbi.nlm.nih.gov/...` directly from
  the value's own shape (a numeric string vs. a `10.xxxx/...` DOI),
  regardless of which field it came from - live data has at least one
  PubMed-typed field holding a DOI instead of a numeric ID, so shape-based
  detection is more correct than trusting the field name. Sentinel
  placeholder values (`Pending Annotation`, `DOI Not Available`, `Under
  Review`) are recognized and skipped rather than templated into a fake IRI.
- **`linkml generate owl` logs "Ambiguous attribute" warnings** for field
  names reused verbatim across multiple CCKP classes (e.g. `grantNumber` on
  Dataset/Publication/Tool/EducationalResource). Each is a `class`-scoped
  LinkML `attribute`, not a shared top-level `slot`, so this is expected
  and non-blocking - fixable later by promoting shared-name fields to
  top-level `slots:` with `slot_usage:` overrides per class, not needed for
  correct RDF output today.

## Interoperating with sagebrain-model

[sagebrain-model](https://github.com/Sage-Bionetworks/sagebrain-model) is a
sibling Sage Bionetworks OWL/SHACL ontology meant to integrate biological,
clinical, and translational data *across* Synapse portals. This pipeline's
own 5 CCKP portal classes have zero entity-type overlap with sagebrain
(sagebrain models participants/specimens/genes/diseases, not
Dataset/Publication/Tool/Grant records) - the real overlap lives one layer
down, in MC2's assay/subject-level modules (biospecimen, individual, model,
sequencing, imaging), which the "MC2 assay-metadata KG" section below
extracts and links into sagebrain's own classes. Both efforts adopt several
of sagebrain's conventions to stay interoperable and to fill real gaps of
their own:

- **Ontology crosswalks for federation, kept separate from harmonization.**
  `make crosswalk-ontology` (`scripts/crosswalk_ontology.py`) produces
  supplementary `mappings/crosswalks/*.sssom.tsv` files mapping this
  pipeline's NCIT/BTO-anchored CVs to the ontologies sagebrain anchors the
  same concepts in - **MONDO** for disease-shaped CVs (`tumorType.csv`,
  `diseaseType.csv`, `diseaseStatus.csv`, matching `biolink:Disease`'s own
  MONDO anchor) and **UBERON** for tissue/anatomy CVs (`tissue.csv`, matching
  the UBERON convention sagebrain's own worked example uses for
  `sagebrain:Tissue`/`Organ` instances). These are proposals for human
  review, like `mapping_suggestions.csv` - never auto-applied to a CV's own
  columns, and never used by `harmonize.py` itself.
- **SHACL structural validation**, adapted from sagebrain's own
  `ontology/shacl/sagebrain-shapes.ttl` + `tests/validate.py` pattern:
  `schema/cckp_portal.shacl.ttl` encodes instance-level invariants an OWL/
  LinkML T-Box can't (a *specific* join property's object must have a
  *specific* `rdf:type`, not just any type in the union of every class that
  ever reuses that join) and is checked via `pyshacl` in `make validate`
  (`scripts/validate_graph.py --shacl`), run without RDFS/OWL entailment for
  the same reason sagebrain's own validation does - inference would make
  `sh:class` checks vacuous by entailing the very type being checked for.
  Known-good/known-bad fixtures live at
  `test/fixtures/shacl_conforming.ttl`/`shacl_violating.ttl`.
- **A 3-tier identifier policy**, matching the one documented in
  sagebrain's `examples/README.md`:
  1. **Registry identifier** - a real external ontology/registry CURIE
     (NCIT, EDAM, ROR, DUO, a resolvable DOI/PubMed IRI) when the concept has
     an external home. The large majority of `{field}Term`/`{field}Iri`
     edges in the graph.
  2. **Locally-minted portal IRI** - `https://w3id.org/mc2-center/cckp-portal/data/{Class}/{id}`
     for the CCKP entities this pipeline itself owns (Dataset/Publication/
     Tool/Grant/EducationalResource instances).
  3. **Provisional placeholder** - for a CV value a human has actively
     checked against every relevant external vocabulary/registry and
     confirmed has no real term (see `mappings/confirmed_unmappable.tsv` and
     the "Confirmed, not just assumed" section above) -
     `build_triples.py` mints `https://w3id.org/mc2-center/cckp-portal/terms/{field}/{slug}`
     and asserts `cckp:provisional true` on it, so the concept stays an
     addressable, annotatable graph node instead of a dead-end string
     literal, while remaining unambiguously distinct from a real resolved
     mapping. Adding a new confirmed-unmappable value is a one-line addition
     to that TSV, not a code change.
- **Governance notes** (documentation only, nothing to build):
  - sagebrain's namespace is `w3id.org/synapse/sagebrain`; this pipeline's
    is `w3id.org/mc2-center/cckp-portal` - an open question for whoever owns
    Sage's w3id.org registrations, not something to silently rename.
  - **`Study Data Use Codes`** (`modules/shared/duo.csv`, feeding the MC2
    assay-metadata `Study` class) turns out to already be almost entirely
    DUO-curated by the MC2 model maintainers - 24 of 32 rows carry a real
    `DUO:00000xx` `Ontology Identifier` (e.g. `GRU` → `DUO:0000042`, `HMB` →
    `DUO:0000006`, `IST` → `DUO:0000028`), a much better fit than CCKP's own
    `Publication.accessibility` (checked and found to have no real DUO/NCIT
    match - see above). Spot-checked against sagebrain's own vendored
    version (`ontology/imports/duo.ttl` in the sagebrain-model repo, pinned
    via its `scripts/import.sh`) - the checked CURIEs are all present there,
    so the two graphs already agree on the same DUO release for this
    vocabulary; if this pipeline ever re-curates or extends this CV, keep
    resolving against that same pinned version rather than a live/
    independent OLS snapshot to avoid future drift.
  - That CV's remaining 8 rows (`DUOPlus1`-`DUOPlus7`, plus the
    `Pending Annotation` sentinel) are the MC2 model's own **local
    extension** to DUO - governance concepts (source geography, population
    type, deidentification type, data tier, license, attribution) DUO
    itself doesn't cover, with no `Ontology Identifier` and, by construction,
    none available in real DUO to give them. This is the same tier-3
    "provisional, locally-owned concept" situation as the identifier policy
    above, just at the level of an entire local vocabulary extension rather
    than individual unmapped values - worth being explicit about if this
    vocabulary is ever shared with sagebrain or another consuming graph, so
    `DUOPlus*` codes aren't mistaken for real DUO terms.

### MC2 assay-metadata KG (biospecimen/individual/model/sequencing/imaging)

A second, separate pipeline stage, extracting and linking the MC2 model's
assay/subject-level modules - the layer that actually overlaps with
sagebrain's own classes. **Access-controlled, not public like the rest of
this README**: per-file Synapse annotations can require login, unlike
CCKP's public portal tables, so every artifact below lives under the
isolated `data/mc2_assay/` tree (never `data/`), is `.gitignore`d with an
explicit access-control comment (not just "generated"), and is built via a
separate Makefile target group never folded into `make all`. `make
publish-mc2-assay` uploads the built `raw/harmonized/rdf` tree to a
private/team-restricted Synapse staging location (`scripts/publish_kg.py
--profile mc2-assay`, default target `syn76957723` - "data-ttl-builds"
under the "CCKP Knowledge Graph - Staging" project) as new file versions on
every run; before uploading anything it resolves the target's *effective*
ACL (its own, or its nearest ACL-owning ancestor's, per Synapse's
"benefactor" model - not a one-time assumption) and refuses to upload if
PUBLIC/AUTHENTICATED_USERS has any read/download grant there. `scripts/
publish_kg.py` is shared with the public portal pipeline's own `make
publish-portal-kg` (`--profile portal`, target `syn76958235` -
"portal-ttl-builds") - that profile skips the ACL check entirely, since
`data/raw|harmonized|rdf/` is meant to be public by design, not "checked
and found safe."

```
make extract-mc2-assay    # walk Dataset entities -> data/mc2_assay/raw/"File View.csv"
make harmonize-mc2-assay   # -> data/mc2_assay/harmonized/
make triples-mc2-assay     # -> data/mc2_assay/rdf/mc2_assay_kg.ttl
make link-sagebrain        # -> data/mc2_assay/rdf/sagebrain_links.ttl
make publish-mc2-assay     # upload raw/harmonized/rdf -> the restricted Synapse staging location
```

**Discovery findings, established by probing live data, not assumed:**
- A CCKP `Dataset.datasetId` is not always a real Synapse `Dataset`/
  `DatasetCollection` entity - some are plain Folders (confirmed live: 2 of
  the first 15 probed). `scripts/extract_mc2_assay_metadata.py` checks
  `entity.concreteType` before treating anything as walkable, mirroring
  `mc2-center-dcc`'s own `identify_download_type()` pattern - a Folder is
  skipped, never walked.
- A confirmed Dataset entity's membership comes from its own `datasetItems`
  property, not from listing a folder's children.
- Per `mc2-center-dcc/utils/table_to_annotations.py` (the DCC's own
  write-side pipeline), metadata is pushed down as **native Synapse
  annotations on each member File entity** - this pipeline only ever reads
  those (`syn.get_annotations`), never re-derives DCC-internal joins. The
  live annotation key set is stable across every Dataset probed and matches
  the MC2 model's own `File View` class (`modules/file/annotationProperty.csv`),
  **not** a full Biospecimen/Individual/Model record - `File View` carries
  only a `Biospecimen Key` *foreign key*, not that specimen's own detail
  fields (Type, Preservation Method, Fixative, ...). Reaching those would
  require the DCC's upstream Biospecimen/Individual/Model *tables*, which
  this pipeline deliberately does not query.
- Two slots seen in every live annotation dict (`File Tissue`, `File Tumor
  Type`) have real CV-backed enum definitions in `schema/mc2_model.linkml.yaml`
  and are registered in `modules/mapping.yaml`, but as of this writing
  aren't attached to any class in the schema - a real, pre-existing model
  gap surfaced here, not silently patched.
- `harmonize.py`/`build_triples.py` needed two small, backward-compatible
  extensions to serve this second pipeline without duplicating either
  script: a `--classes` flag (both scripts' class list was previously a
  hardcoded module constant), and recognizing `mc2_model.linkml.yaml`'s own
  enum convention (`range: X Enum` with no `mc2_enum` annotation - that
  annotation is specific to `cckp_portal.linkml.yaml`) alongside the
  existing one. `class_slug()`/`field_slug()` in `build_triples.py` turn
  spaced/underscored MC2 attribute names (`"File Level"`, `"FileView_id"`)
  into valid, lowerCamelCase IRI-safe predicate names - a no-op on the 5
  CCKP classes' already-camelCase field names, confirmed by the full test
  suite passing unchanged.
- `scripts/link_sagebrain.py` mints one `biolink:MaterialSample` stub node
  per distinct `Biospecimen Key` (not a fabricated full `Biospecimen`
  instance we don't have the fields for), harmonizes `File Tissue`/`File
  Tumor Type` directly against their CVs (since they're not attached to a
  class, `harmonize.py`'s normal pass never touches them), cross-walks the
  resolved NCIT term through the `high`-confidence rows of the MONDO/UBERON
  crosswalks above, and emits sagebrain's own `source_tissue`/`has_pathology`
  properties - never a new predicate. Files sharing a `Biospecimen Key` are
  aggregated with the same "verify consistency, report disagreement" rule
  used elsewhere in this pipeline (`biospecimen_annotation_conflicts.csv`).
- `Model` (PDX/organoid/cell line) has no dedicated sagebrain class -
  asserted `rdfs:subClassOf biolink:MaterialSample` as the closest fit,
  the same reuse-by-IRI pattern sagebrain itself uses for `Biospecimen`.
- Sequencing/Imaging/GeoMx/Visium assay classes describe *how* data was
  generated (technical/experimental parameters), a different, complementary
  ontology dimension from sagebrain's biological-entity focus - anchor
  those via OBI assay classes instead, not a sagebrain property.

## Interoperating with SageCommonDataModel

[SageCommonDataModel](https://github.com/Sage-Bionetworks/SageCommonDataModel)
(SCDM) is a sibling Sage Bionetworks LinkML schema for cross-program/cross-
portal entities - ORGANIZATION, PERSON, PROGRAM, PROJECT, STUDY (Phase 1;
PORTAL and a PERSON role-assignment relationship are tracked as follow-on
work, not yet built). Unlike sagebrain-model, SCDM has zero biological-
entity overlap with this pipeline - the real overlap is administrative:
this pipeline's own `Grant.grantInstitution`/`institutionAlias` and
`Dataset`/`Publication`/`Tool`/`Grant.consortium` fields describe exactly
the kind of organization/program identities SCDM exists to model, just as
flat CV literals rather than real cross-portal entities. Same governance
shape as the sagebrain interop above - crosswalks, generated-but-committed,
a dedicated linking script and Makefile target - applied to a different
kind of entity:

```
make sagecdm-schema   # schema/vendor/sagecdm/*.yaml (pinned) -> schema/sagecdm.ttl
make crosswalk-scdm   # institution_name.csv/consortium_name.csv -> mappings/crosswalks/*_to_scdm_*.tsv
make link-scdm        # data/harmonized/*.csv + those crosswalks -> data/rdf/scdm_links.ttl
```

- **A pinned, vendored copy of SCDM's LinkML source**
  (`schema/vendor/sagecdm/` - see its own `VENDORED.md` for the pinned
  commit and re-vendoring instructions) generates `schema/sagecdm.ttl` via
  `make sagecdm-schema`, the same "vendored, no external clone required"
  precedent `scripts/vendor/csv_to_linkml.py` already set.
- **`make crosswalk-scdm`** (`scripts/crosswalk_scdm.py`) produces two
  crosswalks, at two different trust levels:
  - `mappings/crosswalks/institution_to_scdm_organization.tsv` -
    deterministic: every `modules/institution/institution_name.csv` row
    with a well-formed ROR id gets a minted `org.<slug>` id (a ROR id
    already *is* the organization's identity, so there's no judgment call
    to review, unlike the MONDO/UBERON crosswalks above).
  - `mappings/crosswalks/consortium_to_scdm_program.tsv` - every
    `modules/consortium/consortium_name.csv` value gets a minted
    `program.<slug>` id, but ships `reviewed: false` with `description`/
    `status`/`funding_source` blank - SCDM's `Program` class requires
    `description`/`status`, neither recoverable from the CV alone, and
    `funding_source` isn't reliably attributable per-consortium from
    `modules/consortium/consortium_funding_agency.csv` (a single unlinked
    "NIH" row). A human fills these in and flips `reviewed` to `true`
    per row before `scripts/link_scdm.py` will mint it.
- **`make link-scdm`** (`scripts/link_scdm.py`) mints `sagecdm:Organization`
  (always, from the crosswalk above) and `sagecdm:Program` (**reviewed**
  rows only) instances, links `Grant.grantInstitution`/`institutionAlias`
  values to the matching Organization (`cckp:institutionRef`) and
  `Dataset`/`Publication`/`Tool`/`Grant.consortium` values to a reviewed
  Program (`cckp:consortiumRef`), and mints one provisional
  `sagecdm:Person` stub per distinct display-name string seen in
  `Grant.investigator`/`EducationalResource.contributors` (flagged
  `cckp:provisional true`, explicitly not claiming a resolved identity -
  SCDM's own Person design principle is "capture, don't resolve," and this
  pipeline has no actual Person data in scope to resolve against - see the
  v1 scope note above). `cckp:institutionRef`/`consortiumRef`/
  `investigatorRef`/`contributorRef` are this pipeline's own predicates
  (the `cckp:` namespace), the same way `cckp:doiIri`/`pubMedIdIri` are -
  neither SCDM nor this pipeline's own schema defines an inverse property
  for "this CCKP row relates to that SCDM entity." Output stays a separate
  file, `data/rdf/scdm_links.ttl`, not folded into `cckp_kg.ttl` - same
  reason `sagebrain_links.ttl` stays separate from `mc2_assay_kg.ttl`
  above. Own Makefile target, not part of `make all`, until the program
  crosswalk's first human review pass is done (today every row ships
  `reviewed: false`, so a real run mints 0 Program nodes/edges by design -
  Organization nodes/edges mint every run, no review gate needed there).
- **A fourth identifier tier.** The 3-tier identifier policy documented
  above (registry CURIE / locally-minted portal IRI / provisional
  placeholder) gains SCDM's `org.`/`program.`/`person.` ids as a distinct
  kind of registry identifier - not an external ontology term, but a
  cross-Sage-portal entity id, minted under this pipeline's own
  `data/{Class}/{id}` IRI scheme (tier 2) rather than SCDM's own namespace,
  since this pipeline doesn't own `sage-bionetworks.github.io` and isn't
  claiming to be an authoritative SCDM data source.
- **Governance notes** (documentation only, nothing to build): SCDM's
  own `organization.yaml`/`project.yaml` comments explicitly defer
  grant-level detail (grant number, mechanism, PI, dates) to "a future
  GRANT entity" not yet designed - this pipeline's own `Grant` schema
  (`grantType`, `theme`, `institutionAlias`, `consortium`, `investigator`,
  dates, `nihReporterLink`, Synapse team/project) is real-world input SCDM
  could draw on, worth raising via SCDM's own process (its contribution
  guidelines are themselves a placeholder as of this writing) rather than
  building there from this repo. A known, surfaced data-quality caveat from
  `scripts/link_scdm.py`'s own docstring: `Grant.investigator` is a
  genuinely scalar column whose raw value sometimes crams several PI names
  into one comma-separated string, and `EducationalResource.contributors`
  sometimes lists a degree suffix ("MS"/"PhD") as its own list entry
  separate from the name it modifies - neither is silently cleaned up,
  since guessing at a split would risk the opposite failure (a real name
  that itself contains a comma).

## Data Catalog (native Synapse Dataset entity annotations)

`modules/dataCatalog/` models the "Synapse Data Catalog" manifest - a
schema.org/Bioschemas-flavored dataset-cataloging vocabulary
(`measurementTechnique`, `license`, `includedInDataCatalog`,
`conditionsOfAccess`, `accessType`, ...). Unlike the 5 CCKP portal classes
above, none of this is submitted through this repo's own manifest process -
it's populated as **native Synapse annotations directly on Dataset
entities** (confirmed live: only 11 of 966 probed entities carry a
`Component: Dataset` schematic-submission marker alongside the same key
set - the other ~955 carry it natively, populated by Synapse's own Data
Catalog UI/metadata assistant). See `plans/datacatalog_kg_integration.md`
for the full harvest-and-alignment writeup this stage is built from.

**Which CCKP Dataset rows qualify**: of `syn21897968` (the CCKP Dataset
merged table), only rows with `downloadType` in (`Synapse Hosted`,
`Synapse Indexed`) are backed by a real Synapse `Dataset` entity (confirmed
via a `concreteType` sample) - for those, `downloadSynId` always equals
`datasetId`. `Externally Hosted`/`Not Available for Download` rows have no
backing entity to read annotations from and are skipped.

```
make extract-datacatalog    # syn21897968 (downloadType filter) -> data/raw/DataCatalog.csv
make harmonize-datacatalog  # -> data/harmonized/datacatalog/ (own out-dir, see below)
make triples-datacatalog    # -> data/rdf/DataCatalog.ttl
make merge-datacatalog      # fold data/rdf/DataCatalog.ttl into data/rdf/cckp_kg.ttl, IN PLACE
make combined-kg            # rebuilds triples + triples-datacatalog fresh, merges them into
                             # their OWN file, data/rdf/cckp_kg_with_datacatalog.ttl - use this
                             # instead of merge-datacatalog if you want the combined graph to
                             # survive a later `make triples` (which rebuilds cckp_kg.ttl from
                             # scratch, dropping any in-place DataCatalog merge). See "Consuming
                             # the graph" below for which file to load for what.
```

- **Own `--out-dir`, not `data/harmonized/`.** `harmonize.py` overwrites
  `unmapped_terms.csv` fresh on every run rather than appending - sharing
  the main pipeline's `data/harmonized/` would silently replace its
  coverage report with DataCatalog's own (discovered while implementing
  this: an early manual test run did exactly that, clobbering the real
  5-class report until `make harmonize` was re-run to restore it). Same
  reason `harmonize-mc2-assay` already uses its own
  `data/mc2_assay/harmonized/` - this stays in the public `data/` tree
  (unlike `mc2_assay`, this data is public) but still gets its own
  subdirectory, `data/harmonized/datacatalog/`.
- **Merges onto the *existing* `cckp:Dataset` subject, not a separate
  node.** `DataCatalog_id` always equals that row's own `datasetId`
  (confirmed on every entity carrying a real `DataCatalog_id` annotation) -
  these are two metadata facets of the same real-world dataset.
  `scripts/build_datacatalog_triples.py` adds triples directly onto
  `mint_iri("Dataset", datasetId)`, the same subject IRI
  `scripts/build_triples.py`'s own `Dataset` class pass already uses.
- **schema.org predicates where a real one exists.** This vocabulary was
  deliberately modeled on schema.org Dataset/CreativeWork terms, so
  `license`, `creator`, `contributor`, `keywords`, `citation`,
  `measurementTechnique`, `includedInDataCatalog`, `datePublished`,
  `alternateName`, `funder`, `description`, and `title` (-> `schema:name`)
  are emitted under `https://schema.org/` rather than a new
  `cckp:`-namespaced predicate - this also sidesteps any collision with
  `cckp_portal.linkml.yaml`'s own same-named-but-differently-sourced
  Dataset fields (`cckp:description`, `cckp:species`, ...), since the two
  metadata layers coexist on one subject under different namespaces.
  Everything else gets a `cckp:`-namespaced predicate; `doi` reuses
  `build_triples.py`'s own `external_iri()`/`doiIri` templating directly,
  matching how the CCKP-portal Dataset class already handles DOIs.
  CV-backed fields additionally get a resolved `cckp:{field}Term` edge,
  mirroring `build_triples.py`'s own `{field}Term` convention.
- **Real, evidence-backed CV realignment**, not new parallel CVs. Aligning
  this vocabulary's real values (harvested from 966 live entities) against
  `modules/dataCatalog/annotationProperty.csv`'s prior CV mappings surfaced
  the same "CV source doesn't match what curators actually enter" pattern
  documented for other fields elsewhere in this README - `species` used
  common names (`Human`) where real annotations use scientific binomials
  (`Homo sapiens`); `license` used bare SPDX-less codes (`CC_BY`) where real
  annotations use versioned strings (`CC-BY 4.0`); `measurementTechnique`
  used Title Case spelled-out terms where real annotations mix
  abbreviations (`RNA-seq`) with proper terms; `accessType` was mapped to
  `shared/dataTier.csv`'s Anonymous/Open/Controlled/Private set where real
  annotations use `Open Access`/`Restricted Access`, matching
  `modules/publication/publication_accessibility.csv` instead. Per
  explicit direction: **extend an existing CV first** (as a
  `Nonpreferred Terms` alias or a same-file new row - e.g.
  `shared/dataset_species.csv` already used exactly this alias mechanism
  for `Zebrafish`/`Danio rerio` before this pass touched it), **a genuinely
  new CV file only when nothing existing fits** (`downloadType`'s `Synapse
  Hosted`/`Synapse Indexed` has no repo analog anywhere). `dataType`
  formalizes `modules/shared/mc2_iconTag_map_3-4-25.csv`'s existing
  `term`->`label` taxonomy as a real registered CV (it wasn't registered
  anywhere before this pass) rather than inventing a disconnected one.
- **60 of 73 `measurementTechnique` values now resolve** against
  `shared/assay.csv` (up from 46 before this pass - some already matched,
  most needed a new `Nonpreferred Terms` alias, a few needed a brand-new
  row in that same file). The remaining 13 (`in vivo tumor growth`, `in
  silico synthesis`, `RNA array`, `shRNA-seq`, `spatial transcriptomics`,
  `in vivo PDX viability`, `histology`, `proximity extension assay`,
  `compound screen`, `traction force microscopy`, `array`, `metabolic
  screening`, `scCGI-seq`) either got a new `assay.csv` row with no
  ontology identifier (not guessed) or were left as-is (`traction force
  microscopy`/`scCGI-seq` already had a row with a populated `Ontology
  Url` but blank `Ontology Identifier` - `harmonize.py`'s `load_cv_lookup`
  skips a row entirely when its identifier is blank, a real,
  pre-existing gap unrelated to this pass and not fixed here, except for
  `UPLC-MSMS`, whose identifier was derivable from its own already-cited
  PubMed URL using this repo's existing `PMID:` convention). All 13 show
  up in `data/harmonized/datacatalog/unmapped_terms.csv`, not silently
  dropped.
- **`accessType`/`downloadType`/`dataType`/`funder` are confirmed
  non-mappable or pre-existing gaps, not new bugs.** `accessType`
  (`Open Access`) has no ontology equivalent, same as
  `Publication`/`Tool.accessibility` above. `downloadType` (`Synapse
  Hosted`/`Synapse Indexed`) is a Synapse-specific hosting concept with no
  external analog. `dataType`'s CV rows carry no `Ontology Identifier`
  (they're internal Sage `mc2_iconTag_map` category labels, not external
  ontology terms). `funder`'s blank `Ontology Identifier`
  (`consortium/consortium_funding_agency.csv`) predates this pass and
  wasn't added to while extending that file with the `NIH-NCI` value.
  All four show up in full in the unmapped-terms report by design - the
  coverage-baseline mechanism doesn't apply to this stage at all (its own
  `--out-dir` keeps it out of the main pipeline's baseline entirely, see
  above), so there's no ratchet to move forward for them.

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
    cckp_portal.shacl.ttl    - hand-authored instance-level SHACL shapes (see
                                "Interoperating with sagebrain-model")
    vendor/sagecdm/*.yaml    - vendored, pinned SageCommonDataModel LinkML
                                source + VENDORED.md (see "Interoperating
                                with SageCommonDataModel")
    sagecdm.ttl               - generated via `make sagecdm-schema`
  mappings/sssom/*.sssom.tsv - harmonization crosswalks (generated, committed)
  mappings/crosswalks/*.sssom.tsv - supplementary MONDO/UBERON federation
                                crosswalks (generated, committed, human-review
                                only - never consumed by harmonize.py)
  mappings/crosswalks/institution_to_scdm_organization.tsv - deterministic,
                                no review needed (see "Interoperating with
                                SageCommonDataModel")
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
                                unmapped_terms.csv (see "Data Catalog")
  data/mc2_assay/              - gitignored (access-controlled - see
                                "MC2 assay-metadata KG"): raw/, harmonized/, rdf/
  test/
    fixtures/*.csv, shacl_*.ttl - small hand-made sample rows/graphs
    conftest.py, test_*.py     - pytest suite (no live Synapse access needed,
                                except test_mc2_assay_file_view.py's fixture-only
                                tests, which also need none - live calls are
                                exercised only by running the scripts directly)
```
