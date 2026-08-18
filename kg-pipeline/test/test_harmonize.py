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


def test_grant_theme_now_resolves_after_curation(harmonized_dir):
    # modules/theme/theme_name.csv was curated with real NCIT/EDAM identifiers
    # for its more common, single-concept values (including "Metastasis") -
    # see kg-pipeline/README.md. Confirms harmonize.py picks that curation up.
    with open(harmonized_dir["dir"] / "Grant_harmonized.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    row = next(r for r in rows if r["grantId"] == "syn_grant_1")
    assert row["theme"] == "Metastasis"
    assert row["theme_ontology_iri"] == "http://purl.obolibrary.org/obo/NCIT_C19151"


def test_grant_consortium_still_has_no_mc2_ontology_coverage(harmonized_dir):
    # modules/consortium/consortium_name.csv still has zero populated
    # Ontology Identifier values - confirmed (not just assumed) via live
    # NCIT/EDAM/ROR lookups that these NCI program acronyms have no external
    # ontology or registry entry, see kg-pipeline/README.md - assert this
    # stays visible as "unresolved" rather than being silently treated as
    # resolved.
    unmapped = harmonized_dir["unmapped_rows"]
    assert any(r["table"] == "Grant" and r["field"] == "consortium" and r["value"] == "CCBIR" for r in unmapped)
