# Close SHACL shape gaps in the CCKP portal graph

## Context

The CCKP Copilot's SPARQL-backend plan in the sibling `cckp-chatbot` repo
(`../cckp-chatbot/plans/implement-sparql-backend.md`, findings #4 and #9) read
this repo's `kg-pipeline/` source directly while designing its graph tools, and
found problems that belong to this repo's schema and pipeline, not to the
copilot. The briefing `plans/cckp_copilot_sparql_graph_followups.md` collected
them. This plan re-checks each one against the current branch and turns it into
concrete changes.

**State when checked (2026-09-22):** PR #264 (`aws-upload-pipeline`, "Add
Synapse-canonical IRIs, Biolink dual-typing, and a SageBrain S3 upload
pipeline") is still `OPEN`. HEAD is `32db752`. All paths below are on that
branch. The local build (`data/harmonized/*` from 2026-09-10,
`data/rdf/cckp_kg_full.ttl`) matches the live `urn:sagebrain:cckp:2026-09-15`
counts reported in the other plan: 4,773 Publications, 331 Tool nodes, 10
EducationalResources, 379 `investigatorRef`, and 205 `institutionRef`. So local
checks here are a good stand-in for the live graph. This session could not
reach the live endpoint, so the live re-queries are in Verification.

Why the shapes file matters beyond `make validate`: `upload_sagebrain_s3.py`
uploads every `schema/*.ttl`, including `cckp_portal.shacl.ttl`, under
`data/schema/` in the Neptune load path. The shapes therefore land in the same
named graph as the instance data. Consumers like the copilot's `get_shape(class)`
tool read them there as the graph's own schema. A gap in this file is a gap in
what the published graph says about itself.

### 1. Only 2 of 5 portal classes have a class-targeted shape (confirmed)

`kg-pipeline/schema/cckp_portal.shacl.ttl` §1 has just `shape:DatasetShape`
(`sh:targetClass cckp:Dataset`, `datasetId` exactly once) and
`shape:GrantShape` (`cckp:Grant`, `grantId` exactly once). Every other shape
targets by `sh:targetSubjectsOf`. As a result, `?shape sh:targetClass
cckp:Publication|Tool|EducationalResource` returns nothing.

The briefing proposes copying the Dataset/Grant pattern exactly
(`minCount 1 ; maxCount 1 ; datatype xsd:string`). **Doing that literally would
be wrong for two of the three classes.** These classes have no LinkML
`identifier`. Each uses `FALLBACK_ID_FIELD` in `scripts/build_triples.py:167-171`
instead, and `mint_id()` (`:175`) tries the listed direct fields in order before
falling back to a `synthetic-<sha1>` hash:

| Class | Minting key(s) (`FALLBACK_ID_FIELD`) | Schema facts (`cckp_portal.linkml.yaml`) | What the shape should say |
|---|---|---|---|
| Publication | `pubMedId`, then a hash of `publicationTitle`+`doi` | `pubMedId` is `range: integer` and *documented as possibly blank* (preprints) | `pubMedId`: `maxCount 1`, `datatype xsd:integer`, **no `minCount`**. A blank value is a legitimate, documented path. `xsd:string` would be the wrong datatype: `build_triples.py` emits `xsd:integer` for integer-range slots and only falls back to a plain literal when a value is malformed, which is exactly what this shape should catch. |
| Tool | `toolName`, then a hash of `description`+`downloadUrl` | `toolName: required: true` | `toolName`: `minCount 1 ; maxCount 1 ; datatype xsd:string` |
| EducationalResource | `internalIdentifier`, then `alias`, then a hash of `title` | `title: required: true`; `internalIdentifier` is blank in 100% of rows (schema note); `alias` (a Synapse ID) is the key actually used | `title`: `minCount 1 ; maxCount 1 ; datatype xsd:string`; `alias`: `maxCount 1 ; datatype xsd:string` |

Current data: 0/4,773 Publications lack `pubMedId` and none are duplicated;
0/349 Tool rows lack `toolName`; 0/10 EducationalResources lack `alias` or
`title`, and no `alias` is duplicated.

**Side finding: `Tool.toolName` collisions merge nodes, and the schema says
otherwise.** 18 `toolName` values appear on two rows each (VALIS, DBiTplus,
tHMM, CODA, ...), so 349 source rows become 331 `cckp:Tool` nodes. In every
case the paired rows differ only in `grantNumber`/`consortium`/`theme`. In other
words, it is the same tool listed once per grant. Merging them into one node
with two `grantNumberRef` edges is arguably the right entity resolution. But
the `Tool.toolName` description in `cckp_portal.linkml.yaml` says
"build_triples.py falls back to a synthesized ID on collision", and
`mint_id()` has no collision handling at all. A `ToolShape` with
`toolName maxCount 1` passes either way, because the merged rows share an
identical literal, so the shape can't catch this. The fix is to make the
description accurate (see Approach §3 and the open question).

### 2. Some `Ref` join properties have no range-typing shape (confirmed, narrower than briefed)

§3 of the shapes file has `sh:class` shapes for `grantNumberRef`,
`pubMedIdRef`, `publicationIdRef`, and `datasetRef`. Missing:

- **`cckp:datasetsRef`** (plural). `Tool.datasets` carries
  `cckp_join: "Dataset.datasetAlias"`, and `build_triples.py:406` names the ref
  predicate `field_slug(f"{field}Ref")`, so it emits `datasetsRef`, not
  `datasetRef`. `DatasetRefShape`'s `sh:targetSubjectsOf cckp:datasetRef` never
  reaches these triples. This is a real gap, not intentional coverage. Today
  there are 2 such triples in `data/rdf/Tool.ttl`.
- **The four SCDM-crosswalk refs** from `scripts/link_scdm.py`:
  `institutionRef` → `sagecdm:Organization` (`:236`, 205 edges),
  `consortiumRef` → `sagecdm:Program` (`:251`, 6,659 edges), and
  `investigatorRef`/`contributorRef` → provisional `sagecdm:Person` stubs
  (`:359`, 379 and 12 edges). `SAGECDM` is
  `https://sage-bionetworks.github.io/SageCommonDataModel/` (`:88`).

**Correction to the briefing:** the SCDM refs are *not* unvalidated. Three
sanity queries already check their target types against
`cckp_kg_full.ttl` under `make full-kg`/`make query-checks`:
`queries/institution_ref_targets_are_organizations.rq`,
`consortium_ref_targets_are_programs.rq`, and
`investigator_ref_targets_are_persons.rq` (the last one covers both
`investigatorRef` and `contributorRef` through a UNION). What is missing is the
*declarative, in-graph* form. `queries/*.rq` never reach Neptune, while the
shapes file does, so a graph consumer can't see these guarantees. The README
also says (`kg-pipeline/README.md`, the `queries/*.rq` entry near line 340)
that the queries exist for checks "(e.g. 'does every consortiumRef edge point
at a real sagecdm:Program') that SHACL shapes can't easily express". That
example is wrong: a plain `sh:class` shape expresses it.

Where these shapes take effect: `make validate` checks only
`data/rdf/cckp_kg.ttl`, which has no SCDM edges, so the new shapes pass there
trivially. They take effect in `make full-kg`'s SHACL step (`Makefile:221`,
against `cckp_kg_full.ttl`). That step already exists; no Makefile change is
needed.

**Trial run:** I appended draft versions of all 3 class shapes and 5 ref
shapes to a scratch copy of the shapes file and ran pyshacl (0.40.1,
`inference="none"`, the same settings as `validate_graph.shacl_validate()`)
against the current `data/rdf/cckp_kg_full.ttl`. Result: **conforms, 0
violations.** So the changes below won't break the current build.

### 3. `EducationalResource.publicationId` not resolving: source data-entry issue, not a pipeline bug (resolved)

The one non-blank value, on the row `alias = syn66527467` ("2024 Yale Cancer
Symposium : Quantitative Methods in Protein ..."), is
`'https://doi.org/10.7303/syn66527467 '`. That is a **Synapse DOI**
(`10.7303` is Synapse's DOI prefix) for the resource's *own* entity, and it
carries a trailing space. It is not a PubMed ID, so it can never match the
join index keyed on `Publication.pubMedId` (bare integers like `42151118`).
The join logic (`build_join_indices()` at `:286`, resolution at `:403-410`) is
behaving correctly. `build_triples.py`'s own `EXTERNAL_ID_FIELDS` comment
(`:118-127`) already describes this row as "a source data-entry mismatch, not
something to silently 'fix'". It still gets a correct `cckp:publicationIdIri
<https://doi.org/10.7303/syn66527467>`, because `external_iri()` detects the
kind of value from its shape.

No kg-pipeline code change. The fix belongs to whoever curates the Synapse
EducationalResource table (syn51497305): clear `publicationId` on that row
(the DOI identifies the resource itself, not an associated publication), or
move it to a DOI-typed column if one is added. `alias` already carries the
Synapse ID.

### 4. Stale consortium-review comment in the schema (found while re-checking #2)

The YAML comment on `Grant.consortium` in `cckp_portal.linkml.yaml` says
"every row in that crosswalk is currently reviewed=false", so no
`consortiumRef` edges get minted. Now all 11 rows in
`mappings/crosswalks/consortium_to_scdm_program.tsv` are `reviewed=true`, and
the graph has 11 `sagecdm:Program` nodes and 6,659 `consortiumRef` edges. An
SME reading the schema would be misled.

### 5. A stable "current snapshot" graph name (proposal only, not in this repo's control)

`upload_sagebrain_s3.py` writes each build to `s3://<bucket>/<portal>/YYYY-MM-DD/`.
SageBrain's loader turns that prefix into `urn:sagebrain:cckp:{date}` and never
removes older snapshots. NF already has two live ones. The *loader* chooses the
graph name, not this repo, and a second upload under a fixed prefix like
`cckp/current/` would just add an append-only graph with duplicated triples
unless the loader also clears it first. So a stable alias needs SageBrain
platform support. It could be a loader option that replaces a fixed-name graph,
or the query-layer auto-resolution the SageBrain docs already list as proposed
future work. This plan only raises the issue.

**Sequencing point this plan does create:** republishing the fixes below makes
the **second** CCKP snapshot in the shared store. From then on, any consumer
that doesn't scope by named graph (e.g. an unscoped `?x a cckp:Dataset`) will
double-count. `cckp-chatbot`'s `_resolve_cckp_graph()` design already handles
this, but the SPARQL backend it belongs to isn't deployed yet. Coordinate the
publish timing (Approach §6).

## Approach

All changes are under `kg-pipeline/`. None are in the root model.

1. **`schema/cckp_portal.shacl.ttl` §1: add three class-targeted shapes**,
   following `DatasetShape`/`GrantShape`'s layout (`a sh:NodeShape ;
   sh:targetClass ... ; rdfs:label ... ; sh:property [ sh:path ... ; sh:name ... ;
   ... ; sh:message ... ]`), with the cardinalities from the Context §1 table:
   - `shape:PublicationShape`: `cckp:pubMedId` `maxCount 1`, `datatype
     xsd:integer`. The message should say that a missing value is allowed and
     that `mint_id()` then falls back to a synthetic ID.
   - `shape:ToolShape`: `cckp:toolName` `minCount 1 ; maxCount 1 ; datatype
     xsd:string`.
   - `shape:EducationalResourceShape`: `cckp:title` `minCount 1 ; maxCount 1 ;
     datatype xsd:string`, plus `cckp:alias` `maxCount 1 ; datatype xsd:string`.
   - Update the §1 heading comment so it no longer implies every class has a
     single required identifier. Dataset/Grant have a LinkML `identifier`. The
     other three are keyed by `FALLBACK_ID_FIELD`, and their shapes constrain
     the fields that actually exist, not a guaranteed ID.

2. **`schema/cckp_portal.shacl.ttl` §3: add five ref-typing shapes**, following
   `DatasetRefShape`'s layout:
   - `shape:DatasetsRefShape`: `sh:targetSubjectsOf cckp:datasetsRef` →
     `sh:class cckp:Dataset`.
   - Add `@prefix sagecdm: <https://sage-bionetworks.github.io/SageCommonDataModel/> .`
     to the header, then add `shape:InstitutionRefShape` (→ `sagecdm:Organization`),
     `shape:ConsortiumRefShape` (→ `sagecdm:Program`),
     `shape:InvestigatorRefShape`, and `shape:ContributorRefShape`
     (both → `sagecdm:Person`).
   - Put the four SCDM ones in their own sub-block, with a comment saying they
     only apply to `cckp_kg_full.ttl` (validated by `make full-kg`), since
     `scdm_links.ttl` is merged in there and not into `cckp_kg.ttl`.
   - The `investigatorRef`/`contributorRef` messages should mention that the
     targets are *provisional* stubs (`cckp:provisional true`), so a consumer
     reading the shape doesn't take them as resolved identities.
   - Keep the three `queries/*_ref_targets_are_*.rq` files. They are cheap,
     already wired into `query-checks`, and cover the same guarantee. Removing
     them is a separate cleanup and not worth the churn now.

3. **`schema/cckp_portal.linkml.yaml`: fix two inaccurate descriptions or comments**
   - `Tool.toolName` description: remove "falls back to a synthesized ID on
     collision". Replace it with what really happens: rows with the same
     `toolName` merge into one node, which carries each row's
     `grantNumber`/`consortium`/`theme` values. The synthetic-ID fallback is only
     used when `toolName` is blank. Keep this user-facing: no history, no
     session narration (per the model-description convention).
   - `Grant.consortium` comment: drop the "every row ... reviewed=false" claim.
     Say that `consortiumRef` edges are minted for reviewed crosswalk rows.
   - Run `make schema` afterwards so `schema/cckp_portal.ttl` picks up the
     description change.

4. **`README.md`**: fix the `queries/*.rq` entry's example (near line 340).
   `consortiumRef` target-typing is now also a SHACL shape. Use an example the
   queries really are needed for, such as the aggregate/cardinality checks
   (`person_display_name_cardinality.rq`, `core_classes_present.rq`). Check
   whether the "Additional pipeline stages" section's SHACL paragraph (the one
   the `cckp_portal.shacl.ttl` entry at line 267 points to) lists which shapes
   exist, and update it if so.

5. **Tests**: `test/test_shacl_validation.py` (conforming and violating
   fixtures).
   - `test/fixtures/shacl_conforming.ttl`: add a `cckp:Tool` with one
     `toolName` and a `datasetsRef` to the existing Dataset; add a
     `cckp:EducationalResource` with `title` and `alias`; add one
     `sagecdm:Organization`, `Program`, and `Person` node, each referenced by
     its ref property; add an integer-typed `pubMedId` to the existing
     Publication.
   - A single violating fixture that trips any shape can't show that *each*
     new shape fires. Add one small fixture per new shape
     (`shacl_violating_<shape>.ttl`), each with exactly one violation: a Tool
     with no `toolName`; an EducationalResource with two `title`s; a Publication
     with a string-typed `pubMedId`; a `datasetsRef` pointing at a Grant; and
     one for each SCDM ref pointing at a node of the wrong type. Drive them from
     one parametrized test. This follows the existing `validate_graph.shacl_validate()`
     call pattern.

6. **Publish sequencing (a decision, not code)**: after merge, rebuild
   (`make full-kg`) and republish (`make deploy-kg`, `make upload-sagebrain-s3`)
   **only once** the copilot's graph-scoping work is live or ready to ship with
   it. Otherwise, confirm that no other consumer queries the CCKP graph
   unscoped. Tell the `cckp-chatbot` side the new snapshot's date.

7. **Cross-team items (no code in this repo)**:
   - **SageBrain platform** (`sagebrain-infra`): open an issue proposing a
     stable per-portal "current" graph name (Context §5). Include the
     observation that NF already has two live snapshots and ask whether the
     bulk loader can replace a fixed-name graph on each load.
   - **CCKP data curation**: ask for the syn51497305 row `syn66527467`'s
     `publicationId` value to be cleared or corrected (Context §3).

8. **Cross-references**: add a pointer to this plan in the SHACL paragraph of
   `plans/kg_pipeline_architecture_decisions.md`, the same way it and
   `scdm_alignment.md` point at each other. After implementing, trim
   `plans/cckp_copilot_sparql_graph_followups.md` down to a one-line pointer
   here, or delete it. It was a briefing, and this plan replaces it.

## Verification

- `make test`: the conforming fixture passes, and each per-shape violating
  fixture fails. For the violating fixtures, check the reported
  `sh:sourceShape` too, not only `conforms=False`, so a fixture can't pass
  because the wrong shape fired.
- `make validate`: the SHACL step on `cckp_kg.ttl` still conforms. The three
  new class shapes are checked for real here; the SCDM ref shapes pass
  trivially.
- `make full-kg`: SHACL on `cckp_kg_full.ttl` conforms (the trial run above
  already showed 0 violations), and `query-checks` still pass.
- Negative spot check: temporarily point one `consortium_to_scdm_program.tsv`
  row at a nonexistent program id and rebuild. Both
  `ConsortiumRefShape` and the existing `.rq` query should flag it. Then
  revert.
- **Live, after republish** (run from a machine that can reach the endpoint,
  e.g. `cckp-chatbot`'s `make sparql-test` harness, since this session could
  not). Substitute the new snapshot's date:
  ```sparql
  PREFIX sh: <http://www.w3.org/ns/shacl#>
  SELECT ?shape ?target WHERE { GRAPH <urn:sagebrain:cckp:YYYY-MM-DD> {
    { ?shape a sh:NodeShape ; sh:targetClass ?target }
    UNION { ?shape a sh:NodeShape ; sh:targetSubjectsOf ?target } } }
  ```
  Expect 5 `targetClass` rows (Dataset, Grant, Publication, Tool,
  EducationalResource) and 11 `targetSubjectsOf` rows.
- Also live: re-run the other plan's named-graph listing to confirm the new
  `urn:sagebrain:cckp:{date}` graph is there alongside `2026-09-15`, and
  re-check that `publicationIdRef` is still 0/1 until the curation fix lands.

## Open questions

- **Tool collisions:** is merging same-named Tool rows into one node the
  intended behavior (it's what happens now)? The alternative is minting
  distinct nodes, e.g. a hash of `toolName` plus the row's other fields. This
  plan assumes merging is correct and only fixes the description. If distinct
  nodes are wanted, that is a `mint_id()` change, and it changes Tool IRIs
  that the live graph and portal links may already use.

## Process

Store this plan at `plans/cckp_shacl_shape_gaps.md` for review before
implementing. After implementing, append an Implementation Report below this
line.

## Implementation Report (2026-09-23)

Plan approved as written. **Open question resolved:** same-named Tool rows
merging into one node is the intended behavior, so `mint_id()` is unchanged
and only the `Tool.toolName` description was corrected.

**Changes (all under `kg-pipeline/`):**

- `schema/cckp_portal.shacl.ttl`: new `sagecdm:` prefix. §1 now has a heading
  note that separates identifier-keyed classes from `FALLBACK_ID_FIELD`-keyed
  ones, plus `PublicationShape`, `ToolShape`, and `EducationalResourceShape`
  with the cardinalities from the Context §1 table. §3 adds
  `DatasetsRefShape`. A new §3a sub-block holds `InstitutionRefShape`,
  `ConsortiumRefShape`, `InvestigatorRefShape`, and `ContributorRefShape`; the
  Person-target messages say the targets are provisional stubs. That makes 5
  `targetClass` shapes and 11 `targetSubjectsOf` shapes.
- `schema/cckp_portal.linkml.yaml`: `Tool.toolName` now describes the merge
  behavior and the blank-only synthetic fallback. The `Grant.consortium`
  comment no longer claims the crosswalk is unreviewed.
  `schema/cckp_portal.ttl` was regenerated with `make schema`; the only
  non-blank-node triple change is that description. `make schema` also
  reserialized `schema/mc2_model.ttl` in a different blank-node order. Its
  LinkML source hadn't changed, so that file was restored rather than
  committed as noise.
- `README.md`: the `cckp_portal.shacl.ttl` entry now describes what the shapes
  cover. Its old pointer to "Additional pipeline stages" led nowhere, because
  that section never described the shapes. The `queries/*.rq` example now uses
  `core_classes_present` (a class-existence floor). Two other examples were
  rejected: `consortiumRef` targets are now a SHACL shape, and the plan's other
  suggestion, `person_display_name_cardinality`, is a plain
  `minCount`/`maxCount` rule that SHACL *can* express.
- `scripts/validate_graph.py`: the pyshacl call was split out of
  `shacl_validate()` into `run_shacl()`, which returns the results and shapes
  graphs. `shacl_validate()` keeps its behavior. Tests need the shapes graph
  that pyshacl actually used: `sh:sourceShape` is a blank node, and re-parsing
  the shapes file mints different blank-node IDs.
- Tests: `shacl_conforming.ttl` now covers all 5 classes (including an
  integer-typed `pubMedId`), `datasetsRef`, and all four SCDM refs with typed
  targets. There are 8 new `shacl_violating_<shape>.ttl` fixtures, each with one
  violation. `test_each_shape_fires` checks that there is exactly one
  validation result and that its property shape belongs to the expected named
  shape.
- `plans/kg_pipeline_architecture_decisions.md`: the SHACL paragraph points
  here. `plans/cckp_copilot_sparql_graph_followups.md` was cut down to a pointer
  instead of deleted, because `../cckp-chatbot/agents/README.md` links to it by
  path.

**Verification run:**

- `make test`: 153 passed.
- `make validate`: coverage gate passes with no regressions, and SHACL conforms
  on `cckp_kg.ttl` (304,990 triples).
- `make full-kg`'s SHACL and query steps, run directly against the existing
  2026-09-15 `cckp_kg_full.ttl` (no rebuild; no build code changed): SHACL
  conforms (339,487 triples) and 8/8 query checks pass.
- Negative spot check: added one `consortiumRef` from a real Grant
  (`Synapse:syn10140998`) to a nonexistent program, in a scratch copy of
  `cckp_kg_full.ttl` rather than by editing the TSV. `ConsortiumRefShape` gave
  exactly 1 result and `consortium_ref_targets_are_programs.rq` failed with 1
  row. The scratch copy was deleted afterward.

**Not done here (as planned, outside this repo's code):**

- Approach §6: rebuild and republish only once the copilot's graph-scoping
  work is ready.
- Approach §7: the SageBrain stable-graph-name issue and the syn66527467
  curation request.
- The live-endpoint verification queries. These still need a machine that can
  reach Neptune, after republish.

### Pre-PR review round (2026-09-23)

An independent SME-framed review (`/code-review high`) raised 10 findings.
All were checked against code or data before being fixed:

- **The integer fallback was dead code (confirmed).** rdflib's
  `Literal(v, datatype=XSD.integer)` never raises; it marks a bad lexical form
  `ill_typed`. So the `except` branch in `build_class_graph()` could never run,
  and a value like `"PMC123"` would have shipped as an ill-typed
  `"PMC123"^^xsd:integer`. Context §1 assumed this fallback worked. Fixed: the
  code now checks `lit.ill_typed` and falls back to a plain literal. New test
  `test_malformed_integer_value_becomes_plain_literal_not_ill_typed` fails
  without the fix and passes with it. The current graph has 0 ill-typed
  literals, so the build output doesn't change.
- **`PublicationShape` vs `PubMedIdIriShape`: wording, not a conflict.** The
  DOI-in-a-PubMed-field case applies to `EducationalResource.publicationId`,
  not `Publication.pubMedId`. `PubMedIdIriShape`'s message no longer suggests
  that every pubMedId field may hold a DOI. `PublicationShape`'s message now
  says that a non-integer value is kept as a plain literal and fails the check.
- **`ToolShape` gate vs the documented synthetic fallback.** Both are kept.
  `toolName` is `required: true` in the schema, and the fallback only stops one
  bad row from crashing the build. The §1 comment and the shape message now
  say that a row reaching the fallback is flagged. This means a blank
  `toolName` (0 rows today) blocks `make full-kg` and therefore publishing.
- **Stale "consortiumRef can't be a SHACL shape" example.** It also appeared in
  `validate_graph.py --help` and the Makefile `query-checks` comment; both are
  fixed. The README now says the `*_ref_targets_are_*.rq` queries deliberately
  duplicate the SCDM ref shapes as a cross-check.
- **No shape for `publicationIdIri`.** Added `PublicationIdIriShape`, with the
  same pattern as `PubMedIdIriShape`. Added a conforming fixture triple and
  `shacl_violating_publication_id_iri.ttl`.
- **The `alias` message named the wrong key.** It now says `internalIdentifier`
  is tried first.
- **Merged Tools with conflicting single-valued fields (latent).** The current
  graph has 0 such cases. Added the query check
  `queries/merged_tools_have_no_conflicting_scalars.rq`, which covers the 21
  scalar, non-enum Tool fields. It isn't done as SHACL because their one-value
  limits are already in the TBox as `owl:maxCardinality`. Verified: it passes
  on the real graph, and fails with 1 row after injecting two `version` values
  on the merged `Tool/CODA` node in a scratch copy.
- **Violating fixture didn't match real output:** resolved by the first fix.
  A malformed pubMedId is now emitted as a plain literal, which is exactly
  what `shacl_violating_publication.ttl` contains.
- **Stale file header:** the shapes file header now names both target graphs
  and says the file is published with the graph.

After the fixes: `make test` 155 passed, `make validate` conforms, and SHACL on
`cckp_kg_full.ttl` conforms with 9/9 query checks passing.
