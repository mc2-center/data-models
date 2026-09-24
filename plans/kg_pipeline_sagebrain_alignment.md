# Align kg-pipeline's Synapse-entity typing with sagebrain-model's design principles

## Context

Commit `ca8573d` (this branch, `kg-pipeline-fixes`) added `rdf:type gov:SynapseEntity`
to every kg-pipeline row whose subject already gets the canonical Synapse IRI
(Dataset/Grant/EducationalResource, via `mint_iri()`'s `SYNAPSE_NS` branch), on the
reasoning that both kg-pipeline's CCKP graph and sagebrain-model's graph now land in
the same SageBrain Neptune store, so sharing a type would help them join.

Reviewing sagebrain-model's actual design principles and its own record of issues
hit while integrating governanceDUO (`plans/governance_layer_import.md`,
`plans/governance_layer_realignment.md`) surfaces two problems with that commit,
both confirmed against sagebrain-model's and governanceDUO's *current* files, not
stale docs:

1. **Stale namespace.** `gov:` moved from `https://sagebionetworks.org/governance/`
   to `https://w3id.org/synapse/governance#` in sagebrain-model's governance-layer
   realignment (`plans/governance_layer_realignment.md`, commit `eede778` there).
   Confirmed live today: `ontology/imports/governance_graph.ttl`,
   `ontology/main/sagebrain.ttl`, and `ontology/shacl/sagebrain-shapes.ttl` in
   sagebrain-model all bind `gov:` to the new hash namespace; the old slash
   namespace appears nowhere in sagebrain-model outside that plan's own historical
   record. governanceDUO's own `README.md` "Release artifacts and IRI policy"
   section is *also* stale on this point (per the same plan) - it isn't a safe
   source either. kg-pipeline's commit used the old, now-wrong namespace, so the
   asserted type doesn't even resolve to the same class sagebrain-model uses today.

2. **Violates D9 ("one owner per term and shape").** governanceDUO's SHACL
   (`shapes/governance.shacl.ttl:719-781`, `shape:SynapseEntityShape`) is
   `sh:closed true`, `sh:targetClass gov:SynapseEntity`, allows only ~10 named
   `gov:*` properties, and requires `gov:benefactor` (`sh:minCount 1`) - Synapse ACL
   metadata kg-pipeline doesn't have and shouldn't synthesize. sagebrain-model's own
   usage (`examples/AD-cohort.ttl:239`) types a SynapseEntity bare -
   `syn:syn26999999 a gov:SynapseEntity .`, zero other properties on that node -
   domain data lives on a separate node that only *references* it via
   `sagebrain:derived_from`. Even sagebrain-model, which needs this typing for its
   own `sh:class gov:SynapseEntity` shape check, treats asserting it locally as a
   last resort: `governance_layer_realignment.md`'s Q1 lists asserting-and-
   benefactoring the entity in its own example as "(B) a workaround ... not chosen
   without approval," with "(A) recommended" being that governanceDUO's own
   contract fixture owns the fact - "the governance graph owns the entity's ACL
   facts, and sagebrain only references the entity (D9)." kg-pipeline's
   `cckp:Dataset`/`Grant`/`EducationalResource` nodes carry `cckp:*` properties
   directly on the same subject, so typing them `gov:SynapseEntity` fails the
   closed shape the moment the two graphs' shapes are validated together, and
   duplicates a fact governanceDUO already owns (its README describes
   `SynapseEntity` as mirroring Synapse's real `NODE` table - i.e., every tracked
   Synapse entity, which includes CCKP's).

The cross-graph join this was meant to enable already works with no type
assertion at all: kg-pipeline's `SYNAPSE_NS = "https://www.synapse.org/Synapse:"`
is the identical canonical Synapse IRI base governanceDUO/sagebrain-model use
everywhere (`scripts/graph_iris.py`, all examples/fixtures). The same `syn:synNNN`
IRI already carries both graphs' triples once merged in Neptune; a query joining on
that shared IRI needs no shared `rdf:type` to do it.

**Not in scope here (noted, not actioned):** kg-pipeline's `SYNAPSE_ID_RE` is
case-insensitive (`^syn\d+$`, re.IGNORECASE) while governanceDUO's
`scripts/graph_iris.py` id check is lowercase-only. Real Synapse ids returned by
the API are always lowercase, so this is low-risk today, but a differently-cased
source value would mint an IRI that doesn't match governanceDUO's. Flagging for a
future pass, not fixing now - out of scope for this alignment correction.

## Approach

1. `kg-pipeline/scripts/build_triples.py`: revert the `GOV` namespace constant, the
   "Typing with governanceDUO's `gov:SynapseEntity`" docstring section,
   `g.bind("gov", GOV)`, and the `if str(subject).startswith(SYNAPSE_NS): g.add(...)`
   triple, all added in `ca8573d`.
2. `kg-pipeline/test/test_build_triples_synapse_iri.py`: replace the two tests that
   assert the type is/isn't present with one that documents *why* kg-pipeline
   deliberately does not assert `gov:SynapseEntity` (pointing at D9 and the closed
   `SynapseEntityShape`), so a future contributor doesn't re-add the same mistake
   without knowing this history.
3. No SHACL/README changes needed - kg-pipeline's own shapes file never referenced
   `gov:`, and nothing else in this repo assumed the type existed.

## Verification

- `make test`.
- `make validate` (rebuild `data/rdf/*.ttl` from the already-harmonized local data,
  confirm SHACL still conforms and the coverage gate has no regression - the same
  check run for `ca8573d`, now confirming its reversal is also clean).

## Process

Store this plan at `plans/kg_pipeline_sagebrain_alignment.md` for review before
implementing. After implementing, append an Implementation Report below this line.

## Implementation Report (2026-09-24)

Implemented as written; no deviations.

- `kg-pipeline/scripts/build_triples.py`: removed the `GOV` namespace, its
  docstring section, `g.bind("gov", GOV)`, and the `gov:SynapseEntity` type triple.
  `mint_iri()` and the Synapse-canonical-IRI behavior itself are unchanged - only
  the extra type assertion is gone.
- `kg-pipeline/test/test_build_triples_synapse_iri.py`: removed
  `test_synapse_canonical_subject_is_also_typed_as_gov_synapse_entity` and
  `test_non_synapse_subject_is_not_typed_as_gov_synapse_entity` (added in
  `ca8573d`), replaced with
  `test_synapse_canonical_subject_is_not_typed_as_gov_synapse_entity`, which
  documents the D9 rationale so this doesn't get silently re-added.
- `make test`: 157 passed (net zero test-count change - one test removed, one
  added, matching the pre-`ca8573d` count).
- Rebuilt `data/rdf/*.ttl` from the existing local harmonized data and ran
  `make validate`: SHACL conforms on `cckp_kg.ttl` (306,289 triples, no
  `gov:SynapseEntity` triples present), coverage gate has no regression vs
  baseline.
