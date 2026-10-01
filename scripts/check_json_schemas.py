#!/usr/bin/env python
"""Static checks for generated JSON Schemas (DM-12).

Checks every ``json_schemas/*.json`` file (or an explicit list of schema
files) against ``mc2.model.csv`` and ``mc2.model.jsonld`` for:

  1. No duplicate property keys anywhere in the JSON document (at every
     nesting level, not just the top-level ``properties`` block).
  2. No property key contains a space.
  3. No property key, and no schema filename/``title``/``$id`` name, starts
     with a digit.
  4. Every enum's set of values matches its attribute's CSV ``Valid Values``
     exactly (set equality, case-sensitive) - using the same per-attribute,
     CSV-primary/JSON-LD-fallback lookup as the enum-display-label
     post-processing step (``scripts/enum_display_labels.py``). Comparing
     against each attribute's own Valid Values (rather than a value's
     display name anywhere in the model) is what catches casing collisions:
     curator's class-label algorithm only normalizes the first letter, so
     e.g. the CV value "No" and the ISO 639-1 language code "no" collapse to
     the same class label and could otherwise be silently swapped.
  5. ``required`` includes every attribute of that template which is
     ``Required == true`` (case-insensitive) in ``mc2.model.csv``. A
     template's attributes are the ``sms:requiresDependency`` list of its
     own JSON-LD node (the node whose class label equals the schema
     filename stem).

Intended to be runnable both ad hoc and as a future CI step: it prints every
failure it finds, grouped by rule, and exits non-zero if there are any.

Usage:
    python scripts/check_json_schemas.py
    python scripts/check_json_schemas.py json_schemas/Biospecimen.json json_schemas/Study.json
    python scripts/check_json_schemas.py --schemas-dir json_schemas --model-csv mc2.model.csv --model-jsonld mc2.model.jsonld
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Allow running this file directly (`python scripts/check_json_schemas.py`)
# as well as as a module (`python -m scripts.check_json_schemas`) by making
# sure the repo root is on sys.path before importing our sibling module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.enum_display_labels import (
    EnumMaps,
    build_enum_maps,
    get_valid_display_values,
    iter_properties_blocks,
    load_jsonld_graph,
    strip_prefix,
    walk_enum_containers,
)


@dataclass
class Failure:
    rule: str
    schema: str
    detail: str


def _load_json_with_duplicate_check(path: str) -> Tuple[dict, List[str]]:
    """Parse a JSON file, recording any duplicate object keys at any nesting level.

    Returns the parsed document (last-value-wins per Python dict semantics,
    same as plain `json.load`) plus a list of duplicate key names found.
    """
    duplicates: List[str] = []

    def hook(pairs: List[Tuple[str, Any]]) -> dict:
        seen = set()
        obj: Dict[str, Any] = {}
        for key, value in pairs:
            if key in seen:
                duplicates.append(key)
            seen.add(key)
            obj[key] = value
        return obj

    with open(path, encoding="utf8") as fle:
        data = json.load(fle, object_pairs_hook=hook)
    return data, duplicates


def check_duplicate_keys(schema_name: str, duplicates: List[str]) -> List[Failure]:
    return [
        Failure(
            rule="duplicate_keys",
            schema=schema_name,
            detail=f"duplicate key '{key}' found in the JSON document",
        )
        for key in duplicates
    ]


def check_key_spaces(schema_name: str, schema: dict) -> List[Failure]:
    failures = []
    for properties in iter_properties_blocks(schema):
        for key in properties:
            if " " in key:
                failures.append(
                    Failure(
                        rule="key_has_space",
                        schema=schema_name,
                        detail=f"property key '{key}' contains a space",
                    )
                )
    return failures


def check_leading_digit(schema_name: str, schema: dict) -> List[Failure]:
    failures = []
    for properties in iter_properties_blocks(schema):
        for key in properties:
            if key and key[0].isdigit():
                failures.append(
                    Failure(
                        rule="leading_digit",
                        schema=schema_name,
                        detail=f"property key '{key}' starts with a digit",
                    )
                )

    for label, value in (
        ("filename", schema_name),
        ("title", schema.get("title")),
        ("$id", _id_name(schema.get("$id"))),
    ):
        if value and value[0].isdigit():
            failures.append(
                Failure(
                    rule="leading_digit",
                    schema=schema_name,
                    detail=f"schema {label} '{value}' starts with a digit",
                )
            )
    return failures


def _id_name(schema_id: Optional[str]) -> Optional[str]:
    if not schema_id:
        return None
    return schema_id.rsplit("/", 1)[-1]


def _format_values(values: List[str], limit: int = 8) -> List[str]:
    values = list(values)
    if len(values) <= limit:
        return values
    return values[:limit] + [f"... (+{len(values) - limit} more)"]


def check_enum_display_form(
    schema_name: str, schema: dict, maps: EnumMaps
) -> List[Failure]:
    """Check every enum's values against its attribute's CSV Valid Values.

    A property's own top-level declaration (``properties.<Key>.enum`` /
    ``.items.enum``) must match its attribute's Valid Values *exactly* (set
    equality) - this is what catches a casing/wrong-value bug like "No" vs
    "no" even when every individual value still looks plausible. An enum
    occurrence nested inside a conditional-dependency branch
    (``allOf``/``if``/``then``/etc.) is instead checked as a subset: those
    branches legitimately narrow a property to a handful of its values on
    purpose (e.g. "DataUseCodes includes DUO:0000007"), so only values
    foreign to the attribute's Valid Values are flagged there, not omissions.
    """
    failures = []
    for key, container, field_name, in_conditional in walk_enum_containers(schema):
        valid_map = get_valid_display_values(key, maps)
        if valid_map is None:
            failures.append(
                Failure(
                    rule="enum_not_display_form",
                    schema=schema_name,
                    detail=(
                        f"property '{key}' has an enum but no attribute Valid "
                        "Values were found for it in mc2.model.csv (nor, as a "
                        "fallback, a schema:rangeIncludes range in "
                        "mc2.model.jsonld); cannot verify its enum values"
                    ),
                )
            )
            continue

        expected = set(valid_map.values())
        actual = set(container[field_name])

        unexpected = sorted(actual - expected)
        missing = sorted(expected - actual) if not in_conditional else []
        if not unexpected and not missing:
            continue

        details = []
        if unexpected:
            details.append(
                f"has values not in its attribute's Valid Values: "
                f"{_format_values(unexpected)}"
            )
        if missing:
            details.append(
                f"is missing values from its attribute's Valid Values: "
                f"{_format_values(missing)}"
            )
        failures.append(
            Failure(
                rule="enum_not_display_form",
                schema=schema_name,
                detail=f"property '{key}' enum " + "; ".join(details),
            )
        )
    return failures


def _build_label_index(graph: List[dict]) -> Dict[str, dict]:
    return {node["rdfs:label"]: node for node in graph if node.get("rdfs:label")}


def _load_required_by_display_name(model_csv: str) -> Dict[str, bool]:
    """Map each CSV ``Attribute`` display name (case-insensitively) to whether
    any matching row has ``Required`` == true.

    The lookup is case-insensitive because class-label derivation
    (``get_class_label_from_display_name``) capitalizes the first letter, so
    two CSV rows differing only by the case of their first letter (e.g.
    ``species`` and ``Species``) collide into the *same* JSON-LD node; the
    graph build keeps only one row's data (displayName, Required, etc.),
    which can silently hide the other row's ``Required=true``. Matching
    case-insensitively (and OR-ing across any such colliding rows) avoids
    that blind spot without reimplementing curator's label algorithm.
    """
    import pandas as pd

    df = pd.read_csv(model_csv, dtype=str, keep_default_na=False)
    required_by_name: Dict[str, bool] = {}
    for _, row in df.iterrows():
        key = str(row["Attribute"]).lower()
        is_required = str(row.get("Required", "")).strip().lower() == "true"
        required_by_name[key] = required_by_name.get(key, False) or is_required
    return required_by_name


def check_required_completeness(
    schema_name: str,
    schema: dict,
    label_index: Dict[str, dict],
    required_by_display_name: Dict[str, bool],
) -> List[Failure]:
    template_node = label_index.get(schema_name)
    if template_node is None:
        return [
            Failure(
                rule="required_incomplete",
                schema=schema_name,
                detail=(
                    f"no node with class label '{schema_name}' found in "
                    "mc2.model.jsonld; cannot verify required attributes "
                    "for this template"
                ),
            )
        ]

    dependency_refs = template_node.get("sms:requiresDependency", [])
    schema_required = set(schema.get("required", []))

    failures = []
    for ref in dependency_refs:
        dependency_label = strip_prefix(ref.get("@id", ""))
        dependency_node = label_index.get(dependency_label)
        display_name = (
            dependency_node.get("sms:displayName", dependency_label)
            if dependency_node is not None
            else dependency_label
        )
        is_required = required_by_display_name.get(display_name.lower())
        if is_required and dependency_label not in schema_required:
            failures.append(
                Failure(
                    rule="required_incomplete",
                    schema=schema_name,
                    detail=(
                        f"attribute '{display_name}' (key '{dependency_label}') "
                        "is Required=true in mc2.model.csv for this template "
                        "but missing from the schema's 'required' list"
                    ),
                )
            )
    return failures


def check_schema_file(
    path: str,
    maps: EnumMaps,
    label_index: Dict[str, dict],
    required_by_display_name: Dict[str, bool],
) -> List[Failure]:
    schema_name = os.path.splitext(os.path.basename(path))[0]
    schema, duplicates = _load_json_with_duplicate_check(path)

    failures: List[Failure] = []
    failures += check_duplicate_keys(schema_name, duplicates)
    failures += check_key_spaces(schema_name, schema)
    failures += check_leading_digit(schema_name, schema)
    failures += check_enum_display_form(schema_name, schema, maps)
    failures += check_required_completeness(
        schema_name, schema, label_index, required_by_display_name
    )
    return failures


def run_checks(
    schema_paths: List[str], model_csv: str, model_jsonld: str
) -> List[Failure]:
    maps = build_enum_maps(model_csv, model_jsonld)
    graph = load_jsonld_graph(model_jsonld)
    label_index = _build_label_index(graph)
    required_by_display_name = _load_required_by_display_name(model_csv)

    all_failures: List[Failure] = []
    for path in schema_paths:
        all_failures += check_schema_file(
            path, maps, label_index, required_by_display_name
        )
    return all_failures


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "schemas",
        nargs="*",
        help="Specific schema file(s) to check (default: all files in --schemas-dir)",
    )
    parser.add_argument("--schemas-dir", default="json_schemas")
    parser.add_argument("--model-csv", default="mc2.model.csv")
    parser.add_argument("--model-jsonld", default="mc2.model.jsonld")
    args = parser.parse_args(argv)

    schema_paths = args.schemas or sorted(
        glob.glob(os.path.join(args.schemas_dir, "*.json"))
    )
    if not schema_paths:
        print(f"No schema files found (looked in {args.schemas_dir!r}).")
        return 1

    failures = run_checks(schema_paths, args.model_csv, args.model_jsonld)

    by_rule: Dict[str, List[Failure]] = {}
    for failure in failures:
        by_rule.setdefault(failure.rule, []).append(failure)

    for rule in sorted(by_rule):
        rule_failures = by_rule[rule]
        print(f"\n=== {rule} ({len(rule_failures)}) ===")
        for failure in rule_failures:
            print(f"  [{failure.schema}] {failure.detail}")

    print(f"\n{len(failures)} total failure(s) across {len(schema_paths)} schema file(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
