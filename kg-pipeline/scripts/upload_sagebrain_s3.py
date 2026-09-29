"""Local equivalent of nf-osi/kg-pipeline's
.github/workflows/upload-sagebrain-s3.yml: publish this build's graph to
the SageBrain Neptune S3 data bucket, per
https://github.com/Sage-Bionetworks-IT/sagebrain-infra#2-upload-data-to-s3.

Data is stored under a portal-scoped, date-partitioned prefix:

    s3://<bucket>/<portal>/YYYY-MM-DD/
        data/schema/*.ttl     <- load path: ontology + shapes
        data/rdf/cckp_kg_full.ttl  <- load path: the graph itself
        data/_provenance.ttl  <- load path: copy of the manifest, queryable lineage
        manifest.ttl          <- trigger sentinel, uploaded LAST, outside the load path

Everything Neptune should load must sit under data/ and be Turtle - the
bulk loader takes a literal S3 prefix (no glob, no extension filter) and
parses every object under it as Turtle, so a single stray non-RDF object
fails the entire snapshot load. manifest.ttl is therefore written twice:
once at the top level as the sentinel Neptune's loader watches for
(deliberately kept OUTSIDE data/, so it's never itself parsed as graph
data), and identically as data/_provenance.ttl so its own prov:/void:
triples still land in the graph.

Three guards mirror nf-osi/kg-pipeline's own deposit workflow, in order:

1. **The date must be free.** Before anything is staged, `aws s3 ls
   {prefix}/` must come back empty, or the deposit refuses (SystemExit) -
   a re-deposit on an already-used date is silent data loss otherwise.
   Pass --allow-overwrite to replace it deliberately. Skipped entirely in
   --dry-run mode, like every other aws call below.
2. **Replace, don't add.** Every file that belongs under data/ is staged
   into one local directory first, then uploaded with a single `aws s3
   sync <staging>/data/ {prefix}/data/ --delete`, unfiltered - exactly
   nf's own sync - so a second deposit on the same date fully replaces the
   first, including any file renamed or dropped since, rather than a
   file-by-file `cp` that would leave stale objects behind.
3. **The load path must be Turtle-only before the sentinel.** After the
   sync, `aws s3 ls --recursive {prefix}/data/` is checked against what
   was just staged: refuses (SystemExit), without ever uploading
   manifest.ttl, if the listing is empty, any key isn't `.ttl`, or the
   object count doesn't match. Only then does `aws s3 cp manifest.ttl
   {prefix}/manifest.ttl` run, as the last call - failOnError=TRUE means
   one stray or missing object fails the *entire* snapshot load, and this
   is the last chance to catch that before the sentinel triggers it.

Deliberately narrower than the upstream workflow's `aws s3 sync data/rdf/`:
that pipeline's data/rdf/ only ever holds final per-table graphs, but this
one also accumulates intermediate/merge-stage artifacts there (Dataset.ttl,
cckp_kg.ttl, cckp_kg_with_datacatalog.ttl, ...) - only the single final
merged graph, data/rdf/cckp_kg_full.ttl, is uploaded, matching
`make deploy-kg`'s existing scope for the Synapse publish path.

schema/*.ttl, by contrast, is uploaded in full every run, matching upstream
exactly (all of schema/ontology.ttl + shapes.ttl, unconditionally) even
though two of our four files - mc2_model.ttl and cckp_portal.ttl - are
*also* already merged into cckp_kg_full.ttl itself (build_triples.py's own
--merge-with, unlike upstream's RML stage, which never merges its ontology
into instance output). That overlap is real but harmless (duplicate
triples are a no-op once loaded, since RDF is a set) - matching upstream's
"schema/ is always the canonical, complete TBox source" convention was
chosen over trimming it down to just the non-redundant sagecdm.ttl +
cckp_portal.shacl.ttl, since both reach the identical graph in Neptune.

Before anything is uploaded, every file about to land under data/ (the
schema/*.ttl files and cckp_kg_full.ttl - not _provenance.ttl, which is a
copy of the manifest itself) is parsed with rdflib and its triples
counted, like nf-osi/kg-pipeline's own "Verify snapshot" step. A file
that parses to zero triples aborts the deposit (SystemExit) rather than
publishing a snapshot Neptune would silently under-load. manifest.ttl's
void:triples is the number of distinct triples across those files (they
overlap - cckp_kg_full.ttl already merges the schema), which is what
Neptune holds once the snapshot is loaded, and void:dataDump points at `{prefix}/data/`
- the actual Neptune load path - not the bare `{prefix}/`.

Deliberately absent from that manifest, even here: nf-osi's `buildRunId`,
`depositRunId`, `wasAssociatedWith` and `depositedBy` all name a GitHub
Actions run. This deposit is a local script invocation, not a CI job, so
there's no such run to point at - see build_manifest.py's own docstring
for the full rationale.

No CI/OIDC role assumption - run this with whatever AWS credentials your
shell already has configured (SSO profile, env vars, ~/.aws/credentials).

Requires the `aws` CLI on PATH and these already-built inputs:
    make schema     (schema/*.ttl)
    make full-kg    (data/rdf/cckp_kg_full.ttl)

Usage:
    export SAGEBRAIN_BUCKET=<bucket-name>       # optional - defaults to the
                                                  # prod bucket (SAGEBRAIN_BUCKET below)
    export SAGEBRAIN_PORTAL=cckp                 # optional, default: cckp
    export AWS_REGION=us-east-1                  # optional, default: us-east-1
    python scripts/upload_sagebrain_s3.py

--dry-run [DIR] skips `aws` entirely and mirrors the exact prefix layout
that would be uploaded into a local directory instead (default:
sagebrain_s3_dry_run/) - useful for inspecting the output shape, or for a
first run before real bucket credentials/name are available. --bucket is
still required in dry-run mode (it's part of the mirrored path), but
doesn't need to be a real bucket. It also skips the "date must be free"
guard above, since nothing is at risk of being silently overwritten
locally.

--allow-overwrite lets a deposit replace an existing snapshot for the
same --date instead of refusing - opt-in, since the sync this runs is
`--delete`d and would otherwise silently drop whatever the first deposit
left behind.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import rdflib

from build_manifest import DEFAULT_PORTAL, DEFAULT_REPO_URL, build_manifest, git_info

FULL_KG_PATH = os.path.join("data", "rdf", "cckp_kg_full.ttl")
SCHEMA_DIR = "schema"
DEFAULT_REGION = "us-east-1"
SAGEBRAIN_BUCKET = "app-prod-neptune-neptunedatabucketb8719d9a-jfo3bsfisgfn"


def s3_prefix(bucket, portal, date):
    return f"s3://{bucket}/{portal}/{date}"


def run_aws(*args, region):
    subprocess.run(["aws", "s3", *args, "--region", region], check=True)


def aws_s3_ls(prefix, region, recursive=False):
    """`aws s3 ls [--recursive] <prefix>`, returning stdout. The one aws
    call here whose result we need to inspect rather than just its exit
    code (an occupied-date check, and the post-sync Turtle-only check) -
    bypasses run_aws, which discards output, and captures text instead."""
    args = ["ls"]
    if recursive:
        args.append("--recursive")
    args.append(prefix)
    result = subprocess.run(["aws", "s3", *args, "--region", region],
                             capture_output=True, text=True)
    # `aws s3 ls` exits 1 with no output when nothing matches the prefix -
    # that's the "date is free" answer, not an error (nf-osi's workflow
    # runs the same call as `aws s3 ls ... || true`). Any other failure, or
    # exit 1 with an error message, is real.
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return ""
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return result.stdout


def upload(bucket, portal, region, repo_url=DEFAULT_REPO_URL, date=None, tmp_root=".",
           dry_run_dir=None, allow_overwrite=False):
    if not os.path.isfile(FULL_KG_PATH):
        raise SystemExit(f"{FULL_KG_PATH} not found - run `make full-kg` first")
    schema_ttls = sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.ttl")))
    if not schema_ttls:
        raise SystemExit(f"no *.ttl files found directly under {SCHEMA_DIR}/ - run `make schema` first")
    if dry_run_dir is None and shutil.which("aws") is None:
        raise SystemExit("the `aws` CLI is not on PATH - install/configure it first")

    date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # The loader keys a snapshot's named graph off this YYYY-MM-DD path
    # segment, and the manifest types it xsd:date - refuse anything else
    # before touching S3, as nf-osi's "Resolve snapshot date" step does.
    try:
        if datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d") != date:
            raise ValueError
    except ValueError:
        raise SystemExit(f"--date {date!r} is not a YYYY-MM-DD date") from None
    prefix = s3_prefix(bucket, portal, date)

    # Guard 1: the date must be free unless overwriting is opt-in, since
    # step 2 below replaces the whole prefix with `--delete`. Skipped in
    # dry-run mode along with every other aws call - nothing local is at
    # risk of being silently overwritten.
    if dry_run_dir is None and not allow_overwrite:
        if aws_s3_ls(f"{prefix}/", region=region).strip():
            raise SystemExit(
                f"{prefix}/ already holds a snapshot - rerun with --allow-overwrite to replace it, "
                "or pick another --date"
            )

    # Count triples in every file about to be placed under data/ - the
    # schema/*.ttl files and cckp_kg_full.ttl, never _provenance.ttl (that's
    # a copy of the manifest we haven't rendered yet). Done before rendering
    # the manifest, so the count can be embedded in it, and before any
    # upload, so a zero-triple file aborts the whole deposit rather than
    # publishing a snapshot Neptune would silently under-load.
    #
    # void:triples is the number of *distinct* triples across those files,
    # not the per-file sum nf-osi's verify step uses: cckp_kg_full.ttl
    # already merges mc2_model.ttl and cckp_portal.ttl, and Neptune loads
    # the snapshot into one named graph as a set, so a per-file sum would
    # overstate what's loaded.
    data_files = [*schema_ttls, FULL_KG_PATH]
    union = rdflib.Graph()
    print("Counting triples under data/:")
    for path in data_files:
        g = rdflib.Graph()
        g.parse(path, format="turtle")
        if not len(g):
            raise SystemExit(f"{path} parsed to zero triples - refusing to deposit")
        union += g
        print(f"  {path}: {len(g):,}")
    total_triples = len(union)
    print(f"  distinct total: {total_triples:,}")

    commit_sha, branch = git_info()
    deposited_at = datetime.now(timezone.utc)
    manifest_graph = build_manifest(f"{prefix}/data/", portal=portal, repo_url=repo_url,
                                     commit_sha=commit_sha, branch=branch,
                                     triples=total_triples, snapshot_date=date, deposited_at=deposited_at)
    manifest_path = os.path.join(tmp_root, "manifest.ttl")
    provenance_path = os.path.join(tmp_root, "_provenance.ttl")
    manifest_graph.serialize(destination=manifest_path, format="turtle")
    shutil.copyfile(manifest_path, provenance_path)

    # Everything under data/ is staged into one local directory first,
    # whichever mode this runs in - schema/ only has 4 flat *.ttl files
    # today (no README.md/nested dirs to exclude the way upstream's
    # schema/ does), so nothing here needs an --exclude/--include filter.
    staged = {f"schema/{os.path.basename(path)}": path for path in schema_ttls}
    staged["rdf/cckp_kg_full.ttl"] = FULL_KG_PATH
    staged["_provenance.ttl"] = provenance_path

    if dry_run_dir is not None:
        mirror_root = os.path.join(dry_run_dir, portal, date)
        # Start from an empty mirror, the local analogue of sync --delete,
        # so files left by an earlier dry run don't linger in the rehearsal.
        shutil.rmtree(mirror_root, ignore_errors=True)
        for relative_path, src in staged.items():
            dest = os.path.join(mirror_root, "data", relative_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(src, dest)
        manifest_dest = os.path.join(mirror_root, "manifest.ttl")
        shutil.copyfile(manifest_path, manifest_dest)
        print(f"data/ ({len(staged)} file(s), mirrored) -> {mirror_root}/data/")
        print(f"{manifest_path} -> {manifest_dest}  (sentinel - triggers the load)")
        return prefix

    # Guard 2: replace, don't add. Staged locally, then uploaded with one
    # `sync --delete` rather than a file-by-file `cp`, so a second deposit
    # on the same date fully replaces the first - including anything
    # renamed or dropped since - matching nf-osi's own "Upload the
    # snapshot" step exactly (deliberately unfiltered: the staging dir
    # holds Turtle and nothing else, so there's nothing to --exclude).
    with tempfile.TemporaryDirectory(prefix="sagebrain_stage_") as stage_root:
        stage_data = os.path.join(stage_root, "data")
        for relative_path, src in staged.items():
            dest = os.path.join(stage_data, relative_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(src, dest)

        run_aws("sync", stage_data + "/", f"{prefix}/data/", "--delete", region=region)
        print(f"{stage_data}/ -> {prefix}/data/  (synced, {len(staged)} file(s), stale objects removed)")

    # Guard 3: the load path must be Turtle-only before the sentinel. What
    # matters is what actually sits under the prefix right now - a stray
    # object from an aborted run, a hand-copied file, another writer - not
    # just what this run staged. Neptune's bulk loader runs with
    # failOnError=TRUE, so one bad object fails the *entire* snapshot load,
    # and this is the last check before manifest.ttl triggers it.
    listing = aws_s3_ls(f"{prefix}/data/", region=region, recursive=True)
    keys = [line.split()[-1] for line in listing.splitlines() if line.strip()]
    if not keys:
        raise SystemExit(f"{prefix}/data/ is empty after the upload")
    stray = [key for key in keys if not key.endswith(".ttl")]
    if stray:
        raise SystemExit(
            f"non-Turtle objects under {prefix}/data/ - the bulk loader would fail the whole snapshot: {stray}"
        )
    # Compare exact keys, not just the count: one stray .ttl from another
    # writer plus one missing staged file would otherwise balance out.
    key_root = prefix.split("/", 3)[3] + "/data/"  # "<portal>/<date>/data/"
    expected_keys = {key_root + relative_path for relative_path in staged}
    if set(keys) != expected_keys or len(keys) != len(expected_keys):
        missing = sorted(expected_keys - set(keys))
        unexpected = sorted(set(keys) - expected_keys)
        raise SystemExit(f"{prefix}/data/ doesn't match what was staged - missing: {missing}, unexpected: {unexpected}")
    print(f"{len(keys)} Turtle object(s) under {prefix}/data/")

    # Sentinel last: writing manifest.ttl is what triggers the Neptune load.
    run_aws("cp", manifest_path, f"{prefix}/manifest.ttl", region=region)
    print(f"{manifest_path} -> {prefix}/manifest.ttl  (sentinel - triggers the load)")

    return prefix


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bucket", default=os.environ.get("SAGEBRAIN_BUCKET", SAGEBRAIN_BUCKET),
                         help="SageBrain Neptune S3 bucket name (env: SAGEBRAIN_BUCKET; default: the prod bucket, %(default)s)")
    parser.add_argument("--portal", default=os.environ.get("SAGEBRAIN_PORTAL", DEFAULT_PORTAL),
                         help="Portal-scoped S3 prefix segment (env: SAGEBRAIN_PORTAL, default: %(default)s)")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", DEFAULT_REGION),
                         help="AWS region (env: AWS_REGION, default: %(default)s)")
    parser.add_argument("--date", default=None, help="Override the YYYY-MM-DD prefix (default: today, UTC)")
    parser.add_argument("--dry-run", nargs="?", const="sagebrain_s3_dry_run", default=None, metavar="DIR",
                         help="Skip `aws` and mirror the upload layout into DIR instead "
                              "(default: %(const)s)")
    parser.add_argument("--allow-overwrite", action="store_true",
                         help="Replace an existing snapshot for this --date instead of refusing "
                              "(ignored with --dry-run, which never refuses on an occupied date)")
    args = parser.parse_args()

    if not args.bucket:
        sys.exit("--bucket (or SAGEBRAIN_BUCKET) is required - see sagebrain-infra for the real bucket name "
                  "(any placeholder works with --dry-run)")

    prefix = upload(args.bucket, args.portal, args.region, date=args.date, dry_run_dir=args.dry_run,
                     allow_overwrite=args.allow_overwrite)
    if args.dry_run:
        portal_date = prefix.split(f"{args.bucket}/", 1)[1]  # "<portal>/<date>"
        print(f"Done (dry run): {args.dry_run}/{portal_date}/  (would be {prefix})")
    else:
        print(f"Done: {prefix}")


if __name__ == "__main__":
    main()
