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


def s3_prefix(bucket, portal, date):
    return f"s3://{bucket}/{portal}/{date}"


def run_aws(*args, region):
    subprocess.run(["aws", "s3", *args, "--region", region], check=True)


def upload(bucket, portal, region, repo_url=DEFAULT_REPO_URL, date=None, tmp_root="."):
    if not os.path.isfile(FULL_KG_PATH):
        raise SystemExit(f"{FULL_KG_PATH} not found - run `make full-kg` first")
    schema_ttls = sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.ttl")))
    if not schema_ttls:
        raise SystemExit(f"no *.ttl files found directly under {SCHEMA_DIR}/ - run `make schema` first")
    if shutil.which("aws") is None:
        raise SystemExit("the `aws` CLI is not on PATH - install/configure it first")

    date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prefix = s3_prefix(bucket, portal, date)

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
        run_aws("cp", path, f"{prefix}/data/schema/{os.path.basename(path)}", region=region)

    print(f"{FULL_KG_PATH} -> {prefix}/data/rdf/cckp_kg_full.ttl")
    run_aws("cp", FULL_KG_PATH, f"{prefix}/data/rdf/cckp_kg_full.ttl", region=region)

    print(f"{provenance_path} -> {prefix}/data/_provenance.ttl")
    run_aws("cp", provenance_path, f"{prefix}/data/_provenance.ttl", region=region)

    # Sentinel last: writing manifest.ttl is what triggers the Neptune load.
    print(f"{manifest_path} -> {prefix}/manifest.ttl  (sentinel - triggers the load)")
    run_aws("cp", manifest_path, f"{prefix}/manifest.ttl", region=region)

    return prefix


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bucket", default=os.environ.get("SAGEBRAIN_BUCKET"),
                         help="SageBrain Neptune S3 bucket name (env: SAGEBRAIN_BUCKET, required)")
    parser.add_argument("--portal", default=os.environ.get("SAGEBRAIN_PORTAL", DEFAULT_PORTAL),
                         help="Portal-scoped S3 prefix segment (env: SAGEBRAIN_PORTAL, default: %(default)s)")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", DEFAULT_REGION),
                         help="AWS region (env: AWS_REGION, default: %(default)s)")
    parser.add_argument("--date", default=None, help="Override the YYYY-MM-DD prefix (default: today, UTC)")
    args = parser.parse_args()

    if not args.bucket:
        sys.exit("--bucket (or SAGEBRAIN_BUCKET) is required - see sagebrain-infra for the real bucket name")

    prefix = upload(args.bucket, args.portal, args.region, date=args.date)
    print(f"Done: {prefix}")


if __name__ == "__main__":
    main()
