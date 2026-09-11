import rdflib

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
DATA = "https://w3id.org/mc2-center/cckp-portal/data/"


def test_rdf_type_and_literal_triples(rdf_graphs):
    g = rdf_graphs["Dataset"]
    subject = rdflib.URIRef(DATA + "Dataset/syn_ds_1")
    assert (subject, rdflib.RDF.type, CCKP["Dataset"]) in g
    assert (subject, CCKP["datasetName"], rdflib.Literal("Test Dataset One")) in g


def test_ontology_term_edge_emitted_for_resolved_value(rdf_graphs):
    g = rdf_graphs["Dataset"]
    subject = rdflib.URIRef(DATA + "Dataset/syn_ds_1")
    ncit_melanoma = rdflib.URIRef("http://purl.obolibrary.org/obo/NCIT_C3510")
    assert (subject, CCKP["tumorTypeTerm"], ncit_melanoma) in g


def test_no_ontology_term_edge_for_unresolved_value(rdf_graphs):
    g = rdf_graphs["Dataset"]
    subject = rdflib.URIRef(DATA + "Dataset/syn_ds_2")
    # tumorType is unresolved for this row - the literal is still present...
    assert (subject, CCKP["tumorType"], rdflib.Literal("Completely Made Up Tumor Type")) in g
    # ...but no tumorTypeTerm edge should exist for this subject.
    assert list(g.triples((subject, CCKP["tumorTypeTerm"], None))) == []


def test_grant_join_edge_resolves(rdf_graphs):
    g = rdf_graphs["Dataset"]
    subject = rdflib.URIRef(DATA + "Dataset/syn_ds_1")
    grant_iri = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    assert (subject, CCKP["grantNumberRef"], grant_iri) in g


def test_publication_join_edge_resolves_via_pubmedid(rdf_graphs):
    g = rdf_graphs["Dataset"]
    subject = rdflib.URIRef(DATA + "Dataset/syn_ds_2")  # this row has pubMedId=12345678
    pub_iri = rdflib.URIRef(DATA + "Publication/12345678")
    assert (subject, CCKP["pubMedIdRef"], pub_iri) in g
