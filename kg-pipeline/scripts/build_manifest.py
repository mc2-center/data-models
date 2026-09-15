"""Stage 6: emit manifest.ttl - a small PROV statement describing one graph
build, meant to be published alongside the merged graph as a lightweight
trigger file for downstream consumers (e.g. an auto-loader watching for a
new file version) that would rather check one small file than diff the much
larger merged graph itself.

Deliberately minimal: one prov:Activity (this build, timestamped) that
prov:generated one prov:Entity - the Synapse File `make deploy-kg` publishes
the merged graph to (FULL_KG_TARGET in publish_kg.py), addressed by its own
canonical Synapse IRI (SYNAPSE_NS in build_triples.py) rather than a second,
parallel identifier minted just for this file.

Usage:
    python scripts/build_manifest.py [--graph-entity SYNID] [--out data/rdf/manifest.ttl]
"""

import argparse
from datetime import datetime, timezone

import rdflib
from rdflib.namespace import RDF, XSD

from build_triples import SYNAPSE_NS

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")

# The Synapse File entity `make deploy-kg` publishes the merged graph to -
# see FULL_KG_TARGET in publish_kg.py. Kept as a literal default here (not
# imported) so this script has no dependency on synapseclient.
DEFAULT_GRAPH_ENTITY = "syn77443315"


def build_manifest(graph_entity_id, build_time=None):
    build_time = build_time or datetime.now(timezone.utc)
    g = rdflib.Graph()
    g.bind("cckp", CCKP)
    g.bind("prov", PROV)

    activity = CCKP["kgBuild"]
    entity = rdflib.URIRef(SYNAPSE_NS + graph_entity_id)

    g.add((activity, RDF.type, PROV.Activity))
    g.add((activity, PROV.generatedAtTime, rdflib.Literal(build_time.isoformat(), datatype=XSD.dateTime)))
    g.add((activity, PROV.generated, entity))
    g.add((entity, RDF.type, PROV.Entity))
    g.add((entity, PROV.wasGeneratedBy, activity))
    return g


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--graph-entity", default=DEFAULT_GRAPH_ENTITY,
                         help="Synapse id of the File entity the merged graph is published to (default: %(default)s)")
    parser.add_argument("--out", default="data/rdf/manifest.ttl")
    args = parser.parse_args()

    g = build_manifest(args.graph_entity)
    g.serialize(destination=args.out, format="turtle")
    print(f"{len(g)} triple(s) -> {args.out}")


if __name__ == "__main__":
    main()
