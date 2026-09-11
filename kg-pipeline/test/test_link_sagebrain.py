import link_sagebrain
import rdflib

SAGEBRAIN = rdflib.Namespace("https://w3id.org/synapse/sagebrain#")
BIOLINK = rdflib.Namespace("https://w3id.org/biolink/vocab/")


def test_load_crosswalk_skips_sssom_comment_header(tmp_path):
    path = tmp_path / "crosswalk.sssom.tsv"
    path.write_text(
        "# curie_map:\n#   skos: http://www.w3.org/2004/02/skos/core#\n"
        "subject_id\tsubject_label\tpredicate_id\tobject_id\tobject_label\tmapping_justification\tconfidence\n"
        "NCIT:C12971\tBreast\tskos:exactMatch\tUBERON:0000310\tbreast\tsemapv:LexicalMatching\thigh\n"
        "NCIT:C99999\tLow Confidence Term\tskos:exactMatch\tUBERON:9999999\tunrelated\tsemapv:LexicalMatching\tlow\n"
    )
    crosswalk = link_sagebrain.load_crosswalk(str(path))
    assert crosswalk == {"NCIT:C12971": "UBERON:0000310"}


def test_curie_from_resolved_reverses_obo_purl():
    assert link_sagebrain.curie_from_resolved("http://purl.obolibrary.org/obo/NCIT_C12971") == "NCIT:C12971"


def test_curie_from_resolved_passes_through_a_bare_curie():
    assert link_sagebrain.curie_from_resolved("NCIT:C12971") == "NCIT:C12971"


def test_curie_from_resolved_treats_blank_as_unresolved():
    assert link_sagebrain.curie_from_resolved("") is None
    assert link_sagebrain.curie_from_resolved(None) is None


def test_aggregate_flags_conflicting_values_across_files_sharing_a_key():
    rows = [
        {"Biospecimen Key": "BSP-1", "Tissue_ontology_iri": "http://purl.obolibrary.org/obo/NCIT_C12971",
         "Tumor Type_ontology_iri": ""},
        {"Biospecimen Key": "BSP-1", "Tissue_ontology_iri": "http://purl.obolibrary.org/obo/NCIT_C12468",
         "Tumor Type_ontology_iri": ""},  # disagrees with row 1
    ]
    resolved, conflicts = link_sagebrain.aggregate_by_biospecimen_key(rows)
    assert len(conflicts) == 1
    assert conflicts[0]["biospecimen_key"] == "BSP-1"
    assert conflicts[0]["field"] == "Tissue"
    assert "BSP-1" in resolved  # still emits a best-effort value, doesn't block on the conflict


def test_sentinel_biospecimen_keys_are_skipped():
    rows = [{"Biospecimen Key": "Not Applicable", "Tissue_ontology_iri": "http://purl.obolibrary.org/obo/NCIT_C12971",
             "Tumor Type_ontology_iri": ""}]
    resolved, conflicts = link_sagebrain.aggregate_by_biospecimen_key(rows)
    assert resolved == {}


def test_build_sagebrain_links_end_to_end(tmp_path):
    harmonized_csv = tmp_path / "File View_harmonized.csv"
    harmonized_csv.write_text(
        "Biospecimen Key,Tissue_ontology_iri,Tumor Type_ontology_iri\n"
        "BSP-1,http://purl.obolibrary.org/obo/NCIT_C12971,http://purl.obolibrary.org/obo/NCIT_C71732\n"
    )
    tissue_cw = tmp_path / "tissue.sssom.tsv"
    tissue_cw.write_text(
        "subject_id\tsubject_label\tpredicate_id\tobject_id\tobject_label\tmapping_justification\tconfidence\n"
        "NCIT:C12971\tBreast\tskos:exactMatch\tUBERON:0000310\tbreast\tsemapv:LexicalMatching\thigh\n"
    )
    tumor_cw = tmp_path / "tumortype.sssom.tsv"
    tumor_cw.write_text(
        "subject_id\tsubject_label\tpredicate_id\tobject_id\tobject_label\tmapping_justification\tconfidence\n"
        "NCIT:C71732\tTriple-Negative Breast Carcinoma\tskos:exactMatch\tMONDO:0005494\t"
        "triple-negative breast carcinoma\tsemapv:LexicalMatching\thigh\n"
    )

    g, conflicts, n_source_tissue, n_has_pathology = link_sagebrain.build_sagebrain_links(
        str(harmonized_csv), str(tissue_cw), str(tumor_cw),
    )
    assert conflicts == []
    assert n_source_tissue == 1
    assert n_has_pathology == 1
    subject = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Biospecimen/BSP-1")
    assert (subject, rdflib.RDF.type, BIOLINK.MaterialSample) in g
    assert (subject, SAGEBRAIN.source_tissue, rdflib.URIRef("http://purl.obolibrary.org/obo/UBERON_0000310")) in g
    assert (subject, SAGEBRAIN.has_pathology, rdflib.URIRef("http://purl.obolibrary.org/obo/MONDO_0005494")) in g
