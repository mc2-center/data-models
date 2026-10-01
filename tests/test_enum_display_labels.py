"""Tests for scripts/enum_display_labels.py (DM-7).

Uses small, self-contained CSV (primary source) and JSON-LD (fallback-only)
fixtures (no Synapse access, no real model files) to cover:
  - a top-level `properties.<Key>.enum`
  - an `items.enum` (list-type property)
  - an enum nested inside `allOf[].if.properties` / `.then.properties`
  - a value with no resolvable display name raising an error
  - property keys and `required` being left untouched
  - the casing-collision bug: two attributes whose Valid Values differ only
    by case (e.g. "No" vs "no") must each keep their own casing, since
    curator's class-label algorithm only normalizes the first letter and so
    both collapse to the same class label.
"""

import json

import pytest

from scripts.enum_display_labels import (
    EnumDisplayLabelError,
    build_enum_maps,
    postprocess_schema_files,
    rewrite_schema_enums,
)

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


def _csv_row(attribute, valid_values=""):
    return {
        "Attribute": attribute,
        "Description": "",
        "Valid Values": valid_values,
        "DependsOn": "",
        "Required": "",
        "Properties": "",
        "Validation Rules": "",
        "columnType": "",
        "Format": "",
        "Pattern": "",
        "Minimum": "",
        "Maximum": "",
        "IsTemplate": "",
        "Source": "",
    }


def _write_csv(tmp_path, rows):
    import pandas as pd

    df = pd.DataFrame(rows, columns=CSV_COLUMNS).fillna("")
    path = tmp_path / "mc2.model.csv"
    df.to_csv(path, index=False)
    return str(path)


def _jsonld_node(label, display_name, range_includes=None):
    node = {
        "@id": f"bts:{label}",
        "@type": "rdfs:Class",
        "rdfs:label": label,
        "sms:displayName": display_name,
    }
    if range_includes is not None:
        node["schema:rangeIncludes"] = [{"@id": f"bts:{v}"} for v in range_includes]
    return node


def _write_jsonld(tmp_path, graph):
    path = tmp_path / "mc2.model.jsonld"
    path.write_text(json.dumps({"@graph": graph}), encoding="utf8")
    return str(path)


# CSV fixture covering: a simple property, a list-type property, a property
# used only inside an allOf/if/then branch, and a property with a value that
# has no CSV Valid Values at all (used together with the JSON-LD fallback).
CSV_ROWS = [
    _csv_row("Species", "Human, Not Applicable"),
    _csv_row("Sample Type", "RNA Sequencing, Acinar Cell Carcinoma"),
    _csv_row("Data Use Codes", "Pending Annotation"),
]

# JSON-LD fallback fixture: only "BrokenProp" (no CSV Valid Values) relies on
# this; it's deliberately NOT a CV for any of the CSV-covered attributes
# above, so those tests exercise the CSV path exclusively.
JSONLD_GRAPH = [
    _jsonld_node("BrokenProp", "Broken Prop", range_includes=["GhostValue"]),
]


@pytest.fixture
def csv_path(tmp_path):
    return _write_csv(tmp_path, CSV_ROWS)


@pytest.fixture
def jsonld_path(tmp_path):
    return _write_jsonld(tmp_path, JSONLD_GRAPH)


@pytest.fixture
def enum_maps(csv_path, jsonld_path):
    return build_enum_maps(csv_path, jsonld_path)


def _write_schema(tmp_path, name, schema):
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(schema, sort_keys=True, indent=2), encoding="utf8")
    return str(path)


def test_top_level_enum_rewritten(enum_maps):
    schema = {
        "properties": {
            "Species": {
                "enum": ["Human", "NotApplicable"],
                "title": "Species",
            }
        },
        "required": ["Species"],
    }
    errors, fallback_used = rewrite_schema_enums(schema, "Example", enum_maps)
    assert errors == []
    assert fallback_used == []
    assert schema["properties"]["Species"]["enum"] == ["Human", "Not Applicable"]


def test_items_enum_rewritten(enum_maps):
    schema = {
        "properties": {
            "SampleType": {
                "type": "array",
                "items": {
                    "enum": ["RNASequencing", "AcinarCellCarcinoma"],
                    "type": "string",
                },
                "title": "Sample Type",
            }
        },
        "required": [],
    }
    errors, fallback_used = rewrite_schema_enums(schema, "Example", enum_maps)
    assert errors == []
    assert fallback_used == []
    assert schema["properties"]["SampleType"]["items"]["enum"] == [
        "RNA Sequencing",
        "Acinar Cell Carcinoma",
    ]


def test_enum_in_allof_if_then_rewritten(enum_maps):
    schema = {
        "properties": {
            "DiseaseSpecificResearch": {"title": "Disease Specific Research"},
            "DataUseCodes": {
                "title": "Data Use Codes",
                "items": {"enum": ["PendingAnnotation"], "type": "string"},
                "type": "array",
            },
        },
        "required": [],
        "allOf": [
            {
                "if": {
                    "properties": {"DataUseCodes": {"enum": ["PendingAnnotation"]}},
                    "required": ["DataUseCodes"],
                },
                "then": {
                    "properties": {
                        "DiseaseSpecificResearch": {"not": {"type": "null"}}
                    },
                    "required": ["DiseaseSpecificResearch"],
                },
            }
        ],
    }
    errors, fallback_used = rewrite_schema_enums(schema, "Example", enum_maps)
    assert errors == []
    assert fallback_used == []
    assert schema["allOf"][0]["if"]["properties"]["DataUseCodes"]["enum"] == [
        "Pending Annotation"
    ]
    assert schema["allOf"][0]["then"]["properties"]["DiseaseSpecificResearch"] == {
        "not": {"type": "null"}
    }
    assert schema["properties"]["DataUseCodes"]["items"]["enum"] == [
        "Pending Annotation"
    ]


def test_unresolvable_value_raises(enum_maps):
    schema = {
        "properties": {
            "BrokenProp": {
                "enum": ["GhostValue"],
                "title": "Broken Prop",
            }
        },
        "required": [],
    }
    errors, fallback_used = rewrite_schema_enums(schema, "Example", enum_maps)
    assert errors == [("Example", "BrokenProp", "GhostValue")]
    assert fallback_used == []
    # Left untouched since it could not be fully resolved.
    assert schema["properties"]["BrokenProp"]["enum"] == ["GhostValue"]


def test_jsonld_fallback_used_for_property_with_no_csv_valid_values(enum_maps):
    # "BrokenProp" has schema:rangeIncludes in the JSON-LD fixture via a
    # node "Resolvable" -> display name "Resolvable Value", but no CSV row of
    # its own; add that node and reference it to exercise the fallback path.
    enum_maps.jsonld.property_value_maps["BrokenProp"]["Resolvable"] = "Resolvable Value"
    schema = {
        "properties": {"BrokenProp": {"enum": ["Resolvable"], "title": "Broken Prop"}},
        "required": [],
    }
    errors, fallback_used = rewrite_schema_enums(schema, "Example", enum_maps)
    assert errors == []
    assert fallback_used == [("Example", "BrokenProp", "Resolvable")]
    assert schema["properties"]["BrokenProp"]["enum"] == ["Resolvable Value"]


def test_postprocess_schema_files_raises_and_lists_all_missing(
    tmp_path, csv_path, jsonld_path
):
    good_schema = {
        "properties": {"Species": {"enum": ["Human"], "title": "Species"}},
        "required": ["Species"],
    }
    bad_schema = {
        "properties": {"BrokenProp": {"enum": ["GhostValue"], "title": "Broken Prop"}},
        "required": [],
    }
    good_path = _write_schema(tmp_path, "Good", good_schema)
    bad_path = _write_schema(tmp_path, "Bad", bad_schema)

    with pytest.raises(EnumDisplayLabelError) as exc_info:
        postprocess_schema_files([good_path, bad_path], csv_path, jsonld_path)

    assert exc_info.value.missing == [("Bad", "BrokenProp", "GhostValue")]


def test_keys_and_required_unchanged(enum_maps):
    schema = {
        "properties": {
            "Species": {"enum": ["Human", "NotApplicable"], "title": "Species"},
            "SampleType": {
                "items": {"enum": ["RNASequencing"], "type": "string"},
                "title": "Sample Type",
                "type": "array",
            },
        },
        "required": ["Species", "SampleType"],
    }
    before_keys = set(schema["properties"].keys())
    before_required = list(schema["required"])

    rewrite_schema_enums(schema, "Example", enum_maps)

    assert set(schema["properties"].keys()) == before_keys
    assert schema["required"] == before_required


def test_duplicate_values_dedupe_keeping_first_occurrence(enum_maps):
    schema = {
        "properties": {
            "Species": {
                "enum": ["NotApplicable", "Human", "NotApplicable"],
                "title": "Species",
            }
        },
        "required": [],
    }
    errors, _ = rewrite_schema_enums(schema, "Example", enum_maps)
    assert errors == []
    assert schema["properties"]["Species"]["enum"] == ["Not Applicable", "Human"]


# ---------------------------------------------------------------------------
# The casing-collision bug: two attributes whose Valid Values differ only by
# case (e.g. "No"/"no") must each keep their own attribute's casing, not
# whichever one happens to "win" a shared class label globally.
# ---------------------------------------------------------------------------


def test_casing_collision_each_property_keeps_its_own_casing(tmp_path):
    # PropA's own CV is "No"/"Yes"; PropB's own CV is "no"/"yes" (e.g. an
    # ISO 639-1-style code list). Both collapse to the same class labels
    # ("No" and "Yes") under curator's first-letter-only normalization, so
    # the *raw* (squashed) enum for both properties is literally identical:
    # ["No", "Yes"].
    csv_path = _write_csv(
        tmp_path,
        [
            _csv_row("Prop A", "No, Yes"),
            _csv_row("Prop B", "no, yes"),
        ],
    )
    jsonld_path = _write_jsonld(tmp_path, [])
    maps = build_enum_maps(csv_path, jsonld_path)

    schema = {
        "properties": {
            "PropA": {"enum": ["No", "Yes"], "title": "Prop A"},
            "PropB": {"enum": ["No", "Yes"], "title": "Prop B"},
        },
        "required": [],
    }

    errors, fallback_used = rewrite_schema_enums(schema, "Example", maps)

    assert errors == []
    assert fallback_used == []
    # PropA keeps its own (capitalized) casing...
    assert schema["properties"]["PropA"]["enum"] == ["No", "Yes"]
    # ...and PropB gets its *own* (lowercase) casing, not PropA's.
    assert schema["properties"]["PropB"]["enum"] == ["no", "yes"]


def test_postprocess_refuses_colliding_attributes(tmp_path):
    # "Prop A" and "prop A" share a class label but have different Valid
    # Values, so their generated schemas can't be told apart.
    csv_path = _write_csv(
        tmp_path,
        [_csv_row("Prop A", "No, Yes"), _csv_row("prop A", "Maybe")],
    )
    jsonld_path = _write_jsonld(tmp_path, [])
    schema_path = _write_schema(
        tmp_path, "Example", {"properties": {"PropA": {"enum": ["No"]}}, "required": []}
    )
    with pytest.raises(ValueError, match="PropA"):
        postprocess_schema_files([str(schema_path)], csv_path, jsonld_path)
