from datetime import datetime, timezone

import rdflib

import build_manifest

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")


def test_build_manifest_emits_activity_generated_at_time():
    build_time = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    g = build_manifest.build_manifest("syn77443315", build_time=build_time)

    activity = CCKP["kgBuild"]
    assert (activity, rdflib.RDF.type, PROV.Activity) in g
    assert (activity, PROV.generatedAtTime,
            rdflib.Literal(build_time.isoformat(), datatype=rdflib.XSD.dateTime)) in g


def test_build_manifest_points_at_the_canonical_synapse_iri_of_the_deployed_graph():
    g = build_manifest.build_manifest("syn77443315")

    activity = CCKP["kgBuild"]
    entity = rdflib.URIRef("https://www.synapse.org/Synapse:syn77443315")
    assert (activity, PROV.generated, entity) in g
    assert (entity, rdflib.RDF.type, PROV.Entity) in g
    assert (entity, PROV.wasGeneratedBy, activity) in g


def test_build_manifest_defaults_to_the_full_kg_distribution_target():
    g = build_manifest.build_manifest(build_manifest.DEFAULT_GRAPH_ENTITY)
    entity = rdflib.URIRef(f"https://www.synapse.org/Synapse:{build_manifest.DEFAULT_GRAPH_ENTITY}")
    assert (None, PROV.generated, entity) in g
