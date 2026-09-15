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


def test_grant_consortium_has_no_mc2_enum_and_passes_through_untracked(harmonized_dir):
    # modules/consortium/consortium_name.csv (the bare-acronym CV this field used
    # to resolve against, e.g. CCBIR/CSBC) was deleted this session when
    # Consortium Affiliation was retired in favor of Consortium Key, whose real
    # value space (program.ccbir, program.csbc, ...) is a different, machine-slug
    # format that doesn't match what live CCKP Grant.consortium data actually
    # stores - see schema/cckp_portal.linkml.yaml's Grant.consortium comment and
    # plans/crdc_cde_integration.md's kg-pipeline round for the full writeup.
    # cckp_portal.linkml.yaml's Grant.consortium slot now has NO mc2_enum
    # annotation at all (not just an unresolved one), so harmonize.py's
    # build_field_lookups skips this field entirely - it's not "attempted and
    # unmapped" anymore, it's untracked. Confirm the value still passes through
    # unchanged (not dropped) and is NOT reported to unmapped_rows (a field with
    # no mc2_enum was never eligible for that reporting in the first place).
    with open(harmonized_dir["dir"] / "Grant_harmonized.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    row = next(r for r in rows if r["grantId"] == "syn_grant_1")
    assert row["consortium"] == "CCBIR"
    assert "consortium_ontology_iri" not in row

    unmapped = harmonized_dir["unmapped_rows"]
    assert not any(r["table"] == "Grant" and r["field"] == "consortium" for r in unmapped)
