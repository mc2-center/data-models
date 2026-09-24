import csv

import rdflib

import build_triples

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
GOV = rdflib.Namespace("https://w3id.org/synapse/governance#")


def test_mint_iri_uses_canonical_synapse_iri_for_a_real_synapse_id():
    assert build_triples.mint_iri("Dataset", "syn61795461") == \
        rdflib.URIRef("https://www.synapse.org/Synapse:syn61795461")


def test_mint_iri_is_case_insensitive_for_synapse_ids():
    assert build_triples.mint_iri("Dataset", "SYN61795461") == \
        rdflib.URIRef("https://www.synapse.org/Synapse:SYN61795461")


def test_mint_iri_falls_back_to_placeholder_namespace_for_non_synapse_ids():
    # Organization/Program/Person ids minted by link_scdm.py, and any
    # Publication/Tool/EducationalResource row falling back to a non-Synapse
    # key, never look like a bare "synNNN..." id.
    assert build_triples.mint_iri("Organization", "org.sage-bionetworks") == \
        rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Organization/org.sage-bionetworks")
    assert build_triples.mint_iri("Publication", "12345678") == \
        rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Publication/12345678")


def test_mint_iri_does_not_treat_a_synapse_shaped_substring_as_a_synapse_id():
    # Has a "syn" + digits *inside* it, but isn't itself bare "synNNN...".
    assert build_triples.mint_iri("Biospecimen", "syn123-aliquot-2") == \
        rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Biospecimen/syn123-aliquot-2")


def write_dataset_harmonized_csv(harmonized_dir, dataset_id):
    path = harmonized_dir / "Dataset_harmonized.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datasetId", "datasetName"])
        writer.writerow([dataset_id, "Test Dataset"])
    return path


def test_dataset_row_with_real_synapse_id_is_addressed_as_synapse_entity(tmp_path):
    write_dataset_harmonized_csv(tmp_path, "syn61795461")
    schema_meta = {"Dataset": {
        "datasetId": {"multivalued": False, "range": "string", "mc2_enum": None, "cckp_join": None},
        "datasetName": {"multivalued": False, "range": "string", "mc2_enum": None, "cckp_join": None},
    }}
    g = build_triples.build_class_graph("Dataset", schema_meta, str(tmp_path), join_indices={}, mc2_prefixes={})

    subject = rdflib.URIRef("https://www.synapse.org/Synapse:syn61795461")
    assert (subject, rdflib.RDF.type, CCKP["Dataset"]) in g
    # Never minted as a second, parallel w3id identifier for a row that
    # already has one in Synapse.
    assert not any(str(s).startswith("https://w3id.org/mc2-center/cckp-portal/data/Dataset/")
                   for s, _, _ in g.triples((None, rdflib.RDF.type, CCKP["Dataset"])))


def test_synapse_canonical_subject_is_not_typed_as_gov_synapse_entity(tmp_path):
    # Deliberate, not an oversight: governanceDUO owns gov:SynapseEntity, and
    # its shape:SynapseEntityShape is sh:closed with a required
    # gov:benefactor (Synapse ACL metadata this pipeline doesn't have).
    # Asserting the type here would violate sagebrain-model's own "one owner
    # per term and shape" principle (D9) the moment the two graphs' shapes
    # are validated together - see plans/kg_pipeline_sagebrain_alignment.md.
    # The cross-graph join works via the shared syn:synNNN IRI alone.
    write_dataset_harmonized_csv(tmp_path, "syn61795461")
    schema_meta = {"Dataset": {
        "datasetId": {"multivalued": False, "range": "string", "mc2_enum": None, "cckp_join": None},
        "datasetName": {"multivalued": False, "range": "string", "mc2_enum": None, "cckp_join": None},
    }}
    g = build_triples.build_class_graph("Dataset", schema_meta, str(tmp_path), join_indices={}, mc2_prefixes={})

    assert not any(g.triples((None, rdflib.RDF.type, GOV.SynapseEntity)))
