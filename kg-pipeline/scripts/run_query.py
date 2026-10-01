"""Run one or more SPARQL SELECT queries against one or more Turtle files
and print their results - for ad hoc exploration/evaluation (e.g.
queries/examples/*.rq's domain/research-question queries), as opposed to
validate_graph.py's --queries mode, which runs queries/*.rq as pass/fail
assertions and requires an `# expect: ...` header every file here
deliberately omits (these aren't assertions - see queries/examples' own
README note). Reads the same `# name:`/`# description:` header lines if
present (purely cosmetic here - printed, never required or checked).

Usage:
  python3 scripts/run_query.py queries/examples/datasets_by_tumor_type.rq data/rdf/cckp_kg_full.ttl
  python3 scripts/run_query.py queries/examples data/rdf/cckp_kg_full.ttl   # every *.rq in a directory
"""

import argparse
import glob
import os
import sys

import rdflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_graph import QUERY_HEADER_RE  # noqa: E402 - reuse the same header format, loosely


def parse_query_file_loose(path):
    """(name, description, sparql) - like validate_graph.parse_query_file()
    but neither header line is required (name falls back to the filename,
    description to ""), since these queries never carry `# expect: ...`.
    A `# description: ...` may continue onto following plain `# ...`
    comment lines (no keyword prefix), which are appended to it - the
    queries/examples/*.rq files wrap their description across a few lines."""
    meta = {}
    body_lines = []
    in_header = True
    last_field = None
    with open(path) as f:
        for line in f:
            if in_header:
                stripped = line.strip()
                m = QUERY_HEADER_RE.match(stripped)
                if m:
                    meta[m.group(1)] = m.group(2).strip()
                    last_field = m.group(1)
                    continue
                if not stripped:
                    continue
                if stripped.startswith("#") and last_field:
                    meta[last_field] += " " + stripped.lstrip("#").strip()
                    continue
                in_header = False
            body_lines.append(line)
    name = meta.get("name") or os.path.splitext(os.path.basename(path))[0]
    return name, meta.get("description", ""), "".join(body_lines)


def run_and_print(path, graph, limit):
    name, description, sparql = parse_query_file_loose(path)
    print(f"=== {name} ===  [{path}]")
    if description:
        print(description)
    rows = list(graph.query(sparql))
    print(f"-> {len(rows)} row(s)")
    for row in rows[:limit]:
        print("  ", row)
    if len(rows) > limit:
        print(f"   ... {len(rows) - limit} more row(s) not shown (--limit {limit})")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="A single .rq file, or a directory to run every *.rq file in it")
    parser.add_argument("data", nargs="+", help="Turtle file(s) to load and query together")
    parser.add_argument("--limit", type=int, default=20, help="Max rows printed per query (default: 20)")
    args = parser.parse_args()

    if os.path.isdir(args.query):
        paths = sorted(glob.glob(os.path.join(args.query, "*.rq")))
        if not paths:
            parser.error(f"no *.rq files found in {args.query}")
    else:
        paths = [args.query]

    graph = rdflib.Graph()
    for path in args.data:
        graph.parse(path, format="turtle")
    print(f"Loaded {len(graph)} triple(s) from {', '.join(args.data)}\n")

    for path in paths:
        run_and_print(path, graph, args.limit)


if __name__ == "__main__":
    main()
