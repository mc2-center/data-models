"""Fold data/rdf/DataCatalog.ttl into the main public data/rdf/cckp_kg.ttl.

A separate, explicit step rather than part of `make triples`/`make all`:
DataCatalog is a new, not-yet-broadly-verified pipeline stage (see
plans/datacatalog_kg_integration.md), so this stays opt-in until it's been
run and reviewed at least once. Safe to re-run - parses both files fresh
and re-serializes; DataCatalog's triples enrich the *existing* cckp:Dataset
subjects (same IRI, see scripts/build_datacatalog_triples.py) rather than
adding new nodes, so merging twice is idempotent (RDF triples are a set).
"""

import argparse

import rdflib


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cckp-kg", default="data/rdf/cckp_kg.ttl")
    parser.add_argument("--datacatalog", default="data/rdf/DataCatalog.ttl")
    parser.add_argument("--out", default=None, help="Defaults to overwriting --cckp-kg in place")
    args = parser.parse_args()

    g = rdflib.Graph()
    g.parse(args.cckp_kg, format="turtle")
    n_before = len(g)
    g.parse(args.datacatalog, format="turtle")

    out = args.out or args.cckp_kg
    g.serialize(destination=out, format="turtle")
    print(f"{n_before} + DataCatalog -> {len(g)} triple(s) -> {out}")


if __name__ == "__main__":
    main()
