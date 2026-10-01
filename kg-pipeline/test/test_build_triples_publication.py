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


def test_malformed_integer_value_becomes_plain_literal_not_ill_typed(harmonized_dir, tmp_path, capsys):
    # rdflib doesn't raise on "PMC123"^^xsd:integer, it flags it ill_typed -
    # build_triples.py must fall back to a plain literal so PublicationShape's
    # sh:datatype check (not an ill-typed literal in Neptune) surfaces it, and
    # print a summary line so the downgrade isn't silent otherwise.
    import csv

    import build_triples
    from conftest import MC2_SCHEMA_PATH, SCHEMA_PATH

    src = harmonized_dir["dir"] / "Publication_harmonized.csv"
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))
    rows[0]["pubMedId"] = "PMC123"
    with open(tmp_path / "Publication_harmonized.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    schema_meta = build_triples.get_schema_metadata(SCHEMA_PATH)
    g = build_triples.build_class_graph(
        "Publication", schema_meta, str(tmp_path), {}, build_triples.load_prefixes(MC2_SCHEMA_PATH),
    )
    values = list(g.objects(None, CCKP["pubMedId"]))
    assert rdflib.Literal("PMC123") in values
    assert not any(v.ill_typed for v in values)

    captured = capsys.readouterr()
    assert "Publication: kept 1 ill-typed pubMedId value(s) as plain literals (expected xsd:integer)" in captured.out
