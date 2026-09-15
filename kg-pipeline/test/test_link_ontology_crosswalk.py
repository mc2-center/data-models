import csv

import rdflib

import link_ontology_crosswalk as loc

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")

CROSSWALK_HEADER = ["subject_id", "subject_label", "predicate_id", "object_id", "object_label",
                     "mapping_justification", "confidence", "reviewed"]
PREFIXES = {"NCIT": "http://purl.obolibrary.org/obo/NCIT_", "MONDO": "http://purl.obolibrary.org/obo/MONDO_"}


def write_tsv(path, header, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)


def test_load_reviewed_crosswalk_skips_unreviewed_rows(tmp_path):
    path = tmp_path / "crosswalk.tsv"
    write_tsv(path, CROSSWALK_HEADER, [
        ["NCIT:C3510", "Cutaneous Melanoma", "skos:exactMatch", "MONDO:0005012", "cutaneous melanoma",
         "semapv:LexicalMatching", "high", "true"],
        ["NCIT:C3168", "Adenocarcinoma", "skos:exactMatch", "MONDO:0004970", "adenocarcinoma",
         "semapv:LexicalMatching", "high", "false"],
    ])
    index = loc.load_reviewed_crosswalk(str(path), PREFIXES)
    assert list(index) == ["http://purl.obolibrary.org/obo/NCIT_C3510"]
    assert index["http://purl.obolibrary.org/obo/NCIT_C3510"] == ("MONDO:0005012", "cutaneous melanoma")


def test_load_reviewed_crosswalk_missing_file_returns_empty(tmp_path):
    assert loc.load_reviewed_crosswalk(str(tmp_path / "nope.tsv"), PREFIXES) == {}


def test_link_field_emits_edge_only_for_reviewed_hit(tmp_path):
    harmonized_dir = tmp_path
    with open(harmonized_dir / "Dataset_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datasetId", "tumorType", "tumorType_ontology_iri"])
        writer.writerow(["syn1", "Cutaneous Melanoma", "http://purl.obolibrary.org/obo/NCIT_C3510"])
        writer.writerow(["syn2", "Adenocarcinoma", "http://purl.obolibrary.org/obo/NCIT_C3168"])  # not reviewed
    with open(harmonized_dir / "Publication_harmonized.csv", "w", newline="") as f:
        csv.writer(f).writerow(["pubMedId", "tumorType", "tumorType_ontology_iri"])  # empty table

    crosswalk_index = {"http://purl.obolibrary.org/obo/NCIT_C3510": ("MONDO:0005012", "cutaneous melanoma")}

    g = rdflib.Graph()
    n_edges, n_rows = loc.link_field(g, str(harmonized_dir), "tumorType", crosswalk_index, "Mondo", PREFIXES)
    assert n_edges == 1
    assert n_rows == 1

    reviewed_subject = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Dataset/syn1")
    target = rdflib.URIRef("http://purl.obolibrary.org/obo/MONDO_0005012")
    assert (reviewed_subject, CCKP.tumorTypeMondoTerm, target) in g

    unreviewed_subject = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Dataset/syn2")
    assert (unreviewed_subject, CCKP.tumorTypeMondoTerm, None) not in g


def test_link_field_never_touches_existing_ncit_term_edge(tmp_path):
    """This script only ever adds a *new* predicate (cckp:{field}MondoTerm) -
    it must never write to cckp:{field}Term, the NCIT edge build_triples.py
    already emits, confirming the promotion is additive, not a replacement."""
    harmonized_dir = tmp_path
    with open(harmonized_dir / "Dataset_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datasetId", "tumorType", "tumorType_ontology_iri"])
        writer.writerow(["syn1", "Cutaneous Melanoma", "http://purl.obolibrary.org/obo/NCIT_C3510"])
    with open(harmonized_dir / "Publication_harmonized.csv", "w", newline="") as f:
        csv.writer(f).writerow(["pubMedId", "tumorType", "tumorType_ontology_iri"])

    crosswalk_index = {"http://purl.obolibrary.org/obo/NCIT_C3510": ("MONDO:0005012", "cutaneous melanoma")}
    g = rdflib.Graph()
    loc.link_field(g, str(harmonized_dir), "tumorType", crosswalk_index, "Mondo", PREFIXES)
    assert (None, CCKP.tumorTypeTerm, None) not in g


def test_build_ontology_crosswalk_links_end_to_end(tmp_path):
    harmonized_dir = tmp_path / "harmonized"
    harmonized_dir.mkdir()
    with open(harmonized_dir / "Dataset_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datasetId", "tumorType", "tumorType_ontology_iri", "tissue", "tissue_ontology_iri"])
        writer.writerow(["syn1", "Cutaneous Melanoma", "http://purl.obolibrary.org/obo/NCIT_C3510",
                          "Vein", "http://purl.obolibrary.org/obo/NCIT_C12814"])
    with open(harmonized_dir / "Publication_harmonized.csv", "w", newline="") as f:
        csv.writer(f).writerow(["pubMedId", "tumorType", "tumorType_ontology_iri", "tissue", "tissue_ontology_iri"])

    tumor_cw = tmp_path / "tumor.tsv"
    write_tsv(tumor_cw, CROSSWALK_HEADER, [
        ["NCIT:C3510", "Cutaneous Melanoma", "skos:exactMatch", "MONDO:0005012", "cutaneous melanoma",
         "semapv:LexicalMatching", "high", "true"],
    ])
    tissue_cw = tmp_path / "tissue.tsv"
    write_tsv(tissue_cw, CROSSWALK_HEADER, [
        ["NCIT:C12814", "Vein", "skos:exactMatch", "UBERON:0001638", "vein",
         "semapv:LexicalMatching", "high", "true"],
    ])
    mc2_schema = tmp_path / "mc2_model.linkml.yaml"
    mc2_schema.write_text(
        "id: https://example.org/test\nname: test\nprefixes:\n"
        "  NCIT: http://purl.obolibrary.org/obo/NCIT_\n"
        "  MONDO: http://purl.obolibrary.org/obo/MONDO_\n"
        "  UBERON: http://purl.obolibrary.org/obo/UBERON_\n"
    )

    g, stats = loc.build_ontology_crosswalk_links(
        str(harmonized_dir), str(mc2_schema),
        crosswalk_overrides={"tumorType": str(tumor_cw), "tissue": str(tissue_cw)},
    )

    assert stats["tumorType"] == {"reviewed_rows": 1, "edges": 1, "rows_linked": 1, "predicate": "tumorTypeMondoTerm"}
    assert stats["tissue"] == {"reviewed_rows": 1, "edges": 1, "rows_linked": 1, "predicate": "tissueUberonTerm"}

    dataset = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Dataset/syn1")
    assert (dataset, CCKP.tumorTypeMondoTerm,
            rdflib.URIRef("http://purl.obolibrary.org/obo/MONDO_0005012")) in g
    assert (dataset, CCKP.tissueUberonTerm,
            rdflib.URIRef("http://purl.obolibrary.org/obo/UBERON_0001638")) in g
