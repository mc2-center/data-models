"""Generic two-file Turtle merge - parse both, union the triples, serialize.

Unlike scripts/merge_datacatalog.py (which is specifically about folding
DataCatalog's Dataset-subject enrichment into cckp_kg.ttl and documents that
one relationship in its docstring), this script doesn't assume anything
about what the two inputs represent - it's the same plain rdflib
parse-both/serialize-the-union operation, reused here to fold
data/rdf/scdm_links.ttl (SCDM Organization/Program/Person nodes and their
institutionRef/consortiumRef/investigatorRef/contributorRef edges back into
the base graph's subjects) onto data/rdf/cckp_kg_with_datacatalog.ttl,
producing data/rdf/cckp_kg_full.ttl (see `make full-kg`).

Safe to re-run - RDF triples are a set, so merging twice is idempotent.
"""

import argparse

import rdflib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Turtle file to merge into")
    parser.add_argument("--overlay", required=True, help="Turtle file whose triples are added")
    parser.add_argument("--out", required=True, help="Output path for the merged graph")
    args = parser.parse_args()

    g = rdflib.Graph()
    g.parse(args.base, format="turtle")
    n_before = len(g)
    g.parse(args.overlay, format="turtle")

    g.serialize(destination=args.out, format="turtle")
    print(f"{n_before} + {args.overlay} -> {len(g)} triple(s) -> {args.out}")


if __name__ == "__main__":
    main()
