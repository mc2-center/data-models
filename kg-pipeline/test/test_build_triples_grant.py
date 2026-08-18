import rdflib

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
DATA = "https://w3id.org/mc2-center/cckp-portal/data/"


def test_grant_has_no_outbound_joins(rdf_graphs):
    # Grant is the hub referenced BY other classes; it has no cckp_join
    # slots of its own in v1 scope.
    g = rdf_graphs["Grant"]
    subject = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    assert (subject, rdflib.RDF.type, CCKP["Grant"]) in g
    assert (subject, CCKP["grantName"], rdflib.Literal("Test Grant One")) in g
    ref_predicates = [p for _, p, _ in g.triples((subject, None, None)) if str(p).endswith("Ref")]
    assert ref_predicates == []


def test_theme_now_has_a_term_edge(rdf_graphs):
    # See test_harmonize.py's matching test - theme_name.csv was curated
    # with a real NCIT identifier for "Metastasis".
    g = rdf_graphs["Grant"]
    subject = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    ncit_metastasis = rdflib.URIRef("http://purl.obolibrary.org/obo/NCIT_C19151")
    assert (subject, CCKP["themeTerm"], ncit_metastasis) in g


def test_consortium_still_has_no_term_edge(rdf_graphs):
    # consortium_name.csv still has zero ontology-mapped rows - see
    # test_harmonize.py's matching test.
    g = rdf_graphs["Grant"]
    subject = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    assert list(g.triples((subject, CCKP["consortiumTerm"], None))) == []
