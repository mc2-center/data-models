import rdflib

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
DATA = "https://w3id.org/mc2-center/cckp-portal/data/"


def test_identifier_falls_back_to_toolname(rdf_graphs):
    g = rdf_graphs["Tool"]
    subject = rdflib.URIRef(DATA + "Tool/TestTool")
    assert (subject, rdflib.RDF.type, CCKP["Tool"]) in g


def test_language_ontology_term_edge(rdf_graphs):
    g = rdf_graphs["Tool"]
    subject = rdflib.URIRef(DATA + "Tool/TestTool")
    swo_ada = rdflib.URIRef("http://www.ebi.ac.uk/swo/SWO_0000092")
    assert (subject, CCKP["languageTerm"], swo_ada) in g


def test_datasets_and_grant_and_publication_join_edges(rdf_graphs):
    g = rdf_graphs["Tool"]
    subject = rdflib.URIRef(DATA + "Tool/TestTool")
    assert (subject, CCKP["datasetsRef"], rdflib.URIRef(DATA + "Dataset/syn_ds_1")) in g
    assert (subject, CCKP["grantNumberRef"], rdflib.URIRef(DATA + "Grant/syn_grant_1")) in g
    assert (subject, CCKP["pubMedIdRef"], rdflib.URIRef(DATA + "Publication/12345678")) in g


def _build_tool_graph_with_portal_display(tmp_path, raw_value):
    import csv

    import build_triples
    from conftest import MC2_SCHEMA_PATH, SCHEMA_PATH

    with open(tmp_path / "Tool_harmonized.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["toolName", "portalDisplay"])
        writer.writeheader()
        writer.writerow({"toolName": "TestTool", "portalDisplay": raw_value})

    schema_meta = build_triples.get_schema_metadata(SCHEMA_PATH)
    return build_triples.build_class_graph(
        "Tool", schema_meta, str(tmp_path), {}, build_triples.load_prefixes(MC2_SCHEMA_PATH),
    )


def test_capitalized_boolean_value_becomes_typed_xsd_boolean(tmp_path):
    # The CCKP portal emits capitalized "True"/"False"/"1"/"0", none of which
    # are in xsd:boolean's lexical space (true/false/1/0, case-sensitive) -
    # build_triples.py must normalize these to the canonical lexical form
    # rather than downgrade every boolean field to a plain literal.
    for raw_value, expected_lexical in [("True", "true"), ("FALSE", "false"), ("1", "true"), ("0", "false")]:
        g = _build_tool_graph_with_portal_display(tmp_path, raw_value)
        subject = rdflib.URIRef(DATA + "Tool/TestTool")
        values = list(g.objects(subject, CCKP["portalDisplay"]))
        assert values == [rdflib.Literal(expected_lexical, datatype=rdflib.XSD.boolean)]
        assert not values[0].ill_typed


def test_non_boolean_value_in_boolean_field_becomes_plain_literal_and_is_reported(tmp_path, capsys):
    g = _build_tool_graph_with_portal_display(tmp_path, "Not Available")
    subject = rdflib.URIRef(DATA + "Tool/TestTool")
    values = list(g.objects(subject, CCKP["portalDisplay"]))
    assert values == [rdflib.Literal("Not Available")]
    assert not values[0].ill_typed

    captured = capsys.readouterr()
    assert "Tool: kept 1 ill-typed portalDisplay value(s) as plain literals (expected xsd:boolean)" in captured.out
