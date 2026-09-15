"""Stage 6: emit manifest.ttl - a small PROV/VOID statement describing one
graph build, meant to be published alongside the merged graph as a
lightweight trigger file for downstream consumers (e.g. an auto-loader
watching for a new file version) that would rather check one small file
than diff the much larger merged graph itself.

Shape matches nf-osi/kg-pipeline's own manifest.ttl (see its
.github/workflows/upload-sagebrain-s3.yml "Generate build manifest" step),
so any Neptune bulk-loader wired up for one pipeline's convention works for
both: a single `prov:Activity, void:Dataset` node, one per build (subject
IRI keyed by git commit sha, or a UTC timestamp when no commit is
resolvable), with `prov:generatedAtTime`, `prov:used` pointing at the
source commit, `cckp:portal`/`cckp:gitCommit`/`cckp:gitRef` build metadata,
and `void:dataDump` pointing at wherever this build's graph was actually
published - the one thing that differs per publish target. Two current
callers pass two different kinds of dump location, both valid IRIs:
`make manifest`/`full-kg` default to the Synapse File `make deploy-kg`
publishes to (SYNAPSE_NS in build_triples.py - same canonical-IRI policy
used for instance data, not a second identifier minted for this file
either); scripts/upload_sagebrain_s3.py passes the date-partitioned S3
prefix it just uploaded to instead.

Usage:
    python scripts/build_manifest.py [--data-dump IRI] [--portal NAME] [--out data/rdf/manifest.ttl]
"""

import argparse
import subprocess
from datetime import datetime, timezone

import rdflib
from rdflib.namespace import RDF, XSD

from build_triples import SYNAPSE_NS

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
VOID = rdflib.Namespace("http://rdfs.org/ns/void#")

# The Synapse File entity `make deploy-kg` publishes the merged graph to -
# see FULL_KG_TARGET in publish_kg.py. Composed from SYNAPSE_NS (not
# synapseclient) so this script stays dependency-free at import time.
DEFAULT_DATA_DUMP = SYNAPSE_NS + "syn77443315"
DEFAULT_PORTAL = "cckp"
DEFAULT_REPO_URL = "https://github.com/mc2-center/data-models"


def git_info(cwd=None):
    """(commit_sha, branch) for the checkout building this manifest, or
    (None, None) if git isn't available/this isn't a git checkout (e.g. a
    tarball export) - the manifest is still valid without them, just
    missing the two most useful "what code produced this" fields."""
    def run(*args):
        try:
            result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
            return result.stdout.strip() or None
        except (OSError, subprocess.CalledProcessError):
            return None
    return run("rev-parse", "HEAD"), run("rev-parse", "--abbrev-ref", "HEAD")


def build_manifest(data_dump, build_time=None, portal=DEFAULT_PORTAL, repo_url=DEFAULT_REPO_URL,
                    commit_sha=None, branch=None):
    """Pure builder - commit_sha/branch are taken as given (including both
    None for "no git metadata available"), never auto-detected here. See
    main() below for the CLI's own git_info() call."""
    build_time = build_time or datetime.now(timezone.utc)

    g = rdflib.Graph()
    g.bind("cckp", CCKP)
    g.bind("prov", PROV)
    g.bind("void", VOID)

    build_id = commit_sha or build_time.strftime("%Y%m%dT%H%M%SZ")
    activity = CCKP[f"kgBuild_{build_id}"]

    g.add((activity, RDF.type, PROV.Activity))
    g.add((activity, RDF.type, VOID.Dataset))
    g.add((activity, PROV.generatedAtTime, rdflib.Literal(build_time.isoformat(), datatype=XSD.dateTime)))
    g.add((activity, CCKP.portal, rdflib.Literal(portal)))
    if commit_sha:
        g.add((activity, CCKP.gitCommit, rdflib.Literal(commit_sha)))
        g.add((activity, PROV.used, rdflib.URIRef(f"{repo_url}/commit/{commit_sha}")))
    if branch:
        g.add((activity, CCKP.gitRef, rdflib.Literal(branch)))
    g.add((activity, VOID.dataDump, rdflib.URIRef(data_dump)))
    return g


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dump", default=DEFAULT_DATA_DUMP,
                         help="IRI/URI of where this build's merged graph was (or will be) published - a "
                              "Synapse entity IRI, an s3:// prefix, etc. (default: %(default)s)")
    parser.add_argument("--portal", default=DEFAULT_PORTAL)
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--out", default="data/rdf/manifest.ttl")
    args = parser.parse_args()

    commit_sha, branch = git_info()
    g = build_manifest(args.data_dump, portal=args.portal, repo_url=args.repo_url,
                        commit_sha=commit_sha, branch=branch)
    g.serialize(destination=args.out, format="turtle")
    print(f"{len(g)} triple(s) -> {args.out}")


if __name__ == "__main__":
    main()
