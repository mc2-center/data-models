from datetime import datetime, timezone

import rdflib

import build_manifest

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
VOID = rdflib.Namespace("http://rdfs.org/ns/void#")

BUILD_TIME = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)


def test_build_manifest_dual_types_activity_as_prov_activity_and_void_dataset():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main")
    activity = CCKP["kgBuild_abc123"]
    assert (activity, rdflib.RDF.type, PROV.Activity) in g
    assert (activity, rdflib.RDF.type, VOID.Dataset) in g
    assert (activity, PROV.generatedAtTime, rdflib.Literal(BUILD_TIME.isoformat(), datatype=rdflib.XSD.dateTime)) in g


def test_build_manifest_subject_is_keyed_by_commit_sha_when_available():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main")
    activity = CCKP["kgBuild_abc123"]
    assert (activity, CCKP.gitCommit, rdflib.Literal("abc123")) in g
    assert (activity, CCKP.gitRef, rdflib.Literal("main")) in g
    assert (activity, PROV.used, rdflib.URIRef("https://github.com/mc2-center/data-models/commit/abc123")) in g


def test_build_manifest_falls_back_to_a_timestamp_id_with_no_git_metadata():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha=None, branch=None)
    activity = CCKP["kgBuild_20260915T120000Z"]
    assert (activity, rdflib.RDF.type, PROV.Activity) in g
    # No commit resolvable - no gitCommit/gitRef/prov:used triples asserted at all.
    assert list(g.triples((activity, CCKP.gitCommit, None))) == []
    assert list(g.triples((activity, PROV.used, None))) == []


def test_build_manifest_dataDump_points_at_the_given_target():
    g = build_manifest.build_manifest("s3://some-bucket/cckp/2026-09-15/", build_time=BUILD_TIME,
                                       commit_sha="abc123", branch="main")
    activity = CCKP["kgBuild_abc123"]
    assert (activity, VOID.dataDump, rdflib.URIRef("s3://some-bucket/cckp/2026-09-15/")) in g


def test_build_manifest_records_the_portal_name():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, portal="cckp",
                                       commit_sha="abc123", branch="main")
    activity = CCKP["kgBuild_abc123"]
    assert (activity, CCKP.portal, rdflib.Literal("cckp")) in g


def test_default_data_dump_points_at_the_full_kg_synapse_distribution_target():
    assert build_manifest.DEFAULT_DATA_DUMP == "https://www.synapse.org/Synapse:syn77443315"


def test_build_manifest_emits_triples_as_xsd_integer_when_given():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main",
                                       triples=1234)
    activity = CCKP["kgBuild_abc123"]
    assert (activity, VOID.triples, rdflib.Literal(1234, datatype=rdflib.XSD.integer)) in g


def test_build_manifest_omits_triples_when_not_given():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main")
    activity = CCKP["kgBuild_abc123"]
    assert list(g.triples((activity, VOID.triples, None))) == []


def test_build_manifest_emits_snapshot_date_as_xsd_date_when_given():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main",
                                       snapshot_date="2026-09-15")
    activity = CCKP["kgBuild_abc123"]
    assert (activity, CCKP.snapshotDate, rdflib.Literal("2026-09-15", datatype=rdflib.XSD.date)) in g


def test_build_manifest_omits_snapshot_date_when_not_given():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main")
    activity = CCKP["kgBuild_abc123"]
    assert list(g.triples((activity, CCKP.snapshotDate, None))) == []


def test_build_manifest_emits_deposited_at_time_as_xsd_datetime_when_given():
    deposited_at = datetime(2026, 9, 15, 13, 30, 0, tzinfo=timezone.utc)
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main",
                                       deposited_at=deposited_at)
    activity = CCKP["kgBuild_abc123"]
    assert (activity, CCKP.depositedAtTime,
            rdflib.Literal(deposited_at.isoformat(), datatype=rdflib.XSD.dateTime)) in g


def test_build_manifest_omits_deposited_at_time_when_not_given():
    g = build_manifest.build_manifest("syn77443315", build_time=BUILD_TIME, commit_sha="abc123", branch="main")
    activity = CCKP["kgBuild_abc123"]
    assert list(g.triples((activity, CCKP.depositedAtTime, None))) == []
