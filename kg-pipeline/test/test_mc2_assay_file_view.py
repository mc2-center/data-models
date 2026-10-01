"""End-to-end fixture test for the MC2 assay-metadata pipeline's "File View"
class - a distinct schema (mc2_model.linkml.yaml directly, not
cckp_portal.linkml.yaml) and class list from the rest of test/conftest.py's
session fixtures, so this is self-contained rather than reusing them."""

from collections import defaultdict
from pathlib import Path

import build_triples
import extract_mc2_assay_metadata as extract_mod
import harmonize

KG_PIPELINE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = str(KG_PIPELINE_DIR / "schema" / "mc2_model.linkml.yaml")
MAPPING_PATH = str(KG_PIPELINE_DIR.parent / "modules" / "mapping.yaml")
MODULES_DIR = str(KG_PIPELINE_DIR.parent / "modules")
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_class_slug_strips_spaces_and_is_a_noop_on_single_word_classes():
    assert build_triples.class_slug("File View") == "FileView"
    assert build_triples.class_slug("Dataset") == "Dataset"


def test_field_slug_camel_cases_spaced_and_underscored_names():
    assert build_triples.field_slug("File Level") == "fileLevel"
    assert build_triples.field_slug("FileView_id") == "fileViewId"
    assert build_triples.field_slug("Biospecimen Key") == "biospecimenKey"
    # idempotent on cckp_portal.linkml.yaml's already-camelCase field names
    assert build_triples.field_slug("datasetId") == "datasetId"
    assert build_triples.field_slug("grantNumber") == "grantNumber"


def test_annotation_values_joins_multivalued_with_pipe_delimiter():
    ann = {"FileDataUseCodes": ["GRU", "NPU"], "FileFormat": ["TXT"], "FileLevel": []}
    assert extract_mod.annotation_values(ann, "FileDataUseCodes") == "GRU|NPU"
    assert extract_mod.annotation_values(ann, "FileFormat") == "TXT"
    assert extract_mod.annotation_values(ann, "FileLevel") == ""
    assert extract_mod.annotation_values(ann, "NotPresent") == ""


def test_discover_dataset_entities_filters_by_concrete_type(monkeypatch):
    from synapseclient.models import Dataset, DatasetCollection, Folder

    entities = {
        "syn1": Dataset(id="syn1"),
        "syn2": Folder(id="syn2"),
        "syn3": DatasetCollection(id="syn3"),
    }
    # synapseclient.operations.get(...) (imported as extract_mod.syn_get)
    # replaces syn.get(...) - stand in for it directly, returning real (but
    # network-free) dataclass model instances so isinstance() checks in
    # discover_dataset_entities() behave exactly as they would live.
    monkeypatch.setattr(extract_mod, "syn_get", lambda entity_id, **kwargs: entities[entity_id])
    confirmed, skipped = extract_mod.discover_dataset_entities(None, ["syn1", "syn2", "syn3"], sleep_s=0)
    assert confirmed == ["syn1", "syn3"]
    assert skipped == {"Folder": 1}


def test_extract_file_view_rows_maps_annotation_keys_to_attribute_names(monkeypatch):
    from synapseclient.models import Dataset, EntityRef

    dataset = Dataset(id="syn_ds", items=[EntityRef(id="syn_file_1", version=1)])
    monkeypatch.setattr(extract_mod, "syn_get", lambda entity_id, **kwargs: dataset)

    fake_annotations = {
        "FileViewId": ["syn_file_1"], "BiospecimenKey": ["BSP-01"], "FileAssay": ["RNA-Seq"],
        "FileSpecies": ["Human"], "Component": ["FileView"], "Id": ["uuid-1"],
    }

    class _FakeFile:
        def __init__(self, id, download_file):  # noqa: A002 - matches File(id=..., download_file=...)
            self.annotations = None

        def get(self, synapse_client=None):
            self.annotations = fake_annotations
            return self

    monkeypatch.setattr(extract_mod, "File", _FakeFile)

    rows = extract_mod.extract_file_view_rows(None, ["syn_ds"], sleep_s=0)
    assert len(rows) == 1
    row = rows[0]
    assert row["datasetId"] == "syn_ds"
    assert row["FileView_id"] == "syn_file_1"
    assert row["Biospecimen Key"] == "BSP-01"
    assert row["Assay"] == "RNA-Seq"
    assert row["Species"] == "Human"
    # Component/Id are Synapse/schematic bookkeeping, not modeled MC2 attributes
    assert "Component" not in row
    assert "Id" not in row


def test_file_view_harmonizes_and_builds_triples_with_real_cv_resolution(tmp_path):
    malformed_rows = []
    field_lookups = harmonize.build_field_lookups(
        SCHEMA_PATH, MAPPING_PATH, MODULES_DIR, malformed_rows, class_order=["File View"]
    )
    unmapped_rows, sssom_rows = [], defaultdict(set)
    out_path = tmp_path / "File View_harmonized.csv"
    harmonize.harmonize_table(
        "File View", str(FIXTURES_DIR / "FileView.csv"), str(out_path), field_lookups, unmapped_rows, sssom_rows,
    )

    schema_meta = build_triples.get_schema_metadata(SCHEMA_PATH, class_order=["File View"])
    join_indices = build_triples.build_join_indices(schema_meta, str(tmp_path))
    mc2_prefixes = build_triples.load_prefixes(SCHEMA_PATH)
    g = build_triples.build_class_graph("File View", schema_meta, str(tmp_path), join_indices, mc2_prefixes)

    subject = build_triples.mint_iri("File View", "syn_file_1")
    CCKP = __import__("rdflib").Namespace("https://w3id.org/mc2-center/cckp-portal/")
    assert (subject, __import__("rdflib").RDF.type, CCKP["FileView"]) in g
    # "Human" and "TXT" are real, already-curated NCIT mappings in the
    # committed modules/ CV CSVs (confirmed against live-data output before
    # writing this test, not guessed).
    assert (subject, CCKP["speciesTerm"],
            __import__("rdflib").URIRef("http://purl.obolibrary.org/obo/NCIT_C14225")) in g
    assert (subject, CCKP["fileFormatTerm"],
            __import__("rdflib").URIRef("http://purl.obolibrary.org/obo/NCIT_C85873")) in g
