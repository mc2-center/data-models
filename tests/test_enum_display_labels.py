"""Tests for scripts/enum_display_labels.py (DM-7).

Uses small, self-contained JSON-LD and JSON-Schema fixtures (no Synapse
access, no real model files) to cover:
  - a top-level `properties.<Key>.enum`
  - an `items.enum` (list-type property)
  - an enum nested inside `allOf[].if.properties` / `.then.properties`
  - a value with no resolvable display name raising an error
  - property keys and `required` being left untouched
"""

import json

import pytest

from scripts.enum_display_labels import (
    EnumDisplayLabelError,
    build_jsonld_maps,
    postprocess_schema_files,
    rewrite_schema_enums,
)


def _node(label, display_name, range_includes=None, **extra):
    node = {
        "@id": f"bts:{label}",
        "@type": "rdfs:Class",
        "rdfs:label": label,
        "sms:displayName": display_name,
    }
    if range_includes is not None:
        node["schema:rangeIncludes"] = [{"@id": f"bts:{v}"} for v in range_includes]
    node.update(extra)
    return node


FIXTURE_GRAPH = [
    # A plain property with a simple CV.
    _node("Species", "Species", range_includes=["Human", "NotApplicable"]),
    _node("Human", "Human"),
    _node("NotApplicable", "Not Applicable"),
    # A list-type property with a CV that needs real de-squashing.
    _node(
        "SampleType",
        "Sample Type",
        range_includes=["RNASequencing", "AcinarCellCarcinoma"],
    ),
    _node("RNASequencing", "RNA Sequencing"),
    _node("AcinarCellCarcinoma", "Acinar Cell Carcinoma"),
    # A property used only inside an allOf/if/then conditional dependency.
    _node("DataUseCodes", "Data Use Codes", range_includes=["PendingAnnotation"]),
    _node("PendingAnnotation", "Pending Annotation"),
    # A property whose CV has a value with no node anywhere in the graph.
    _node("BrokenProp", "Broken Prop", range_includes=["GhostValue"]),
]


@pytest.fixture
def jsonld_path(tmp_path):
    path = tmp_path / "mc2.model.jsonld"
    path.write_text(json.dumps({"@graph": FIXTURE_GRAPH}), encoding="utf8")
    return str(path)


@pytest.fixture
def jsonld_maps(jsonld_path):
    return build_jsonld_maps(jsonld_path)


def _write_schema(tmp_path, name, schema):
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(schema, sort_keys=True, indent=2), encoding="utf8")
    return str(path)


def test_top_level_enum_rewritten(jsonld_maps):
    schema = {
        "properties": {
            "Species": {
                "enum": ["Human", "NotApplicable"],
                "title": "Species",
            }
        },
        "required": ["Species"],
    }
    errors = rewrite_schema_enums(schema, "Example", jsonld_maps)
    assert errors == []
    assert schema["properties"]["Species"]["enum"] == ["Human", "Not Applicable"]


def test_items_enum_rewritten(jsonld_maps):
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
    errors = rewrite_schema_enums(schema, "Example", jsonld_maps)
    assert errors == []
    assert schema["properties"]["SampleType"]["items"]["enum"] == [
        "RNA Sequencing",
        "Acinar Cell Carcinoma",
    ]


def test_enum_in_allof_if_then_rewritten(jsonld_maps):
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
    errors = rewrite_schema_enums(schema, "Example", jsonld_maps)
    assert errors == []
    assert schema["allOf"][0]["if"]["properties"]["DataUseCodes"]["enum"] == [
        "Pending Annotation"
    ]
    # The "then" branch has no enum at all; make sure walking it didn't blow up
    # and it was left alone.
    assert schema["allOf"][0]["then"]["properties"]["DiseaseSpecificResearch"] == {
        "not": {"type": "null"}
    }
    # The property's own items.enum was independently rewritten too.
    assert schema["properties"]["DataUseCodes"]["items"]["enum"] == [
        "Pending Annotation"
    ]


def test_unresolvable_value_raises(jsonld_maps):
    schema = {
        "properties": {
            "BrokenProp": {
                "enum": ["GhostValue"],
                "title": "Broken Prop",
            }
        },
        "required": [],
    }
    errors = rewrite_schema_enums(schema, "Example", jsonld_maps)
    assert errors == [("Example", "BrokenProp", "GhostValue")]
    # Left untouched since it could not be fully resolved.
    assert schema["properties"]["BrokenProp"]["enum"] == ["GhostValue"]


def test_postprocess_schema_files_raises_and_lists_all_missing(tmp_path, jsonld_path):
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
        postprocess_schema_files([good_path, bad_path], jsonld_path)

    assert exc_info.value.missing == [("Bad", "BrokenProp", "GhostValue")]


def test_keys_and_required_unchanged(jsonld_maps):
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

    rewrite_schema_enums(schema, "Example", jsonld_maps)

    assert set(schema["properties"].keys()) == before_keys
    assert schema["required"] == before_required


def test_duplicate_values_dedupe_keeping_first_occurrence(jsonld_maps):
    # Two different class labels that map to the same display name:
    # NotApplicable -> "Not Applicable" is already in the fixture; add a
    # second value resolving to the same display name via the property map.
    schema = {
        "properties": {
            "Species": {
                "enum": ["NotApplicable", "Human", "NotApplicable"],
                "title": "Species",
            }
        },
        "required": [],
    }
    errors = rewrite_schema_enums(schema, "Example", jsonld_maps)
    assert errors == []
    assert schema["properties"]["Species"]["enum"] == ["Not Applicable", "Human"]
