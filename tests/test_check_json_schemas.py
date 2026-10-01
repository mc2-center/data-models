"""Tests for scripts/check_json_schemas.py (DM-12).

Tiny, self-contained fixtures (CSV + JSON-LD + schema file written to
tmp_path) covering one pass case and one fail case per rule. No Synapse
access and no real model files are used.
"""

import json

import pandas as pd
import pytest

from scripts.check_json_schemas import run_checks

CSV_COLUMNS = [
    "Attribute",
    "Description",
    "Valid Values",
    "DependsOn",
    "Required",
    "Properties",
    "Validation Rules",
    "columnType",
    "Format",
    "Pattern",
    "Minimum",
    "Maximum",
    "IsTemplate",
    "Source",
]


def _write_csv(tmp_path, rows):
    df = pd.DataFrame(rows, columns=CSV_COLUMNS).fillna("")
    path = tmp_path / "mc2.model.csv"
    df.to_csv(path, index=False)
    return str(path)


def _row(attribute, required="", valid_values="", depends_on="", is_template=""):
    return {
        "Attribute": attribute,
        "Description": "",
        "Valid Values": valid_values,
        "DependsOn": depends_on,
        "Required": required,
        "Properties": "",
        "Validation Rules": "",
        "columnType": "",
        "Format": "",
        "Pattern": "",
        "Minimum": "",
        "Maximum": "",
        "IsTemplate": is_template,
        "Source": "",
    }


def _node(label, display_name, range_includes=None, requires_dependency=None):
    node = {"@id": f"bts:{label}", "rdfs:label": label, "sms:displayName": display_name}
    if range_includes is not None:
        node["schema:rangeIncludes"] = [{"@id": f"bts:{v}"} for v in range_includes]
    if requires_dependency is not None:
        node["sms:requiresDependency"] = [{"@id": f"bts:{v}"} for v in requires_dependency]
    return node


def _write_jsonld(tmp_path, graph):
    path = tmp_path / "mc2.model.jsonld"
    path.write_text(json.dumps({"@graph": graph}), encoding="utf8")
    return str(path)


def _write_schema_raw(tmp_path, name, text):
    path = tmp_path / f"{name}.json"
    path.write_text(text, encoding="utf8")
    return str(path)


def _write_schema(tmp_path, name, schema):
    return _write_schema_raw(tmp_path, name, json.dumps(schema))


def _rules(failures):
    return {f.rule for f in failures}


# ---------------------------------------------------------------------------
# Rule: no duplicate keys anywhere in the document
# ---------------------------------------------------------------------------


def test_no_duplicate_keys_pass(tmp_path):
    csv_path = _write_csv(tmp_path, [_row("Example", is_template="True")])
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {"title": "Example", "properties": {"Foo": {"title": "Foo"}}, "required": []},
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    assert "duplicate_keys" not in _rules(failures)


def test_duplicate_keys_fail(tmp_path):
    csv_path = _write_csv(tmp_path, [_row("Example", is_template="True")])
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    # Literal duplicate "properties" key at the top level (valid JSON syntax;
    # python's json module silently keeps the last value, which is exactly
    # what the object_pairs_hook-based check must catch).
    raw = (
        '{"title": "Example", "properties": {"Foo": {"title": "Foo"}}, '
        '"properties": {"Bar": {"title": "Bar"}}, "required": []}'
    )
    schema_path = _write_schema_raw(tmp_path, "Example", raw)

    failures = run_checks([schema_path], csv_path, jsonld_path)
    dup_failures = [f for f in failures if f.rule == "duplicate_keys"]
    assert len(dup_failures) == 1
    assert "properties" in dup_failures[0].detail


# ---------------------------------------------------------------------------
# Rule: no property key contains a space
# ---------------------------------------------------------------------------


def test_key_no_space_pass(tmp_path):
    csv_path = _write_csv(tmp_path, [_row("Example", is_template="True")])
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {"title": "Example", "properties": {"FooBar": {"title": "Foo Bar"}}, "required": []},
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    assert "key_has_space" not in _rules(failures)


def test_key_with_space_fails(tmp_path):
    csv_path = _write_csv(tmp_path, [_row("Example", is_template="True")])
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {"title": "Example", "properties": {"Foo Bar": {"title": "Foo Bar"}}, "required": []},
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    key_failures = [f for f in failures if f.rule == "key_has_space"]
    assert len(key_failures) == 1
    assert "Foo Bar" in key_failures[0].detail


# ---------------------------------------------------------------------------
# Rule: no property key / filename / title / $id starts with a digit
# ---------------------------------------------------------------------------


def test_no_leading_digit_pass(tmp_path):
    csv_path = _write_csv(tmp_path, [_row("TenXExample", is_template="True")])
    jsonld_path = _write_jsonld(tmp_path, [_node("TenXExample", "10x Example")])
    schema_path = _write_schema(
        tmp_path,
        "TenXExample",
        {
            "title": "TenXExample",
            "$id": "http://example.com/TenXExample",
            "properties": {"FooBar": {"title": "FooBar"}},
            "required": [],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    assert "leading_digit" not in _rules(failures)


def test_leading_digit_fails(tmp_path):
    csv_path = _write_csv(tmp_path, [_row("10xExample", is_template="True")])
    jsonld_path = _write_jsonld(tmp_path, [_node("10xExample", "10x Example")])
    schema_path = _write_schema(
        tmp_path,
        "10xExample",
        {
            "title": "10xExample",
            "$id": "http://example.com/10xExample",
            "properties": {"1Foo": {"title": "1Foo"}},
            "required": [],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    digit_failures = [f for f in failures if f.rule == "leading_digit"]
    reasons = {f.detail for f in digit_failures}
    assert any("key '1Foo'" in d for d in reasons)
    assert any("filename '10xExample'" in d for d in reasons)
    assert any("title '10xExample'" in d for d in reasons)
    assert any("$id '10xExample'" in d for d in reasons)


# ---------------------------------------------------------------------------
# Rule: enum values must exactly match the attribute's CSV Valid Values
# ---------------------------------------------------------------------------


def test_enum_display_form_pass(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            _row("Example", is_template="True"),
            _row("Species", valid_values="Human, Not Applicable"),
        ],
    )
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {
            "title": "Example",
            "properties": {
                "Species": {"enum": ["Human", "Not Applicable"], "title": "Species"}
            },
            "required": [],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    assert "enum_not_display_form" not in _rules(failures)


def test_enum_not_display_form_fails(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            _row("Example", is_template="True"),
            _row("Species", valid_values="Human, Not Applicable"),
        ],
    )
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    # Squashed class label "NotApplicable" left in the enum instead of being
    # rewritten to its display name "Not Applicable".
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {
            "title": "Example",
            "properties": {
                "Species": {"enum": ["Human", "NotApplicable"], "title": "Species"}
            },
            "required": [],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    enum_failures = [f for f in failures if f.rule == "enum_not_display_form"]
    assert len(enum_failures) == 1
    assert "NotApplicable" in enum_failures[0].detail


def test_enum_casing_collision_pass(tmp_path):
    # Two attributes whose Valid Values differ only by case ("No"/"no") both
    # collapse to the class label "No" under curator's first-letter-only
    # normalization. Each schema's enum must match its *own* attribute's
    # casing exactly.
    csv_path = _write_csv(
        tmp_path,
        [
            _row("Example", is_template="True"),
            _row("Prop A", valid_values="No, Yes"),
            _row("Prop B", valid_values="no, yes"),
        ],
    )
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {
            "title": "Example",
            "properties": {
                "PropA": {"enum": ["No", "Yes"], "title": "Prop A"},
                "PropB": {"enum": ["no", "yes"], "title": "Prop B"},
            },
            "required": [],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    assert "enum_not_display_form" not in _rules(failures)


def test_enum_casing_collision_fails_with_wrong_case(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            _row("Example", is_template="True"),
            _row("Prop A", valid_values="No, Yes"),
            _row("Prop B", valid_values="no, yes"),
        ],
    )
    jsonld_path = _write_jsonld(tmp_path, [_node("Example", "Example")])
    # PropB wrongly carries PropA's casing ("No"/"Yes") instead of its own
    # ("no"/"yes") - the exact bug a JSON-LD-node-keyed (or any
    # cross-property) lookup can produce.
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {
            "title": "Example",
            "properties": {
                "PropA": {"enum": ["No", "Yes"], "title": "Prop A"},
                "PropB": {"enum": ["No", "Yes"], "title": "Prop B"},
            },
            "required": [],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    enum_failures = [f for f in failures if f.rule == "enum_not_display_form"]
    assert len(enum_failures) == 1
    assert "PropB" in enum_failures[0].detail


# ---------------------------------------------------------------------------
# Rule: required includes every Required=true attribute of the template
# ---------------------------------------------------------------------------


def test_required_completeness_pass(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            _row("Example", is_template="True", depends_on="Foo, Bar"),
            _row("Foo", required="True"),
            _row("Bar", required="False"),
        ],
    )
    jsonld_path = _write_jsonld(
        tmp_path,
        [
            _node("Example", "Example", requires_dependency=["Foo", "Bar"]),
            _node("Foo", "Foo"),
            _node("Bar", "Bar"),
        ],
    )
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {
            "title": "Example",
            "properties": {"Foo": {"title": "Foo"}, "Bar": {"title": "Bar"}},
            "required": ["Foo"],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    assert "required_incomplete" not in _rules(failures)


def test_required_completeness_fails_when_missing(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            _row("Example", is_template="True", depends_on="Foo, Bar"),
            _row("Foo", required="True"),
            _row("Bar", required="False"),
        ],
    )
    jsonld_path = _write_jsonld(
        tmp_path,
        [
            _node("Example", "Example", requires_dependency=["Foo", "Bar"]),
            _node("Foo", "Foo"),
            _node("Bar", "Bar"),
        ],
    )
    # "Foo" is Required=true in the CSV but missing from the schema's
    # "required" list.
    schema_path = _write_schema(
        tmp_path,
        "Example",
        {
            "title": "Example",
            "properties": {"Foo": {"title": "Foo"}, "Bar": {"title": "Bar"}},
            "required": [],
        },
    )

    failures = run_checks([schema_path], csv_path, jsonld_path)
    req_failures = [f for f in failures if f.rule == "required_incomplete"]
    assert len(req_failures) == 1
    assert "Foo" in req_failures[0].detail
