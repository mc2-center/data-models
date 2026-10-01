import rdflib

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
DATA = "https://w3id.org/mc2-center/cckp-portal/data/"


def test_identifier_falls_back_to_alias_when_internal_identifier_blank(rdf_graphs):
    # internalIdentifier is blank in the fixture (matching live data - see
    # schema comments); `alias` is the practical id.
    g = rdf_graphs["EducationalResource"]
    subject = rdflib.URIRef(DATA + "EducationalResource/syn_edu_alias_1")
    assert (subject, rdflib.RDF.type, CCKP["EducationalResource"]) in g
    assert (subject, CCKP["title"], rdflib.Literal("Test Educational Resource")) in g


def test_topic_ontology_term_edge(rdf_graphs):
    g = rdf_graphs["EducationalResource"]
    subject = rdflib.URIRef(DATA + "EducationalResource/syn_edu_alias_1")
    ncit_evolution = rdflib.URIRef("http://purl.obolibrary.org/obo/NCIT_C16565")
    assert (subject, CCKP["topicTerm"], ncit_evolution) in g


def test_grant_and_publication_join_edges(rdf_graphs):
    g = rdf_graphs["EducationalResource"]
    subject = rdflib.URIRef(DATA + "EducationalResource/syn_edu_alias_1")
    assert (subject, CCKP["grantNumberRef"], rdflib.URIRef(DATA + "Grant/syn_grant_1")) in g
    assert (subject, CCKP["publicationIdRef"], rdflib.URIRef(DATA + "Publication/12345678")) in g
