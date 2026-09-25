# kg-pipeline pre-PR review fixes

## Context

An independent review ran on `kg-pipeline-fixes` before its PR to
`cde-model-revisions`. The run was high effort, with reviewers covering
RDF/SHACL, LinkML and schematic CSV. It raised 10 findings. The
orchestrator checked findings 1, 3, 5, 6, 9 and 10 against the code and
the built graph:

1. **Booleans lose their datatype.** `build_triples.py` (at about line
   372) now keeps a value as a plain literal whenever rdflib flags it
   `ill_typed`. The portal's booleans are capitalized ("True"/"False"),
   and that isn't in xsd:boolean's lexical space. As a result, all 331
   `cckp:portalDisplay` values and 39 `cckp:toolPackageDependenciesPresent`
   values in `Tool.ttl` are plain strings. The code before this branch
   emitted `"True"^^xsd:boolean`, which was typed but invalid.
2. **Downgrades are silent.** The comment claims "the SHACL sh:datatype
   shapes flag it", but only `pubMedId` has a typed `sh:datatype` shape. Any
   other ill-typed value gets downgraded without anything noticing.
3. **Stale schema.** kg-pipeline's schema never picked up the CV quoting
   fixes. `schema/mc2_model.linkml.yaml` still has the truncated
   descriptions and no `meaning:` for "In situ hybridization", "LC-MS/MS"
   or "Quantitative Immunofluorescence".
4. **Dirty rows block deploy.** The new Publication, Tool and
   EducationalResource SHACL shapes are at Violation severity, so one dirty
   portal row fails `make full-kg` and blocks the manifest and deploy.
5. **Wrong claim about review.** `docs/knowledge-graph.md` says every
   crosswalk is human-reviewed before it produces edges. SCDM
   Organizations are minted deterministically from ROR, and Persons are
   provisional stubs; neither has a review gate.
6. **Nonexistent slot.** `docs/knowledge-graph.md` cites
   `Publication.datasetAlias`. The real slot is `Publication.dataset`.
7. **Noisy schema diffs.** `make schema` output isn't deterministic
   (blank-node order), so each regeneration produces a large diff with
   almost no real change.
8. **Duplicate checks.** The InstitutionRef, ConsortiumRef and
   InvestigatorRef shapes duplicate `queries/*_ref_targets_are_*.rq`.
9. **Rows vs nodes.** The docs give 349 Tools. That is the number of source
   rows; the graph has 331 `cckp:Tool` nodes.
10. **CSV conventions.** `tissue.csv` used `False` for Required, and two
    Source cells said "Sag". This is already fixed in commit `0f7e00d`.

The user decided three design questions on 2026-09-25:
- Finding 4: split SHACL severity (see Approach step B).
- Finding 8: drop the three duplicate queries.
- Finding 7: canonicalize the schema serialization.

## Approach

Dispatch **A** and **B** in parallel; their files don't overlap. Run **C**
after B, since both edit `kg-pipeline/Makefile`. The orchestrator does
**D** last, because the page has to describe the final state.

- **A (findings 1 and 2)**, in `scripts/build_triples.py` and its tests:
  - Normalize boolean text before typing. Case-insensitive
    `true`/`false`/`1`/`0` become canonical `true`/`false` with
    `datatype=XSD.boolean`.
  - Keep the plain-literal fallback for anything else that is still
    ill-typed, but record it: count each downgrade per (class, field),
    print a summary line per field, and fix the comment.
  - Add tests for booleans and for the downgrade report.
- **B (findings 4 and 8)**, in the SHACL file, `validate_graph.py`, the
  queries and their tests/docs:
  - Set `sh:severity sh:Warning` on the literal data-quality property
    shapes (`sh:datatype`, and `sh:minCount` on free-text fields) in the
    Publication, Tool and EducationalResource shapes.
  - Keep ref-target `sh:class` and `sh:nodeKind` constraints as
    Violations.
  - Make `validate_graph.py` print warnings and fail only when a
    Violation is present.
  - Delete the three duplicate queries and update every reference to them.
- **C (findings 3 and 7)**, in the Makefile, a canonicalization step and
  `schema/`:
  - Add a post-step to `make schema` that re-serializes `schema/*.ttl`
    deterministically.
  - Regenerate the schema: `make mc2-model-linkml`, then `make schema`.
  - Add a test that regenerating twice gives byte-identical output.
- **D (findings 5, 6 and 9)**, in `docs/knowledge-graph.md` and the plans:
  - Correct the review-gate claims, the slot name and the Tool counts.
  - Reflect B's severity split and the removed queries, and C's
    deterministic schema.

## Verification

- `make test` passes (156 tests, plus the new ones).
- `make triples` followed by validation: `Tool.ttl` has
  `"true"^^xsd:boolean`, with zero plain "True" strings.
- SHACL on `cckp_kg_full.ttl` reports no Violations, and the 6 remaining
  query checks pass.
- `make schema`, run twice, produces identical output. `mc2_model.ttl`
  carries `NCIT_C17562`, `NCIT_C122168` and `NCIT_C221816`.
- The orchestrator reviews each diff against this plan, then re-runs a
  focused review before `gh pr create`.

## Process

Store this plan at plans/kg_pipeline_pre_pr_review_fixes.md for review
before implementing. After implementing, append an Implementation Report
below this line.

## Implementation Report (2026-09-25)

**Findings 1–2 (commit c2cfd8c).** Portal booleans are now normalized to
canonical `true`/`false` before typing. All 331 `portalDisplay` and 39
`toolPackageDependenciesPresent` literals are `xsd:boolean`. Any value that
is still ill-typed stays a plain literal and is counted per field in the
build output. The live build currently has none. Two tests were added and
the integer test was extended.

**Findings 4 and 8 (commit 1bed188).** These SHACL checks are now
`sh:Warning`:
- `Publication.pubMedId`
- `Tool.toolName`
- `EducationalResource` title and alias

The `sh:class` ref shapes and `PublicationIdIriShape` stay `sh:Violation`.
`external_iri()` only ever mints DOI or PubMed IRIs, so a failure of that
shape means a code bug rather than dirty data. `validate_graph.py` splits
results by `sh:resultSeverity` and fails only on violations. The three
duplicate `*_ref_targets_are_*.rq` queries were removed after checking that
each one's predicate and target match its shape.

**Finding 3 (commit 89f8c76).** Ran `make mc2-model-linkml` and then
`make schema`. The YAML diff is exactly the three repaired terms, which now
have full descriptions and NCIT meanings. The semantic diff of
`mc2_model.ttl` is +16/-17 triples, all from those terms. The regenerated
`cckp_portal.ttl` had no semantic change, so its cosmetic reordering was
reverted rather than committed.

**Finding 7: deviated from the Approach.** A canonicalizing serializer was
built and it worked, but it was dropped.
- `rdflib.compare` canonicalization is unusable on `mc2_model.ttl`: a
  1152-item `owl:unionOf` never finished. That left a hand-written 254-line
  Turtle serializer in front of every published schema file.
- `PYTHONHASHSEED` doesn't fix it. owlgen varies even with a fixed seed.
- The user and orchestrator judged that cost too high for a
  review-convenience benefit. Instead, `.gitattributes` marks the three
  generated schema TTLs `linguist-generated` (commit 691b781), and review
  focuses on the `*.linkml.yaml` sources.
- The hand-written `cckp_portal.shacl.ttl` stays visible.

**Findings 5, 6 and 9 (commit 032cd99).**
- Corrected the design page's review-gate claims: only the Program and
  MONDO/UBERON crosswalks are gated. Organizations mint from ROR, and the
  336 Person stubs are `cckp:provisional`.
- Corrected the join slot to `Publication.dataset`.
- Tool counts now read 349 rows / 331 nodes.
- Added the severity split and the 6/6 query count.

**Finding 10 (commit 0f7e00d).** `tissue.csv` Required changed from
`False` to `FALSE` in every row; that is the only column changed. The Source
typo "Sag" became "Sage".

**Verification.**
- `pytest`: 158 passed.
- SHACL on `cckp_kg_full.ttl`: 0 violations and 0 warnings.
- Query checks: 6/6 pass.
- `validate_graph.py --parse-only schema/*.ttl`: all OK.
