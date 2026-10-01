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
display-name form. It should be removed (or replaced with a single call into
curator) once synapsePythonClient exposes a setting to control property-key
and enum-value labeling independently.

Why CSV ``Valid Values``, not JSON-LD, is the primary source
--------------------------------------------------------------
Curator's class-label algorithm (``get_class_label_from_display_name``) only
normalizes the *first* letter, so two otherwise-different display names can
collide into the exact same class label (e.g. the attribute value ``No`` and
the ISO 639-1 language code ``no`` both become the class label ``No``;
``Immunoassay``/``immunoassay`` both become ``Immunoassay``). Because
JSON-LD nodes are keyed by class label, such a collision leaves only *one*
node - and one ``sms:displayName`` - in the whole graph, shared by every
property whose own CV happens to include that label. Using the JSON-LD as
the primary lookup (as an earlier version of this module did) can therefore
silently borrow a *different* property's casing/spelling for a colliding
value.

Each attribute's own ``Valid Values`` column in ``mc2.model.csv`` does not
have this problem - it is scoped to that one attribute - so it is used as
the primary source here. The JSON-LD is only a fallback, for properties with
no ``Valid Values`` of their own (e.g. enums that only appear inside an
``if``/``then`` conditional-dependency branch, built from validation rules
rather than a CV column).

Usage
-----
    maps = build_enum_maps("mc2.model.csv", "mc2.model.jsonld")
    errors, fallback_used = rewrite_schema_enums(schema_dict, "Biospecimen", maps)
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


def get_curator_class_label(display_name: str) -> str:
    """The exact class-label algorithm curator uses for JSON Schema property
    keys, JSON-LD class labels, and (per-row) CSV attribute/value labels.

    Imported from synapseclient itself (not reimplemented) so this always
    matches whatever generate_jsonschema / generate_jsonld actually produced,
    including its one-letter-only normalization quirk that causes the
    value-casing collisions this module works around.
    """
    from synapseclient.extensions.curator.schema_generation import (
        get_class_label_from_display_name,
    )

    return get_class_label_from_display_name(display_name)


def _split_csv_list(raw: str) -> List[str]:
    """Split a CSV list-type cell the same way curator's own CSV parser does
    (``DataModelCSVParser.parse_entry``): strip, split on comma, strip each
    entry, drop empties.
    """
    if not raw or not raw.strip():
        return []
    return [part.strip() for part in raw.strip().split(",") if part.strip()]


@dataclass
class CsvValueMaps:
    """Per-attribute class-label -> display-value maps built from mc2.model.csv.

    Attributes:
        property_value_maps: {attribute class label: {value class label: value
            display string}}, built from that attribute's own ``Valid Values``
            column. This is scoped per attribute, so it cannot suffer the
            cross-property casing collisions that a single global (or
            JSON-LD-node-keyed) map can.
        colliding_attributes: class label -> sorted list of CSV ``Attribute``
            names, for class labels claimed by more than one CSV attribute
            row with different (and differing) non-empty Valid Values. Such
            attributes are left out of ``property_value_maps`` entirely
            (resolution falls through to the JSON-LD fallback for them) and
            should be reported, since it means mc2.model.csv itself has two
            rows that collide at the class-label level.
    """

    property_value_maps: Dict[str, Dict[str, str]] = field(default_factory=dict)
    colliding_attributes: Dict[str, List[str]] = field(default_factory=dict)


def build_csv_value_maps(model_csv_path: str) -> CsvValueMaps:
    """Build per-attribute class-label -> display-value maps from mc2.model.csv.

    Raises:
        FileNotFoundError: if ``model_csv_path`` does not exist.
        ValueError: if a single attribute's own Valid Values list contains
            two different values that both resolve to the same class label
            (e.g. "No" and "no" both appearing in one attribute's own CV) -
            there would be no way to tell, from the class label alone, which
            of that attribute's own values an enum entry meant.
    """
    if not os.path.exists(model_csv_path):
        raise FileNotFoundError(f"Model CSV file not found at '{model_csv_path}'.")

    import pandas as pd

    df = pd.read_csv(model_csv_path, dtype=str, keep_default_na=False)

    # attribute class label -> list of (csv Attribute name, {value label: value})
    rows_by_label: Dict[str, List[Tuple[str, Dict[str, str]]]] = defaultdict(list)

    for _, row in df.iterrows():
        attribute_name = row["Attribute"]
        valid_values = _split_csv_list(row.get("Valid Values", ""))
        if not valid_values:
            continue

        value_map: Dict[str, str] = {}
        for value in valid_values:
            value_label = get_curator_class_label(value)
            if value_label in value_map and value_map[value_label] != value:
                raise ValueError(
                    f"Attribute '{attribute_name}' has two of its own Valid "
                    f"Values ({value_map[value_label]!r} and {value!r}) that "
                    f"both resolve to the class label '{value_label}'; "
                    "cannot build an unambiguous enum display-name map for "
                    "this attribute."
                )
            value_map[value_label] = value

        property_label = get_curator_class_label(attribute_name)
        rows_by_label[property_label].append((attribute_name, value_map))

    property_value_maps: Dict[str, Dict[str, str]] = {}
    colliding_attributes: Dict[str, List[str]] = {}
    for property_label, rows in rows_by_label.items():
        if len(rows) == 1:
            property_value_maps[property_label] = rows[0][1]
            continue

        distinct_maps = {tuple(sorted(vm.items())) for _, vm in rows}
        if len(distinct_maps) == 1:
            # Multiple CSV rows collapse to the same class label (curator's
            # label algorithm only normalizes the first letter), but they
            # happen to carry identical Valid Values, so there's no real
            # ambiguity for this lookup.
            property_value_maps[property_label] = rows[0][1]
        else:
            colliding_attributes[property_label] = sorted(name for name, _ in rows)

    return CsvValueMaps(
        property_value_maps=property_value_maps,
        colliding_attributes=colliding_attributes,
    )


@dataclass
class JsonLdMaps:
    """Lookups derived from the model's JSON-LD; used only as a fallback for
    properties with no CSV Valid Values of their own (see module docstring).

    Attributes:
        label_to_displayname: Global map of class label -> display name, for
            every node in the graph whose label maps to exactly one display
            name model-wide. Labels with more than one distinct display name
            (ambiguous) are omitted here and recorded in ``ambiguous`` instead.
        property_value_maps: Per-property map of
            {property class label: {valid-value class label: display name}},
            built from each property node's ``schema:rangeIncludes`` list.
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
            "in mc2.model.csv's Valid Values (nor, as a fallback, in "
            "mc2.model.jsonld). Refusing to write schemas with "
            "silently-squashed enum values:\n" + "\n".join(lines)
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
    """Build the class-label -> display-name fallback lookups from the JSON-LD.

    See module docstring and ``JsonLdMaps``: this is only consulted for
    properties with no CSV Valid Values of their own (see ``CsvValueMaps``,
    the primary source).
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


@dataclass
class EnumMaps:
    """Bundles the primary (CSV) and fallback (JSON-LD) lookups together."""

    csv: CsvValueMaps
    jsonld: JsonLdMaps


def build_enum_maps(model_csv_path: str, jsonld_path: str) -> EnumMaps:
    """Build the combined CSV-primary / JSON-LD-fallback enum display-name maps."""
    return EnumMaps(
        csv=build_csv_value_maps(model_csv_path),
        jsonld=build_jsonld_maps(jsonld_path),
    )


def get_valid_display_values(
    property_key: Optional[str], maps: EnumMaps
) -> Optional[Dict[str, str]]:
    """Return the {value class label: display value} map a property's enum
    should be checked/rewritten against, preferring CSV Valid Values and
    falling back to the JSON-LD range, or None if neither has one.
    """
    csv_map = maps.csv.property_value_maps.get(property_key or "")
    if csv_map:
        return csv_map
    jsonld_map = maps.jsonld.property_value_maps.get(property_key or "")
    if jsonld_map:
        return jsonld_map
    return None


def resolve_display_name(
    property_key: Optional[str], value_label: str, maps: EnumMaps
) -> Tuple[Optional[str], str]:
    """Resolve a single enum value's class label to its display name.

    Looks in the property's own CSV Valid Values map first (scoped to that
    attribute, so immune to cross-property class-label collisions), then
    falls back to the JSON-LD per-property range map, then the JSON-LD's
    unambiguous global class-label -> display-name map.

    Returns:
        (display_name, source) where source is one of "csv", "jsonld", or
        "none" (display_name is None iff source == "none").
    """
    csv_map = maps.csv.property_value_maps.get(property_key or "")
    if csv_map and value_label in csv_map:
        return csv_map[value_label], "csv"

    jsonld_map = maps.jsonld.property_value_maps.get(property_key or "")
    if jsonld_map and value_label in jsonld_map:
        return jsonld_map[value_label], "jsonld"

    global_display_name = maps.jsonld.label_to_displayname.get(value_label)
    if global_display_name is not None:
        return global_display_name, "jsonld"

    return None, "none"


def _walk_nodes(
    node: Any, current_key: Optional[str] = None, in_conditional: bool = False
) -> Iterator[Tuple[Optional[str], dict, bool]]:
    """Recursively yield every JSON-Schema-fragment dict in a schema, with the
    nearest enclosing property key and whether it sits inside a conditional
    dependency branch.

    Descends into ``properties`` (resetting the tracked key to each property
    name), ``items`` and the conditional/combinator keywords
    (``if``/``then``/``else``/``not``/``allOf``/``anyOf``/``oneOf``), all of
    which can carry their own ``properties.<Key>`` blocks that need the same
    per-key enum treatment as a top-level property. ``in_conditional`` is
    True for anything reached through one of those branch keywords (and
    stays True for everything nested further inside it) - such a branch can
    legitimately narrow a property's enum to a strict subset of its full
    Valid Values (e.g. "this is only required when DataUseCodes includes
    DUO:0000007"), so it must be checked differently than the property's own
    top-level declaration.
    """
    if not isinstance(node, dict):
        return

    yield current_key, node, in_conditional

    properties = node.get("properties")
    if isinstance(properties, dict):
        for prop_key, prop_schema in properties.items():
            yield from _walk_nodes(prop_schema, prop_key, in_conditional)

    items = node.get("items")
    if isinstance(items, dict):
        yield from _walk_nodes(items, current_key, in_conditional)

    for branch_key in _SINGLE_BRANCH_KEYS:
        branch = node.get(branch_key)
        if isinstance(branch, dict):
            yield from _walk_nodes(branch, current_key, True)

    for list_key in _LIST_BRANCH_KEYS:
        branch_list = node.get(list_key)
        if isinstance(branch_list, list):
            for item in branch_list:
                yield from _walk_nodes(item, current_key, True)


def walk_enum_containers(
    schema: dict,
) -> Iterator[Tuple[Optional[str], dict, str, bool]]:
    """Yield (property_key, container, field, in_conditional) for every enum
    array in a schema.

    ``container[field]`` is the actual (mutable) enum list, found either
    directly under a property (``properties.<Key>.enum``), under
    ``items.enum``, or nested inside ``allOf``/``anyOf``/``oneOf``/``if``/
    ``then``/``else``/``not`` branches that themselves contain
    ``properties.<Key>`` blocks. ``in_conditional`` is True iff this enum
    occurrence is inside one of those conditional branches rather than the
    property's own top-level declaration (see ``_walk_nodes``).
    """
    for key, node, in_conditional in _walk_nodes(schema):
        if isinstance(node.get("enum"), list):
            yield key, node, "enum", in_conditional


def iter_properties_blocks(schema: dict) -> Iterator[Dict[str, Any]]:
    """Yield every ``properties`` mapping found anywhere in a schema (recursively)."""
    for _, node, _ in _walk_nodes(schema):
        properties = node.get("properties")
        if isinstance(properties, dict):
            yield properties


def rewrite_schema_enums(
    schema: dict, schema_name: str, maps: EnumMaps
) -> Tuple[List[Tuple[str, str, str]], List[Tuple[str, str, str]]]:
    """Rewrite every enum in ``schema`` from class-label to display-name form, in place.

    Enum order is preserved; if two values map to the same display name the
    first occurrence wins (duplicates after mapping are dropped). Property
    keys and ``required`` are never touched.

    An enum array is only rewritten if *every* value in it resolves to a
    display name; if any value fails to resolve, that array is left
    unmodified (the caller is expected to treat any returned errors as fatal
    and not persist a partially-converted schema).

    Returns:
        (errors, fallback_used) - ``errors`` is a list of
        (schema_name, property_key, value) tuples for every enum value that
        could not be resolved to a display name at all; ``fallback_used`` is
        a list of (schema_name, property_key, value) tuples for every value
        that resolved only via the JSON-LD fallback (i.e. the property had no
        CSV Valid Values of its own to resolve it from).
    """
    errors: List[Tuple[str, str, str]] = []
    fallback_used: List[Tuple[str, str, str]] = []

    for key, container, field_name, _ in walk_enum_containers(schema):
        values = container[field_name]
        resolved: List[str] = []
        seen = set()
        unresolved: List[Tuple[str, str, str]] = []
        local_fallback: List[Tuple[str, str, str]] = []
        for value in values:
            display_name, source = resolve_display_name(key, value, maps)
            if display_name is None:
                unresolved.append((schema_name, key or "<unknown>", value))
                continue
            if source == "jsonld":
                local_fallback.append((schema_name, key or "<unknown>", value))
            if display_name not in seen:
                seen.add(display_name)
                resolved.append(display_name)

        if unresolved:
            errors.extend(unresolved)
        else:
            container[field_name] = resolved
            fallback_used.extend(local_fallback)

    return errors, fallback_used


def postprocess_schema_files(
    file_paths: List[str], model_csv_path: str, jsonld_path: str
) -> List[Tuple[str, str, str]]:
    """Rewrite enum values in each generated JSON Schema file to display-name form.

    Reads and re-writes each file in ``file_paths`` (already written to disk
    by ``generate_jsonschema``), preserving curator's own JSON formatting
    (``sort_keys=True, indent=2, ensure_ascii=False``, no trailing newline)
    so diffs show only enum-value changes.

    Returns:
        A list of (schema_name, property_key, value) tuples for every enum
        value that only resolved via the JSON-LD fallback (no CSV Valid
        Values for that property) - callers may want to log/report this.

    Raises:
        ValueError: if two CSV attributes share a class label but have
            different Valid Values.
        EnumDisplayLabelError: if any enum value across any of the files has
            no resolvable display name. Files whose enums all resolved
            cleanly are still written; only the offending (schema, key,
            value) triples are reported, so nothing is ever silently
            squashed.
    """
    maps = build_enum_maps(model_csv_path, jsonld_path)
    if maps.csv.colliding_attributes:
        # Attributes whose names share a class label but whose Valid Values
        # differ can't be told apart in a generated schema, so neither one's
        # casing can be trusted.
        details = "\n".join(
            f"  {label}: {', '.join(names)}"
            for label, names in sorted(maps.csv.colliding_attributes.items())
        )
        raise ValueError(
            "Attributes in the model CSV collapse to the same class label but "
            "have different Valid Values; rename one of each pair:\n" + details
        )

    all_errors: List[Tuple[str, str, str]] = []
    all_fallback_used: List[Tuple[str, str, str]] = []
    for file_path in file_paths:
        schema_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, encoding="utf8") as fle:
            schema = json.load(fle)

        errors, fallback_used = rewrite_schema_enums(schema, schema_name, maps)
        if errors:
            all_errors.extend(errors)
            continue

        all_fallback_used.extend(fallback_used)
        with open(file_path, "w", encoding="utf8") as fle:
            json.dump(schema, fle, sort_keys=True, indent=2, ensure_ascii=False)

    if all_errors:
        raise EnumDisplayLabelError(all_errors)

    return all_fallback_used
