import csv


def test_known_term_resolves_to_ontology_iri(harmonized_dir):
    with open(harmonized_dir["dir"] / "Dataset_harmonized.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    row = next(r for r in rows if r["datasetId"] == "syn_ds_1")
    assert row["tumorType"] == "Cutaneous Melanoma"
    assert row["tumorType_ontology_iri"] == "http://purl.obolibrary.org/obo/NCIT_C3510"


def test_unknown_term_passes_through_unresolved_not_dropped(harmonized_dir):
    with open(harmonized_dir["dir"] / "Dataset_harmonized.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    row = next(r for r in rows if r["datasetId"] == "syn_ds_2")
    # Value is preserved even though it didn't resolve.
    assert row["tumorType"] == "Completely Made Up Tumor Type"
    assert row["tumorType_ontology_iri"] == ""

    unmapped = harmonized_dir["unmapped_rows"]
    assert any(
        r["table"] == "Dataset" and r["field"] == "tumorType" and r["value"] == "Completely Made Up Tumor Type"
        for r in unmapped
    )


def test_no_rows_dropped(harmonized_dir):
    with open(harmonized_dir["dir"] / "Dataset_harmonized.csv", newline="") as f:
        assert len(list(csv.DictReader(f))) == 2


def test_grant_theme_and_consortium_have_no_mc2_ontology_coverage_yet(harmonized_dir):
    # modules/theme/theme_name.csv and modules/consortium/consortium_name.csv
    # currently have zero populated Ontology Identifier values across the
    # board (a real, pre-existing gap in the MC2 model - see
    # kg-pipeline/README.md) - assert this stays visible as "unresolved"
    # rather than being silently treated as resolved.
    unmapped = harmonized_dir["unmapped_rows"]
    assert any(r["table"] == "Grant" and r["field"] == "theme" and r["value"] == "Metastasis" for r in unmapped)
    assert any(r["table"] == "Grant" and r["field"] == "consortium" and r["value"] == "CCBIR" for r in unmapped)
