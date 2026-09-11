import json

import validate_graph


def test_excluded_fields_never_counted_as_regressions(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({}))
    unmapped_csv = tmp_path / "unmapped_terms.csv"
    unmapped_csv.write_text(
        "table,field,value,row\n"
        "Publication,grantNumber,CA123456,0\n"
        "Publication,grantNumber,CA123457,1\n"
    )
    ok = validate_graph.coverage(str(unmapped_csv), [], baseline_path=str(baseline_path), fail_on_regression=True)
    assert ok is True


def test_growth_on_a_non_excluded_field_fails_the_gate(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({"Publication.tumorType": 5}))
    unmapped_csv = tmp_path / "unmapped_terms.csv"
    unmapped_csv.write_text(
        "table,field,value,row\n" + "".join(f"Publication,tumorType,Value{i},{i}\n" for i in range(6))
    )
    ok = validate_graph.coverage(str(unmapped_csv), [], baseline_path=str(baseline_path), fail_on_regression=True)
    assert ok is False


def test_shrinking_below_baseline_does_not_fail(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({"Publication.tumorType": 5}))
    unmapped_csv = tmp_path / "unmapped_terms.csv"
    unmapped_csv.write_text("table,field,value,row\nPublication,tumorType,Value0,0\n")
    ok = validate_graph.coverage(str(unmapped_csv), [], baseline_path=str(baseline_path), fail_on_regression=True)
    assert ok is True


def test_update_baseline_excludes_configured_fields(tmp_path):
    out_path = tmp_path / "baseline.json"
    unmapped_csv = tmp_path / "unmapped_terms.csv"
    unmapped_csv.write_text(
        "table,field,value,row\n"
        "Publication,grantNumber,CA1,0\n"
        "Publication,tumorType,Value0,1\n"
    )
    validate_graph.coverage(str(unmapped_csv), [], update_baseline_path=str(out_path))
    written = json.loads(out_path.read_text())
    assert written == {"Publication.tumorType": 1}
