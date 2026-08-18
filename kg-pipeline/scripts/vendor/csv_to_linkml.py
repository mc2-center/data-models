#!/usr/bin/env python3
# Vendored from the `csv-to-linkml` Claude Code skill (originally
# ~/.claude/skills/csv-to-linkml/scripts/csv_to_linkml.py) so `make
# mc2-model-linkml` is reproducible without that skill installed. Pure
# stdlib, no dependency on the skill's runtime - safe to update by copying
# a newer version of the same file over this one.
"""Convert a schematic-style data model into a LinkML schema YAML.

Accepts two input shapes, freely mixed in one `convert` call:
  - schematic CSVs (Attribute/Description/Valid Values/DependsOn/IsTemplate/
    Properties/...), e.g. mc2.model.csv or modules/*/annotationProperty.csv
  - exported JSON Schemas (as in json_schemas/*.json), one class per file, with
    conditional `allOf`/`if`/`then` blocks translated into LinkML `rules`

Usage:
    python csv_to_linkml.py convert INPUT [INPUT ...] --out schema.yaml
    python csv_to_linkml.py convert mc2.model.csv --mapping modules/mapping.yaml \
        --modules-dir modules --out mc2.model.linkml.yaml
    python csv_to_linkml.py convert json_schemas/*.json --out mc2.model.linkml.yaml

See ../references/mapping-rules.md for the full column -> LinkML mapping table
and the assumptions this script makes.
"""
import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(1)

TRUE_STRINGS = {"true", "1", "yes"}

# OBO Foundry ontologies follow a predictable purl pattern; used to auto-register
# prefixes for CURIEs found in the Properties column (e.g. DUO:0000026, NCIT:C12345).
OBO_PREFIXES = {
    "DUO": "http://purl.obolibrary.org/obo/DUO_",
    "NCIT": "http://purl.obolibrary.org/obo/NCIT_",
    "UBERON": "http://purl.obolibrary.org/obo/UBERON_",
    "CL": "http://purl.obolibrary.org/obo/CL_",
    "MONDO": "http://purl.obolibrary.org/obo/MONDO_",
    "OBI": "http://purl.obolibrary.org/obo/OBI_",
    "CHEBI": "http://purl.obolibrary.org/obo/CHEBI_",
    "BTO": "http://purl.obolibrary.org/obo/BTO_",
}

CURIE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]*:[^\s:]+$")

COLUMN_TYPE_TO_RANGE = {
    "string": "string",
    "string_list": "string",
    "number": "float",
    "boolean": "boolean",
}


def is_true(val):
    return (val or "").strip().lower() in TRUE_STRINGS


def split_list(val):
    return [v.strip() for v in (val or "").split(",") if v.strip()]


def sanitize_enum_name(attribute):
    return f"{attribute} Enum"


class ConversionReport:
    def __init__(self):
        self.warnings = []
        self.notes = []

    def warn(self, msg):
        self.warnings.append(msg)

    def note(self, msg):
        self.notes.append(msg)

    def write(self, path, stats):
        lines = ["# CSV -> LinkML conversion report", ""]
        lines.append("## Summary")
        for k, v in stats.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
        lines.append(f"## Warnings ({len(self.warnings)})")
        lines.append("Rows/values that need human review before the schema is trusted.")
        lines.append("")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"- {w}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append(f"## Notes ({len(self.notes)})")
        lines.append("Design decisions applied automatically — verify they're right for your case.")
        lines.append("")
        if self.notes:
            for n in self.notes:
                lines.append(f"- {n}")
        else:
            lines.append("- none")
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def dict_reader(path):
    """csv.DictReader that tolerates a BOM anywhere in the file, not just at byte 0
    (some exported CV CSVs embed it inside the first quoted field)."""
    text = Path(path).read_text(encoding="utf-8-sig").replace("﻿", "")
    return csv.DictReader(io.StringIO(text))


EMPTY_ROW_FIELDS = (
    "Attribute", "Description", "Valid Values", "DependsOn", "Required", "Properties",
    "Validation Rules", "columnType", "Format", "Pattern", "Minimum", "Maximum",
    "IsTemplate", "Source",
)


def blank_row(**overrides):
    row = {k: "" for k in EMPTY_ROW_FIELDS}
    row.update(overrides)
    return row


def read_json_schema_file(path, report, json_valid_values, rules_by_class):
    """Read one exported JSON Schema file (one class per file, as in json_schemas/)
    and return {attribute_title: pseudo_csv_row}, in the same shape read_csv_file
    produces, so the rest of the pipeline doesn't need to know the source format.

    `allOf`/`if`/`then` conditional-requirement blocks (schematic's DependsOn,
    already compiled with the triggering value) are recorded into `rules_by_class`
    keyed by the class title, for build_schema to turn into real LinkML `rules`.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    class_title = data.get("title") or Path(path).stem
    required_keys = set(data.get("required") or [])
    key_to_title = {}
    rows = {}
    slot_order = []

    for key, prop in (data.get("properties") or {}).items():
        title = prop.get("title") or key
        key_to_title[key] = title
        slot_order.append(title)

        ptype = prop.get("type") or ""
        pattern = prop.get("pattern") or ""
        enum_vals = prop.get("enum")
        if ptype == "array":
            col_type = "string_list"
            items = prop.get("items") or {}
            if not pattern:
                pattern = items.get("pattern") or ""
            if enum_vals is None:
                enum_vals = items.get("enum")
        else:
            col_type = ptype

        row = blank_row(
            Attribute=title,
            Description=prop.get("description") or "",
            Required="True" if key in required_keys else "",
            columnType=col_type,
            Pattern=pattern,
        )
        if enum_vals:
            row["Valid Values"] = ", ".join(enum_vals)
            json_valid_values[title] = row["Valid Values"]
        rows[title] = row

    rows[class_title] = blank_row(
        Attribute=class_title,
        Description=data.get("description") or "",
        DependsOn=", ".join(slot_order),
        IsTemplate="True",
    )

    rules = []
    for rule in data.get("allOf", []) or []:
        try:
            (if_key, if_val), = rule["if"]["properties"].items()
            (then_key, _then_val), = rule["then"]["properties"].items()
            precondition_values = if_val.get("enum") or []
            if not precondition_values:
                raise ValueError("if-condition has no enum")
            rules.append({
                "precondition_slot": key_to_title.get(if_key, if_key),
                "precondition_values": precondition_values,
                "postcondition_slot": key_to_title.get(then_key, then_key),
            })
        except (KeyError, ValueError):
            report.warn(f"{path}: an `allOf` rule had an unexpected shape and was skipped: {rule}")
    if rules:
        rules_by_class.setdefault(class_title, []).extend(rules)

    return rows


def read_csv_file(path):
    """Read one schematic-format CSV into {Attribute: row}."""
    rows = {}
    for row in dict_reader(path):
        attr = (row.get("Attribute") or "").strip()
        if attr:
            rows[attr] = row
    return rows


# Fields skipped in the cross-file conflict check because a thinner source (e.g. a
# JSON Schema export, which carries no Properties/Source/Format/bounds and mangles
# enum spelling) is *expected* to differ here without that being a real conflict —
# `Valid Values` is separately surfaced by its own JSON-provenance warning, and
# `DependsOn` is unioned below rather than compared for equality.
CONFLICT_CHECK_SKIP_FIELDS = {"Valid Values", "DependsOn"}


def merge_row(existing, new, attr, path, report):
    """Field-by-field merge: fill in blanks from `new`, keep `existing` where both
    are populated, and warn only on a genuine conflict (both sides non-empty and
    different) rather than on every difference in richness between sources.
    `DependsOn` (a class's slot roster) is unioned instead of picked, so combining a
    CSV and a narrower/differently-ordered JSON definition of the same class doesn't
    silently drop fields."""
    merged = dict(existing)
    for key in EMPTY_ROW_FIELDS:
        new_val = (new.get(key) or "").strip()
        old_val = (merged.get(key) or "").strip()
        if key == "DependsOn":
            old_list = split_list(old_val)
            new_items = [v for v in split_list(new_val) if v not in old_list]
            if new_items:
                merged[key] = ", ".join(old_list + new_items)
            continue
        if not new_val:
            continue
        if not old_val:
            merged[key] = new.get(key)
        elif old_val != new_val and key not in CONFLICT_CHECK_SKIP_FIELDS:
            report.warn(
                f"'{attr}' has conflicting {key} between sources ({path}): "
                f"{old_val!r} vs {new_val!r} — kept the first value seen."
            )
    return merged


def read_inputs(paths, report):
    """Merge one or more schematic CSVs and/or exported JSON Schemas into a single
    Attribute -> row dict. Dispatches on file extension (.csv vs .json)."""
    rows = {}
    json_valid_values = {}
    rules_by_class = {}
    for path in paths:
        suffix = Path(path).suffix.lower()
        if suffix == ".json":
            file_rows = read_json_schema_file(path, report, json_valid_values, rules_by_class)
        else:
            file_rows = read_csv_file(path)
        for attr, row in file_rows.items():
            if attr in rows:
                rows[attr] = merge_row(rows[attr], row, attr, path, report)
            else:
                rows[attr] = row

    # Only warn about JSON-sourced enum spelling for attributes where the JSON value
    # actually survived the merge (i.e. wasn't superseded by a richer CSV source).
    json_enum_attrs = {
        attr for attr, val in json_valid_values.items()
        if rows.get(attr, {}).get("Valid Values", "").strip() == val.strip()
    }
    return rows, json_enum_attrs, rules_by_class


def parse_mapping_yaml(path):
    """Flatten modules/mapping.yaml (module -> [{name, src}]) into attr -> src."""
    if not path:
        return {}
    with open(path, encoding="utf-8-sig") as f:
        data = yaml.safe_load(f) or {}
    attr_to_src = {}
    for _module, entries in data.items():
        if not entries:
            continue
        for entry in entries:
            name = entry.get("name")
            src = entry.get("src")
            if name and src:
                attr_to_src[name] = src
    return attr_to_src


def load_cv_terms(modules_dir, src):
    """Read a controlled-vocabulary CSV and return {term: {description, meaning}}."""
    path = Path(modules_dir) / src
    if not path.exists():
        return None
    terms = {}
    reader = dict_reader(path)
    cols = {c.lower(): c for c in (reader.fieldnames or [])}
    term_col = cols.get("attribute")
    desc_col = cols.get("description")
    onto_col = cols.get("ontology identifier")
    if not term_col:
        return None
    for row in reader:
        term = (row.get(term_col) or "").strip()
        if not term:
            continue
        meta = {}
        if desc_col and (row.get(desc_col) or "").strip():
            meta["description"] = row[desc_col].strip()
        if onto_col and (row.get(onto_col) or "").strip():
            curie = row[onto_col].strip()
            if CURIE_RE.match(curie):
                meta["meaning"] = curie
        terms[term] = meta
    return terms


def build_schema(rows, report, cv_lookup, schema_id, schema_name, extra_prefixes, json_enum_attrs=None, rules_by_class=None):
    json_enum_attrs = json_enum_attrs or set()
    rules_by_class = rules_by_class or {}
    classes = {}
    slots = {}
    enums = {}
    prefixes = {
        "linkml": "https://w3id.org/linkml/",
        "mc2": schema_id.rstrip("/") + "/",
    }
    prefixes.update(extra_prefixes)

    all_attrs = set(rows.keys())

    def register_prefix(curie):
        prefix = curie.split(":", 1)[0]
        if prefix in prefixes:
            return
        if prefix in OBO_PREFIXES:
            prefixes[prefix] = OBO_PREFIXES[prefix]
        else:
            prefixes[prefix] = f"https://example.org/UNKNOWN_PREFIX_{prefix}/"
            report.warn(
                f"Properties CURIE uses unregistered prefix '{prefix}:' — "
                f"placeholder namespace written; fill in the real URI in `prefixes.{prefix}`."
            )

    def build_slot(attr, row):
        slot = {}
        desc = (row.get("Description") or "").strip()
        if desc:
            slot["description"] = desc

        if is_true(row.get("Required")):
            slot["required"] = True

        col_type = (row.get("columnType") or "").strip()
        if col_type == "string_list":
            slot["multivalued"] = True

        valid_values = split_list(row.get("Valid Values"))
        if valid_values:
            enum_name = sanitize_enum_name(attr)
            permissible_values = {}
            cv_terms = cv_lookup.get(attr)
            for v in valid_values:
                meta = (cv_terms or {}).get(v, {})
                permissible_values[v] = meta if meta else None
            enums[enum_name] = {"permissible_values": permissible_values}
            slot["range"] = enum_name
            if attr in json_enum_attrs:
                slot.setdefault("comments", []).append(
                    "Valid Values sourced from a JSON Schema export — the exporter strips spaces/"
                    "punctuation from enum values, so these permissible values may not match the "
                    "original CSV wording. Prefer converting from the source CSV when available."
                )
                report.warn(
                    f"'{attr}' enum values came from a JSON Schema file — spacing/punctuation may "
                    "be lost versus the original CSV Valid Values; treat as provisional."
                )
        elif col_type in COLUMN_TYPE_TO_RANGE:
            if col_type != "string" and col_type != "string_list":
                slot["range"] = COLUMN_TYPE_TO_RANGE[col_type]
        # else: default_range (string) applies, no need to set explicitly

        pattern = (row.get("Pattern") or "").strip()
        if pattern:
            slot["pattern"] = pattern

        for bound_col, bound_key in (("Minimum", "minimum_value"), ("Maximum", "maximum_value")):
            val = (row.get(bound_col) or "").strip()
            if val:
                try:
                    slot[bound_key] = int(val)
                except ValueError:
                    try:
                        slot[bound_key] = float(val)
                    except ValueError:
                        report.warn(f"'{attr}' has non-numeric {bound_col}='{val}'; dropped.")

        fmt = (row.get("Format") or "").strip()
        validation_rules = (row.get("Validation Rules") or "").strip()
        comments = []
        if fmt:
            comments.append(f"schematic Format: {fmt}")
        if validation_rules:
            comments.append(f"schematic Validation Rules (not translated): {validation_rules}")
            report.warn(f"'{attr}' has a Validation Rules DSL string that was not translated: {validation_rules!r}")

        source = (row.get("Source") or "").strip()
        if source:
            comments.append(f"Source: {source}")

        annotations = {}
        exact_mappings = []
        for tok in split_list(row.get("Properties")):
            low = tok.lower()
            if low == "primary_key":
                slot["identifier"] = True
            elif low == "foreign_key":
                annotations["foreign_key"] = True
            elif low.startswith("cde:"):
                annotations["cde_id"] = tok.split(":", 1)[1]
            elif CURIE_RE.match(tok):
                exact_mappings.append(tok)
                register_prefix(tok)
            else:
                comments.append(f"schematic Properties token (unrecognized): {tok}")
                report.warn(f"'{attr}' has an unrecognized Properties token: {tok!r}")

        if exact_mappings:
            slot["exact_mappings"] = exact_mappings
        if annotations:
            slot["annotations"] = annotations
        if comments:
            slot["comments"] = comments

        sibling_deps = split_list(row.get("DependsOn"))
        if sibling_deps:
            slot.setdefault("comments", []).append(
                "schematic DependsOn (conditional requirement on sibling attributes, "
                f"not represented as a LinkML rule): {', '.join(sibling_deps)}"
            )
            report.note(
                f"'{attr}' has a conditional DependsOn on {sibling_deps} — "
                "consider encoding as a LinkML `rules:` entry if this must be enforced."
            )

        return slot

    for attr, row in rows.items():
        deps = split_list(row.get("DependsOn"))
        is_template = is_true(row.get("IsTemplate"))
        # A DependsOn list of >1 items is a component's field roster (a class),
        # even when IsTemplate wasn't set. A single-item DependsOn is a sibling
        # conditional requirement (handled as a slot annotation in build_slot).
        if is_template or len(deps) > 1:
            cls = {}
            desc = (row.get("Description") or "").strip()
            if desc:
                cls["description"] = desc
            if is_template:
                cls["tree_root"] = True
            else:
                report.note(
                    f"'{attr}' treated as a class (DependsOn lists {len(deps)} fields) "
                    "even though IsTemplate is not set — verify this is a component, not a typo."
                )
            cls["slots"] = deps

            class_rules = []
            for r in rules_by_class.get(attr, []):
                values = r["precondition_values"]
                slot_cond = {"equals_string": values[0]} if len(values) == 1 else {"equals_string_in": values}
                class_rules.append({
                    "preconditions": {"slot_conditions": {r["precondition_slot"]: slot_cond}},
                    "postconditions": {"slot_conditions": {r["postcondition_slot"]: {"required": True}}},
                })
            if class_rules:
                cls["rules"] = class_rules

            classes[attr] = cls
            for dep in deps:
                if dep not in all_attrs:
                    report.warn(
                        f"Class '{attr}' DependsOn references '{dep}', which has no "
                        "row of its own in the input — check for a typo or missing module file."
                    )
                    if dep not in slots:
                        slots[dep] = {"description": "TODO: no source row found for this slot — verify name/module."}
        else:
            slots[attr] = build_slot(attr, row)

    # Any slot referenced by a class but not yet built (e.g. defined in another,
    # un-supplied module file) gets a minimal stub above; skip re-processing here.
    schema = {
        "id": schema_id,
        "name": schema_name,
        "description": f"LinkML schema generated from a schematic-style data model CSV ({schema_name}).",
        "prefixes": prefixes,
        "default_prefix": "mc2",
        "default_range": "string",
        "imports": ["linkml:types"],
        "classes": classes,
        "slots": slots,
    }
    if enums:
        schema["enums"] = enums
    return schema


def cmd_convert(args):
    report = ConversionReport()
    rows, json_enum_attrs, rules_by_class = read_inputs(args.input, report)

    cv_lookup = {}
    if args.mapping:
        attr_to_src = parse_mapping_yaml(args.mapping)
        modules_dir = args.modules_dir or Path(args.mapping).parent
        for attr in rows:
            src = attr_to_src.get(attr)
            if not src:
                continue
            terms = load_cv_terms(modules_dir, src)
            if terms is None:
                report.warn(f"'{attr}' maps to CV file '{src}' but it could not be read.")
                continue
            cv_lookup[attr] = terms

    extra_prefixes = {}
    if args.prefix:
        for entry in args.prefix:
            if "=" not in entry:
                print(f"--prefix must be PREFIX=URI, got: {entry}", file=sys.stderr)
                sys.exit(1)
            k, v = entry.split("=", 1)
            extra_prefixes[k] = v

    schema = build_schema(
        rows, report, cv_lookup, args.schema_id, args.schema_name, extra_prefixes,
        json_enum_attrs=json_enum_attrs, rules_by_class=rules_by_class,
    )

    header = (
        "# Generated by csv_to_linkml.py — review before treating as authoritative.\n"
        "# `id` and any UNKNOWN_PREFIX_* namespaces below are placeholders; confirm/replace them.\n"
    )
    yaml_text = header + yaml.dump(schema, sort_keys=False, default_flow_style=False, allow_unicode=True, width=100)
    Path(args.out).write_text(yaml_text, encoding="utf-8")

    stats = {
        "input files": len(args.input),
        "attributes read": len(rows),
        "classes": len(schema["classes"]),
        "slots": len(schema["slots"]),
        "enums": len(schema.get("enums", {})),
        "warnings": len(report.warnings),
    }
    report_path = args.report or (Path(args.out).with_suffix("").as_posix() + "_conversion_report.md")
    report.write(report_path, stats)

    print(f"Wrote {args.out}")
    print(f"Wrote {report_path}")
    for k, v in stats.items():
        print(f"  {k}: {v}")


def cmd_check(args):
    """Best-effort structural check without requiring the `linkml` package."""
    with open(args.schema, encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    problems = []
    slot_names = set(schema.get("slots", {}).keys())
    enum_names = set(schema.get("enums", {}).keys())
    type_names = {"string", "integer", "boolean", "float", "double", "decimal", "date", "datetime", "uriorcurie", "uri"}
    known_ranges = slot_names | enum_names | type_names | set(schema.get("classes", {}).keys())

    for cname, cls in schema.get("classes", {}).items():
        for sname in cls.get("slots", []):
            if sname not in slot_names:
                problems.append(f"class '{cname}' references undefined slot '{sname}'")

    for sname, sdef in schema.get("slots", {}).items():
        rng = (sdef or {}).get("range")
        if rng and rng not in known_ranges:
            problems.append(f"slot '{sname}' has range '{rng}' which is not a defined class/slot/enum/type")

    try:
        import linkml_runtime  # noqa: F401
        from linkml_runtime.utils.schemaview import SchemaView

        sv = SchemaView(args.schema)
        sv.all_classes()
        print("linkml_runtime SchemaView loaded the schema successfully.")
    except ImportError:
        print("(linkml_runtime not installed — skipped full LinkML validation; ran structural checks only.)")
    except Exception as e:  # pragma: no cover
        problems.append(f"linkml_runtime SchemaView failed to load schema: {e}")

    if problems:
        print(f"{len(problems)} problem(s) found:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("No structural problems found.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_convert = sub.add_parser("convert", help="Convert schematic CSV(s) to a LinkML schema YAML")
    p_convert.add_argument("input", nargs="+", help="One or more schematic-format CSVs (mc2.model.csv, modules/*/annotationProperty.csv) and/or exported JSON Schemas (json_schemas/*.json); freely mixable")
    p_convert.add_argument("--out", required=True, help="Output LinkML schema YAML path")
    p_convert.add_argument("--report", help="Output conversion report path (default: <out>_conversion_report.md)")
    p_convert.add_argument("--mapping", help="Path to modules/mapping.yaml, used to enrich enums with descriptions/meanings from CV CSVs")
    p_convert.add_argument("--modules-dir", help="Base directory the mapping.yaml `src` paths are relative to (default: mapping.yaml's parent dir)")
    p_convert.add_argument("--schema-id", default="https://w3id.org/mc2-center/mc2-model", help="LinkML schema `id` URI (placeholder default — override with the real one)")
    p_convert.add_argument("--schema-name", default="mc2_model", help="LinkML schema `name`")
    p_convert.add_argument("--prefix", action="append", help="Extra PREFIX=URI to register (repeatable)")
    p_convert.set_defaults(func=cmd_convert)

    p_check = sub.add_parser("check", help="Structurally validate a generated LinkML schema")
    p_check.add_argument("schema", help="Path to the LinkML schema YAML")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
