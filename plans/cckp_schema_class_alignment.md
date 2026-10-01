# Align CCKP portal classes to schema.org (Layer-1 ontology alignment)

## Context

Reviewed `SageBrain RDF Knowledge Graph Construction` (draft doc, Sage
Bionetworks' NF-OSI-derived KG pipeline architecture reference, not checked
into this repo) against `kg-pipeline/`'s ontology-alignment code. That doc's
"Internal Ontology" section recommends, as the cheapest and fastest
ontology-alignment step: "Use BioLink Model where appropriate for
schema-level type assertions... BioLink alignment is faster to adopt and
immediately enables cross-portal schema-level queries. Domain ontology
alignment is a slower path... Portals can start with BioLink and layer in
domain ontology alignments incrementally." It also gives explicit modeling
guidance: "prefer `rdfs:subClassOf` over `owl:equivalentClass` for external
alignments unless bidirectional equivalence is truly intended. It is a safer
semantic commitment and less expensive for reasoners."

This repo's `kg-pipeline/schema/cckp_portal.linkml.yaml` defines the 5 core
CCKP classes (`Dataset`, `Publication`, `Tool`, `Grant`,
`EducationalResource`, lines 70/159/242/411/494) with **no class-level
external-ontology alignment at all** — confirmed via `grep -n "biolink\|
class_uri\|exact_mappings\|close_mappings" schema/cckp_portal.linkml.yaml`
(no hits). The generated `schema/cckp_portal.ttl` bears this out: each class
is only ever `a owl:Class` (lines 13, 114, 221, 313, 399) with nothing
pointing outward.

This is a real gap even though the rest of the vocabulary choice is already
schema.org-shaped:

- `scripts/build_datacatalog_triples.py` already binds
  `SCHEMA = rdflib.Namespace("https://schema.org/")` and asserts real
  `schema:` **predicates** (not just cckp: ones) onto the very same
  `cckp:Dataset` subjects `build_triples.py` mints — its own docstring says
  "this vocabulary was deliberately modeled on schema.org Dataset/CreativeWork
  terms." The *predicates* are already schema.org-aligned; the *class
  identity* is not.
- This repo already has a working, low-risk precedent for exactly the kind
  of "safe semantic commitment" the PDF asks for: `schema/mc2_model.ttl:813`
  asserts `skos:exactMatch CRDC_CDE:12922545` on a slot to link it to an
  external CDE, rather than an OWL-semantics-heavy alternative. The same
  `skos:exactMatch`/`close_match` style (via LinkML's `exact_mappings`/
  `close_mappings` slots, which apply to classes too, not just slots) is the
  natural mechanism here — weaker and safer than `owl:equivalentClass`, and
  in the same spirit as (arguably even more conservative than) the PDF's
  `rdfs:subClassOf` recommendation.

Scope is intentionally the **T-Box only**: adding a class-level mapping
annotation to the schema. This does not touch `scripts/build_triples.py`,
any instance data, or harmonization at all — no CV curation, no coverage
gate, no live-data run involved.

## Approach

1. Add the `schema` prefix to `schema/cckp_portal.linkml.yaml`'s
   `prefixes:` block (currently only `linkml`, `cckp`, `mc2` — see lines
   ~38-45): `schema: https://schema.org/`, matching the exact namespace
   `build_datacatalog_triples.py` already uses.

2. Add an `exact_mappings:` (or `close_mappings:` where the fit is looser)
   entry directly under each class definition in
   `schema/cckp_portal.linkml.yaml`. Proposed targets, real schema.org (or
   Bioschemas-profile-backed schema.org) types — not invented:

   | CCKP class | Target | Mapping strength | Rationale |
   |---|---|---|---|
   | `Dataset` | `schema:Dataset` | `exact_mappings` | Direct match; already the vocabulary `build_datacatalog_triples.py` models against. |
   | `Publication` | `schema:ScholarlyArticle` | `exact_mappings` | schema.org has no bare "Publication" class; `ScholarlyArticle` (under `CreativeWork`) is the real type the Bioschemas `Publication` profile itself is built on. |
   | `Tool` | `schema:SoftwareApplication` | `exact_mappings` | The Bioschemas `Tool` profile is built on `schema:SoftwareApplication`. |
   | `Grant` | `schema:MonetaryGrant` | `exact_mappings` | schema.org's own guidance prefers the `MonetaryGrant` subtype over the bare `Grant` class for funding-type grants, which is what CCKP's `Grant` class represents. |
   | `EducationalResource` | `schema:LearningResource` | `close_mappings` | schema.org has no `EducationalResource` class; `LearningResource` (under `CreativeWork`) is the closest real type — use `close_mappings` rather than `exact_mappings` since the fit is looser than the other four. |

3. Do not touch `scripts/build_triples.py` or any `data/rdf/*.ttl` instance
   output — this is a schema-only (`make schema`) change.

4. Regenerate `schema/cckp_portal.ttl` via `make schema`
   (`linkml generate owl`) and confirm the mapping actually renders into the
   turtle. **This is unverified going in** — LinkML's OWL generator does not
   always emit `exact_mappings`/`close_mappings` as triples without an extra
   flag or post-processing step. If it doesn't render as-is:
   - Check `linkml generate owl --help` for a mappings/annotation-inclusion
     flag first.
   - If no built-in flag works, follow this repo's own precedent for "LinkML
     doesn't quite do X, add a documented Python fixup"
     (`scripts/resolve_prefixes.py` is exactly this pattern for a different
     LinkML gap) — a small `scripts/resolve_class_mappings.py` post-processing
     step run after `linkml generate owl`, appending
     `cckp:{Class} skos:exactMatch schema:{Target} .` (or `skos:closeMatch`
     for `close_mappings`) triples directly, wired into the `schema` Makefile
     target the same way `resolve_prefixes.py` already is.
   - Document whichever path was taken in this plan's Implementation Report,
     including why, so a future re-run of `make schema` doesn't silently
     regress.

5. Update `kg-pipeline/README.md`'s directory-layout comment for
   `cckp_portal.linkml.yaml` (currently just "hand-authored; imports
   mc2_model.linkml.yaml") to mention the schema.org class alignment, and add
   a one-line pointer from `plans/kg_pipeline_architecture_decisions.md`'s
   "Design decisions" section, matching how the DataCatalog/SCDM stages are
   each cross-referenced there.

## Verification

- `make schema` runs clean; `schema/cckp_portal.ttl` regenerates and
  contains a mapping triple for each of the 5 classes (via whichever
  mechanism step 4 lands on) — confirm with
  `grep -n "schema:Dataset\|schema:ScholarlyArticle\|schema:SoftwareApplication\|schema:MonetaryGrant\|schema:LearningResource" schema/cckp_portal.ttl`.
- `make test` (in particular `test/test_schema_loads.py`) still passes
  unchanged — this confirms the schema still loads via `SchemaView` and
  `build_triples.py`'s existing logic (which reads `schema_meta` per class)
  is unaffected by the new class-level annotation.
- `make validate`'s schema-turtle parse-check still passes (no malformed
  turtle introduced).
- Spot-check with `rdflib`: `Graph().parse("schema/cckp_portal.ttl")` then
  confirm `list(g.objects(CCKP.Dataset, SKOS.exactMatch))` (or whichever
  predicate was actually used) returns `schema:Dataset`.
- No change expected to `make all`'s live-data run (extract/harmonize/
  triples/validate) — this is schema-only, so re-verify by diffing
  `data/rdf/*.ttl` instance output before/after (should be byte-identical
  aside from anything `make schema` itself regenerates upstream).

## Process

Store this plan at `plans/cckp_schema_class_alignment.md` for review before
implementing. After implementing, append an Implementation Report below this
line — what was actually done, any deviations from the Approach section
(especially which path step 4 took), and verification results.

## Implementation Report

Implemented as planned, steps 1-5, with one deviation in step 4 (documented
below) and no changes needed to `scripts/build_triples.py` or any instance
data, as scoped.

**Step 1-2:** Added `schema: https://schema.org/` to `schema/
cckp_portal.linkml.yaml`'s `prefixes:` block, and a class-level mapping to
each of the 5 classes exactly as proposed: `Dataset`/`Publication`/`Tool`/
`Grant` -> `exact_mappings: [schema:Dataset|ScholarlyArticle|
SoftwareApplication|MonetaryGrant]`, `EducationalResource` ->
`close_mappings: [schema:LearningResource]`.

**Step 4 deviation - CURIE vs. full IRI:** the plan anticipated `linkml
generate owl` might not render `exact_mappings`/`close_mappings` at all
without a flag or a post-processing fixup script. In practice it rendered
them out of the box (as `skos:exactMatch`/`skos:closeMatch`, confirming the
plan's expected mechanism) - **but** only when the mapping was written as a
full IRI (`https://schema.org/Dataset`), not a CURIE (`schema:Dataset`).
Writing the CURIE form caused the OWL generator to resolve it against a
different, built-in default prefix map (yielding `http://schema.org/Dataset`
with no `@prefix schema:` line at all), silently inconsistent with
`build_datacatalog_triples.py`'s `https://schema.org/` predicate namespace.
Switched all 5 mappings to the full-IRI form, which correctly produces
`@prefix schema: <https://schema.org/> .` and compact `schema:Dataset`-style
objects matching the rest of the pipeline. No post-processing script needed.
Full root-cause and a reusable note for future class mappings is recorded in
`plans/kg_pipeline_architecture_decisions.md`'s new "Schema.org class
alignment" section, per that section's own cross-reference back to this plan.

**Step 3:** No changes to `scripts/build_triples.py` or any `data/rdf/*.ttl`
instance output - confirmed schema-only by `test_build_triples_*.py` passing
unchanged (they exercise `build_triples.py`'s `SchemaView`-based field
reading, which never touches class-level annotations).

**Step 5:** Updated `kg-pipeline/README.md`'s directory-layout comment for
`cckp_portal.linkml.yaml` and added a full "Schema.org class alignment"
section to `plans/kg_pipeline_architecture_decisions.md` (rather than one
line, since the CURIE/IRI quirk found in step 4 is worth preserving in full
for anyone adding a future class-level mapping).

**Verification results:**
- `make schema` regenerates `schema/cckp_portal.ttl` cleanly (only the
  pre-existing, documented "Ambiguous attribute" warnings, unrelated to this
  change) and parses OK via `scripts/validate_graph.py --parse-only`
  (1173 triples).
- Confirmed via `grep`/`rdflib` that all 5 classes carry the expected
  mapping: `Dataset`/`Publication`/`Tool`/`Grant` ->
  `skos:exactMatch` -> `schema:Dataset`/`ScholarlyArticle`/
  `SoftwareApplication`/`MonetaryGrant`; `EducationalResource` ->
  `skos:closeMatch` -> `schema:LearningResource`.
- `make test` - all 86 tests pass unchanged, including
  `test_schema_loads.py` and every `test_build_triples_*.py`.
- **Noteworthy, unrelated finding:** regenerating `cckp_portal.ttl` from the
  *original, unmodified* committed YAML (before any edit in this plan) also
  produces a ~1000-line diff against the already-committed file - confirming
  `linkml generate owl`'s blank-node/restriction ordering is non-deterministic
  across runs, independent of this change. The actual `make schema` diff
  produced by this plan's edits is therefore mostly this pre-existing,
  unrelated reordering; the real substantive addition (1 prefix line + 5
  mapping triples) was isolated and confirmed separately before committing.
  Documented in `plans/kg_pipeline_architecture_decisions.md` so a future
  `cckp_portal.ttl` diff isn't mistaken for unexpected schema drift.
- Did not run `make validate`'s coverage/SHACL checks or a live
  extract/harmonize/triples cycle - both require live Synapse credentials
  and gitignored `data/raw|harmonized|rdf/` artifacts not present in this
  session, and are out of scope for a schema-only (T-Box) change per the
  plan's own Context section. The fixture-based `test_build_triples_*.py`
  suite (which exercises the same `SchemaView` schema-reading path
  `build_triples.py` uses live) passing unchanged is the available
  substitute verification.
