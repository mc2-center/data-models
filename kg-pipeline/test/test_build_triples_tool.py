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
