import rdflib

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
DATA = "https://w3id.org/mc2-center/cckp-portal/data/"


def test_identifier_falls_back_to_pubmedid(rdf_graphs):
    # Publication has no declared LinkML `identifier` slot (see schema
    # comments); pubMedId is the practical id used to mint the IRI.
    g = rdf_graphs["Publication"]
    subject = rdflib.URIRef(DATA + "Publication/12345678")
    assert (subject, rdflib.RDF.type, CCKP["Publication"]) in g
    assert (subject, CCKP["publicationTitle"], rdflib.Literal("Test Publication One")) in g


def test_dataset_join_edge_resolves_via_alias(rdf_graphs):
    g = rdf_graphs["Publication"]
    subject = rdflib.URIRef(DATA + "Publication/12345678")
    dataset_iri = rdflib.URIRef(DATA + "Dataset/syn_ds_1")
    assert (subject, CCKP["datasetRef"], dataset_iri) in g


def test_grant_join_edge_resolves(rdf_graphs):
    g = rdf_graphs["Publication"]
    subject = rdflib.URIRef(DATA + "Publication/12345678")
    grant_iri = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    assert (subject, CCKP["grantNumberRef"], grant_iri) in g
