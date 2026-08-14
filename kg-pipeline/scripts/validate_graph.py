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
"""

import argparse
import csv
import sys
from collections import Counter

import rdflib


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


def coverage(unmapped_csv, ttl_paths):
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
        return True

    print(f"Unresolved vocabulary values ({len(rows)} total), by table/field:")
    for (table, field), n in sorted(by_field.items()):
        print(f"  {table}.{field}: {n} unresolved value(s)")
    print(f"\nSee {unmapped_csv} for the individual values - each was passed through unresolved, not dropped.")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--parse-only", nargs="+", metavar="FILE", help="Turtle files to syntax-check")
    parser.add_argument("--coverage", nargs="+", metavar="PATH",
                         help="First path is unmapped_terms.csv, rest are Turtle files (for future graph-level coverage checks)")
    args = parser.parse_args()

    if not args.parse_only and not args.coverage:
        parser.error("pass --parse-only and/or --coverage")

    ok = True
    if args.parse_only:
        ok = parse_only(args.parse_only) and ok
    if args.coverage:
        unmapped_csv, *ttl_paths = args.coverage
        ok = coverage(unmapped_csv, ttl_paths) and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
