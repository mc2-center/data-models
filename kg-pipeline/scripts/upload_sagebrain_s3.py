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

No CI/OIDC role assumption - run this with whatever AWS credentials your
shell already has configured (SSO profile, env vars, ~/.aws/credentials).

Requires the `aws` CLI on PATH and these already-built inputs:
    make schema     (schema/*.ttl)
    make full-kg    (data/rdf/cckp_kg_full.ttl)

Usage:
    export SAGEBRAIN_BUCKET=<bucket-name>       # required - no default; see
                                                  # sagebrain-infra for the real value
    export SAGEBRAIN_PORTAL=cckp                 # optional, default: cckp
    export AWS_REGION=us-east-1                  # optional, default: us-east-1
    python scripts/upload_sagebrain_s3.py

--dry-run [DIR] skips `aws` entirely and mirrors the exact prefix layout
that would be uploaded into a local directory instead (default:
sagebrain_s3_dry_run/) - useful for inspecting the output shape, or for a
first run before real bucket credentials/name are available. --bucket is
still required in dry-run mode (it's part of the mirrored path), but
doesn't need to be a real bucket.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from build_manifest import DEFAULT_PORTAL, DEFAULT_REPO_URL, build_manifest, git_info

FULL_KG_PATH = os.path.join("data", "rdf", "cckp_kg_full.ttl")
SCHEMA_DIR = "schema"
DEFAULT_REGION = "us-east-1"
SAGEBRAIN_BUCKET = "app-prod-neptune-neptunedatabucketb8719d9a-jfo3bsfisgfn"


def s3_prefix(bucket, portal, date):
    return f"s3://{bucket}/{portal}/{date}"


def run_aws(*args, region):
    subprocess.run(["aws", "s3", *args, "--region", region], check=True)


def upload(bucket, portal, region, repo_url=DEFAULT_REPO_URL, date=None, tmp_root=".", dry_run_dir=None):
    if not os.path.isfile(FULL_KG_PATH):
        raise SystemExit(f"{FULL_KG_PATH} not found - run `make full-kg` first")
    schema_ttls = sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.ttl")))
    if not schema_ttls:
        raise SystemExit(f"no *.ttl files found directly under {SCHEMA_DIR}/ - run `make schema` first")
    if dry_run_dir is None and shutil.which("aws") is None:
        raise SystemExit("the `aws` CLI is not on PATH - install/configure it first")

    date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prefix = s3_prefix(bucket, portal, date)

    def place(src, relative_path):
        """Upload src to `{prefix}/{relative_path}` for real, or mirror it
        under dry_run_dir at the same relative layout when dry-running."""
        dest = f"{prefix}/{relative_path}"
        if dry_run_dir is not None:
            local_dest = os.path.join(dry_run_dir, portal, date, relative_path)
            os.makedirs(os.path.dirname(local_dest), exist_ok=True)
            shutil.copyfile(src, local_dest)
        else:
            run_aws("cp", src, dest, region=region)
        return dest

    commit_sha, branch = git_info()
    manifest_graph = build_manifest(f"{prefix}/", portal=portal, repo_url=repo_url,
                                     commit_sha=commit_sha, branch=branch)
    manifest_path = os.path.join(tmp_root, "manifest.ttl")
    provenance_path = os.path.join(tmp_root, "_provenance.ttl")
    manifest_graph.serialize(destination=manifest_path, format="turtle")
    shutil.copyfile(manifest_path, provenance_path)

    # schema/ only has 4 flat *.ttl files today (no README.md/nested dirs to
    # exclude the way upstream's schema/ does) - uploaded individually
    # rather than via `aws s3 sync --exclude/--include`, since that filter
    # would also need to guard against schema/vendor/*.yaml if that ever
    # grows a vendored .ttl.
    print(f"data/schema/ ({len(schema_ttls)} file(s)) -> {prefix}/data/schema/")
    for path in schema_ttls:
        place(path, f"data/schema/{os.path.basename(path)}")

    print(f"{FULL_KG_PATH} -> {place(FULL_KG_PATH, 'data/rdf/cckp_kg_full.ttl')}")
    print(f"{provenance_path} -> {place(provenance_path, 'data/_provenance.ttl')}")

    # Sentinel last: writing manifest.ttl is what triggers the Neptune load.
    print(f"{manifest_path} -> {place(manifest_path, 'manifest.ttl')}  (sentinel - triggers the load)")

    return prefix


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bucket", default=os.environ.get("SAGEBRAIN_BUCKET", SAGEBRAIN_BUCKET),
                         help="SageBrain Neptune S3 bucket name (env: SAGEBRAIN_BUCKET, required)")
    parser.add_argument("--portal", default=os.environ.get("SAGEBRAIN_PORTAL", DEFAULT_PORTAL),
                         help="Portal-scoped S3 prefix segment (env: SAGEBRAIN_PORTAL, default: %(default)s)")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", DEFAULT_REGION),
                         help="AWS region (env: AWS_REGION, default: %(default)s)")
    parser.add_argument("--date", default=None, help="Override the YYYY-MM-DD prefix (default: today, UTC)")
    parser.add_argument("--dry-run", nargs="?", const="sagebrain_s3_dry_run", default=None, metavar="DIR",
                         help="Skip `aws` and mirror the upload layout into DIR instead "
                              "(default: %(const)s)")
    args = parser.parse_args()

    if not args.bucket:
        sys.exit("--bucket (or SAGEBRAIN_BUCKET) is required - see sagebrain-infra for the real bucket name "
                  "(any placeholder works with --dry-run)")

    prefix = upload(args.bucket, args.portal, args.region, date=args.date, dry_run_dir=args.dry_run)
    if args.dry_run:
        portal_date = prefix.split(f"{args.bucket}/", 1)[1]  # "<portal>/<date>"
        print(f"Done (dry run): {args.dry_run}/{portal_date}/  (would be {prefix})")
    else:
        print(f"Done: {prefix}")


if __name__ == "__main__":
    main()
