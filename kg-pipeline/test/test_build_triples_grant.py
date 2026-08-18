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


def test_consortium_still_has_no_real_ontology_term_edge(rdf_graphs):
    # consortium_name.csv still has zero ontology-mapped rows - see
    # test_harmonize.py's matching test. It may still get a *provisional*
    # local term edge (see test_confirmed_unmappable_value_gets_provisional_term_
    # not_bare_literal below) - this only asserts no *external* ontology IRI.
    g = rdf_graphs["Grant"]
    subject = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    real_ontology_edges = [
        o for _, _, o in g.triples((subject, CCKP["consortiumTerm"], None))
        if not str(o).startswith("https://w3id.org/mc2-center/cckp-portal/terms/")
    ]
    assert real_ontology_edges == []


def test_confirmed_unmappable_value_gets_provisional_term_not_bare_literal(rdf_graphs):
    # Grant.csv's fixture consortium value "CCBIR" is one of the confirmed-
    # unmappable entries in mappings/confirmed_unmappable.tsv (an NCI-internal
    # program acronym with no real ontology/registry home) - it should still
    # get a cckp:consortiumTerm edge to an addressable, explicitly-flagged
    # provisional local IRI, not just the plain literal.
    g = rdf_graphs["Grant"]
    subject = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    provisional_iri = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/terms/consortium/ccbir")
    assert (subject, CCKP["consortiumTerm"], provisional_iri) in g
    assert (provisional_iri, CCKP["provisional"], rdflib.Literal(True)) in g
