import crosswalk_ontology as co


def test_write_sssom_defaults_reviewed_false_for_new_rows(tmp_path):
    path = tmp_path / "crosswalk.tsv"
    results = [{
        "source_term": "Cutaneous Melanoma", "source_curie": "NCIT:C3510",
        "target_curie": "MONDO:0005012", "target_label": "cutaneous melanoma",
        "target_url": "", "exact_label_match": True,
    }]
    co.write_sssom(str(path), "NCIT", "mondo", results)

    rows = _read_data_rows(path)
    assert len(rows) == 1
    assert rows[0]["reviewed"] == "false"


def test_write_sssom_preserves_reviewed_true_on_rerun(tmp_path):
    path = tmp_path / "crosswalk.tsv"
    results = [{
        "source_term": "Cutaneous Melanoma", "source_curie": "NCIT:C3510",
        "target_curie": "MONDO:0005012", "target_label": "cutaneous melanoma",
        "target_url": "", "exact_label_match": True,
    }]
    co.write_sssom(str(path), "NCIT", "mondo", results)
    # A human reviews and flips the row to true.
    rows = _read_data_rows(path)
    rows[0]["reviewed"] = "true"
    _rewrite_data_rows(path, rows)

    # Re-running the crosswalk (e.g. after a CV edit) must not reset it.
    co.write_sssom(str(path), "NCIT", "mondo", results)
    rows_after = _read_data_rows(path)
    assert rows_after[0]["reviewed"] == "true"


def test_write_sssom_new_row_on_rerun_still_defaults_false(tmp_path):
    path = tmp_path / "crosswalk.tsv"
    first = [{
        "source_term": "Cutaneous Melanoma", "source_curie": "NCIT:C3510",
        "target_curie": "MONDO:0005012", "target_label": "cutaneous melanoma",
        "target_url": "", "exact_label_match": True,
    }]
    co.write_sssom(str(path), "NCIT", "mondo", first)
    rows = _read_data_rows(path)
    rows[0]["reviewed"] = "true"
    _rewrite_data_rows(path, rows)

    # Re-running with an added, never-before-seen row.
    second = first + [{
        "source_term": "Adenocarcinoma", "source_curie": "NCIT:C3168",
        "target_curie": "MONDO:0004970", "target_label": "adenocarcinoma",
        "target_url": "", "exact_label_match": True,
    }]
    co.write_sssom(str(path), "NCIT", "mondo", second)
    rows_after = {r["subject_id"]: r["reviewed"] for r in _read_data_rows(path)}
    assert rows_after == {"NCIT:C3510": "true", "NCIT:C3168": "false"}


def _read_data_rows(path):
    import csv
    with open(path, newline="") as f:
        lines = [line for line in f if not line.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def _rewrite_data_rows(path, rows):
    import csv
    with open(path, newline="") as f:
        comment_lines = [line for line in f if line.startswith("#")]
    with open(path, "w", newline="") as f:
        f.writelines(comment_lines)
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def test_tumor_type_crosswalk_subjects_are_all_current_cv_terms():
    # A term removed from the tumorType CV (e.g. 14.1.0 dropped "Not-Applicable")
    # must not linger as a crosswalk row.
    import csv
    from pathlib import Path

    kg_dir = Path(__file__).resolve().parent.parent
    with open(kg_dir.parent / "modules" / "shared" / "tumorType.csv", encoding="utf-8-sig", newline="") as f:
        cv_terms = {(row.get("Attribute") or "").strip() for row in csv.DictReader(f)}
    with open(kg_dir / "mappings" / "crosswalks" / "tumorType_ncit_to_mondo.sssom.tsv", newline="") as f:
        lines = [line for line in f if not line.startswith("#")]
    stale = [r["subject_label"] for r in csv.DictReader(lines, delimiter="\t") if r["subject_label"] not in cv_terms]
    assert stale == []
