"""Enum display-label post-processing for generated JSON Schemas.

Background / why this exists
-----------------------------
``synapseclient.extensions.curator.generate_jsonschema`` takes a single
``data_model_labels`` setting (``"class_label"`` vs. ``"display_label"``) that
controls *both* the JSON Schema property keys (e.g. ``RNASequencing``) *and*
the values listed in ``enum``/``items.enum`` arrays. We need class labels for
property keys (curator disallows spaces in keys), but portal tables and
curation manifests store the human-readable *display* value for enums (e.g.
``RNA Sequencing``, not ``RNASequencing``). synapsePythonClient 4.13 has no
option to split these two behaviors apart (see
``synapseclient/extensions/curator/schema_generation.py``: ``use_display_labels``
drives both key and enum formatting together).

This module is a stand-in post-processing pass that walks the JSON Schema
files curator already wrote, and rewrites every enum array back to its
display-name form, using the model's own JSON-LD (``mc2.model.jsonld``) as
the source of truth for the class-label -> display-name mapping. It should be
removed (or replaced with a single call into curator) once synapsePythonClient
exposes a setting to control property-key and enum-value labeling
independently.

Usage
-----
    maps = build_jsonld_maps("mc2.model.jsonld")
    errors = rewrite_schema_enums(schema_dict, "Biospecimen", maps)
    if errors:
        raise EnumDisplayLabelError(errors)
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple

# JSON Schema branch keywords that introduce a *single* nested schema fragment
# sharing the current property context (used by conditional dependencies,
# e.g. {"if": {"properties": {"DataUseCodes": {...}}}}).
_SINGLE_BRANCH_KEYS = ("if", "then", "else", "not")

# JSON Schema branch keywords that introduce a *list* of nested schema
# fragments sharing the current property context.
_LIST_BRANCH_KEYS = ("allOf", "anyOf", "oneOf")


@dataclass
class JsonLdMaps:
    """Lookups derived from the model's JSON-LD, used to recover enum display names.

    Attributes:
        label_to_displayname: Global map of class label -> display name, for
            every node in the graph whose label maps to exactly one display
            name model-wide. Labels with more than one distinct display name
            (ambiguous) are omitted here and recorded in ``ambiguous`` instead.
        property_value_maps: Per-property map of
            {property class label: {valid-value class label: display name}},
            built from each property node's ``schema:rangeIncludes`` list.
            This is the primary (preferred) lookup; ``label_to_displayname``
            is only a fallback for values that a property's own range does
            not (or no longer) include.
        ambiguous: class label -> sorted list of distinct display names, for
            labels that could not be used as an unambiguous global fallback.
    """

    label_to_displayname: Dict[str, str] = field(default_factory=dict)
    property_value_maps: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ambiguous: Dict[str, List[str]] = field(default_factory=dict)


class EnumDisplayLabelError(ValueError):
    """Raised when one or more enum values could not be mapped to a display name.

    Args:
        missing: list of (schema_name, property_key, value) tuples, one per
            enum value that has no resolvable display name.
    """

    def __init__(self, missing: List[Tuple[str, str, str]]):
        self.missing = missing
        lines = [
            f"  schema={schema_name!r} key={key!r} value={value!r}"
            for schema_name, key, value in missing
        ]
        message = (
            f"{len(missing)} enum value(s) have no resolvable display name "
            "in mc2.model.jsonld (nothing in the property's own "
            "schema:rangeIncludes, and no unambiguous global class-label "
            "match). Refusing to write schemas with silently-squashed enum "
            "values:\n" + "\n".join(lines)
        )
        super().__init__(message)


def strip_prefix(curie: str) -> str:
    """Strip a leading 'bts:' (or any single prefix:) from a JSON-LD @id/CURIE."""
    return curie.split(":", 1)[1] if ":" in curie else curie


def load_jsonld_graph(jsonld_path: str) -> List[dict]:
    """Load the '@graph' list from the model's JSON-LD file.

    Raises:
        FileNotFoundError: with a message pointing at the Makefile step that
            produces it, if the file is missing (the Makefile's
            ``generate-json`` target depends on ``convert`` having run first).
    """
    if not os.path.exists(jsonld_path):
        raise FileNotFoundError(
            f"JSON-LD model file not found at '{jsonld_path}'. It is produced "
            "by `make convert` (python convert_model_to_jsonld.py), which "
            "must run before generating JSON Schemas / enum display labels."
        )
    with open(jsonld_path, encoding="utf8") as fle:
        data = json.load(fle)
    graph = data.get("@graph")
    if not isinstance(graph, list):
        raise ValueError(f"'{jsonld_path}' has no top-level '@graph' list.")
    return graph


def build_jsonld_maps(jsonld_path: str) -> JsonLdMaps:
    """Build the class-label -> display-name lookups used to de-squash enums.

    See module docstring and ``JsonLdMaps`` for the mapping strategy: a
    per-property map (preferred) built from each node's
    ``schema:rangeIncludes``, plus a global fallback map that is populated
    only for class labels with exactly one display name model-wide.
    """
    graph = load_jsonld_graph(jsonld_path)

    label_to_node: Dict[str, dict] = {}
    label_to_displayname_sets: Dict[str, set] = defaultdict(set)
    for node in graph:
        label = node.get("rdfs:label")
        if not label:
            continue
        label_to_node[label] = node
        display_name = node.get("sms:displayName", label)
        label_to_displayname_sets[label].add(display_name)

    label_to_displayname: Dict[str, str] = {}
    ambiguous: Dict[str, List[str]] = {}
    for label, names in label_to_displayname_sets.items():
        if len(names) == 1:
            label_to_displayname[label] = next(iter(names))
        else:
            ambiguous[label] = sorted(names)

    property_value_maps: Dict[str, Dict[str, str]] = {}
    for node in graph:
        range_includes = node.get("schema:rangeIncludes")
        if not range_includes:
            continue
        property_label = node["rdfs:label"]
        value_map: Dict[str, str] = {}
        for ref in range_includes:
            ref_id = ref.get("@id", "")
            value_label = strip_prefix(ref_id)
            value_node = label_to_node.get(value_label)
            if value_node is None:
                # Range references a label with no node in the graph (stale
                # model). Deliberately left unmapped so the lookup falls
                # through to the global map / raises, rather than silently
                # keeping the class label as if it were the display name.
                continue
            value_map[value_label] = value_node.get("sms:displayName", value_label)
        property_value_maps[property_label] = value_map

    return JsonLdMaps(
        label_to_displayname=label_to_displayname,
        property_value_maps=property_value_maps,
        ambiguous=ambiguous,
    )


def resolve_display_name(
    property_key: Optional[str], value_label: str, maps: JsonLdMaps
) -> Optional[str]:
    """Resolve a single enum value's class label to its display name.

    Looks in the property's own value map first (the per-property,
    `schema:rangeIncludes`-derived mapping), then falls back to the
    unambiguous global class-label -> display-name map. Returns None if
    neither resolves it.
    """
    property_map = maps.property_value_maps.get(property_key or "")
    if property_map and value_label in property_map:
        return property_map[value_label]
    return maps.label_to_displayname.get(value_label)


def _walk_nodes(
    node: Any, current_key: Optional[str] = None
) -> Iterator[Tuple[Optional[str], dict]]:
    """Recursively yield every JSON-Schema-fragment dict in a schema, with the
    nearest enclosing property key.

    Descends into ``properties`` (resetting the tracked key to each property
    name), ``items`` and the conditional/combinator keywords
    (``if``/``then``/``else``/``not``/``allOf``/``anyOf``/``oneOf``), all of
    which can carry their own ``properties.<Key>`` blocks that need the same
    per-key enum treatment as a top-level property.
    """
    if not isinstance(node, dict):
        return

    yield current_key, node

    properties = node.get("properties")
    if isinstance(properties, dict):
        for prop_key, prop_schema in properties.items():
            yield from _walk_nodes(prop_schema, prop_key)

    items = node.get("items")
    if isinstance(items, dict):
        yield from _walk_nodes(items, current_key)

    for branch_key in _SINGLE_BRANCH_KEYS:
        branch = node.get(branch_key)
        if isinstance(branch, dict):
            yield from _walk_nodes(branch, current_key)

    for list_key in _LIST_BRANCH_KEYS:
        branch_list = node.get(list_key)
        if isinstance(branch_list, list):
            for item in branch_list:
                yield from _walk_nodes(item, current_key)


def walk_enum_containers(
    schema: dict,
) -> Iterator[Tuple[Optional[str], dict, str]]:
    """Yield (property_key, container, field) for every enum array in a schema.

    ``container[field]`` is the actual (mutable) enum list, found either
    directly under a property (``properties.<Key>.enum``), under
    ``items.enum``, or nested inside ``allOf``/``anyOf``/``oneOf``/``if``/
    ``then``/``else``/``not`` branches that themselves contain
    ``properties.<Key>`` blocks.
    """
    for key, node in _walk_nodes(schema):
        if isinstance(node.get("enum"), list):
            yield key, node, "enum"


def iter_properties_blocks(schema: dict) -> Iterator[Dict[str, Any]]:
    """Yield every ``properties`` mapping found anywhere in a schema (recursively)."""
    for _, node in _walk_nodes(schema):
        properties = node.get("properties")
        if isinstance(properties, dict):
            yield properties


def rewrite_schema_enums(
    schema: dict, schema_name: str, maps: JsonLdMaps
) -> List[Tuple[str, str, str]]:
    """Rewrite every enum in ``schema`` from class-label to display-name form, in place.

    Enum order is preserved; if two values map to the same display name the
    first occurrence wins (duplicates after mapping are dropped). Property
    keys and ``required`` are never touched.

    An enum array is only rewritten if *every* value in it resolves to a
    display name; if any value fails to resolve, that array is left
    unmodified (the caller is expected to treat any returned errors as fatal
    and not persist a partially-converted schema).

    Returns:
        A list of (schema_name, property_key, value) tuples for every enum
        value that could not be resolved to a display name.
    """
    errors: List[Tuple[str, str, str]] = []

    for key, container, field_name in walk_enum_containers(schema):
        values = container[field_name]
        resolved: List[str] = []
        seen = set()
        unresolved: List[Tuple[str, str, str]] = []
        for value in values:
            display_name = resolve_display_name(key, value, maps)
            if display_name is None:
                unresolved.append((schema_name, key or "<unknown>", value))
                continue
            if display_name not in seen:
                seen.add(display_name)
                resolved.append(display_name)

        if unresolved:
            errors.extend(unresolved)
        else:
            container[field_name] = resolved

    return errors


def postprocess_schema_files(file_paths: List[str], jsonld_path: str) -> None:
    """Rewrite enum values in each generated JSON Schema file to display-name form.

    Reads and re-writes each file in ``file_paths`` (already written to disk
    by ``generate_jsonschema``), preserving curator's own JSON formatting
    (``sort_keys=True, indent=2, ensure_ascii=False``, no trailing newline)
    so diffs show only enum-value changes.

    Raises:
        EnumDisplayLabelError: if any enum value across any of the files has
            no resolvable display name. Files whose enums all resolved
            cleanly are still written; only the offending (schema, key,
            value) triples are reported, so nothing is ever silently
            squashed.
    """
    maps = build_jsonld_maps(jsonld_path)

    all_errors: List[Tuple[str, str, str]] = []
    for file_path in file_paths:
        schema_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, encoding="utf8") as fle:
            schema = json.load(fle)

        errors = rewrite_schema_enums(schema, schema_name, maps)
        if errors:
            all_errors.extend(errors)
            continue

        with open(file_path, "w", encoding="utf8") as fle:
            json.dump(schema, fle, sort_keys=True, indent=2, ensure_ascii=False)

    if all_errors:
        raise EnumDisplayLabelError(all_errors)
