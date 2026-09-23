"""Stage 5: validate generated Turtle files and report harmonization coverage.

Two independent checks, either or both can be requested in one invocation:
  --parse-only FILE...   Parse each Turtle file with rdflib as a syntax smoke
                          test (this project uses rdflib for triple-building
                          already, so this avoids nf-osi's extra `rapper`/
                          raptor2 dependency for the same purpose).
  --coverage UNMAPPED_CSV FILE...
                          Report, per source field, what fraction of
                          controlled-vocabulary values seen during
                          harmonization resolved to a real ontology IRI
                          (read from harmonize.py's unmapped_terms.csv
                          report - see scripts/harmonize.py).

Coverage gate (ratchet, not a fixed threshold): a field's unmapped-value
count is only a *regression* if it grows past a checked-in baseline - a
brand-new CV with 100 unmapped values isn't a failure the day it's added,
but 101 unmapped values on a field the baseline already recorded at 100 is.
Fields in suggest_mappings.EXCLUDED_FIELDS (accession-number/free-identifier
fields that were never meant to carry an ontology mapping - see
scripts/suggest_mappings.py and README.md) are always excluded from the gate.

  --baseline PATH --fail-on-regression   Compare current per-field unmapped
                                          counts against the checked-in
                                          baseline; exit 1 if any non-excluded
                                          field's count increased.
  --update-baseline PATH                 Write current per-field unmapped
                                          counts (non-excluded fields only)
                                          to PATH - run after intentionally
                                          curating a field or accepting a
                                          new, legitimate gap.

  --shacl SHAPES_FILE DATA_FILE...        Validate the built instance graph
                                          against schema/cckp_portal.shacl.ttl
                                          via pyshacl, WITHOUT RDFS/OWL
                                          entailment (matches sagebrain-
                                          model's own tests/validate.py
                                          configuration - inference would
                                          make sh:class join-target checks
                                          vacuous by entailing the very type
                                          being checked for).
  --queries QUERY_DIR DATA_FILE...        Run every queries/*.rq sanity
                                          query (graph-wide aggregate and
                                          cross-row checks that are awkward
                                          or impossible to express as a
                                          SHACL shape - e.g. "is every core
                                          class present at all")
                                          against the given Turtle file(s).
                                          See queries/*.rq for the query
                                          format (a `# name:`/`# expect:`/
                                          `# description:` header followed
                                          by a SPARQL SELECT).
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import Counter

import rdflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suggest_mappings import EXCLUDED_FIELDS  # noqa: E402


def parse_only(paths):
    ok = True
    for path in paths:
        g = rdflib.Graph()
        try:
            g.parse(path, format="turtle")
        except Exception as exc:  # noqa: BLE001 - report and continue to check every file
            print(f"FAIL  {path}: {exc}")
            ok = False
        else:
            print(f"OK    {path}  ({len(g)} triples)")
    return ok


def load_baseline(path):
    if not path or not os.path.isfile(path):
        return {}
    with open(path) as f:
        return {tuple(k.split(".", 1)): v for k, v in json.load(f).items()}


def save_baseline(path, by_field):
    serializable = {f"{table}.{field}": n for (table, field), n in sorted(by_field.items())}
    with open(path, "w") as f:
        json.dump(serializable, f, indent=2)
        f.write("\n")


def coverage(unmapped_csv, ttl_paths, baseline_path=None, fail_on_regression=False, update_baseline_path=None):
    # Every field harmonize.py touches gets one row per source row it saw,
    # whether or not it resolved - unmapped_terms.csv only records the
    # misses, so total-seen has to come from the harmonized CSVs' own
    # <field>_ontology_iri columns; here we just summarize what's known
    # from the miss log, since that's what's available post-hoc from a
    # Turtle-only validation pass.
    try:
        with open(unmapped_csv, newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"No unmapped-terms report found at {unmapped_csv} (harmonize.py may not have run yet, "
              "or everything resolved).")
        return True

    by_field = Counter((r["table"], r["field"]) for r in rows)
    if not by_field:
        print("unmapped_terms.csv is empty - every vocabulary value resolved to an ontology IRI.")
    else:
        print(f"Unresolved vocabulary values ({len(rows)} total), by table/field:")
        for (table, field), n in sorted(by_field.items()):
            excluded = " (excluded from coverage gate: not ontology-mappable, see README.md)" \
                if (table, field) in EXCLUDED_FIELDS else ""
            print(f"  {table}.{field}: {n} unresolved value(s){excluded}")
        print(f"\nSee {unmapped_csv} for the individual values - each was passed through unresolved, not dropped.")

    if update_baseline_path:
        gate_field_counts = {k: v for k, v in by_field.items() if k not in EXCLUDED_FIELDS}
        save_baseline(update_baseline_path, gate_field_counts)
        print(f"\nWrote coverage baseline ({len(gate_field_counts)} field(s)) -> {update_baseline_path}")
        return True

    if not fail_on_regression:
        return True

    baseline = load_baseline(baseline_path)
    ok = True
    regressions = []
    for (table, field), n in sorted(by_field.items()):
        if (table, field) in EXCLUDED_FIELDS:
            continue
        prior = baseline.get((table, field), 0)
        if n > prior:
            regressions.append((table, field, prior, n))
    if regressions:
        ok = False
        print(f"\nCOVERAGE REGRESSION: {len(regressions)} field(s) have more unresolved values than the "
              f"baseline at {baseline_path}:")
        for table, field, prior, n in regressions:
            print(f"  {table}.{field}: {prior} -> {n} (+{n - prior})")
        print("If this growth is expected (e.g. a newly-added CV), run with --update-baseline "
              "to accept the new counts.")
    else:
        print(f"\nCoverage gate: no regressions vs baseline at {baseline_path}.")
    return ok


def run_shacl(shapes_path, data_paths):
    """(conforms, results_graph, results_text, data_graph, shapes_graph)
    from pyshacl, without printing - shacl_validate() is the reporting
    wrapper. shapes_graph is returned so a caller can resolve a result's
    sh:sourceShape blank node back to its named shape."""
    import pyshacl

    data_graph = rdflib.Graph()
    for path in data_paths:
        data_graph.parse(path, format="turtle")
    shapes_graph = rdflib.Graph()
    shapes_graph.parse(shapes_path, format="turtle")

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph, shacl_graph=shapes_graph, inference="none", abort_on_first=False,
    )
    return conforms, results_graph, results_text, data_graph, shapes_graph


def shacl_validate(shapes_path, data_paths):
    conforms, _, results_text, data_graph, _ = run_shacl(shapes_path, data_paths)
    if conforms:
        print(f"OK    {shapes_path} conforms against {', '.join(data_paths)} "
              f"({len(data_graph)} triple(s) checked)")
    else:
        print(f"FAIL  {shapes_path} violated by {', '.join(data_paths)}:\n{results_text}")
    return conforms


QUERY_HEADER_RE = re.compile(r"^#\s*(name|expect|description):\s*(.*)$")
MIN_COUNT_RE = re.compile(r"^min_count\s+(\d+)$")


def parse_query_file(path):
    """(name, expect, description, sparql) from one queries/*.rq file - a
    `# name: ...` / `# expect: ...` / `# description: ...` header (any
    order, blank lines allowed between them) followed by the SPARQL SELECT
    itself. `expect` is either "empty" (pass iff the query returns zero
    rows - a find-the-violations query) or "min_count N" (pass iff it
    returns at least N rows - a sanity floor)."""
    meta = {}
    body_lines = []
    in_header = True
    with open(path) as f:
        for line in f:
            if in_header:
                m = QUERY_HEADER_RE.match(line.strip())
                if m:
                    meta[m.group(1)] = m.group(2).strip()
                    continue
                if not line.strip():
                    continue
                in_header = False
            body_lines.append(line)
    for required in ("name", "expect"):
        if required not in meta:
            raise ValueError(f"{path}: missing required '# {required}: ...' header line")
    return meta["name"], meta["expect"], meta.get("description", ""), "".join(body_lines)


def check_expectation(expect, n_rows):
    if expect == "empty":
        return n_rows == 0
    m = MIN_COUNT_RE.match(expect)
    if m:
        return n_rows >= int(m.group(1))
    raise ValueError(f"unknown '# expect: {expect}' - must be 'empty' or 'min_count N'")


def run_query_checks(query_dir, data_paths):
    """Run every queries/*.rq sanity query against the union of data_paths.
    Returns a list of {name, path, expect, n_rows, passed, description,
    sample} dicts, one per query file, sorted by filename."""
    graph = rdflib.Graph()
    for path in data_paths:
        graph.parse(path, format="turtle")

    results = []
    for path in sorted(glob.glob(os.path.join(query_dir, "*.rq"))):
        name, expect, description, sparql = parse_query_file(path)
        rows = list(graph.query(sparql))
        results.append({
            "name": name, "path": path, "expect": expect, "description": description,
            "n_rows": len(rows), "passed": check_expectation(expect, len(rows)), "sample": rows[:5],
        })
    return results


def print_query_check_results(results):
    n_failed = sum(1 for r in results if not r["passed"])
    for r in results:
        status = "OK" if r["passed"] else "FAIL"
        print(f"{status}    {r['name']}  (expect: {r['expect']}, got {r['n_rows']} row(s))  [{r['path']}]")
        if not r["passed"]:
            print(f"      {r['description']}")
            for row in r["sample"]:
                print(f"      violation: {row}")
    print(f"\n{len(results) - n_failed}/{len(results)} query check(s) passed")
    return n_failed == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--parse-only", nargs="+", metavar="FILE", help="Turtle files to syntax-check")
    parser.add_argument("--coverage", nargs="+", metavar="PATH",
                         help="First path is unmapped_terms.csv, rest are Turtle files (for future graph-level coverage checks)")
    parser.add_argument("--baseline", default="mappings/coverage_baseline.json",
                         help="Checked-in per-field unmapped-count baseline for --fail-on-regression")
    parser.add_argument("--fail-on-regression", action="store_true",
                         help="Exit 1 if any non-excluded field's unmapped count grew past --baseline")
    parser.add_argument("--update-baseline", metavar="PATH",
                         help="Write current per-field unmapped counts (non-excluded fields only) to PATH "
                              "instead of gating - run after intentionally curating or accepting new gaps")
    parser.add_argument("--shacl", nargs="+", metavar="PATH",
                         help="First path is a SHACL shapes Turtle file, rest are instance-data Turtle "
                              "files to validate against it")
    parser.add_argument("--queries", nargs="+", metavar="PATH",
                         help="First path is a directory of queries/*.rq sanity queries, rest are "
                              "instance-data Turtle files to run them against")
    args = parser.parse_args()

    if not args.parse_only and not args.coverage and not args.shacl and not args.queries:
        parser.error("pass --parse-only, --coverage, --shacl, and/or --queries")

    ok = True
    if args.parse_only:
        ok = parse_only(args.parse_only) and ok
    if args.coverage:
        unmapped_csv, *ttl_paths = args.coverage
        ok = coverage(unmapped_csv, ttl_paths, baseline_path=args.baseline,
                       fail_on_regression=args.fail_on_regression,
                       update_baseline_path=args.update_baseline) and ok
    if args.shacl:
        shapes_path, *data_paths = args.shacl
        ok = shacl_validate(shapes_path, data_paths) and ok
    if args.queries:
        query_dir, *data_paths = args.queries
        ok = print_query_check_results(run_query_checks(query_dir, data_paths)) and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
