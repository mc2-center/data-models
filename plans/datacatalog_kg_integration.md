# Pull Synapse Dataset-entity annotations into the CCKP knowledge graph

## Context

`modules/dataCatalog/` models the "Synapse Data Catalog" manifest — a
schema.org/Bioschemas-flavored dataset-cataloging vocabulary (`measurementTechnique`,
`license`, `includedInDataCatalog`, `conditionsOfAccess`, `accessType`, ...) —
but nothing in this repo or `kg-pipeline` currently reads it from anywhere.
The user's request: these fields are populated today as **native Synapse
annotations directly on Dataset entities** (e.g.
`https://www.synapse.org/Synapse:syn77160335.draft/datasets/`), not through
this repo's own manifest-submission process, and should be pulled into the
KG. Scope: only CCKP Dataset rows that are backed by a real Synapse Dataset
entity — "the datasets ... listed in the CCKP Datasets merged table" that
refer to "a native Synapse Dataset entity (which can contain Synapse-stored
or indexed files)."

### Identifying which of the 1,141 CCKP Dataset rows qualify

Queried `syn21897968` (kg-pipeline's existing "Dataset" merged table, see
`data_sources.yaml`) live:

```
downloadType                    n
Synapse Indexed                953
Externally Hosted              140
Not Available for Download      24
Synapse Hosted                  24
```

For every `Synapse Hosted`/`Synapse Indexed` row (977 total), `downloadSynId`
is populated and **always equals `datasetId`**; for `Externally Hosted`/`Not
Available for Download` rows it's blank. Verified against a random sample of
15 `datasetId`s from the 977: all 15 resolve to a real
`org.sagebionetworks.repo.model.table.Dataset` entity via `syn.get`. This is
exactly the discriminator the user described — **`downloadType` in
(`Synapse Hosted`, `Synapse Indexed`)** identifies the rows to pull.

### What's actually on those entities — harvested and analyzed 966 of the 977 live

Pulled `syn.get_annotations()` for all 977 qualifying `datasetId`s (966 unique
entities — a `datasetId` can appear more than once in the merged table, e.g.
under different grants/themes) and tallied every key's presence, blank/non-blank
rate, cardinality, and distinct values. Full methodology is one Python script
against `synapseclient`; this becomes the seed of the extraction script in
Approach step 4. Key findings, organized by what they mean for the model:

**1. Exact matches already — no change needed:** `description`, `keywords`
(list), `title`, `doi`, `citation`, `specimenCount`, `series`,
`visualizeDataOn`, `includedInDataCatalog`, `conditionsOfAccess`,
`alternateName`, `croissant_s3_file_object`, `countryOfOrigin` (only 1
non-blank value across all 966 — `'US'` — matches the existing ISO
alpha-2 CV, `shared/sourceGeography.csv`, exactly), `DataCatalog_id` (present
non-blank on 11/966 — always equal to that entity's own `datasetId`, same
"same-ID" pattern as `org.<slug>`/`program.<slug>` — confirms the model's
existing `^syn\d{7,8}$` pattern is correct).

**2. Renames needed (live annotation key ≠ model attribute name):**

| Model attribute (current) | Live annotation key | Action |
|---|---|---|
| `contributors` | `contributor` | rename to match live (singular) |
| `individuals` | `individualCount` | rename to match live |
| `dataUseModifiersCatalog` | `dataUseModifiers` | rename to match live (drop `Catalog` suffix) |

**3. Cardinality fix needed:** `creator` is declared `string` (scalar) in
the model but is genuinely multivalued in practice — 807/953 populated rows
list more than one name (e.g. 18 co-authors on one dataset). Model should
declare it `string_list`.

**4. Controlled-vocabulary mismatches — model's CV source doesn't match
what curators actually enter (the user's "prefer the formatting from the
annotations already in use"):**

| Attribute | Model's current CV source | Real values (966 entities) |
|---|---|---|
| `species` | `shared/dataset_species.csv` (common names: "Human", "Mouse") | **19 distinct**, scientific binomial: `Homo sapiens` (635), `Mus musculus` (358), `Zebrafish` (9, the one common-name outlier), `Saccharomyces cerevisiae` (6), `Drosophila melanogaster` (5), `Rattus norvegicus` (3), ... |
| `license` | `shared/studyLicense.csv` (`CC0, CC_BY, CC_BY_NC, ...`, no version) | **2 distinct**: `CC-BY 4.0` (939), `CC BY-NC 3.0` (11) |
| `measurementTechnique` | `shared/assay.csv` (Title Case, spelled out: "RNA Sequencing") | **73 distinct**, mixed lowercase/abbreviated + some Title Case: `RNA-seq` (707), `single-cell RNA-seq` (239), `ChIP-seq` (124), `ATAC-seq` (118), `in vivo tumor growth` (96), `flow cytometry` (85), `quantitative PCR` (71), ... down to singletons |
| `accessType` | `shared/dataTier.csv` (`Anonymous, Open, Controlled, Private`) | **2 distinct**: `Open Access` (942), `Open` (1, likely a stray/legacy value) — matches `modules/publication/publication_accessibility.csv`'s `Open Access`/`Restricted Access` pair, not the dataTier CV |
| `funder` | `consortium/consortium_funding_agency.csv` (`NIH` only) | **2 distinct**: `NIH-NCI` (936), `NIH` (5) — same CV, just missing a value |
| `dataUseModifiers` (renamed above) | none currently | Only 1 non-blank value across 966: `Pending Annotation` — the exact sentinel `shared/duo.csv` already uses for Study/File Data Use Codes |
| `manifestation` (new attribute) | none currently | 3 non-blank values total (`Breast Cancer`, `Meningioma`, `Melanoma`) — **aligns with `tumorType`** (per user), confirmed: all 3 already exist in `shared/tumorType.csv`, either as the primary `Attribute` (`Meningioma`) or an existing `Nonpreferred Terms` alias (`Breast Cancer` under `Breast Carcinoma`, `Melanoma` under `Cutaneous Melanoma`). Map directly to that CV — zero new rows needed. |

**5. Genuinely new attributes to add** (present on ~942-953/966 entities as
a key, i.e. part of the stable schema, regardless of how often populated):

| New attribute | Example value(s) | Notes |
|---|---|---|
| `studyId` | `syn7315805` (96 distinct across the corpus) | A real Synapse ID — **confirmed (per user) these are real Synapse Projects associated with the dataset's `grantNumber`**, not this repo's own `Study_id`/`Study Key` concept. A cross-reference opportunity (see Out of scope), but the join target is "Synapse Project for this grant," not `modules/study`. |
| `dataType` | `gene expression` (757), `chromatin activity` (209), `genomic variants` (42), `immunoassay` (3), `network` (2), `nucleic acid sequence record` (1), `image` (1) | Small, closed, 7-value set. **`modules/shared/mc2_iconTag_map_3-4-25.csv` already models this exact concept** — a `term`→`label` mapping (`label` values: `bioChemicalPhysical`, `clinical`, `computationalTool`, `dataReuse`, `epigenomeProfiling`, `expressionProfiling`, `genomeProfiling`, `imaging`, `inSilicoModel`, `modelSystem`, `proteomics`, `spatialProfiling`) that isn't registered in `modules/mapping.yaml` or used by any attribute today. `gene expression`→`expressionProfiling`, `chromatin activity`→`epigenomeProfiling`, `genomic variants`→`genomeProfiling`, `image`→`imaging` all map cleanly; `immunoassay`/`network`/`nucleic acid sequence record` need a closer look (extend the file's own label set if none fits — see Approach step 2). `cckp_portal.linkml.yaml`'s own `Dataset.dataType` field has **no CV at all** today (confirmed) — formalizing this could seed one for that too. |
| `grantNumber` | `CA209975` (935/966 populated, scalar) | Same concept CCKP's curated `DatasetView` already carries independently |
| `downloadType` | `Synapse Hosted` (935), `Synapse Indexed` (7) | New small CV — this is a *different* field than the merged table's own `downloadType` column (this one lives as an annotation on the entity itself) |
| `externalRepositoryUri` | `geo:GSE235874`, `sra:SRP279383`, `bioproject:PRJNA660307` | Free CURIE-shaped identifiers, not a picklist — 949 distinct values across 942 non-blank, 7 rows multivalued |
| `authors` | list of names, e.g. `['Kloetgen Andreas', 'Thandapani Palaniraja', ...]` | 83/966 populated (8.6%) — real, not noise, but rarer than `creator`; possible conceptual overlap with `creator`/`citation`, flagged for awareness not resolved |
| `ageGroup` | `Adult` (only 3 non-blank total) | Too sparse to seed a confident CV yet — model as free string for now |
| `diseaseFocus` | *(zero non-blank across all 966)* | Real, defined key, never populated in practice — add as free string, no CV to seed |

**6. Existing model attributes never observed in any of the 966 real
annotation sets:** `community`, `link`, `datePublished`. Recommend **keeping**
them (harmless, optional, and this repo doesn't delete attributes just for
being currently unpopulated) but flagging them here as apparently unused in
current practice.

**7. Administrative/technical keys seen on the entities.** `entityType`
(20/966, always `dataset`, redundant with `concreteType`) and `newKey`
(11/966, always blank — a leftover placeholder from someone's manifest,
pure noise) are not descriptive dataset metadata and are **not** proposed
as `DataCatalog` content attributes. `portal` (20/966, always `CCKP` today)
**is** kept — per the user, worth modeling — added as a new scalar
attribute (see Approach step 1); it's a real provenance signal (which
portal curated this record) that becomes meaningful the moment this
vocabulary or pipeline is ever shared across more than one Sage portal, the
same reasoning `kg-pipeline/README.md` already applies to keeping
`cckp:provisional`-style bookkeeping predicates. `Component`
(11/966, always `Dataset`) is a real, useful signal though: it's schematic's
own marker for which manifest template an entity was annotated under, and
it co-occurs exactly with the 11 rows that also carry `DataCatalog_id` +
`croissant_s3_file_object` — i.e. the only 11 entities (of 966) that have
gone through an actual schematic `DataCatalog` submission. The other ~955
carry the same `DataCatalog`-shaped keys natively (populated by Synapse's
own Data Catalog UI/metadata assistant, not this repo's manifest process) —
**the extraction process must read raw entity annotations directly and not
assume a `DataCatalog_id`/`Component` tag is present.**

**8. A handful of entities (≤11) also carry a completely different,
camelCase-concatenated key set** (`DatasetDoi`, `DatasetUrl`, `DatasetName`,
`GrantViewKey`, `duoCodes`, `DatasetAssay`, ...) — this repo's own `Dataset`
schematic-component annotations, bleeding onto a tiny number of the same
entities. The extraction script must read only the known `DataCatalog` key
set and ignore these, not get confused by the overlap.

## Approach

**Governing principle for every CV decision below** (per user direction):
1st preference — map new/misaligned values into an existing repo CV as-is
or via `Nonpreferred Terms` aliases; 2nd preference — extend an existing
CV with new rows when no alias relationship fits but the CV is still the
right home; 3rd preference — add a brand-new CV file only when nothing
existing is a reasonable fit. Re-evaluated every CV decision in the
original plan against this order (several changed as a result — see steps
2-3 below, which now touch fewer new files and more existing ones than the
first draft did).

**1. Update `modules/dataCatalog/annotationProperty.csv`.**
- Rename `contributors`→`contributor`, `individuals`→`individualCount`,
  `dataUseModifiersCatalog`→`dataUseModifiers` (updating the `DataCatalog`
  class's own `DependsOn` list to match).
- Change `creator`'s `columnType` from `string` to `string_list`.
- Update `subject`'s description — it currently says "use the Library of
  Congress Subject Headings (LCSH) scheme," but real values are model-system/
  specimen descriptors (`C57BL/6`, `NOD SCID`, `CUTLL1 / T-ALL`), never LCSH
  terms. Reword to match actual usage rather than force a scheme nothing
  follows.
- Add new attributes: `studyId` (scalar, `^syn\d{7,8}$` pattern — a Synapse
  Project ID associated with the grant, per the user's confirmation, not
  this repo's `Study_id`), `dataType` (`string_list`, CV per step 2),
  `grantNumber` (scalar, `^CA\d{6}$` pattern matching `Grant Number`'s own),
  `downloadType` (scalar, new CV), `externalRepositoryUri` (`string_list`,
  free — no CV), `authors` (`string_list`, no CV, description notes
  possible overlap with `creator`), `ageGroup` (scalar, free string — too
  sparse for a CV), `diseaseFocus` (scalar, free string — never populated
  yet), `manifestation` (scalar, CV per step 2 — `shared/tumorType.csv`),
  `portal` (scalar, free string — real provenance signal, kept per user).
  All added to the `DataCatalog` class's `DependsOn` list.

**2. Extend existing CVs first; only two genuinely new CV files are needed.**

- **`species` → extend `shared/dataset_species.csv` in place (no re-point,
  no new file).** Confirmed this file already has exactly the mechanism
  needed: `Zebrafish`'s row already carries `Danio rerio` as a
  `Nonpreferred Terms` alias (`harmonize.py`'s `load_cv_lookup` matches
  aliases to the same `Ontology Identifier` as the primary term), and
  `Human`/`Mouse` rows already exist too. Add each observed scientific name
  as a `Nonpreferred Terms` alias of its existing common-name row (`Homo
  sapiens`→`Human`, `Mus musculus`→`Mouse`, `Rattus norvegicus`→`Rat`,
  `Drosophila melanogaster`→`Fruit Fly`, `Saccharomyces cerevisiae`→`Yeast`,
  `Caenorhabditis elegans`→`Worm`, `Escherichia coli str. K-12 substr.
  MG1655`/`Escherichia coli BW25113`→`Escherichia coli`,
  `Monodelphis domestica`→`Opossum`, `Dasypus novemcinctus`→`Armadillo`,
  `Macaca nemestrina`/`Rhesus macaque`→`Rhesus monkey`, `Sus scrofa`→`Boar`,
  `Gallus gallus`→`Chicken`). Only 1-2 organisms have no existing row at all
  (`Candida albicans`; possibly `Schizosaccharomyces pombe`, a judgment call
  on whether it's close enough to alias under `Yeast`) — add those as new
  rows, not a new file.
- **`license` → extend `shared/studyLicense.csv` in place.** Add
  `CC-BY 4.0` as a `Nonpreferred Terms` alias of the existing `CC_BY` row
  and `CC BY-NC 3.0` under `CC_BY_NC` — and, while there, populate real
  SPDX `Ontology Identifier`s (`CC-BY-4.0`, `CC-BY-NC-3.0`) on those rows,
  since none of this CV's rows are ontology-grounded yet.
- **`measurementTechnique` → map into `shared/assay.csv` first, extend it
  second; no new file** (per the user's explicit steer). Run a fuzzy/exact
  match of the 73 observed values against `assay.csv`'s existing
  `Attribute`+`Nonpreferred Terms` (some already align — `ATAC-Seq` is
  already a term there, close to observed `ATAC-seq`); add each confirmed
  match as a `Nonpreferred Terms` alias on the matching row; for the
  minority with no reasonable existing match, add new rows to `assay.csv`
  itself. This is real curation work across 73 values — the matching pass
  itself (not the CV architecture) is what's deferred to a follow-up (see
  Out of scope), likely via a small script modeled on
  `kg-pipeline/scripts/crosswalk_ontology.py`'s exact-then-fuzzy pattern.
- **`dataType` → formalize `shared/mc2_iconTag_map_3-4-25.csv`'s existing
  `label` taxonomy as a real CV**, since nothing registers it today. Map
  the 7 observed values onto existing labels where they fit
  (`gene expression`→`expressionProfiling`, `chromatin activity`→
  `epigenomeProfiling`, `genomic variants`→`genomeProfiling`, `image`→
  `imaging`); for `immunoassay`/`network`/`nucleic acid sequence record`,
  decide during implementation whether an existing label
  (`bioChemicalPhysical` is a plausible fit for `immunoassay`) covers it or
  a new label needs to be added to that file — either way, the CV this
  repo registers should be sourced from (and keep in sync with) the
  existing `label` set rather than invent a parallel, disconnected one.
- **`manifestation` → map into `shared/tumorType.csv` directly.** No new
  rows needed at all (see Context finding 4/5 above — all 3 observed
  values already resolve there).
- **`accessType`**: reuse `modules/publication/publication_accessibility.csv`
  directly (values match exactly) — unchanged from the original plan, and
  already the right "map to an existing CV" choice.
- **`downloadType`**: the one attribute here with no existing analog
  anywhere in the repo (`Synapse Hosted`/`Synapse Indexed` is a
  Synapse-specific hosting concept) — new file,
  `modules/dataCatalog/dataCatalog_download_type.csv`, 2 rows, no ontology
  equivalent (same "confirmed non-mappable" treatment as
  `Tool.cost`/`accessibility` in `kg-pipeline/README.md`).

**3. Update `modules/mapping.yaml`'s `dataCatalog:` block.** Because
`species`/`license`/`measurementTechnique` now *extend* their existing CV
files rather than move to new ones, their `mapping.yaml` entries are
**unchanged** (`shared/dataset_species.csv`, `shared/studyLicense.csv`,
`shared/assay.csv`). Actual changes:
- `accessType` → `publication/publication_accessibility.csv` (was `shared/dataTier.csv`)
- new: `downloadType` → `dataCatalog/dataCatalog_download_type.csv`
- new: `dataType` → the newly-registered `shared/mc2_iconTag_map_3-4-25.csv`-derived CV (exact path/shape decided in step 2)
- new: `manifestation` → `shared/tumorType.csv`
- new: `dataUseModifiers` → `shared/duo.csv` (reuse, matching Study/File)
- `countryOfOrigin`, `funder` mappings unchanged (already correct — just
  add the missing `NIH-NCI` row to the existing
  `modules/consortium/consortium_funding_agency.csv`, no re-pointing).

**4. New kg-pipeline extraction script, `scripts/extract_datacatalog.py`:**
query `syn21897968` for `datasetId` where `downloadType IN ('Synapse
Hosted','Synapse Indexed')`, deduplicate `datasetId`, call
`syn.get_annotations()` per entity, and write `data/raw/DataCatalog.csv`
with exactly the `DataCatalog` class's attribute columns (ignoring the
noise/administrative keys and the occasional bleed-through `Dataset*`-style
keys from finding 8) — same shape `extract_cckp_tables.py` already produces
for the 5 CCKP portal tables.

**5. Reuse the existing harmonize/triples machinery, not new code**, the
same way the MC2 assay-metadata pipeline already reuses
`harmonize.py`/`build_triples.py` generically via `--classes`: once
`modules/dataCatalog/annotationProperty.csv` is collated into
`mc2.model.csv` and regenerated into `schema/mc2_model.linkml.yaml`, the
`DataCatalog` class already has real attributes/enums attached, so
`harmonize.py --schema schema/mc2_model.linkml.yaml --classes "DataCatalog"`
resolves `species`/`license`/`measurementTechnique`/`accessType`/`downloadType`/
`dataType`/`dataUseModifiers` against their CVs exactly like any other class.

**6. Merge `DataCatalog` triples onto the *existing* `cckp:Dataset` subject,
not a separate node.** `DataCatalog_id == datasetId` always (confirmed on
all 11 populated cases) — these are two metadata facets of the same
real-world dataset, not two joined entities. A small dedicated script
(`scripts/build_datacatalog_triples.py`, not the generic
`build_triples.py` class loop) reads the harmonized `DataCatalog` CSV and
adds triples directly onto `mint_iri("Dataset", datasetId)` — the same
subject IRI `build_triples.py` already mints for that row in
`data/rdf/Dataset.ttl`. **Predicate choice**: this vocabulary was
deliberately modeled on schema.org/Bioschemas Dataset terms (`license`,
`creator`, `contributor`, `keywords`, `citation`, `measurementTechnique`,
`includedInDataCatalog`, `datePublished`, `alternateName`, `funder` are all
real schema.org `Dataset` properties) — use the real `https://schema.org/`
predicate URI for every field that has one, rather than inventing a new
`cckp:`-namespaced predicate for a concept that already has a standard
equivalent. This also sidesteps any predicate-name collision with
`cckp_portal.linkml.yaml`'s own same-named-but-differently-sourced Dataset
fields (`cckp:description`, `cckp:species`, ...) — the two metadata layers
coexist on one subject under two different, both-correct namespaces.
Fields with no real schema.org equivalent (`accessType`, `conditionsOfAccess`,
`dataUseModifiers`, `individualCount`, `specimenCount`, `downloadType`,
`studyId`, `dataType`, `ageGroup`, `diseaseFocus`, `manifestation`,
`externalRepositoryUri`, `series`, `croissant_s3_file_object`) get a
`cckp:`-namespaced predicate, same as everything else this pipeline mints.
Exact prefix/URI choices per field (confirming which are true schema.org
core vs. a Bioschemas/DATS extension) are implementation detail to pin down
while building this, not re-litigated here.

**7. New Makefile target `extract-datacatalog`** (own target, not folded
into `make all` initially — it's a new, unverified pipeline stage, matching
how new stages in this pipeline start standalone until proven out), plus
wiring `harmonize`/`triples` to also process `DataCatalog` (either as a
`--classes` addition to the main pipeline run, or its own
`harmonize-datacatalog`/`triples-datacatalog` pair mirroring the MC2
assay-metadata pattern — decide during implementation based on whether
mixing `DataCatalog` into the main 5-class loop's coverage-baseline
reporting makes sense or muddies it).

**8. README + coverage.** Document the new stage in `kg-pipeline/README.md`
(new section, matching the existing "Interoperating with..." style — this
isn't interop with an external model, more a "Data Catalog" stage
description). `measurementTechnique`'s 73 uncurated values will show up in
`unmapped_terms.csv` until curated — expected, tracked by the existing
coverage-baseline mechanism, not a new bug.

## Out of scope for this pass (flagged as follow-ups, not acted on)

- **The `measurementTechnique`→`assay.csv` matching pass itself** — mapping
  all 73 observed values (exact match, alias, or genuinely new row) is real
  per-value curation work; the *architecture* (extend `assay.csv`, don't
  create a parallel CV) is decided here, but doing all 73 by hand (or
  building the small matching script this needs) is its own pass, not a
  blocker for landing the rest of this integration.
- **Deciding `immunoassay`/`network`/`nucleic acid sequence record`'s exact
  `dataType` label** — whether an existing `mc2_iconTag_map` label fits or
  a new one is needed for each; a small, bounded decision left for
  implementation rather than guessed here.
- **Validating/joining `studyId`** against the real Synapse Project it
  names (confirmed per user to be grant-associated, not this repo's own
  `Study_id`) — flagged as a cross-reference opportunity, not designed here.
- **Removing `community`/`link`/`datePublished`** since they're unused in
  practice — kept as-is; removal is a separate, destructive decision the
  user should make explicitly, not a side effect of this alignment pass.
- **Deciding the exact `DataCatalog`/`Dataset` extraction+triples split**
  between "one more `--classes` addition to the main loop" vs. "its own
  parallel stage" — noted as an implementation-time decision in step 7.

## Verification

- Re-run the `downloadType IN ('Synapse Hosted','Synapse Indexed')` query
  and confirm the extraction script's row count matches (977, or whatever
  the live count is at implementation time — it will have grown).
- Spot-check `scripts/build_datacatalog_triples.py`'s output: for the 11
  entities carrying a real `DataCatalog_id`, confirm the merged
  `cckp:Dataset` subject carries both the CCKP-portal-sourced triples
  (`cckp:datasetName`, ...) and the new schema.org/`cckp:`-namespaced
  DataCatalog triples on the *same* IRI, not two separate nodes.
- `make harmonize`'s new `unmapped_terms.csv`/`malformed_cv_terms.csv`
  entries reviewed — expect `measurementTechnique` values not yet matched
  into `assay.csv` to dominate, nothing else.
- New fixture-based pytest coverage for `extract_datacatalog.py` and
  `build_datacatalog_triples.py`, following this pipeline's existing
  no-live-Synapse-needed test convention.
- Full `make test` suite still passes.

## Process

- Store this plan at `plans/datacatalog_kg_integration.md` for review before
  implementing.
- After implementing (in this conversation or a future one), append an
  Implementation Report below this line, documenting what was actually
  built, any deviations from the approach above, and verification results.

## Implementation Report

Implemented as six commits on `database-model-kg`. Followed the approach as
planned, with the CV strategy corrected mid-implementation per user
feedback (see the user's `[REVIEW]` comments on the plan, addressed before
implementation began) to prefer extending existing CVs over creating new
ones - already reflected in the Approach/Context sections above, so not
re-described here. Notes on what actually happened during implementation:

### Steps 1-3 (attributes, CVs, mapping.yaml)

Implemented exactly as planned. Two things worth recording that weren't
fully known at plan time:

- **Species needed 3 new rows, not "1-2".** Checking every organism against
  `shared/dataset_species.csv` turned up two more genuinely-uncovered
  species than expected: `Macaca nemestrina` (pig-tailed macaque - distinct
  from the already-present `Rhesus monkey`/`Macaca mulatta`) and
  `Schizosaccharomyces pombe` (fission yeast - judged distinct enough from
  the already-present `Yeast`/`Saccharomyces cerevisiae` to warrant its own
  row rather than an alias). `Candida albicans` was the only one confirmed
  in the original plan text.
- **`measurementTechnique` resolved 60/73, not just "some."** Systematic
  matching (a small script indexing every `assay.csv` `Attribute`+
  `Nonpreferred Terms`, then checking all 73 real values against it) found
  46 already matched by name, 13 more resolvable as a new alias on an
  existing row, and 11 needing a genuinely new row. Two of the "matched by
  name" rows (`Traction Force Microscopy`, `scCGI-seq`) turned out not to
  actually resolve in `harmonize.py` despite matching by name - both have a
  populated `Ontology Url` but a **blank** `Ontology Identifier`, and
  `load_cv_lookup` skips a row entirely (not even flagged malformed) when
  its identifier is blank. Fixed this for `UPLC-MSMS` (which had the same
  bug) since its `Ontology Url` was a PubMed link and this file already has
  an established `PMID:` convention for exactly that case (row 0,
  `10-cell RNA Sequencing`) - didn't invent a fix for
  `Traction Force Microscopy` (Wikipedia URL, no established CURIE
  convention in this file to reuse) or `scCGI-seq` (no URL at all), leaving
  both as discovered-but-not-fixed pre-existing gaps.

### Steps 4-6 (extraction, triples, merge)

Implemented as planned, verified against real live data at every stage
(not just fixtures) - see Verification below for numbers. One real,
practical problem found and fixed during this pass, not anticipated in the
plan: `harmonize.py` overwrites `data/harmonized/unmapped_terms.csv` fresh
on every run (no append). An early manual test run
(`--out-dir data/harmonized`, matching the main pipeline's own directory)
silently replaced the real 5-class pipeline's coverage report with
DataCatalog's own before the Makefile target existed. Caught by running
`make validate` afterward and seeing the *wrong* fields flagged as
regressions; fixed by giving `harmonize-datacatalog` and
`triples-datacatalog` their own `data/harmonized/datacatalog/` directory
(mirroring `harmonize-mc2-assay`'s own separate directory, for the same
reason) and re-running the main `make harmonize` to restore the real
report before re-validating. Documented prominently in both the Makefile
comment and the new README section so this doesn't get rediscovered later.

### Step 7 (Makefile) / Step 8 (README)

Implemented as planned. Resolved the one explicitly-deferred decision
("fold into the main loop, or its own stage?"): gave DataCatalog fully
separate `extract-datacatalog`/`harmonize-datacatalog`/`triples-datacatalog`
targets, none part of `make all`, plus a new `merge-datacatalog` target
(not in the original plan text, added during implementation) that folds
`data/rdf/DataCatalog.ttl` into `data/rdf/cckp_kg.ttl` as its own explicit,
idempotent step - needed because `build_triples.py`'s own `--merge-with`
mechanism assumes its inputs already exist, which doesn't fit a
new-and-separate stage that a user opts into later.

### Verification (real, not just fixture-based)

- Extracted all 966 native Synapse Dataset entities live via
  `make extract-datacatalog` (`data/raw/DataCatalog.csv`).
- `make harmonize-datacatalog`: `license` 2/2, `species` 19/19,
  `manifestation` 3/3, `measurementTechnique` 60/73 resolved.
  `accessType`/`downloadType`/`dataType`/`funder` fully unresolved by
  design (confirmed non-mappable, internal-only labels, or a pre-existing
  gap - see README). 4,121 unresolved values logged to
  `data/harmonized/datacatalog/unmapped_terms.csv`, none silently dropped.
- `make triples-datacatalog`: 29,421 triples (`schema.org`: 13,294; `cckp:`:
  11,229; resolved `*Term` edges: 4,063; `doiIri`: 842).
- `make merge-datacatalog`: `data/rdf/cckp_kg.ttl` 431,744 -> 461,116
  triples. Confirmed the new triples land on the *same* subject IRI as the
  existing `cckp:Dataset` triples (spot-checked `syn61794747`: both
  `cckp:datasetName` from the CCKP-portal pass and `schema:name`/
  `cckp:speciesTerm`/etc. from this pass on one node, not two).
- `make validate` on the full merged graph: coverage gate passes with
  **no regression** on the main 5-class baseline (confirms the separate
  `--out-dir` fix actually worked); SHACL conforms against all 461,116
  triples.
- `python3 -m pytest test/`: **74/74 passed** (69 previous + 5 new in
  `test/test_datacatalog.py`), including an end-to-end
  harmonize-then-build-triples fixture test with real CV resolution
  assertions (species/manifestation NCIT identifiers, doiIri templating,
  confirmed absence of a `*Term` edge for the non-mappable `accessType`).
