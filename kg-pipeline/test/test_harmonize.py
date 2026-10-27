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


def test_write_sssom_namespaces_mapping_set_id_per_pass(tmp_path):
    # Two passes writing a same-named enum file must not claim one
    # mapping_set_id - SSSOM treats that id as globally unique.
    import harmonize
    rows = [("Human", "NCIT:C14225", "http://purl.obolibrary.org/obo/NCIT_C14225")]
    portal = harmonize.write_sssom(str(tmp_path / "portal"), "Species Enum", rows)
    catalog = harmonize.write_sssom(str(tmp_path / "dc"), "species Enum", rows, set_id_prefix="datacatalog/")
    ids = [next(l for l in open(p) if l.startswith("# mapping_set_id:")).split(": ", 1)[1].strip() for p in (portal, catalog)]
    assert ids == ["https://w3id.org/mc2-center/cckp-portal/mappings/species.sssom.tsv",
                   "https://w3id.org/mc2-center/cckp-portal/mappings/datacatalog/species.sssom.tsv"]


def test_split_field_values_legacy_comma_and_pipe_forms_agree():
    from harmonize import split_field_values

    for cell in ("MIT, BSD-2-Clause", "MIT|BSD-2-Clause"):
        assert split_field_values(cell, True, True) == ["MIT", "BSD-2-Clause"]
    for cell in ("Jane Doe, John Roe", "Jane Doe|John Roe"):
        assert split_field_values(cell, True, True) == ["Jane Doe", "John Roe"]
    # a "|" cell splits on "|" only, even for a legacy slot
    assert split_field_values("Roe, Jane|John Doe", True, True) == ["Roe, Jane", "John Doe"]


def test_split_field_values_unannotated_multivalued_never_splits_on_comma():
    from harmonize import split_field_values

    text = "Request access via the portal, then contact the data manager."
    assert split_field_values(text, True) == [text]
    assert split_field_values(text, True, False) == [text]
    assert split_field_values("a|b, c", True) == ["a", "b, c"]


def test_split_field_values_scalar_enum_comma_split_unchanged():
    from harmonize import split_field_values

    assert split_field_values("A, B", False) == ["A", "B"]
    assert split_field_values("A", False) == ["A"]


def test_schema_marks_the_three_cutover_slots_multivalued_and_legacy_comma():
    from build_triples import get_schema_metadata
    from conftest import SCHEMA_PATH

    meta = get_schema_metadata(SCHEMA_PATH)
    for cls, field in (("Tool", "license"), ("EducationalResource", "license"), ("Grant", "investigator")):
        assert meta[cls][field]["multivalued"] and meta[cls][field]["legacy_comma_separated"]
    assert meta["Grant"]["investigator"]["legacy_comma_separated"] == "person_names"
    assert meta["Dataset"]["accessInformation"]["multivalued"]
    assert not meta["Dataset"]["accessInformation"]["legacy_comma_separated"]


def test_legacy_person_names_mode_keeps_last_first_as_one_person():
    from harmonize import split_field_values

    assert split_field_values("Krogan, Nevan", True, "person_names") == ["Nevan Krogan"]
    assert split_field_values("Amy Brock, Thomas E. Yankeelov", True, "person_names") == [
        "Amy Brock", "Thomas E. Yankeelov"]
    assert split_field_values("Krogan, Nevan|Amy Brock", True, "person_names") == [
        "Krogan, Nevan", "Amy Brock"]
