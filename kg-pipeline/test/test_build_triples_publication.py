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


def test_bare_doi_is_templated_to_resolvable_iri(rdf_graphs):
    g = rdf_graphs["Publication"]
    subject = rdflib.URIRef(DATA + "Publication/12345678")
    assert (subject, CCKP["doiIri"], rdflib.URIRef("https://doi.org/10.1000/test")) in g


def test_numeric_pubmed_id_is_templated_to_resolvable_iri(rdf_graphs):
    g = rdf_graphs["Publication"]
    subject = rdflib.URIRef(DATA + "Publication/12345678")
    assert (subject, CCKP["pubMedIdIri"], rdflib.URIRef("https://pubmed.ncbi.nlm.nih.gov/12345678")) in g


def test_sentinel_placeholder_values_get_no_external_iri():
    import build_triples

    assert build_triples.external_iri("doi", "DOI Not Available") is None
    assert build_triples.external_iri("pubmed", "Pending Annotation") is None
    assert build_triples.external_iri("pubmed", "Under Review") is None


def test_doi_shaped_value_in_a_pubmed_field_is_still_recognized():
    import build_triples

    # EducationalResource.publicationId is declared as a PubMed-join field,
    # but live CCKP data has at least one row holding a DOI there instead -
    # detection is by value shape, not by trusting the field's declared kind.
    assert build_triples.external_iri("pubmed", "https://doi.org/10.7303/syn66527467") == \
        "https://doi.org/10.7303/syn66527467"
