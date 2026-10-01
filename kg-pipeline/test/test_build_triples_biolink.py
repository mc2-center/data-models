import csv

import rdflib

import build_triples

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
BIOLINK = rdflib.Namespace("https://w3id.org/biolink/vocab/")


def test_only_the_five_cckp_portal_classes_have_a_biolink_mapping():
    # MC2 assay-metadata classes (Biospecimen, "File View", ...) share this
    # same build_class_graph() dual-typing branch via their own --classes
    # pipeline run, but Biolink has no meaningful class for most of them -
    # BIOLINK_TYPE.get() returning None for those is what skips the second
    # rdf:type triple, so the mapping must stay scoped to classes it's
    # actually been reviewed for.
    assert set(build_triples.BIOLINK_TYPE) == {"Dataset", "Publication", "Tool", "Grant", "EducationalResource"}


def test_dataset_row_is_dual_typed_with_biolink(tmp_path):
    path = tmp_path / "Dataset_harmonized.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datasetId", "datasetName"])
        writer.writerow(["syn61795461", "Test Dataset"])

    schema_meta = {"Dataset": {
        "datasetId": {"multivalued": False, "range": "string", "mc2_enum": None, "cckp_join": None},
        "datasetName": {"multivalued": False, "range": "string", "mc2_enum": None, "cckp_join": None},
    }}
    g = build_triples.build_class_graph("Dataset", schema_meta, str(tmp_path), join_indices={}, mc2_prefixes={})

    subject = rdflib.URIRef("https://www.synapse.org/Synapse:syn61795461")
    assert (subject, rdflib.RDF.type, CCKP["Dataset"]) in g
    assert (subject, rdflib.RDF.type, BIOLINK["Dataset"]) in g
