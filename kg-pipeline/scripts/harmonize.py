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


DEFAULT_CLASS_ORDER = ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]


def build_field_lookups(schema_path, mapping_path, modules_dir, malformed_rows, class_order=None):
    """Return {ClassName: {field: (enum_name, cv_src, lookup_dict, multivalued, legacy_comma_separated)}}.

    class_order defaults to the 5 CCKP portal classes - the MC2 assay-metadata
    pipeline (scripts/extract_mc2_assay_metadata.py + `make harmonize-mc2-assay`)
    passes its own class list (Biospecimen, Individual, Model, ...) so this
    same script serves both pipelines without a second hardcoded copy."""
    sv = SchemaView(schema_path)
    attr_to_src = load_attribute_to_src(mapping_path)
    field_lookups = defaultdict(dict)
    src_cache = {}

    for cls_name in (class_order or DEFAULT_CLASS_ORDER):
        cls = sv.induced_class(cls_name)
        for field, slot in cls.attributes.items():
            ann = slot.annotations
            if "mc2_enum" in ann:
                # cckp_portal.linkml.yaml's convention: a plain-string slot
                # carrying an explicit mc2_enum annotation naming its enum.
                enum_name = ann["mc2_enum"].value
            elif slot.range and str(slot.range).endswith(" Enum"):
                # mc2_model.linkml.yaml's own convention (no mc2_enum
                # annotation anywhere in that file - confirmed, not assumed):
                # the slot's LinkML `range` IS the enum name directly.
                enum_name = str(slot.range)
            else:
                continue
            attr_name = enum_name[: -len(" Enum")] if enum_name.endswith(" Enum") else enum_name
            src = attr_to_src.get(attr_name)
            if not src:
                print(f"WARNING: no mapping.yaml entry found for '{attr_name}' "
                      f"(from {cls_name}.{field}'s mc2_enum annotation) - skipping harmonization for this field")
                continue
            if src not in src_cache:
                src_cache[src] = load_cv_lookup(modules_dir, src, malformed_rows)
            field_lookups[cls_name][field] = (enum_name, src, src_cache[src], bool(slot.multivalued),
                                                  slot_legacy_comma_separated(slot))
    return field_lookups


LEGACY_COMMA_ANNOTATION = "legacy_comma_separated"
LEGACY_COMMA_MODES = ("true", "person_names")


# Lowercase surname particles that can make a single last name span 2+
# words (e.g. "Van't Veer, Laura", "De La Cruz, Maria") - checked by exact
# match on the first word before the first comma, not by prefix, so a
# genuine first name that merely starts with the same letters (e.g.
# "Vanessa") isn't caught by mistake. Not exhaustive - a multi-word surname
# using some other, rarer particle still falls through to the word-count
# heuristic in split_person_names().
SURNAME_PARTICLES = {
    "van", "van't", "vander", "vanden", "von", "der", "den", "de", "des",
    "du", "da", "di", "del", "della", "dos", "das", "la", "le", "mac", "mc",
    "st", "st.", "o'",
}


def split_person_names(raw_value):
    """Split a free-text scalar like Grant.investigator into individual
    person names.

    Two real formats show up in the live data, indistinguishable without a
    heuristic: multiple people already in "First [MI] Last" order, joined
    by commas (e.g. "Amy Brock, Thomas E. Yankeelov" - two people); or a
    single person in "Last, First MI" order (e.g. "Krogan, Nevan"). Told
    apart by the text before the first comma: a single word there reads as
    a last name (LAST, FIRST MI - one person, put back in First MI Last
    order below) rather than the first person's full name in a comma-joined
    list (two-plus words - FIRST MI LAST, FIRST MI LAST, ...) - unless that
    first word is a known surname particle (SURNAME_PARTICLES above), in
    which case the whole multi-word segment is still read as one last name
    (e.g. "Van't Veer, Laura" - one person, not two). Still a heuristic,
    not infallible: a multi-word surname using some other, rarer particle
    not in that list still gets treated as a list instead - a known,
    accepted false positive, not silently hidden.
    """
    raw_value = (raw_value or "").strip()
    if not raw_value:
        return []
    parts = [p.strip() for p in raw_value.split(",")]
    if len(parts) == 1:
        return [parts[0]] if parts[0] else []
    first_words = parts[0].split()
    starts_with_particle = bool(first_words) and first_words[0].casefold() in SURNAME_PARTICLES
    if len(first_words) < 2 or starts_with_particle:
        # LAST, FIRST MI - one person, not a comma-joined list of names.
        last = parts[0]
        first_mi = " ".join(p for p in parts[1:] if p)
        name = f"{first_mi} {last}".strip()
        return [name] if name else []
    return [p for p in parts if p]


def slot_legacy_comma_separated(slot):
    """The `legacy_comma_separated` mode of a LinkML slot (see
    cckp_portal.linkml.yaml's header): "true" (plain comma split),
    "person_names" (split_person_names() heuristic), or None."""
    ann = slot.annotations
    if LEGACY_COMMA_ANNOTATION not in ann:
        return None
    mode = str(ann[LEGACY_COMMA_ANNOTATION].value).strip().lower()
    return mode if mode in LEGACY_COMMA_MODES else None


def split_field_values(raw_value, multivalued, legacy_comma_separated=False):
    """Split a raw CCKP cell into its individual value(s) (stripped, empties
    dropped). The single splitting rule shared by harmonize.py and
    build_triples.py.

    Multivalued fields use LIST_DELIMITER ("|") per this pipeline's own
    convention. A multivalued slot annotated `legacy_comma_separated` (the
    live column is still, or was until the data model 14.x cutover, plain
    STRING holding comma-joined text such as "MIT, BSD-2-Clause" or
    "Jane Doe, John Roe") additionally splits a cell that holds no "|": on ","
    for mode "true", or with split_person_names() for mode "person_names"
    (Grant.investigator: "Krogan, Nevan" is one person, "Amy Brock, Thomas E.
    Yankeelov" two). A cell containing "|" is a real list and is split on "|" only.
    Multivalued slots without the annotation never split on commas (e.g.
    Dataset.accessInformation is free text containing commas).

    Scalar (non-multivalued) fields are declared single-valued in
    cckp_portal.linkml.yaml, but real submitted data sometimes crams several
    comma-separated terms into one cell anyway (e.g. Tool.toolEntityRole and
    Tool.linkType) - splitting scalar values on comma is safe specifically
    for callers that restrict it to `mc2_enum`-tagged fields only: confirmed
    no real CV term registered anywhere in modules/mapping.yaml contains a
    literal comma. Callers must not invoke the scalar branch for free-text
    fields.
    """
    if multivalued:
        if legacy_comma_separated == "person_names" and LIST_DELIMITER not in raw_value:
            values = split_person_names(raw_value)
        elif legacy_comma_separated and LIST_DELIMITER not in raw_value:
            values = raw_value.split(",")
        else:
            values = raw_value.split(LIST_DELIMITER)
    elif "," in raw_value:
        values = raw_value.split(",")
    else:
        values = [raw_value]
    return [v.strip() for v in values if v.strip()]


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
        for field, (enum_name, src, lookup, multivalued, legacy_comma) in lookups.items():
            raw_value = row.get(field, "") or ""
            values = split_field_values(raw_value, multivalued, legacy_comma)
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


def write_sssom(sssom_dir, enum_name, rows, set_id_prefix=""):
    """set_id_prefix namespaces mapping_set_id per harmonize pass (e.g.
    "datacatalog/"), so two passes' same-named enum files don't both claim
    one mapping_set_id - SSSOM treats that id as globally unique."""
    os.makedirs(sssom_dir, exist_ok=True)
    fname = enum_name.replace(" Enum", "").strip().lower().replace(" ", "_") + ".sssom.tsv"
    path = os.path.join(sssom_dir, fname)
    with open(path, "w", newline="") as f:
        f.write(f"# curie_map:\n#   skos: http://www.w3.org/2004/02/skos/core#\n#   semapv: https://w3id.org/semapv/vocab/\n")
        f.write(f"# mapping_set_id: https://w3id.org/mc2-center/cckp-portal/mappings/{set_id_prefix}{fname}\n")
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
    parser.add_argument("--sssom-set-id-prefix", default="",
                        help="Prefix for each SSSOM file's mapping_set_id path, e.g. 'datacatalog/' "
                             "(default: none - the main portal pass)")
    parser.add_argument("--classes", nargs="+", default=DEFAULT_CLASS_ORDER,
                         help=f"Schema classes to harmonize (default: {' '.join(DEFAULT_CLASS_ORDER)}) - "
                              "the MC2 assay-metadata pipeline passes its own class list here")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    malformed_rows = []
    field_lookups = build_field_lookups(args.schema, args.mapping, args.modules_dir, malformed_rows,
                                         class_order=args.classes)

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

    for cls_name in args.classes:
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
        path = write_sssom(args.sssom_dir, enum_name, rows, set_id_prefix=args.sssom_set_id_prefix)
        print(f"{enum_name}: {len(rows)} resolved term(s) -> {path}")


if __name__ == "__main__":
    main()
