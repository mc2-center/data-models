# kg-pipeline manifest deposit fields

## Context

SageBrain's graph-connection check, and anyone re-pinning a snapshot, read
each deposited graph's own VoID/PROV manifest. The ALS and NF manifests
carry `void:triples`, a snapshot date and deposit-run fields. The CCKP
manifest carries only the build half:

- `prov:Activity, void:Dataset`
- `prov:generatedAtTime`
- `prov:used` (the commit)
- `cckp:gitCommit`, `cckp:gitRef`, `cckp:portal`
- `void:dataDump`

As a result, the demo check that looks for `void:triples` misses CCKP.

**Where the NF fields come from.** nf-osi/kg-pipeline's
`.github/workflows/deposit-sagebrain.yml` renders them in its "Generate
manifest" step, after its "Verify snapshot" step. The verify step streams
every file under the snapshot's `data/` and sums the triples. It refuses to
deposit when a file isn't Turtle, parses to zero triples, or `data/rdf/` is
empty. The manifest template emits:

- `prov:Activity, void:Dataset` and `prov:generatedAtTime` (the build time)
- `prov:wasAssociatedWith` (the build run URL)
- `prov:used` (the commit)
- `nf:portal`
- `nf:snapshotDate` (`xsd:date`)
- `nf:gitRef` and `nf:gitCommit`
- `nf:buildRunId` and `nf:depositRunId`
- `nf:depositedAtTime` (`xsd:dateTime`)
- `nf:depositedBy` (the deposit run URL)
- `void:triples`
- `void:dataDump <{prefix}/data/>`

**This repo's equivalent.** Here the deposit step is the local
`kg-pipeline/scripts/upload_sagebrain_s3.py` (`make upload-sagebrain-s3`).
It calls `build_manifest()` before it has counted anything, so it never
emits a triple count, snapshot date or deposit time. It also sets
`void:dataDump` to `{prefix}/`, whereas NF uses `{prefix}/data/`, the
actual load path.

The live CCKP snapshot (`cckp/2026-09-15/`) was deposited from the
`aws-upload-pipeline` branch. Fixing the code doesn't change that
snapshot; a re-deposit does.

## Approach

1. **`build_manifest()`** gets three optional keyword arguments, `triples`,
   `snapshot_date` and `deposited_at`, each emitted only when given:
   - `void:triples` as `xsd:integer`
   - `cckp:snapshotDate` as `xsd:date`
   - `cckp:depositedAtTime` as `xsd:dateTime`

   These mirror nf's property local names in this pipeline's own `cckp:`
   namespace, the same way `cckp:gitCommit`/`cckp:gitRef` mirror
   `nf:gitCommit`/`nf:gitRef`. `make manifest`, the build-only local
   manifest, stays as it is.
2. **`upload()`** in `upload_sagebrain_s3.py`:
   - Before rendering the manifest, count the triples in every file it's
     about to place under `data/` (the `schema/*.ttl` files and
     `cckp_kg_full.ttl`), excluding `_provenance.ttl`, as NF does.
   - Refuse to deposit (`SystemExit`) if any of those files parses to zero
     triples.
   - Pass `triples`, `snapshot_date` (the prefix's date) and
     `deposited_at` (now, UTC).
   - Point `void:dataDump` at `{prefix}/data/`.
   - Print the per-file counts and the total.
3. **No invented CI fields.** Deposit is local, and there's no build or
   deposit GitHub Actions run, so `buildRunId`, `depositRunId`,
   `wasAssociatedWith` and `depositedBy` are omitted rather than faked.
   Document this in the module docstrings.
4. **Tests:** cover each new `build_manifest` field, and that its absence
   emits nothing. Cover the upload computing the triple total across
   exactly the placed `data/` files, refusing a zero-triple file,
   `dataDump` ending in `/data/`, and `_provenance.ttl` being identical to
   `manifest.ttl`.
5. **Docs:** update the manifest description in `kg-pipeline/README.md`
   and in `docs/knowledge-graph.md`'s Stage 6/manifest mentions.
6. **Stale-object guard.** The user added this on 2026-09-29. It mirrors
   `deposit-sagebrain.yml`'s three guards, because a stray object under the
   prefix fails the whole Neptune load:
   - Refuse to deposit to a date prefix that already holds objects, unless
     `--allow-overwrite` is given.
   - Stage the `data/` tree locally and upload it with
     `aws s3 sync ... --delete`, so a re-deposit replaces the earlier
     snapshot instead of adding to it.
   - Before uploading the `manifest.ttl` sentinel, list `{prefix}/data/`
     and refuse if it's empty, holds any non-`.ttl` key, or its object
     count doesn't match the staged file count.

## Verification

- `make test` passes.
- `make upload-sagebrain-s3` with `--dry-run` produces a manifest with
  `void:triples` equal to an independent rdflib count of the mirrored
  `data/**/*.ttl`, a `cckp:snapshotDate` matching the prefix date, and
  `void:dataDump <.../data/>`.
- The d5-style query `SELECT ?t WHERE { ?d a void:Dataset ; void:triples ?t }`
  returns one row against the dry-run `data/_provenance.ttl`.

## Process

Store this plan at plans/kg_manifest_deposit_fields.md for review before
implementing. After implementing, append an Implementation Report below this
line.

## Implementation Report

### Files changed

- `kg-pipeline/scripts/build_manifest.py` — `build_manifest()` gained
  three optional keyword arguments, `triples`, `snapshot_date` and
  `deposited_at`, each emitted only when given (`void:triples` as
  `xsd:integer`, `cckp:snapshotDate` as `xsd:date`,
  `cckp:depositedAtTime` as `xsd:dateTime`). `make manifest`/`full-kg`
  never pass them, so the build-only local manifest is unchanged. Module
  and function docstrings now state which nf-osi fields are deliberately
  absent (`buildRunId`, `depositRunId`, `wasAssociatedWith`,
  `depositedBy`) and why — this deposit is a local script invocation,
  never a GitHub Actions run.
- `kg-pipeline/scripts/upload_sagebrain_s3.py` —
  - Added `count_triples()` (rdflib parse + `len(graph)`) and
    `aws_s3_ls()` (captures `aws s3 ls [--recursive]` stdout, the one aws
    call whose output matters rather than just its exit code).
  - `upload()` now: (1) refuses an occupied `{prefix}/` date unless
    `--allow-overwrite`, skipped entirely in `--dry-run`; (2) counts
    triples in every file about to land under `data/` (schema/*.ttl +
    `cckp_kg_full.ttl`, never `_provenance.ttl`) before rendering the
    manifest, refusing a zero-triple file; (3) stages all `data/` files
    into one local directory and, in real mode, uploads them with a
    single `aws s3 sync <staging>/data/ {prefix}/data/ --delete` (dry-run
    still mirrors file-by-file into `--dry-run DIR/<portal>/<date>/`,
    unchanged in effect); (4) after the sync, lists `{prefix}/data/`
    `--recursive` and refuses (without ever uploading `manifest.ttl`) if
    the listing is empty, any key isn't `.ttl`, or the count doesn't
    match what was staged; (5) uploads `manifest.ttl` last as the
    sentinel, via `aws s3 cp`. `void:dataDump` now points at
    `{prefix}/data/`, not the bare `{prefix}/`. `--allow-overwrite` is a
    new CLI flag, plumbed through to `upload()`.
- `kg-pipeline/test/test_build_manifest.py` — added tests for each new
  field's presence when given and absence when not (`triples`,
  `snapshot_date`, `deposited_at`).
- `kg-pipeline/test/test_upload_sagebrain_s3.py` — rewritten around a
  `_rig_aws()` helper that fakes `aws_s3_ls`/`run_aws` (no real
  subprocess/network calls) and records call order. Fixture content
  changed from a comment-only placeholder to real one-triple Turtle
  (`MINIMAL_TURTLE`), since empty/placeholder files now fail the
  zero-triples guard. New/updated tests cover: occupied-date refusal;
  `--allow-overwrite` and `--dry-run` both proceeding despite an occupied
  date; the sync targeting `{prefix}/data/` with `--delete`; call order
  (ls, sync, ls --recursive, cp manifest last); a stray non-`.ttl` key
  and an object-count mismatch each refusing without ever calling `cp`
  for the manifest; an empty post-sync listing refusing; the manifest's
  triple total matching the staged files; and the existing dry-run/
  zero-triple/missing-file/missing-aws-CLI tests, updated for the new
  fixtures and code paths.
- `kg-pipeline/Makefile` — `upload-sagebrain-s3` target comment now notes
  the occupied-date refusal and the `sync --delete` replace semantics.
- `kg-pipeline/README.md` — updated the `make upload-sagebrain-s3` command
  summary and the `scripts/` file listing (`build_manifest.py` and
  `upload_sagebrain_s3.py` entries) to describe the new manifest fields
  and the overwrite/replace/Turtle-only-check behavior.
- `docs/knowledge-graph.md` — updated the layer table's Manifest row and
  section 6's `make upload-sagebrain-s3` publish-path bullet to describe
  the triple count, snapshot date, deposit time, `void:dataDump` load-path
  target, the occupied-date refusal/`--allow-overwrite`, the
  `sync --delete` replace semantics, and the post-sync Turtle-only check.

### Deviations from the plan

- The plan's step 2 said "count the triples... Refuse to deposit
  (SystemExit) if any of those files parses to zero triples," without
  specifying non-Turtle/parse-error handling the way nf's workflow does
  (stray non-`.ttl` files, unparseable content). Only the zero-triples
  case is guarded explicitly here; a genuinely malformed Turtle file
  still fails, just via rdflib's own parser exception rather than a
  custom message — matching the plan's literal wording, not nf's fuller
  "Verify snapshot" step.
- The later-added scope (three nf-osi deposit guards: occupied-date
  refusal, `sync --delete` replace, post-sync Turtle-only check) replaced
  the original per-file `aws s3 cp` uploads for `data/` with a
  stage-then-sync approach. `manifest.ttl` itself is still uploaded with
  a single `aws s3 cp` as the last call, unchanged.
- `upload()` gained a new `allow_overwrite=False` parameter and `main()`
  a new `--allow-overwrite` flag; neither existed in the original spec's
  file/flag list.

### Check results

**1. `pytest -q`:**

```
173 passed, 1 warning in 26.41s
```

(warning is a pre-existing, unrelated `rdflib` boolean-parsing warning in
`test_build_triples_tool.py`.)

**2. Dry run** — `.venv/bin/python scripts/upload_sagebrain_s3.py --dry-run /private/tmp/claude-504/deposit-dry --date 2026-09-29`:

```
Counting triples under data/:
  schema/cckp_portal.shacl.ttl: 160
  schema/cckp_portal.ttl: 1,178
  schema/mc2_model.ttl: 53,559
  schema/sagecdm.ttl: 802
  data/rdf/cckp_kg_full.ttl: 340,786
  total: 396,485
data/ (6 file(s), mirrored) -> /private/tmp/claude-504/deposit-dry/cckp/2026-09-29/data/
./manifest.ttl -> /private/tmp/claude-504/deposit-dry/cckp/2026-09-29/manifest.ttl  (sentinel - triggers the load)
Done (dry run): /private/tmp/claude-504/deposit-dry/cckp/2026-09-29/  (would be s3://app-prod-neptune-neptunedatabucketb8719d9a-jfo3bsfisgfn/cckp/2026-09-29)
```

`manifest.ttl`:

```turtle
@prefix cckp: <https://w3id.org/mc2-center/cckp-portal/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

cckp:kgBuild_17aeae3ab844e7e9b7872ba7a2d8cd8639dc1da0 a void:Dataset,
        prov:Activity ;
    void:dataDump <s3://app-prod-neptune-neptunedatabucketb8719d9a-jfo3bsfisgfn/cckp/2026-09-29/data/> ;
    void:triples 396485 ;
    prov:generatedAtTime "2026-09-29T20:53:03.144235+00:00"^^xsd:dateTime ;
    prov:used <https://github.com/mc2-center/data-models/commit/17aeae3ab844e7e9b7872ba7a2d8cd8639dc1da0> ;
    cckp:depositedAtTime "2026-09-29T20:53:03.143814+00:00"^^xsd:dateTime ;
    cckp:gitCommit "17aeae3ab844e7e9b7872ba7a2d8cd8639dc1da0" ;
    cckp:gitRef "kg-manifest-deposit-fields" ;
    cckp:portal "cckp" ;
    cckp:snapshotDate "2026-09-29"^^xsd:date .
```

Independent rdflib sum over the mirrored `data/**/*.ttl`, excluding
`_provenance.ttl`: **396485** — matches `void:triples` above exactly.

**3. `void:Dataset` query against `data/_provenance.ttl`:**

```
(rdflib.term.URIRef('https://w3id.org/mc2-center/cckp-portal/kgBuild_17aeae3ab844e7e9b7872ba7a2d8cd8639dc1da0'),
 rdflib.term.Literal('396485', datatype=rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#integer')),
 rdflib.term.URIRef('s3://app-prod-neptune-neptunedatabucketb8719d9a-jfo3bsfisgfn/cckp/2026-09-29/data/'))
```

**4. `cmp manifest.ttl data/_provenance.ttl`:** no output — the files are
byte-identical.

### Notes / things to flag

- `upload()`'s default `tmp_root="."` (unchanged, pre-existing) means
  `manifest.ttl`/`_provenance.ttl` are written into the current working
  directory by default — which, for this repo, is `kg-pipeline/`, where
  both files happen to already be tracked in git. Running the dry-run
  check as specified (no `--tmp-root` CLI flag exists) overwrote those
  two tracked files each time; they were restored via
  `git checkout -- kg-pipeline/manifest.ttl kg-pipeline/_provenance.ttl`
  after every run in this session, and the final `git status` is clean
  apart from the intended source/doc/plan changes. This is pre-existing
  behavior, not introduced by this change, and was left as-is per scope.
- Everything above ran with `--dry-run` only; no real `aws`/AWS credentials
  were used, and nothing was pushed, committed, or branch-switched.

### Orchestrator review (2026-09-29)
- **Bug fixed: the first deposit to a new date would crash.** On a prefix
  with no objects, `aws s3 ls` exits 1 and prints nothing; nf's workflow
  runs it as `aws s3 ls ... || true` for that reason. The new
  `aws_s3_ls()` used `check=True`, so the "date is free" case raised
  `CalledProcessError`. The tests hid this because they mocked
  `aws_s3_ls` itself. It now treats exit 1 with no output as empty and
  still raises on any other failure. Subprocess-level tests cover both
  paths.
- **Independent dry-run check.** Ran it with `--date 2026-09-29`. The
  manifest reports `void:triples 396485`, and an rdflib sum over the
  mirrored `data/**/*.ttl` (excluding `_provenance.ttl`) is also 396,485.
  `void:dataDump` ends in `/data/`, and the snapshot date is `2026-09-29`.
- The first version of `void:triples` summed per-file counts, as nf's
  verify step does. That overcounts here, because `cckp_kg_full.ttl`
  already merges `mc2_model.ttl` and `cckp_portal.ttl`. The pre-PR review
  changed it to count distinct triples across the deposited files; see
  that section below.

### Pre-PR review fixes (2026-09-29)
The review found no path that uploads `manifest.ttl` without passing every
guard, and found that `sync --delete` is always scoped to `{prefix}/data/`.
Its findings and what was done:

1. **Medium: `void:triples` double-counted.** The schema files are also
   merged into `cckp_kg_full.ttl`. It now counts distinct triples across
   the deposited files, which is what Neptune stores. The dry run gives
   363,253; the per-file sum was 396,485. An independent rdflib union
   agrees.
2. **Medium: `--date` wasn't validated.** Anything that isn't a real
   YYYY-MM-DD date is now refused before any S3 call.
3. **Low: the docs called `SAGEBRAIN_BUCKET` required, but it defaults to
   the prod bucket.** The default is deliberate, from an earlier commit
   that added "default SAGEBRAIN_BUCKET". The docstring, CLI help,
   Makefile, README and CLAUDE.md now say it deposits to prod by default.
   Also added `UPLOAD_ARGS` to `make upload-sagebrain-s3`, so
   `--allow-overwrite`, `--date` and `--dry-run` can be passed through make.
4. **Low: the post-sync check compared only suffixes and the count.** It
   now compares exact keys against the staged set.
5. **Low: dry runs left files from earlier runs in the mirror.** The
   mirror directory is now cleared first.
6. **Low: exit 1 with stderr had no test.** It still fails safe, and a
   test now covers it.

The test fake for `aws s3 ls --recursive` returned keys relative to the
sync source. The real CLI returns bucket-relative keys
(`<portal>/<date>/data/...`), so the fake was changed to match. 184 tests
pass.
