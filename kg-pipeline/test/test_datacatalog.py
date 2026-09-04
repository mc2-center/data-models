"""Fixture-based tests for the Data Catalog stage (native Synapse Dataset
entity annotations - see plans/datacatalog_kg_integration.md). A distinct
schema pass (mc2_model.linkml.yaml directly, the DataCatalog class) and its
own fixture, so this is self-contained rather than reusing
test/conftest.py's session fixtures - mirrors test_mc2_assay_file_view.py's
own pattern."""

from collections import defaultdict
from pathlib import Path

import build_datacatalog_triples
import build_triples
import extract_datacatalog
import harmonize
import pandas as pd
import rdflib

KG_PIPELINE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = str(KG_PIPELINE_DIR / "schema" / "mc2_model.linkml.yaml")
MAPPING_PATH = str(KG_PIPELINE_DIR.parent / "modules" / "mapping.yaml")
MODULES_DIR = str(KG_PIPELINE_DIR.parent / "modules")
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
SCHEMA = rdflib.Namespace("https://schema.org/")


def test_annotation_value_scalar_takes_first_value_only():
    ann = {"title": ["A Dataset Title"], "empty": []}
    assert extract_datacatalog.annotation_value(ann, "title", multivalued=False) == "A Dataset Title"
    assert extract_datacatalog.annotation_value(ann, "empty", multivalued=False) == ""
    assert extract_datacatalog.annotation_value(ann, "missing", multivalued=False) == ""


def test_annotation_value_multivalued_joins_with_pipe_delimiter():
    ann = {"keywords": ["Pancreas", "C57BL/6"]}
    assert extract_datacatalog.annotation_value(ann, "keywords", multivalued=True) == "Pancreas|C57BL/6"


class _FakeTableQueryResult:
    def __init__(self, df):
        self._df = df

    def asDataFrame(self):  # noqa: N802 - matches synapseclient's real method name
        return self._df


class _FakeSynapseForQuery:
    """Minimal stand-in for synapseclient.Synapse.tableQuery - no live network calls."""

    def __init__(self, df):
        self._df = df

    def tableQuery(self, query):  # noqa: N802 - matches synapseclient's real method name
        return _FakeTableQueryResult(self._df)


def test_find_dataset_entity_ids_deduplicates_and_warns_on_mismatch(capsys):
    df = pd.DataFrame({
        "datasetId": ["syn1", "syn1", "syn2", "syn3"],
        "downloadSynId": ["syn1", "syn1", "syn2", "syn_MISMATCH"],
    })
    syn = _FakeSynapseForQuery(df)
    ids = extract_datacatalog.find_dataset_entity_ids(syn, dataset_table_id="synTEST")
    assert ids == ["syn1", "syn2", "syn3"]  # deduplicated, datasetId used even on mismatch
    assert "WARNING" in capsys.readouterr().out


class _FakeSynapseForAnnotations:
    def __init__(self, annotations):
        self._annotations = annotations

    def get_annotations(self, entity_id):
        return self._annotations[entity_id]


def test_extract_datacatalog_rows_renames_license_and_datausemodifiers_to_schema_field_names():
    # Regression test: modules/dataCatalog/annotationProperty.csv renamed
    # these two attributes to dataCatalogLicense/dataCatalogDataUseModifiers,
    # but the live Synapse annotation keys are still license/dataUseModifiers.
    # extract_datacatalog.py must write the CSV under the renamed schema
    # field names, or harmonize.py/build_datacatalog_triples.py (which key
    # off schema/mc2_model.linkml.yaml) silently find nothing.
    syn = _FakeSynapseForAnnotations({
        "syn1": {"license": ["CC-BY 4.0"], "dataUseModifiers": ["Pending Annotation"]},
    })
    row = extract_datacatalog.extract_datacatalog_rows(syn, ["syn1"])[0]
    assert row["dataCatalogLicense"] == "CC-BY 4.0"
    assert row["dataCatalogDataUseModifiers"] == "Pending Annotation"
    assert "license" not in row
    assert "dataUseModifiers" not in row


def test_extract_datacatalog_rows_reads_known_keys_only():
    syn = _FakeSynapseForAnnotations({
        "syn1": {
            "title": ["A Dataset"], "species": ["Homo sapiens"], "creator": ["Jane Doe", "John Smith"],
            "entityType": ["dataset"], "newKey": [""], "Component": ["Dataset"],  # noise, must be ignored
        },
    })
    rows = extract_datacatalog.extract_datacatalog_rows(syn, ["syn1"])
    assert len(rows) == 1
    row = rows[0]
    assert row["DataCatalog_id"] == "syn1"
    assert row["title"] == "A Dataset"
    assert row["species"] == "Homo sapiens"
    assert row["creator"] == "Jane Doe|John Smith"  # multivalued
    assert "entityType" not in row
    assert "newKey" not in row
    assert "Component" not in row


def test_datacatalog_harmonizes_and_merges_onto_existing_dataset_subject(tmp_path):
    malformed_rows = []
    field_lookups = harmonize.build_field_lookups(
        SCHEMA_PATH, MAPPING_PATH, MODULES_DIR, malformed_rows, class_order=["DataCatalog"]
    )
    unmapped_rows, sssom_rows = [], defaultdict(set)
    out_path = tmp_path / "DataCatalog_harmonized.csv"
    harmonize.harmonize_table(
        "DataCatalog", str(FIXTURES_DIR / "DataCatalog.csv"), str(out_path), field_lookups, unmapped_rows, sssom_rows,
    )

    g, stats = build_datacatalog_triples.build_datacatalog_graph(str(tmp_path), SCHEMA_PATH)
    assert stats["schema"] > 0
    assert stats["cckp"] > 0
    assert stats["term"] > 0
    assert stats["doi"] == 1

    # Same subject IRI build_triples.py's own Dataset class pass would use for
    # this datasetId - this script must enrich it, not mint a separate node.
    subject = build_triples.mint_iri("Dataset", "syn_dc_1")
    assert (subject, SCHEMA.name, rdflib.Literal("Test Dataset Title")) in g
    assert (subject, SCHEMA.creator, rdflib.Literal("Jane Doe")) in g
    assert (subject, SCHEMA.creator, rdflib.Literal("John Smith")) in g
    assert (subject, CCKP.doiIri, rdflib.URIRef("https://doi.org/10.1234/test.doi")) in g
    # "Mus musculus" and "Meningioma" are real, already-curated NCIT mappings
    # in the committed modules/ CV CSVs (confirmed live before writing this
    # test, not guessed).
    assert (subject, CCKP.speciesTerm,
            rdflib.URIRef("http://purl.obolibrary.org/obo/NCIT_C14238")) in g
    assert (subject, CCKP.manifestationTerm,
            rdflib.URIRef("http://purl.obolibrary.org/obo/NCIT_C3230")) in g
    # accessType has no real ontology equivalent (confirmed non-mappable,
    # like Publication/Tool.accessibility) - literal present, no *Term edge.
    assert (subject, CCKP.accessType, rdflib.Literal("Open Access")) in g
    assert (subject, CCKP.accessTypeTerm, None) not in g
    # Regression coverage for the dataCatalogLicense/dataCatalogDataUseModifiers
    # rename (see test_extract_datacatalog_rows_renames_license_and_datausemodifiers_to_schema_field_names):
    # dataCatalogLicense still maps to the real schema.org "license" property
    # (SCHEMA_ORG_FIELDS is keyed by the schema field name, not "license"),
    # and resolves to the real SPDX term already curated in
    # modules/shared/studyLicense.csv. dataCatalogDataUseModifiers has no
    # schema.org equivalent, so it's cckp-namespaced; "Pending Annotation"
    # is a real DUO CV term with no ontology mapping (by design), so it gets
    # a literal but no *Term edge.
    assert (subject, SCHEMA.license, rdflib.Literal("CC-BY 4.0")) in g
    assert (subject, CCKP.dataCatalogLicenseTerm,
            rdflib.URIRef("https://spdx.org/licenses/CC-BY-4.0.html")) in g
    assert (subject, CCKP.dataCatalogDataUseModifiers, rdflib.Literal("Pending Annotation")) in g
    assert (subject, CCKP.dataCatalogDataUseModifiersTerm, None) not in g
