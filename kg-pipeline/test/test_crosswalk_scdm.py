import csv

import pytest

import crosswalk_scdm


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


INSTITUTION_HEADER = ["Attribute", "Description", "Valid Values", "DependsOn", "Required", "Properties", "Parent",
                      "DependsOn Component", "Source", "Validation Rules", "Nonpreferred Terms",
                      "Ontology Identifier", "Ontology Url", "NCIt Code", "Notes"]


def institution_row(name, ror_curie="", ror_url=""):
    return [name, "", "", "", "FALSE", "", "Institution Name", "", "ROR", "", "", ror_curie, ror_url, "", ""]


def test_build_organization_crosswalk_skips_rows_without_ror(tmp_path):
    institution_csv = tmp_path / "institution_name.csv"
    write_csv(institution_csv, INSTITUTION_HEADER, [
        institution_row("Sage Bionetworks", "ROR:049ncjx51", "https://ror.org/049ncjx51"),
        institution_row("No ROR University"),
    ])
    rows, skipped = crosswalk_scdm.build_organization_crosswalk(str(institution_csv), None)
    assert [r["institution_name"] for r in rows] == ["Sage Bionetworks"]
    assert skipped == ["No ROR University"]


def test_build_organization_crosswalk_joins_alias_by_ror(tmp_path):
    institution_csv = tmp_path / "institution_name.csv"
    write_csv(institution_csv, INSTITUTION_HEADER, [
        institution_row("Sage Bionetworks", "ROR:049ncjx51", "https://ror.org/049ncjx51"),
    ])
    alias_csv = tmp_path / "institution_alias.csv"
    write_csv(alias_csv, INSTITUTION_HEADER, [
        institution_row("Sage", "ROR:049ncjx51", "https://ror.org/049ncjx51"),
    ])
    rows, _ = crosswalk_scdm.build_organization_crosswalk(str(institution_csv), str(alias_csv))
    assert rows[0]["scdm_organization_id"] == "org.sage-bionetworks"
    assert rows[0]["scdm_ror_id"] == "https://ror.org/049ncjx51"
    assert rows[0]["scdm_acronym"] == "Sage"


def test_build_organization_crosswalk_raises_on_id_collision(tmp_path):
    institution_csv = tmp_path / "institution_name.csv"
    write_csv(institution_csv, INSTITUTION_HEADER, [
        institution_row("Sage Bionetworks", "ROR:049ncjx51", "https://ror.org/049ncjx51"),
        institution_row("Sage, Bionetworks", "ROR:0aaaaaa12", "https://ror.org/0aaaaaa12"),  # slugifies the same
    ])
    with pytest.raises(ValueError, match="org id collision"):
        crosswalk_scdm.build_organization_crosswalk(str(institution_csv), None)


def test_build_program_crosswalk_ships_unreviewed(tmp_path):
    consortium_csv = tmp_path / "consortium_name.csv"
    write_csv(consortium_csv, INSTITUTION_HEADER, [
        ["HTAN", "", "", "", "FALSE", "", "Consortium Name", "", "Sage", "", "", "NCIT:C181842",
         "http://purl.obolibrary.org/obo/NCIT_C181842", "", ""],
    ])
    rows = crosswalk_scdm.build_program_crosswalk(str(consortium_csv))
    assert rows == [{
        "consortium_name": "HTAN", "scdm_program_id": "program.htan", "scdm_name": "HTAN",
        "scdm_description": "", "scdm_status": "", "scdm_funding_source": "", "reviewed": "false",
    }]
