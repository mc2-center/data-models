"""Stage 3: harmonize CCKP controlled-vocabulary values against MC2 ontology IRIs.

For every slot in cckp_portal.linkml.yaml carrying an `mc2_enum` annotation
(see schema comments), resolve which MC2 controlled-vocabulary CSV backs it
via modules/mapping.yaml, build a normalized label -> (Ontology Identifier,
Ontology Url) lookup from that CSV (including `Nonpreferred Terms` as
aliases), and join each raw CCKP value against it.

Design discipline (matches nf-osi/kg-pipeline's harmonization scripts):
never silently drop an unresolved value - pass it through in the harmonized
CSV unresolved, and log it to unmapped_terms.csv so coverage gaps are
visible rather than invisible.
"""

import argparse
import csv
import os
import re
from collections import defaultdict

from linkml_runtime import SchemaView

LIST_DELIMITER = "|"

# A real ontology mapping is either a CURIE ("NCIT:C12345") or a resolvable
# http(s) URL. Some CV rows have neither - e.g. modules/shared/tissue.csv
# stores bare ICD-O-3 topography codes like "C15.2" in the Ontology
# Identifier column with no Ontology Url, and one tumorType.csv row has a
# bare ICD-O-3 morphology code "9835/3". These are real, pre-existing
# data-quality gaps in the source model (not something to guess a fix for
# here) - treated as "no ontology mapping" rather than passed through as a
# fake IRI, and reported separately from genuinely-unmapped CCKP values.
CURIE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]*:\S+$")
URL_RE = re.compile(r"^https?://\S+$")


def normalize(label):
    return " ".join(label.strip().casefold().split())


def load_attribute_to_src(mapping_path):
    import yaml

    with open(mapping_path) as f:
        mapping = yaml.safe_load(f)
    attr_to_src = {}
    for entries in mapping.values():
        for entry in entries:
            attr_to_src[entry["name"]] = entry["src"]
    return attr_to_src


def load_cv_lookup(modules_dir, src, malformed_rows):
    path = os.path.join(modules_dir, src)
    lookup = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            term = (row.get("Attribute") or "").strip()
            ident = (row.get("Ontology Identifier") or "").strip()
            url = (row.get("Ontology Url") or "").strip()
            if not term or not ident:
                continue
            if not CURIE_RE.match(ident) and not URL_RE.match(url):
                malformed_rows.append({"cv_file": src, "term": term, "ontology_identifier": ident, "ontology_url": url})
                continue
            lookup[normalize(term)] = (ident, url)
            nonpreferred = (row.get("Nonpreferred Terms") or "").strip()
            if nonpreferred:
                for alias in nonpreferred.split(","):
                    alias = alias.strip()
                    if alias:
                        lookup[normalize(alias)] = (ident, url)
    return lookup


def build_field_lookups(schema_path, mapping_path, modules_dir, malformed_rows):
    """Return {ClassName: {field: (enum_name, cv_src, lookup_dict, multivalued)}}."""
    sv = SchemaView(schema_path)
    attr_to_src = load_attribute_to_src(mapping_path)
    field_lookups = defaultdict(dict)
    src_cache = {}

    for cls_name in ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]:
        cls = sv.induced_class(cls_name)
        for field, slot in cls.attributes.items():
            ann = slot.annotations
            if "mc2_enum" not in ann:
                continue
            enum_name = ann["mc2_enum"].value
            attr_name = enum_name[: -len(" Enum")] if enum_name.endswith(" Enum") else enum_name
            src = attr_to_src.get(attr_name)
            if not src:
                print(f"WARNING: no mapping.yaml entry found for '{attr_name}' "
                      f"(from {cls_name}.{field}'s mc2_enum annotation) - skipping harmonization for this field")
                continue
            if src not in src_cache:
                src_cache[src] = load_cv_lookup(modules_dir, src, malformed_rows)
            field_lookups[cls_name][field] = (enum_name, src, src_cache[src], bool(slot.multivalued))
    return field_lookups


def harmonize_table(cls_name, raw_path, out_path, field_lookups, unmapped_rows, sssom_rows):
    lookups = field_lookups.get(cls_name, {})
    if not lookups:
        # No vocab-tagged fields for this class - copy through unchanged.
        with open(raw_path) as fin, open(out_path, "w") as fout:
            fout.write(fin.read())
        return

    with open(raw_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    iri_columns = [f"{field}_ontology_iri" for field in lookups]
    out_fieldnames = fieldnames + [c for c in iri_columns if c not in fieldnames]

    for row_idx, row in enumerate(rows):
        for field, (enum_name, src, lookup, multivalued) in lookups.items():
            raw_value = row.get(field, "") or ""
            values = raw_value.split(LIST_DELIMITER) if multivalued else [raw_value]
            resolved_iris = []
            for v in values:
                v = v.strip()
                if not v:
                    continue
                hit = lookup.get(normalize(v))
                if hit:
                    ident, url = hit
                    resolved_iris.append(url or ident)
                    sssom_rows[enum_name].add((v, ident, url))
                else:
                    unmapped_rows.append({"table": cls_name, "field": field, "value": v, "row": row_idx})
            row[f"{field}_ontology_iri"] = LIST_DELIMITER.join(resolved_iris)

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_sssom(sssom_dir, enum_name, rows):
    os.makedirs(sssom_dir, exist_ok=True)
    fname = enum_name.replace(" Enum", "").strip().lower().replace(" ", "_") + ".sssom.tsv"
    path = os.path.join(sssom_dir, fname)
    with open(path, "w", newline="") as f:
        f.write(f"# curie_map:\n#   skos: http://www.w3.org/2004/02/skos/core#\n#   semapv: https://w3id.org/semapv/vocab/\n")
        f.write(f"# mapping_set_id: https://w3id.org/mc2-center/cckp-portal/mappings/{fname}\n")
        f.write("# license: https://creativecommons.org/publicdomain/zero/1.0/\n")
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["subject_id", "subject_label", "predicate_id", "object_id", "mapping_justification"])
        for value, ident, url in sorted(rows):
            writer.writerow([value, value, "skos:exactMatch", url or ident, "semapv:ManualMappingCuration"])
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--modules-dir", required=True)
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--sssom-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    malformed_rows = []
    field_lookups = build_field_lookups(args.schema, args.mapping, args.modules_dir, malformed_rows)

    if malformed_rows:
        malformed_path = os.path.join(args.out_dir, "malformed_cv_terms.csv")
        with open(malformed_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["cv_file", "term", "ontology_identifier", "ontology_url"])
            writer.writeheader()
            writer.writerows(malformed_rows)
        print(f"WARNING: {len(malformed_rows)} MC2 CV row(s) have an Ontology Identifier that isn't a "
              f"valid CURIE and no valid http(s) Ontology Url fallback (e.g. a bare ICD-O-3 code) - "
              f"treated as having no ontology mapping. See {malformed_path}.")

    unmapped_rows = []
    sssom_rows = defaultdict(set)

    for cls_name in ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]:
        raw_path = os.path.join(args.raw_dir, f"{cls_name}.csv")
        if not os.path.isfile(raw_path):
            print(f"Skipping {cls_name}: no raw extract at {raw_path} (run extract_cckp_tables.py first)")
            continue
        out_path = os.path.join(args.out_dir, f"{cls_name}_harmonized.csv")
        harmonize_table(cls_name, raw_path, out_path, field_lookups, unmapped_rows, sssom_rows)
        print(f"{cls_name}: harmonized -> {out_path}")

    unmapped_path = os.path.join(args.out_dir, "unmapped_terms.csv")
    with open(unmapped_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["table", "field", "value", "row"])
        writer.writeheader()
        writer.writerows(unmapped_rows)
    print(f"{len(unmapped_rows)} unresolved value(s) logged to {unmapped_path}")

    for enum_name, rows in sssom_rows.items():
        path = write_sssom(args.sssom_dir, enum_name, rows)
        print(f"{enum_name}: {len(rows)} resolved term(s) -> {path}")


if __name__ == "__main__":
    main()
