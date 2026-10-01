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
