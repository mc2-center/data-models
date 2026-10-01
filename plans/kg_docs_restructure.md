# Knowledge graph docs restructure

## Context

`docs/knowledge-graph.md` is 665 lines on a single page. It has 9 numbered
sections and 2 mermaid diagrams, and most of it is long paragraphs, often
with several asides in parentheses per sentence. The user asked for four
things on 2026-09-30:
- Move the major sections onto sub-pages under the Knowledge Graph tab.
- Use tables instead of prose wherever possible.
- Add figures where they illustrate a point and cut text.
- Organize it like governanceDUO's knowledge-graph docs.

governanceDUO's docs use three tiers (`docs/.pages`):

| Tier | governanceDUO page | Character |
|---|---|---|
| Overview | `graph-design.md` (330 lines) | Readable "no predicate names, IRIs or code required". At-a-glance tables, one diagram per concept, numbered sections |
| Technical implementation | `graph-design-implementation.md` | Full depth: classes, predicates, scripts, Make targets, literal SPARQL ("query cookbook") |
| Representation | `knowledge-graph.md` | Each RDF artifact, file by file, with its validation |

Deep material lives under a "Deep reference" nav group.

This repo's site builds its nav from `nav.yml`, which `scripts/hooks.py`
loads wholesale. The hook only overwrites the `Standard Terms` key. A nested
`Knowledge Graph:` section therefore works, and `navigation.indexes` is
already enabled in `mkdocs.yml`. `docs-check.yml` runs
`mkdocs build --strict` with `validation.anchors: warn`, so every internal
link and anchor has to resolve.

## Approach

1. **Replace the single page with a `docs/knowledge-graph/` directory.**
   Titles are proposals:

   | Page | Tier | Content, from current sections |
   |---|---|---|
   | `index.md`: "Overview" | Overview | §1 purpose and non-goals, §2 where it sits (diagram), §3 layers (table), §9 status (table), a "where to look next" table |
   | `model.md`: "Model and identifiers" | Technical | §4 LinkML schemas, class-alignment table, Key→Ref joins (diagram), worked example; §5 namespaces table and IRI minting (decision diagram) |
   | `build.md`: "Build and validation" | Technical | §6 stage pipeline (diagram plus a stage table: target, script, input, output), harmonization and SSSOM, human-review crosswalks, validation (a table of each check with what it catches and its severity), tests |
   | `publishing.md`: "Publishing and deposit" | Technical | §6 publish paths as a table (target, destination, contents), manifest fields (a table, including which nf-osi fields are absent and why), deposit guards (sequence diagram) |
   | `querying.md`: "Querying the graph" | Technical | §7 example queries as a cookbook, each with a one-line question and its result |
   | `federation.md`: "Federation and sagebrain-model" | Technical | §8: SCDM, the MONDO/UBERON crosswalks, D9 (a diagram of the shared `syn:` IRI join) |

2. **Tables first.** Anything that is a list of parallel facts becomes a
   table: namespaces, layers, stages, checks, publish targets, manifest
   fields, crosswalk review gates and status. Prose stays only for
   rationale that doesn't fit a cell, cut to short paragraphs.
3. **Figures: rendered PNGs, not mermaid.** The user found the mermaid
   diagrams illegible (2026-09-30). Figures now follow `figures/STYLE.md`:
   - the SageBrain Home Week deck's visual language and legibility rules,
     as applied in governanceDUO's `docs/assets/graph-design/*.png`;
   - built as `figures/src/*.html`, rendered by `figures/render.py` to
     transparent PNGs under `docs/assets/knowledge-graph/`.

   The page-split task leaves `![alt](...png)` placeholders, each with a
   `<!-- FIGURE SPEC -->` comment. A separate figure task then builds each
   one and reviews it visually against the STYLE.md checklist. The 2
   mermaid diagrams are removed. Planned figures, each replacing
   paragraphs:
   - a layer strip at the top of the Overview (`kg-layers`);
   - where the graph sits;
   - the build pipeline;
   - the Key→Ref join;
   - the IRI-minting decision;
   - the deposit sequence, with its guards and the sentinel;
   - the federation join on `syn:` IRIs;
   - optionally, a worked-example node graph.

   Every diagram must render in mkdocs-material, both light and dark.
4. **Preserve every fact.** Nothing factual is dropped; it moves. Every
   file path, Make target, count and link in the current page must appear
   on some sub-page, or be deliberately cut as redundant and listed in the
   report. Facts are verified against code, as before. No history or
   process narration.
5. **Links.** Update `nav.yml` to a `Knowledge Graph:` section listing the
   pages. Update inbound links: `README.md` points at
   `https://mc2-center.github.io/data-models/knowledge-graph/`, which
   `index.md` keeps valid, and `kg-pipeline/README.md` points at
   `../docs/knowledge-graph.md`, which changes to
   `../docs/knowledge-graph/index.md`. Check whether anything else links to
   the old page.

## Verification

- `mkdocs build --strict` passes with 0 warnings.
- A fact-preservation check: extract every backticked path or target,
  every number and every URL from the old page, and confirm each appears
  in the new pages. List any intentional cuts.
- The Overview page is at most about 200 lines. The total prose word count
  drops substantially; report the before and after.
- Render check: every mermaid block appears in the built HTML as
  `class="mermaid"`, and none has syntax errors (check with the mermaid CLI
  if it's available, otherwise by careful review).
- The orchestrator reviews the diff, then an independent pre-PR review
  runs.

## Process

Store this plan at plans/kg_docs_restructure.md for review before
implementing. After implementing, append an Implementation Report below
this line.

---

## Implementation Report

### Scope change mid-implementation

The orchestrator changed the figures approach partway through: mermaid
blocks were found illegible and were replaced with PNG figures to be
rendered by a separate later task. All mermaid blocks were removed from
the new pages (none were added in their place). Each of the 7 planned
figures, plus a `kg-layers` figure added at the top of the Overview, is
now a `![alt](../assets/knowledge-graph/NAME.png)` reference immediately
followed by an HTML `<!-- FIGURE SPEC: ... -->` comment describing its
nodes/edges/labels, so a separate figure-rendering pass can build the PNG
from the spec alone. Every page still reads on its own without the image,
since the table or prose beside each figure carries the same facts. 8
placeholder PNGs (1x1 transparent) were created under
`docs/assets/knowledge-graph/` so `mkdocs build --strict` passes; they are
meant to be replaced by real renders, not kept.

### Files changed

- **New:** `docs/knowledge-graph/index.md`, `model.md`, `build.md`,
  `publishing.md`, `querying.md`, `federation.md`
- **New (placeholders):** `docs/assets/knowledge-graph/kg-layers.png`,
  `kg-architecture.png`, `kg-build-pipeline.png`, `kg-key-ref-join.png`,
  `kg-iri-minting.png`, `kg-worked-example.png`, `kg-deposit-sequence.png`,
  `kg-federation.png`
- **Deleted:** `docs/knowledge-graph.md` (`git rm`, after the
  fact-preservation check passed)
- **Modified:** `nav.yml` (replaced `Knowledge Graph: knowledge-graph.md`
  with a `Knowledge Graph:` section listing the 6 new pages, in the same
  position after Data Models), `kg-pipeline/README.md` (its
  `../docs/knowledge-graph.md` link now points at
  `../docs/knowledge-graph/index.md`)
- `README.md`'s `https://mc2-center.github.io/data-models/knowledge-graph/`
  link needed no change — `docs/knowledge-graph/index.md` takes over that
  URL under `navigation.indexes`. A repo-wide grep for `knowledge-graph.md`
  found no other inbound references outside `plans/`, which was left alone
  per instructions.

### Page outlines (headings)

**`index.md` — Knowledge graph: Overview** (123 lines)
- 1. What the graph is for
- 2. Where it sits
- 3. The layers
- 4. What's operational today
- Where to look next

**`model.md` — Model and identifiers** (191 lines)
- LinkML schemas
- Class alignment (schema.org / Biolink)
- Foreign keys: "Key" in the model, "Ref" in the graph
- Identifiers and namespaces
- A worked example

**`build.md` — Build and validation** (129 lines)
- The stage pipeline
- Harmonization and SSSOM
- Suggest-mappings and crosswalks (human review, never auto-applied)
- Validation
- Tests

**`publishing.md` — Publishing and deposit** (77 lines)
- Publish paths
- The manifest
- Deposit guards

**`querying.md` — Querying the graph** (67 lines, cookbook only, no
sub-headings beyond the title)

**`federation.md` — Federation and sagebrain-model** (82 lines)
- SCDM and the ontology crosswalks
- The MC2 assay-metadata KG
- The D9 join with governanceDUO
- Where to look next

### Checks (verbatim)

**1. `mkdocs build --strict`**

```
$ /private/tmp/claude-504/mkdocs-venv/bin/mkdocs build --strict -d /private/tmp/claude-504/site-kg
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /private/tmp/claude-504/site-kg
INFO    -  Documentation built in 3.53 seconds
EXIT CODE: 0
WARNING lines: 0
```

Cleanup ran afterward:
`git ls-files --others --exclude-standard -- 'docs/valid_values/*.md' 'modules/*/reference.csv'`
listed 24 `docs/valid_values/*.md` files and 32 `modules/*/reference.csv`
files (pre-existing generated artifacts from an earlier build on this
branch, regenerated by this build too); all were removed, no tracked file
was touched.

**2. Fact-preservation script**

Script: extracted every inline-code span (`` `...` ``), every URL, and
every multi-digit number from `docs/knowledge-graph.md` (its last
committed `HEAD` version), then checked each against the concatenated text
of all 6 new pages (whitespace-normalized on both sides, to tolerate
markdown line-wrapping differences).

```
Code spans: 300 total, 9 missing
  - ' ### Harmonization and SSSOM '
  - " (a CV row's own "
  - ' (a value that matched nothing in its CV — passed through unresolved, never dropped) and '
  - ' - **Synapse** holds the source data: the 5 CCKP View tables ('
  - " That query's own header comment records a real, load-bearing lesson: an earlier draft with three independent "
  - ' as aliases. Two reports come out of every run: '
  - " blocks effectively hung against the full ~330K-triple graph (rdflib's engine handles several independent "
  - 'https://www.synapse.org/Synapse:synNNN...'
  - 's very badly at this size); the single-join-plus- '
URLs: 40 total, 0 missing
Numbers: 18 total, 0 missing
```

All 9 "missing code spans" are regex artifacts, not real gaps: the old
page's `` ``` ``-fenced SPARQL/turtle blocks defeat a naive single-backtick
span regex (it mis-pairs backticks across a triple-backtick fence,
swallowing the prose between two fences as one fake "code span" — e.g.
the heading `### Harmonization and SSSOM` and the prose around the
`OPTIONAL` performance note, both of which sit next to SPARQL fences, and
both of which are verified present in the new pages by direct `grep`).
The one real near-miss, `https://www.synapse.org/Synapse:synNNN...`, is
the same URL as the (present) `https://www.synapse.org/Synapse:synNNN`
plus the old prose's trailing ellipsis — not a distinct fact. 0 URLs and 0
numbers missing, with no normalization tolerance needed for either.

No facts were found to be redundant/cut; everything identified by the
script was traced to either a direct restatement or a deliberate
paraphrase in a new page (e.g., `data/harmonized/*_harmonized.csv`,
`pyshacl`, `schema/cckp_portal.shacl.ttl`, `tests/validate.py`,
`shape:SynapseEntityShape`, `mappings/crosswalks/consortium_to_scdm_program.tsv`,
`kg-pipeline/data_sources.yaml`, `aws s3 sync --delete`, `make
upload-sagebrain-s3 UPLOAD_ARGS=--allow-overwrite`, the counts 349 and
304,990, and the `exact_mappings`/`close_mappings` terms were all
initially missing on a first pass and were added back in).

**3. Line counts and word counts**

| Page | Lines |
|---|---|
| `index.md` | 123 |
| `model.md` | 191 |
| `build.md` | 129 |
| `publishing.md` | 77 |
| `querying.md` | 67 |
| `federation.md` | 82 |
| **Total** | **669** |

Prose word count (fenced code blocks, HTML figure-spec comments, image
lines and table rows stripped before counting):

- Old page (`docs/knowledge-graph.md`, `HEAD`): **3597** words
- New pages combined: **2609** words (a 27% drop)
  - `index.md`: 288, `model.md`: 735, `build.md`: 533,
    `publishing.md`: 416, `querying.md`: 233, `federation.md`: 404

**4. Placeholder-image and mermaid-block check**

Per the orchestrator's scope change, mmdc validation was skipped (no
mermaid blocks remain). Built HTML was checked instead for `class="mermaid"`
occurrences (must be 0) and for how many of the 8 placeholder PNGs each
page actually references:

| Page | `class="mermaid"` count | Distinct placeholder images referenced |
|---|---|---|
| `index.md` | 0 | 2 (`kg-layers.png`, `kg-architecture.png`) |
| `model.md` | 0 | 3 (`kg-key-ref-join.png`, `kg-iri-minting.png`, `kg-worked-example.png`) |
| `build.md` | 0 | 1 (`kg-build-pipeline.png`) |
| `publishing.md` | 0 | 1 (`kg-deposit-sequence.png`) |
| `querying.md` | 0 | 0 |
| `federation.md` | 0 | 1 (`kg-federation.png`) |

All 8 planned figures (the 7 from the plan plus the added `kg-layers`
strip) are referenced exactly once, each with its own FIGURE SPEC comment
for the later rendering task.

**5. `git status --short`**

```
D  docs/knowledge-graph.md
 M kg-pipeline/README.md
 M nav.yml
?? .venv-docs/
?? docs/assets/knowledge-graph/
?? docs/knowledge-graph/
?? figures/
?? plans/kg_docs_restructure.md
```

`.venv-docs/` predates this session (present in the branch's starting git
status). `figures/` (`render.py`, `STYLE.md`, `src/`) also appeared during
this session but was not created by this task — it belongs to the
separate, later figure-rendering task the orchestrator described, and was
left untouched.

### Wrong facts found

None. Every fact in the old page that was cross-checked against
`kg-pipeline/` code (Makefile targets, `build_manifest.py`,
`upload_sagebrain_s3.py`'s deposit guards, `mint_id()`/`mint_iri()` and
`SYNAPSE_ID_RE` in `build_triples.py`, the `queries/` and
`queries/examples/` directory listings, `data_sources.yaml`) matched the
current code exactly. No corrections were needed.

### Cuts

None of substance. Every fact the extraction script found in the old page
was traced into the new pages (see the fact-preservation section above).
The only material removed was narrative framing prose ("Reading this one
node top to bottom...", "As of this writing...") — replaced with the
underlying facts stated directly, per the no-history-narration rule — and
the old page's own 2 mermaid diagrams, which became 2 of the 8 new figure
placeholders (`kg-architecture.png`, `kg-build-pipeline.png`) rather than
being dropped.

## Second pass: tighten the pages and build the figures (2026-09-30)

### Orchestrator review of the page split
The page split works and the tables help, but four problems need fixing:
- **Still verbose.** Prose is only 27% shorter, and table cells run to 30+
  words.
- **The Overview isn't plain.** It keeps code spans and file paths, which
  governanceDUO keeps out of its overview entirely.
- **A regression.** The Components table claims both federation targets
  are human-reviewed. Only the consortium→Program and MONDO/UBERON
  crosswalks are gated.
- **Stale counts.** The latest build (2026-09-29) has `cckp_kg.ttl` at
  304,989 triples, `cckp_kg_full.ttl` at 337,917, and 360,370 distinct
  triples deposited.

### Figure set
These designs, set by the orchestrator, replace the placeholder specs.
The worked-example figure is dropped, because the Turtle snippet already
shows it.

| Figure | Page | Shows |
|---|---|---|
| `kg-layers` | Overview, top | A strip of 4 tiles: **Schema** (the model and portal schema), **Portal graph** (one node per portal record), **Enrichment** (ontology terms, Biolink typing, Data Catalog annotations), **Federation** (SCDM and MONDO/UBERON links). Next to it, a dashed tile: **Assay metadata graph**, marked "access-controlled, published separately". Below, a gold chip, "Deposited to SageBrain Neptune", with a bracket spanning the 4 tiles |
| `kg-architecture` | Overview §2 | Left, sources: "Synapse portal tables", "Synapse Dataset annotations", "MC2 data model + vocabularies". Middle, the 4 layer tiles in a column, each with its colored left edge. Right, consumers: "Synapse distribution folder" and "SageBrain Neptune". Under Neptune, a chip: "joins governanceDUO and sagebrain-model on shared Synapse IDs" |
| `kg-build-pipeline` | Build | A horizontal line of 6 stages: Extract → Harmonize → Build triples → Link and merge → Validate → Publish. Each has its make target as a muted sub-label |
| `kg-key-ref-join` | Model | A Dataset card showing "grant number: CA209891", with an arrow labeled "grant reference" to a Grant card. A muted note: "matched on the Grant's own number; unmatched values stay as text" |
| `kg-iri-minting` | Model | A decision flow. "Row has a Synapse ID?": yes → "Synapse's own URL"; no → "Pipeline placeholder IRI". Separately, "vocabulary value confirmed to have no ontology term" → "provisional term IRI" |
| `kg-deposit-sequence` | Publishing | A horizontal line of 6 steps: Count triples → Date is free? → Sync data (replace) → Check load path → Upload manifest (trigger) → Neptune loads. Steps 2 and 4 are marked as guards that stop the deposit |
| `kg-federation` | Federation | One Synapse-ID node in the center. On its left, "CCKP graph: Dataset facts"; on its right, "governanceDUO graph: access facts". A chip: "Same ID, separate owners — CCKP never asserts governance types" |

### Second-pass report (2026-09-30)

**Fixes applied**

1. The "human-reviewed" regression is fixed. `index.md`'s Components table
   and Overview text no longer claim both federation targets are
   human-reviewed. The correct, asymmetric gating (Program edges
   human-reviewed; Organization edges mint from a ROR id every run; Person
   stubs flagged provisional instead) now appears on `index.md` (plain
   language), `build.md`'s crosswalk table (unchanged, was already
   correct), and `federation.md`'s Partner table + note (unchanged, was
   already correct). A repo-wide grep of all 6 pages for
   `human-reviewed`/`reviewed before` found no other incorrect claim.
2. Counts updated to the 2026-09-29 build, verified against code:
   - Row counts confirmed against `kg-pipeline/data_sources.yaml`: 1141
     Datasets, 4773 Publications, 349 Tool rows, 160 Grants, 10
     EducationalResources, 966 DataCatalog rows.
   - Triple counts confirmed by parsing `kg-pipeline/data/rdf/cckp_kg.ttl`
     and `cckp_kg_full.ttl` with `kg-pipeline/.venv/bin/python` + rdflib:
     304,989 and 337,917 respectively — exact matches.
   - The deposited `void:triples` figure (360,370) was taken as given per
     the task instructions (only the row counts and the two `.ttl` triple
     counts were asked to be independently confirmed by parsing).
   - All three now live in one "Last verified build" table on the
     Overview only; `querying.md` and `model.md` no longer repeat the old
     stale 340,786 total — they link to the Overview instead. The
     cookbook's own per-query row counts (174/394/26) were re-run live
     against `cckp_kg_full.ttl` and updated (174, was 175; 394 and 26
     unchanged).

**Overview (`index.md`)**: rewritten in plain language — 0 code spans
(`grep -c` verified), no file paths, no `cckp:`/`rdf:` names, no make
targets, 78 lines (target ≤90). The old "Output" column and all file
names moved to `build.md`'s stage table and `model.md`'s namespace table;
the old 9-row layers table collapsed to one paragraph backed by the
`kg-layers` figure.

**Figures**: all 7 figures from the plan's Figure set table are referenced
exactly once, each as `![one plain sentence](../assets/knowledge-graph/NAME.png)`
with no `<!-- FIGURE SPEC -->` comment (all removed). `kg-worked-example`
is gone from `model.md`; the Turtle snippet stays. All 7 PNGs already
exist under `docs/assets/knowledge-graph/` (built by the parallel figures
task — no placeholders were needed).

**Word and line counts (before -> after)**

| Page | Words before | Words after | Lines before | Lines after |
|---|---|---|---|---|
| `index.md` | 288 | 267 | 123 | 78 |
| `model.md` | 735 | 365 | 191 | 118 |
| `build.md` | 533 | 292 | 129 | 91 |
| `publishing.md` | 416 | 185 | 77 | 58 |
| `querying.md` | 233 | 188 | 67 | 61 |
| `federation.md` | 404 | 249 | 82 | 56 |
| **Total** | **2609** | **1546** | **669** | **462** |

Prose dropped 40.7% (target: ≥40%, to ≤~1550). Every table cell checked
programmatically is ≤15 words (extra detail moved to one sentence below
the table, or cut — see below). Every prose paragraph checked
programmatically is ≤3 sentences.

**Checks (verbatim)**

1. `mkdocs build --strict`:
```
$ /private/tmp/claude-504/mkdocs-venv/bin/mkdocs build --strict -d /private/tmp/claude-504/site-kg2
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /private/tmp/claude-504/site-kg2
INFO    -  Documentation built in 3.47 seconds
EXIT CODE: 0
WARNING lines: 0
```
   No PNG placeholders were needed — all 7 figures already existed as
   real (non-1x1) files from the parallel figures task. Cleanup ran
   afterward: `git ls-files --others --exclude-standard -- 'docs/valid_values/*.md' 'modules/*/reference.csv'`
   listed 24 `docs/valid_values/*.md` files and 32 `modules/*/reference.csv`
   files (regenerated build artifacts); all removed, no tracked file
   touched.
2. See the word/line table above.
3. `grep -c '`' docs/knowledge-graph/index.md` → `0`.
4. Cuts and delegations: see below.

**Cut and delegation list**

Delegated to the kg-pipeline README (pure command/flag/file reference,
now linked from `index.md`, `model.md` and `build.md`):
- `model.md`: the exact `mint_id()`/`mint_iri()` fallback-field and regex
  logic (`FALLBACK_ID_FIELD`, `SYNAPSE_ID_RE`) — the figure now carries
  the decision tree, prose just points at the README.
- `build.md`: `suggest_mappings.py`'s `choose_registry()` per-CV registry
  selection, and the full file-by-file "Consuming the graph" picture.

Cut outright (not preserved elsewhere, listed for review):
- `index.md`: the old doesn't-do table's "reason over schema-level
  ontology mappings" row (still covered in `model.md`'s Class alignment
  section, just not repeated on the Overview); the old 9-row layers
  table's Output column and file names; the 8-row "what's operational"
  status table (replaced by the one-sentence federation-gating note);
  the closing pointer to `modules/shared/annotationProperty.csv`
  (redundant with `model.md`'s Foreign Keys section).
- `model.md`: the LinkML schema table's regeneration-timing prose and
  `schema/mc2_model_prefixes_report.md` mention; the Namespace table's
  "Examples" column (redundant with the worked example below it); the
  `cckp_join: "TargetClass.target_field"` annotation-syntax detail.
- `build.md`: the DataCatalog stage's second Make target
  (`combined-kg`/`merge-datacatalog`), its design-doc link, and the
  `cckp_kg_with_datacatalog.ttl` intermediate filename (folded into one
  row); the SHACL section's `rdfs:range`-union-typing rationale and the
  `plans/cckp_shacl_shape_gaps.md` link; `build_triples.py`'s per-field
  literal-mismatch print note; the private assay layer's
  fixture-only-tests detail in Tests.
- `publishing.md`: the live ACL-refusal check description for
  `make publish-mc2-assay` (that it resolves the target's effective ACL
  and refuses on public/authenticated access) — this is a real safety
  behavior, not pure command reference, so flagging it here rather than
  silently dropping it; the manifest table's "written twice, once as
  sentinel once as `data/_provenance.ttl`" detail.
- `federation.md`: the redundant restatement of what SCDM is (already in
  the Partner table); "not a domain ontology at all, and not one
  kg-pipeline builds toward" framing in the D9 section.
- `querying.md`: the specific "~330K-triple graph" figure in the
  performance-note blockquote, replaced with "the full merged graph" to
  avoid a second stale count needing its own future update.

No wrong facts were found beyond the human-reviewed regression and the
stale counts already covered above.

### Pre-PR review fixes (2026-09-30, continued)

The independent pre-PR review found fact errors and lost content from the
second pass. All 11 findings were fixed, each re-verified against
`kg-pipeline/` code (the orchestrator had already applied fixes for the
"index.md doesn't include people" claim's replacement wording context and
the `publish-mc2-assay` ACL-check row before this pass resumed; this pass
built on those files and finished the remaining items).

1. **index.md, "doesn't include people."** Reworded: the graph does carry
   provisional SCDM Person stubs (`link_scdm.py`); the real limit is that
   the portal's own Person table isn't extracted. The doesn't-do table row
   now reads "Extract the portal's own Person table" / "Not pulled in yet;
   investigators and contributors become provisional stubs instead."
2. **index.md/federation.md, crosswalk-approval scope.** Verified
   `scripts/link_sagebrain.py`'s `load_crosswalk(path, min_confidence="high")`:
   it keeps only `confidence == "high"` rows, with no `reviewed` check at
   all. Reworded both pages: the Program and disease/tissue crosswalks
   into the *public* graph wait for human approval; the private
   assay-metadata layer's links into sagebrain-model apply automatically
   on an exact label match, no review. Added a row to index.md's status
   table distinguishing "public graph" vs "private layer" crosswalk
   status, and a note to federation.md's Partner table gate cell
   ("automatic, not reviewed").
3. **model.md, Key vs Ref.** Confirmed against
   `schema/cckp_portal.linkml.yaml` (10 `cckp_join` annotations, all on
   portal columns — `grantNumber`, `pubMedId`, `dataset`/`datasets` —
   never a model "Key" field) and `schema/mc2_model.linkml.yaml` (0
   `cckp_join` occurrences). Rewrote the section to 3 sentences: the
   model's Key convention, that `cckp_join` marks portal columns only,
   and that a model Key field (e.g. `Biospecimen Key`) stays a plain
   literal unless a separate stage (`link_sagebrain.py`) resolves it. Added
   a 3-row table mapping the real `cckp_join` columns to their `Ref`
   edges.
4. **model.md, key-ref-join alt text.** Replaced with "A Dataset's grant
   number matched to its Grant, next to an unmatched value that stays as
   plain text," matching the plan's actual figure design.
5. **model.md, fallback logic.** Confirmed in `scripts/build_triples.py`:
   `IDENTIFIER_FIELD` (`Dataset`: `datasetId`, `Grant`: `grantId`) and
   `FALLBACK_ID_FIELD` (`Publication`: `pubMedId`, else hash of
   `publicationTitle`+`doi`; `Tool`: `toolName`, else hash of
   `description`+`downloadUrl`; `EducationalResource`:
   `internalIdentifier`/`alias`, else hash of `title`), the synthetic-id
   form `"synthetic-" + sha1(...)[:16]`, and `PROVISIONAL_NS =
   "https://w3id.org/mc2-center/cckp-portal/terms/"`. Restored all of this
   as one short table plus two sentences, removing the false "documented
   in the kg-pipeline README" claim.
6. **model.md, namespace table.** Restored the Base IRI column, verified
   against the schemas and scripts: `cckp:`/`mc2:` from the LinkML
   schemas' own `prefixes:` blocks, `biolink:`
   (`scripts/build_triples.py`'s `BIOLINK` namespace), `sagecdm:`
   (`scripts/link_scdm.py`), `sagebrain:` (`scripts/link_sagebrain.py`),
   `shape:` (`schema/cckp_portal.shacl.ttl`'s own `@prefix`), the
   `data/`/`terms/` placeholder bases (`DATA_NS`/`PROVISIONAL_NS` in
   `build_triples.py`), and `gov:` = `https://w3id.org/synapse/governance#`
   (confirmed against governanceDUO's own
   `governance_graph_export/governance_graph.ttl`), added back as the one
   namespace never asserted here.
7. **publishing.md, `make publish-portal-kg`.** Confirmed in
   `scripts/publish_kg.py`: the `portal` profile's `SUBDIRS = ["raw",
   "harmonized", "rdf"]` uploads only those three subfolders; `mc2-assay`
   is a fully separate profile/data_dir (`data/mc2_assay`) never touched
   by the portal publish. Row now reads
   "`data/{raw,harmonized,rdf}/` only — never `data/mc2_assay/`."
8. **publishing.md, guards table.** Verified the real order and checks in
   `scripts/upload_sagebrain_s3.py`: date-free check, then a triple count
   (zero-triple files abort the deposit), then `sync --delete`, then a
   post-sync check that every uploaded key ends `.ttl` and the exact key
   set matches what was staged. Rebuilt the table to 3 guards in that
   order (dropping "replace, don't add" as its own row, since it's a
   mechanism with no abort condition, not a gate — it's now one sentence
   between the table and the manifest-upload note instead). Renamed the
   misleading "Escape hatch" column to "Bypass" and set it accurately:
   only the date guard has one (`--allow-overwrite`); the other two have
   none.
9. **Figure alt texts.** `publishing.md`'s deposit alt text now describes
   the linear strip: date check, triple count, sync, load-path check,
   manifest upload, Neptune load. `build.md`'s stage-pipeline alt text now
   describes Extract → Harmonize → Build triples → Validate → Link, merge
   and check → Publish, with no mention of the model CSV or the manifest,
   matching the figure's new design.
10. **build.md, Extract row.** Filled the Script cell with
    `scripts/extract_cckp_tables.py`, confirmed as the script the
    Makefile's `extract` target actually runs.
11. **querying.md, history narration.** Removed the "an earlier draft ...
    hung" anecdote from the performance note; it now states the
    `OPTIONAL`-block performance characteristic directly, without
    narrating the draft history.

**Checks (verbatim)**

```
$ /private/tmp/claude-504/mkdocs-venv/bin/mkdocs build --strict -d /private/tmp/claude-504/site-kg4
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /private/tmp/claude-504/site-kg4
INFO    -  Documentation built in 3.65 seconds
EXIT CODE: 0
WARNING lines: 0

$ grep -c '`' docs/knowledge-graph/index.md
0
```

Generated `docs/valid_values/*.md`/`modules/*/reference.csv` artifacts
were removed after the build, as before; `git status --short` matches the
pre-existing scope (only `docs/knowledge-graph/`, the `docs/knowledge-graph.md`
deletion, `nav.yml`, and `kg-pipeline/README.md` touched).

While tightening the `publish-mc2-assay` ACL-check row back to the ≤15-word
cell style, its detail moved to one sentence below the Publish paths table
instead — the same "extra detail moves to a sentence under the table"
convention used elsewhere on these pages.
