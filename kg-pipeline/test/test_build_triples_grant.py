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


def test_consortium_has_no_term_edge_at_all_now(rdf_graphs):
    # Grant.consortium's mc2_enum annotation was removed entirely this
    # session (see cckp_portal.linkml.yaml and test_harmonize.py's
    # test_grant_consortium_has_no_mc2_enum_and_passes_through_untracked) -
    # no surviving MC2 CV covers this field's real bare-acronym value space.
    # build_triples.py gates its *entire* Term-edge block - including the
    # confirmed_unmappable.tsv provisional-IRI fallback - on
    # `meta["mc2_enum"]` being truthy, so removing the annotation also
    # disabled the provisional mechanism for this field: "CCBIR" is a
    # confirmed_unmappable.tsv entry, but with no mc2_enum at all the field
    # is now untracked, not "attempted and confirmed unmappable", so it gets
    # no consortiumTerm edge of any kind (real or provisional) - just the
    # bare literal via the normal scalar/multivalued predicate.
    #
    # This is flagged, not silently patched: build_triples.py's gate could
    # be loosened to fire the confirmed_unmappable path independent of
    # mc2_enum (a field can be "known unmappable" without ever having had a
    # live CV), which would restore provisional-term treatment for consortium
    # acronyms like CCBIR. That's a real design change to core triple-
    # generation logic, left for a deliberate human decision alongside the
    # broader Consortium CV gap - see plans/crdc_cde_integration.md.
    g = rdf_graphs["Grant"]
    subject = rdflib.URIRef(DATA + "Grant/syn_grant_1")
    assert list(g.triples((subject, CCKP["consortiumTerm"], None))) == []
    assert (subject, CCKP["consortium"], rdflib.Literal("CCBIR")) in g
