# Align the CCKP knowledge graph with the Sage Common Data Model (SCDM)

## Context

Reviewed `/Users/obanks/SageCommonDataModel` (main branch) against `kg-pipeline/`
(this repo's RDF knowledge-graph pipeline for the Cancer Complexity Knowledge
Portal). SCDM is a LinkML schema, Phase 1 complete for five entities —
ORGANIZATION, PERSON, PROGRAM, PROJECT, STUDY (`src/*.yaml`) — with PORTAL and a
PERSON-role-assignment relationship still open (SCDM-2, tracked on the SCDM
board). It ships source YAML only; no generated OWL/TTL is committed
(`docs/.gitkeep` is a placeholder) and its own contribution process is itself a
placeholder (SCDM-3).

kg-pipeline already has a precedent for exactly this kind of cross-repo
alignment: its "Interoperating with sagebrain-model" section
(`kg-pipeline/README.md`) documents ontology crosswalks
(`mappings/crosswalks/*.sssom.tsv`, human-review only), a 3-tier identifier
policy, SHACL structural validation, and a separate `scripts/link_sagebrain.py`
+ `make link-sagebrain` stage. This plan reuses that same shape for SCDM
instead of inventing a new one.

Concrete correspondences found between kg-pipeline's live CCKP data and SCDM's
entities:

1. **Institution → ORGANIZATION.** `modules/institution/institution_name.csv`
   is already 90/91 populated with real ROR CURIEs/URLs (a prior curation
   pass, see `kg-pipeline/README.md`'s "Curation pass results" note). SCDM's
   `Organization` class (`src/organization.yaml`) is explicitly "a thin wrapper
   around ROR" with the identical shape (`ror_id`, cached `name`/`acronym`).
   `cckp_portal.linkml.yaml`'s `Grant.grantInstitution`/`institutionAlias`
   fields are CV-backed against that same CSV. This is close to a 1:1,
   deterministic mint — not a judgment call the way ontology crosswalks are.

2. **Consortium → PROGRAM.** `modules/consortium/consortium_name.csv` holds 11
   values (CCBIR, CSBC, HTAN, ICBP, MetNet, NCI, NCI Clinical and Translational
   Exploratory/Developmental Studies, PDMC, PS-ON, Sage Bionetworks, TEC),
   reused verbatim across the `Grant`, `Project`, `Person`, and (per
   `modules/mapping.yaml`) `Dataset`/`Publication` modules as a `Consortium
   Name` CV field. `kg-pipeline/README.md`'s own "Confirmed, not just assumed,
   genuinely non-ontology-mappable fields" section already documents that
   "most of `Grant.consortium`" has **no real NCIT equivalent** — because
   these are program identities, not biomedical concepts. SCDM's `Program`
   class (`src/program.yaml`) is exactly the entity type built for this: a
   named, funded, status-tracked scientific initiative. This turns an
   accepted, permanent "unmappable" gap into a real, addressable, richly-typed
   graph node — the single highest-value item in this plan.

3. **Investigator → PERSON.** `Grant.investigator`, `Project Investigator`, and
   `Study Investigator` are all free-text, unresolved personal-name fields
   ("no controlled vocabulary — personal names", per `cckp_portal.linkml.yaml`
   comments). `kg-pipeline/README.md`'s own v1 scope note says "Person/
   PersonView is out of scope" and flags it as "a documented follow-up, not an
   oversight." SCDM's `Person` class (`src/person.yaml`) was designed for
   exactly this problem — "Sage has no stable, unique identifier for a person
   that holds across every source system... capture, don't resolve" — and its
   `PersonIdentifier`/`display_name` shape needs no new design work, just
   reuse.

4. **MC2 assay-metadata `Study` ↔ SCDM STUDY.** `schema/mc2_model.linkml.yaml`
   already has a `Study` class (`Study_id`, `GrantView Key`, `ProjectView Key`,
   `Study Investigator`, `PersonView Key`, ...) that structurally mirrors
   SCDM's STUDY (parent program, parent project, primary contact) without
   using real entity references — flat FK-style columns instead. Not acted on
   in this pass (see Out of scope), but recorded as the same shape recurring a
   third time.

5. **A future SCDM GRANT entity, informed by a real schema.** SCDM's own
   `organization.yaml` and `project.yaml` comments explicitly defer
   grant-level detail (grant number, mechanism, PI, dates) to "a future GRANT
   entity" not yet designed. `cckp_portal.linkml.yaml`'s `Grant` class is a
   live, fielded schema for exactly that (`grantType`, `theme`,
   `institutionAlias`, `consortium`, `investigator`, `grantStartDate`,
   `durationOfFunding`, `embargoEndDate`, `nihReporterLink`,
   `grantSynapseTeam`/`grantSynapseProject`). Worth surfacing to SCDM's
   maintainers as real-world input — a coordination action, not a code change
   this repo can make unilaterally.

## Approach

**1. Vendor a pinned copy of SCDM's LinkML source.**
Add `schema/vendor/sagecdm/` holding `src/*.yaml` from SageCommonDataModel at
a pinned commit (mirrors the existing "vendored, no external install
required" precedent set by `scripts/vendor/csv_to_linkml.py`). Record the
pinned commit hash in a header comment in the vendored files and in this
plan's Implementation Report — re-vendor deliberately on a schedule, not
automatically track `main`, matching the DUO-pinned-version governance
discipline already documented for sagebrain. Add a `make sagecdm-schema`
target: `linkml generate owl -f ttl schema/vendor/sagecdm/sage_cdm.yaml >
schema/sagecdm.ttl`, parse-checked via the existing
`scripts/validate_graph.py --parse-only` alongside `mc2_model.ttl`/
`cckp_portal.ttl`.

**2. New crosswalk: institutions → `sagecdm:Organization`.**
`mappings/crosswalks/institution_to_scdm_organization.tsv` — one row per
`modules/institution/institution_name.csv` entry that already carries a ROR
`Ontology Url`, minting a `sagecdm:Organization` id (`org.<slug>`, SCDM's own
`^org\.[a-z0-9]+(-[a-z0-9]+)*$` pattern) plus `name`/`ror_id`. Deterministic,
not human-review-gated like the MONDO/UBERON crosswalks — a ROR ID already
*is* the organization's identity, so there's no judgment call to review.
Institutions still missing a ROR id (`Lurie`, the merged/renamed IUPUI row —
per the README's existing curation notes) are left out, not guessed.

**3. New crosswalk: consortia → `sagecdm:Program`.**
`mappings/crosswalks/consortium_to_scdm_program.tsv` — one row per
`modules/consortium/consortium_name.csv` entry, minting `program.<slug>` ids
per SCDM's `^program\.[a-z0-9]+(-[a-z0-9]+)*$` pattern. `funding_source`
populated only where actually determinable from
`modules/consortium/consortium_funding_agency.csv` (today: NIH, unlinked to
any specific consortium — left blank rather than guessed a per-consortium
association that doesn't exist in the source data). Generated but
**human-review only**, matching the exact convention of the existing
sagebrain crosswalks — program `status`/`description` is a judgment call, ROR
lookup is not.

**4. New script `scripts/link_scdm.py`**, structured like
`scripts/link_sagebrain.py` and reusing existing helpers rather than
duplicating them (`mint_iri`/`class_slug`/`field_slug` from
`build_triples.py`, `ror_search` from `suggest_mappings.py`):
- Mint `sagecdm:Organization` triples from crosswalk #2.
- Mint `sagecdm:Program` triples from crosswalk #3, gated on a per-row
  `reviewed`/`confidence` column so an un-reviewed program mint is skipped,
  not asserted — same discipline as `crosswalk_ontology.py`'s `confidence:
  high` gate.
- Add object-property edges from existing `Grant`/`Dataset`/`Publication`/
  `Project`/`Person`/`Study` instances to these new nodes wherever their
  `grantInstitution`/`institutionAlias`/`consortium` value resolves —
  additive, alongside (not replacing) the existing CV-literal/NCIT-style
  edges, which still serve ontology-anchored queries the new edges don't
  replace.
- Mint provisional `sagecdm:Person` stub records from `Grant.investigator`/
  `Project Investigator`/`Study Investigator` free text: one stub per distinct
  display-name string, `sagecdm:display_name` populated, explicitly **not**
  claiming resolved identity (matching SCDM Person's own design principle) —
  same "verify, report, don't silently merge" discipline
  `link_sagebrain.py` already applies to Biospecimen Key stubs.
- Output: `data/rdf/scdm_links.ttl`, folded into `data/rdf/cckp_kg.ttl` via the
  main public pipeline (**not** the access-controlled `data/mc2_assay/` tree —
  Grant/Dataset/Publication/Project/Person/Study are public CCKP portal data,
  a different access domain than the sagebrain assay-metadata linkage).

**5. New Makefile target `link-scdm`**, wired like `link-sagebrain` — its own
target, **not** folded into `make all` until crosswalk #3's first human
review pass is complete (matches "generated, human-review only, never
auto-applied" everywhere else in this pipeline).

**6. New README section "## Interoperating with SageCommonDataModel"**,
modeled directly on the existing sagebrain section: an architecture-diagram
addition, an identifier-policy note (SCDM's `program.`/`org.`/`person.` ids
become a fourth kind of registry identifier alongside NCIT/EDAM/ROR/DOI-
PubMed), and governance notes — the namespace question (SCDM's
`sage-bionetworks.github.io/SageCommonDataModel/` vs. this pipeline's
`w3id.org/mc2-center/cckp-portal`, an open question for whoever owns those
registrations, not something to silently pick), and a note flagging this
pipeline's live `Grant` schema as input for SCDM's not-yet-designed GRANT
entity (to be raised via the SCDM repo's own process, not implemented there
from this repo).

**7. Give the canonical data model (`modules/`) real Organization/Program
referential integrity, not just the KG layer.** Steps 1-6 above only change
what `kg-pipeline` derives at RDF-build time; the source-of-truth CSVs still
repeat institution names and consortium names as flat CV-literal/free-text
columns independently on `Grant`, `Project`, `Study`, and `Person`. This step
proposes closing that gap at the model level, using the exact same source
data as crosswalks #2/#3 above so the two layers agree:

- **New `modules/organization/` module.** `organization.csv`: `Organization
  Id` (`org.<slug>`, same pattern SCDM uses), `Name`, `ROR Id`, `Acronym`,
  `Type`, `Country`. Seeded 1:1 from the 90 ROR-populated rows already in
  `modules/institution/institution_name.csv` — the same source crosswalk #2
  mints from, so the canonical model and the KG layer stay in agreement
  rather than drifting into two independent institution registries.
- **New `modules/program/` module.** `program.csv`: `Program Id`
  (`program.<slug>`), `Name`, `Description`, `Status`, `Funding Source`.
  Seeded from `modules/consortium/consortium_name.csv`'s 11 values — same
  source as crosswalk #3.
- **Additive reference columns, not replacements.** Add new attributes —
  e.g. `Grant Institution Ref` (`DependsOn` the new `organization.csv`),
  `Grant Program Ref` / `Project Program Ref` / `Study Program Ref`
  (`DependsOn` the new `program.csv`) — to `modules/grant`, `modules/project`,
  and `modules/study`'s `annotationProperty.csv`, **alongside** the existing
  `Grant Institution Name`/`Institution Alias`/`Consortium Name` columns
  rather than replacing them outright. Live Synapse manifests and curator
  workflows already depend on the existing columns; a breaking rename/removal
  needs its own migration/deprecation window, not a same-PR swap.
- **Investigator fields reference `modules/person` (existing), not a new
  SCDM-shaped registry.** `modules/person` already exists in this repo, but
  its shape (curated roster with `Working Group Participation`/`Chair
  Roles`/`Consent For Portal Display`) is a resolved-identity model, not
  SCDM's own capture-don't-resolve `PersonIdentifier` design — reusing it here
  means referencing *this repo's* existing Person registry, not importing
  SCDM's Person shape wholesale. Add `Grant Investigator Ref`/`Project
  Investigator Ref`/`Study Investigator Ref` (multivalued, `DependsOn` the
  existing `modules/person`) alongside the existing free-text
  `Investigator`/`Grant Investigator` columns; an investigator not yet in
  `modules/person` simply has no ref value yet and stays free-text-only,
  matching SCDM Person's own "don't force a match" principle. Distinct from
  step 4's `sagecdm:Person` stub-minting in the KG layer — that mints
  disposable RDF nodes for cross-portal queries; this is the canonical model
  gaining real referential integrity to its own existing registry.
- **`modules/person`'s own `Last Known Institution` field** is currently
  unconstrained free text with no CV backing at all (unlike Grant's
  ROR-curated institution fields) — the most direct, lowest-risk item here.
  Add a `Person Institution Ref` attribute `DependsOn`-ing the new
  `organization.csv` alongside it.
- **This is a proposal, not a same-pass merge.** Per `CLAUDE.md`, PRs to
  `main` require exactly one semantic label and `modules/` is this repo's
  primary data model that other DCC pipelines depend on — draft the new
  module CSVs and the `annotationProperty.csv` additions as a reviewable diff
  for its own PR, not something folded into the kg-pipeline-only work above.

## Out of scope for this pass (flagged as follow-ups, not acted on)

- Opening a PR against SageCommonDataModel to add a GRANT entity. That repo's
  contribution process is itself a placeholder (SCDM-3) and new entities go
  through DMG review; this plan only proposes raising the idea.
- Crosswalking the MC2 assay-metadata `Study` class to SCDM STUDY (item 4
  above) — recorded for awareness, not designed here.
- PORTAL (SCDM-2) — no CCKP-side analog exists yet to align against.

## Verification

- `make sagecdm-schema` output parses cleanly via
  `scripts/validate_graph.py --parse-only`.
- Row counts in both new crosswalk TSVs spot-checked against
  `modules/institution/institution_name.csv` (92 rows, 90 ROR-populated) and
  `modules/consortium/consortium_name.csv` (11 rows).
- New fixture-based pytest coverage in `test/`, following
  `test_link_sagebrain.py`'s pattern (no live Synapse/network access needed).
- `make link-scdm` run against `test/fixtures/` sample data; resulting
  `scdm_links.ttl` checked for exactly one `sagecdm:Organization`/
  `sagecdm:Program` node per distinct crosswalked value (no duplicate mints
  across repeated rows).
- New `modules/organization/`/`modules/program/` CSVs: row counts match
  `modules/institution/institution_name.csv`'s 90 ROR-populated rows and
  `modules/consortium/consortium_name.csv`'s 11 rows respectively. New
  `*Ref` attributes' `DependsOn` additions verified against the new modules'
  own id columns; `make collate && make convert` (root repo) still succeeds
  with the new modules included.

## Process

- Store this plan at `plans/scdm_alignment.md` for review before implementing.
- After implementing (in this conversation or a future one), append an
  Implementation Report below this line, documenting what was actually built,
  any deviations from the approach above, and verification results.

## Implementation Report — approach steps 1-6

Implemented as five commits on `database-model-kg`: vendor SCDM + Makefile
scaffolding, the two crosswalks, `link_scdm.py`, and the README section.
Step 7 (canonical `modules/` registries) is a separate batch, reported
separately below once implemented.

### 1. Vendored SCDM

`schema/vendor/sagecdm/` pinned to SageCommonDataModel `main` @
`210c73f18c1bbe75195e6028fc2aaf87f555fb22` (2026-09-01), with its own
`VENDORED.md` recording the pin, the license, and re-vendoring instructions.
`make sagecdm-schema` generates `schema/sagecdm.ttl` (802 triples,
parse-checked) exactly as planned.

### 2-3. Crosswalks

`scripts/crosswalk_scdm.py` as planned: 90 institutions (of 91) get a
deterministic `org.<slug>` id, joined against `institution_alias.csv` on
the shared ROR id for `scdm_acronym` (the 1 skip — "Indiana University -
Purdue University Indianapolis" — matches the pre-existing, already-known
unmapped row). All 11 consortia get a `program.<slug>` id but ship
`reviewed: false` with `description`/`status`/`funding_source` blank, per
plan.

### 4-5. `link_scdm.py` + Makefile target — deviations from the plan's literal wording

Implemented the crosswalk-driven minting/linking as planned, reusing
`build_triples.py`'s `mint_id`/`mint_iri`/`read_harmonized` directly rather
than reimplementing them. Three corrections made while implementing, all
because the plan's Context section (written before re-checking
`cckp_portal.linkml.yaml` field-by-field) named CCKP portal classes more
broadly than actually exist in this pipeline's v1 scope:

- **Only `Grant` carries `grantInstitution`/`institutionAlias`.**
  `Dataset`/`Publication`/`Tool`/`EducationalResource` don't have an
  institution-shaped field at all — confirmed against the schema, not
  assumed. `cckp:institutionRef` edges come only from `Grant`.
- **Only `Dataset`/`Publication`/`Tool`/`Grant` carry `consortium`** —
  `EducationalResource` doesn't have that field either.
- **Investigator-stub minting reads `Grant.investigator` (scalar) and
  `EducationalResource.contributors` (free-text list)**, not "Project
  Investigator"/"Study Investigator" as the plan's Context section named —
  those are MC2-model-internal attributes, not fields on any of the 5
  actual CCKP portal classes this pipeline instantiates (`Project`/`Study`
  aren't extracted in v1 at all, per `cckp_portal.linkml.yaml`'s own header
  comment). The Project/Study investigator fields belong to step 7 (the
  canonical `modules/` layer), not this KG-layer script.
- **Output is a separate file, not merged into `cckp_kg.ttl`.** The plan
  said "folded into `data/rdf/cckp_kg.ttl`"; on implementation, the
  established precedent this repo actually uses for supplementary linking
  output is to keep it separate (`data/mc2_assay/rdf/sagebrain_links.ttl`
  is never merged into `mc2_assay_kg.ttl`) — followed that same convention
  instead: `data/rdf/scdm_links.ttl` stays its own file, is not part of
  `--merge-with`, and `link-scdm` is not a dependency of `triples`.
- **Predicate names**: `cckp:institutionRef`, `cckp:consortiumRef`,
  `cckp:investigatorRef`, `cckp:contributorRef` — all in this pipeline's own
  `cckp:` namespace (matching the existing `{field}Ref` convention
  `build_triples.py` already uses for `cckp_join`-resolved edges), since
  neither SCDM nor sagebrain defines an inverse property for "this CCKP row
  relates to that SCDM entity."

**Discovered, not fixed**, while verifying against real data: `Grant.investigator`
is a genuinely scalar column whose value sometimes crams several PI names
into one comma-separated string (one real Grant row: 10 names in one
field), and `EducationalResource.contributors` sometimes lists a degree
suffix ("MS"/"PhD") as its own `|`-delimited entry, separate from the name
it modifies. Both are documented in `link_scdm.py`'s own docstring rather
than silently cleaned up — splitting on commas would risk the opposite
failure (a real name that itself contains a comma, e.g. "Van't Veer,
Laura"-style orderings).

### 6. README section

Added "## Interoperating with SageCommonDataModel" (governance shape mirrors
the sagebrain section — crosswalks, generated-but-committed, dedicated
script + Makefile target), a small `make` flow block (the closest
equivalent to an "architecture diagram" this README uses for supplementary
stages — the top-level pipeline diagram doesn't depict the sagebrain flow
either, so this follows that same convention rather than editing the main
diagram), the fourth-identifier-tier note, and the governance notes
(SCDM's own deferred GRANT entity + the investigator data-quality caveat).
Also updated "Directory layout" and the top-level `make` command list.

### Verification

- `make sagecdm-schema && make crosswalk-scdm && make link-scdm` run in
  sequence from a clean state: all three succeed;
  `scripts/validate_graph.py --parse-only` passes on `schema/sagecdm.ttl`.
- Real end-to-end run against live-pulled CCKP data already present in
  `data/harmonized/` (not just fixtures): `data/rdf/scdm_links.ttl` — 1,244
  triples, 90 Organizations, 0 Programs (every crosswalk row still
  unreviewed, correctly, by design), 169 provisional Person stubs, 206
  `institutionRef` edges, 172 `investigatorRef`/`contributorRef` edges.
- 11 new fixture-based tests (`test/test_crosswalk_scdm.py`,
  `test/test_link_scdm.py`), including an id-collision case and a
  reviewed-vs-unreviewed program-gating case. Full suite:
  **69/69 passed**, no regressions.

## Implementation Report — approach step 7

Implemented as four commits, in a substantially corrected design from the
approach text above — the plan's draft named the new attributes
`Grant Institution Ref`/`Grant Program Ref`/`*Investigator Ref` before
checking this repo's own existing foreign-key convention. Mid-implementation,
the user flagged: *"In all the situations where the word 'Ref' was used in
the attribute, I think this better aligns with the 'Key' designation
established in the model - key implies the attribute is a foreign key. Keys
are always derived from '_id' fields, e.g., Biospecimen Key is always
populated from Biospecimen_id."* Checking `modules/shared/annotationProperty.csv`
confirmed this: every cross-entity reference in this model (`Study Key`,
`GrantView Key`, `Biospecimen Key`, `PersonView Key`, `Consortium Key`, …) is
a single, globally-shared attribute defined once and reused via `DependsOn`
across every class that needs it — not a separate uniquely-named attribute
per referencing class. Two of the three "entities" I needed a Key for
**already existed**, just unused:

- **`Consortium Key`** was already fully defined in `modules/shared/
  annotationProperty.csv`, referencing `Consortium_id` (itself already
  defined in `modules/consortium/annotationProperty.csv`) — but **neither
  was referenced in any class's `DependsOn` list anywhere in the model**.
  Confirmed via repo-wide grep before touching anything.
- **`PersonView Key`** was already defined and already used (in `Study`'s
  own `DependsOn`) — just missing from `Grant View`/`Project View`.
- **`Institution Key`** genuinely didn't exist — added it (mirroring
  `Consortium Key`'s exact shape), plus a new `Institution_id` primary key
  for the `Institution` composite class (which had no `_id` attribute at
  all before this).

Reworked plan, actually implemented (discarded and redone after the
correction, since the original `*Ref` attribute rows were already committed
by that point — see commit history):

1. **`Institution_id`** (new) and **`Consortium_id`** (pre-existing,
   previously uncontrolled) both gained real CV backing from
   `modules/institution/institution_id.csv` (90 `org.<slug>` ids) and
   `modules/consortium/consortium_id.csv` (11 `program.<slug>` ids) — same
   seed data as the kg-pipeline crosswalks from steps 2-3, so the canonical
   model and the KG layer agree. `Institution_id`'s generated LinkML enum
   carries a real ROR `meaning:` per value automatically, since
   `institution_id.csv` uses the same Ontology Identifier/Url columns every
   other CV file does.
2. **`Institution Key`** added to `modules/shared/annotationProperty.csv`,
   matching `Consortium Key`'s exact shape (no CV/pattern — matching the
   *majority* of existing `*Key` attributes, which validate only by
   consumer convention, not an enumerated picklist. A few `*Key` attributes
   do carry a regex `Pattern` — e.g. `Biospecimen Key`'s `-B\d{1,9}` — but
   most don't; going patternless keeps this consistent with the plurality
   and avoids over-constraining a still-provisional identifier scheme).
3. **`Grant View`**: added `Institution Key`, `PersonView Key`, and
   `Consortium Key` — additive alongside the existing `Grant Institution
   Name`/`Institution Alias`/`Investigator`/`Consortium Name` columns.
4. **`Project View`**: added `PersonView Key` and `Consortium Key`. Also
   added `Project Consortium Name` itself to `Project View`'s own
   `DependsOn` — a separate, pre-existing gap (the attribute was defined
   but not part of the submission template) that had to be fixed here too,
   since `Consortium Key` is meaningless without it.
5. **`Person View`**: added `Institution Key` (alongside `Last Known
   Institution`, previously uncontrolled free text) and `Consortium Key`
   (alongside `Person Consortium Name`).
6. **`Study`**: no changes — `PersonView Key` was already wired in.

No new attribute rows were added to `modules/grant`, `modules/project`, or
`modules/person`'s own `annotationProperty.csv` files at all — every
reference is a `DependsOn` addition pointing at an attribute already (or
now) defined once in `modules/shared`/`modules/institution`/
`modules/consortium`.

Regenerated `mc2.model.csv` (`make collate`) and kg-pipeline's
`schema/mc2_model.linkml.yaml`/`.ttl` (`make mc2-model-linkml && make
schema`) after these changes.

### Verification

- `python3 -c "..."` spot-check: `Institution_id`/`Institution Key`/
  `Consortium_id`/`Consortium Key` all present with correct Valid Values
  (90 `org.*` / 11 `program.*` ids respectively) after `update_valid_values.py`;
  re-ran the same "revert unrelated pre-existing drift" step used in the
  earlier kg-pipeline-fixes pass (7 unrelated modules + `all_valid_values.csv`
  picked up unconnected whitespace/dedup fixes again, reverted again).
- `schema/mc2_model.linkml.yaml`: confirmed `Grant View`/`Project View`/
  `Person View` classes list the new `slots:` in the right position via
  direct grep; confirmed `Institution_id Enum` carries `meaning: ROR:...`
  per value and `Consortium_id Enum` carries none (correct — no ontology
  grounding exists for a program identity).
- `make schema` (kg-pipeline): both TTLs regenerate and parse-check clean
  (`schema/mc2_model.ttl` 185,894 triples, up from 185,325;
  `schema/cckp_portal.ttl` unchanged at 1,172 — expected, this pass never
  touched `cckp_portal.linkml.yaml`).
- `python3 -m pytest test/` (kg-pipeline): **69/69 passed** — this change
  is canonical-model-only and doesn't touch any kg-pipeline script, so an
  unchanged, fully-passing suite is the correct outcome, not just "no new
  failures."
