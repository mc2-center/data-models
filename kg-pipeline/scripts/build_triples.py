"""Stage 4: build RDF triples from harmonized CCKP CSVs.

Pure Python + rdflib (no RML/Java) - the right-sized choice for ~5 tables
and a stack that already depends on rdflib. Two passes over the harmonized
CSVs:

  Pass A: mint each row's instance IRI (identifier slot when the schema
          declares one; a documented fallback key otherwise - see
          `mint_id` below) and build the small set of secondary join
          indices (`cckp_join` targets - e.g. Grant.grantNumber ->
          Grant's IRI) needed to resolve foreign keys in Pass B.
  Pass B: emit one graph per class: an rdf:type triple, one triple per
          populated scalar/multivalued field (`cckp:{field}`), a second
          triple per resolved controlled-vocabulary value pointing at its
          real ontology IRI (`cckp:{field}Term`), and an object-property
          triple per resolved join (`cckp:{field}Ref`) to the related
          entity's minted IRI.

Instance IRIs: https://w3id.org/mc2-center/cckp-portal/data/{Class}/{id}
(placeholder namespace, matching the convention already used by
schema/mc2_model.linkml.yaml's default schema-id).
"""

import argparse
import csv
import hashlib
import os
import re
from urllib.parse import quote

import rdflib
import yaml
from linkml_runtime import SchemaView
from rdflib.namespace import RDF, XSD

LIST_DELIMITER = "|"
DATA_NS = "https://w3id.org/mc2-center/cckp-portal/data/"
# Tier-3 of the identifier policy documented in README.md ("registry CURIE" /
# "w3id.org-minted portal IRI" / "provisional placeholder"): a stable, local
# IRI for a raw CV value a human has actively checked against every relevant
# external ontology/registry and confirmed has no real term - not a value
# nobody has gotten to yet. Addressable and annotatable (unlike a bare
# literal), and flagged cckp:provisional so nothing downstream mistakes it
# for a resolved external ontology mapping.
PROVISIONAL_NS = "https://w3id.org/mc2-center/cckp-portal/terms/"
CLASS_ORDER = ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]


def normalize(label):
    return " ".join(label.strip().casefold().split())


def slugify(value):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.strip().casefold())).strip("-")


def load_confirmed_unmappable(path):
    """{(table, field): {normalized_value, ...}} from mappings/confirmed_unmappable.tsv
    - see that file's header for the reason each entry was added. Missing
    file (e.g. a fresh checkout before it's been curated) just means no
    provisional terms get minted, not an error."""
    confirmed = {}
    if not path or not os.path.isfile(path):
        return confirmed
    with open(path, newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            key = (row["table"], row["field"])
            confirmed.setdefault(key, set()).add(normalize(row["value"]))
    return confirmed

# Fields that (per live data) hold a DOI or PubMed ID as a bare/URL string,
# not backed by any MC2 CV - no SSSOM curation possible, but a resolvable
# external IRI can be templated directly from the value with zero lookups.
# Keyed by field name (applies across every class that declares it), value
# names which detector in `external_iri` to try first.
EXTERNAL_ID_FIELDS = {
    "doi": "doi",
    "pubMedId": "pubmed",
    # EducationalResource's PubMed-join field; live data shows at least one
    # row holding a DOI here instead of a numeric PMID (a source data-entry
    # mismatch, not something to silently "fix") - external_iri's kind
    # detection is by value shape first, so either kind of value in this
    # field still yields a correct external IRI rather than none at all.
    "publicationId": "pubmed",
}
DOI_URL_RE = re.compile(r"^https?://(dx\.)?doi\.org/(10\.\S+)$", re.IGNORECASE)
BARE_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
PUBMED_ID_RE = re.compile(r"^\d+$")


def external_iri(kind, value):
    """Template a resolvable external IRI from a raw doi/pubMedId-shaped
    value, or return None for sentinel placeholders ("Pending Annotation",
    "DOI Not Available", "Under Review") and other non-identifier noise
    seen in live CCKP data - never emit a fake IRI for those. Detection is
    by the value's own shape rather than blindly trusting the field name:
    live data has at least one PubMed-typed field holding a DOI instead."""
    v = value.strip()
    m = DOI_URL_RE.match(v)
    if m:
        return f"https://doi.org/{m.group(2)}"
    if BARE_DOI_RE.match(v):
        return f"https://doi.org/{v}"
    if kind == "pubmed" and PUBMED_ID_RE.match(v):
        return f"https://pubmed.ncbi.nlm.nih.gov/{v}"
    return None

# Per-class identifying key. Dataset/Grant have a real LinkML `identifier`
# slot, always populated in live data. Publication/Tool/EducationalResource
# don't (see schema comments) - each falls back to a documented
# next-best-populated field, and finally to a content hash. This was
# verified against the live tables, not assumed: EducationalResource's own
# `internalIdentifier` column is blank in 100% of current rows despite
# being declared identifier-shaped in the MC2 model - `alias` (a Synapse
# ID) is what's actually populated.
IDENTIFIER_FIELD = {
    "Dataset": "datasetId",
    "Grant": "grantId",
    # MC2 assay-metadata pipeline (see extract_mc2_assay_metadata.py) - one
    # File View row per member file, keyed by that file's own entity id.
    "File View": "FileView_id",
}
# Each entry: (candidate fields tried directly, in priority order; fields
# hashed together as a last-resort synthetic id if none of those are
# populated either).
FALLBACK_ID_FIELD = {
    "Publication": (("pubMedId",), ("publicationTitle", "doi")),
    "Tool": (("toolName",), ("description", "downloadUrl")),
    "EducationalResource": (("internalIdentifier", "alias"), ("title",)),
}


def mint_id(cls_name, row):
    """Return the row's stable identifying string, per-class rules."""
    if cls_name in IDENTIFIER_FIELD:
        value = (row.get(IDENTIFIER_FIELD[cls_name]) or "").strip()
        if value:
            return value
        raise ValueError(f"{cls_name} row missing its declared identifier field {IDENTIFIER_FIELD[cls_name]!r}: {row}")
    if cls_name in FALLBACK_ID_FIELD:
        direct_fields, hash_basis_fields = FALLBACK_ID_FIELD[cls_name]
        for field in direct_fields:
            value = (row.get(field) or "").strip()
            if value:
                return value
        basis = "|".join((row.get(field) or "").strip() for field in hash_basis_fields)
        if basis.strip("|"):
            return "synthetic-" + hashlib.sha1(basis.encode()).hexdigest()[:16]
        raise ValueError(f"{cls_name} row has no usable field to derive an id from: {row}")
    raise ValueError(f"no id-minting rule for class {cls_name}")


def class_slug(cls_name):
    """IRI-safe class local name - the 5 CCKP portal classes are already one
    word (no-op here); MC2 assay classes like "File View" have a space in
    their real LinkML name, stripped rather than percent-encoded to match
    the schema's own squashed convention for such names (e.g. "FileView_id")."""
    return cls_name.replace(" ", "")


def field_slug(name):
    """IRI-safe, lowerCamelCase predicate local name. Idempotent on already-
    camelCase field names (datasetId, grantNumber, ...) from cckp_portal.linkml.yaml,
    so this is safe to apply universally rather than only for MC2 assay
    classes with spaced/underscored names ("File Level" -> "fileLevel",
    "FileView_id" -> "fileViewId")."""
    parts = [p for p in re.split(r"[ _]+", name.strip()) if p]
    if not parts:
        return name
    first, rest = parts[0], parts[1:]
    first = first[:1].lower() + first[1:]
    return first + "".join(p[:1].upper() + p[1:] for p in rest)


def mint_iri(cls_name, row_id):
    return rdflib.URIRef(DATA_NS + class_slug(cls_name) + "/" + quote(str(row_id), safe=""))


def load_prefixes(mc2_schema_path):
    with open(mc2_schema_path) as f:
        schema = yaml.safe_load(f)
    return schema.get("prefixes", {})


def expand_curie_or_url(value, prefixes):
    """A resolved `_ontology_iri` cell is either a real http(s) URL (harmonize.py
    prefers the CV row's Ontology Url when present) or a bare CURIE (when only
    Ontology Identifier was valid). Expand the latter using the MC2 model
    schema's own prefixes block - the same source of truth used to fix
    schema/mc2_model.ttl's broken CURIEs in Stage 0."""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if ":" in value:
        prefix, local = value.split(":", 1)
        base = prefixes.get(prefix)
        if base:
            return base + local
    return None  # unexpandable - caller skips rather than emit a broken IRI


def get_schema_metadata(schema_path, class_order=None):
    """Return {ClassName: {field: {"multivalued": bool, "range": str, "mc2_enum": str|None, "cckp_join": str|None}}}.

    class_order defaults to the 5 CCKP portal classes - see harmonize.py's
    build_field_lookups for why this is a parameter rather than always
    reading the module-level CLASS_ORDER: the MC2 assay-metadata pipeline
    passes its own class list."""
    sv = SchemaView(schema_path)
    meta = {}
    for cls_name in (class_order or CLASS_ORDER):
        cls = sv.induced_class(cls_name)
        meta[cls_name] = {}
        for field, slot in cls.attributes.items():
            ann = slot.annotations
            if "mc2_enum" in ann:
                mc2_enum = ann["mc2_enum"].value
            elif slot.range and str(slot.range).endswith(" Enum"):
                # mc2_model.linkml.yaml's own convention (no mc2_enum
                # annotation anywhere in that file) - see harmonize.py's
                # matching fallback in build_field_lookups.
                mc2_enum = str(slot.range)
            else:
                mc2_enum = None
            meta[cls_name][field] = {
                "multivalued": bool(slot.multivalued),
                "range": slot.range,
                "mc2_enum": mc2_enum,
                "cckp_join": ann["cckp_join"].value if "cckp_join" in ann else None,
            }
    return meta


def read_harmonized(harmonized_dir, cls_name):
    path = os.path.join(harmonized_dir, f"{cls_name}_harmonized.csv")
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def build_join_indices(schema_meta, harmonized_dir):
    """{(TargetClass, target_field): {normalized_value: iri}}"""
    targets = set()
    for cls_meta in schema_meta.values():
        for field_meta in cls_meta.values():
            if field_meta["cckp_join"]:
                target_cls, target_field = field_meta["cckp_join"].split(".")
                targets.add((target_cls, target_field))

    indices = {}
    for target_cls, target_field in targets:
        index = {}
        for row in read_harmonized(harmonized_dir, target_cls):
            key = (row.get(target_field) or "").strip()
            if not key:
                continue
            index[key] = mint_iri(target_cls, mint_id(target_cls, row))
        indices[(target_cls, target_field)] = index
    return indices


def xsd_datatype(range_name):
    return {"integer": XSD.integer, "boolean": XSD.boolean, "float": XSD.float, "double": XSD.double}.get(range_name)


def build_class_graph(cls_name, schema_meta, harmonized_dir, join_indices, mc2_prefixes, confirmed_unmappable=None):
    g = rdflib.Graph()
    CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
    g.bind("cckp", CCKP)
    class_uri = CCKP[class_slug(cls_name)]
    fields_meta = schema_meta[cls_name]

    for row in read_harmonized(harmonized_dir, cls_name):
        row_id = mint_id(cls_name, row)
        subject = mint_iri(cls_name, row_id)
        g.add((subject, RDF.type, class_uri))

        for field, meta in fields_meta.items():
            # `field` (the harmonized CSV's actual column header, e.g. "File
            # Level") is used for every row.get(...) lookup below; only the
            # RDF predicate local name is ever slugified via field_slug().
            raw_value = (row.get(field) or "").strip()
            values = [v.strip() for v in raw_value.split(LIST_DELIMITER)] if meta["multivalued"] else [raw_value]
            values = [v for v in values if v]

            predicate = CCKP[field_slug(field)]
            datatype = xsd_datatype(meta["range"])
            for v in values:
                if datatype:
                    try:
                        g.add((subject, predicate, rdflib.Literal(v, datatype=datatype)))
                    except Exception:  # noqa: BLE001 - malformed source value, keep as plain literal rather than drop the row
                        g.add((subject, predicate, rdflib.Literal(v)))
                else:
                    g.add((subject, predicate, rdflib.Literal(v)))

            if field in EXTERNAL_ID_FIELDS:
                ext_predicate = CCKP[field_slug(f"{field}Iri")]
                for v in values:
                    iri = external_iri(EXTERNAL_ID_FIELDS[field], v)
                    if iri:
                        g.add((subject, ext_predicate, rdflib.URIRef(iri)))

            if meta["mc2_enum"]:
                iri_cell = (row.get(f"{field}_ontology_iri") or "").strip()
                term_predicate = CCKP[field_slug(f"{field}Term")]
                for entry in iri_cell.split(LIST_DELIMITER):
                    entry = entry.strip()
                    if not entry:
                        continue
                    expanded = expand_curie_or_url(entry, mc2_prefixes)
                    if expanded:
                        g.add((subject, term_predicate, rdflib.URIRef(expanded)))

                # harmonize.py's `_ontology_iri` column only ever lists the
                # values that resolved - a raw value with no ontology match
                # simply has no corresponding entry there (there's no
                # positional alignment to a specific miss for a multivalued
                # field), so provisional-term minting is checked directly
                # against each raw value here rather than against gaps in
                # iri_cell.
                confirmed_values = (confirmed_unmappable or {}).get((cls_name, field))
                if confirmed_values:
                    for v in values:
                        if normalize(v) not in confirmed_values:
                            continue
                        provisional_iri = rdflib.URIRef(PROVISIONAL_NS + quote(field, safe="") + "/" + slugify(v))
                        g.add((subject, term_predicate, provisional_iri))
                        g.add((provisional_iri, CCKP["provisional"], rdflib.Literal(True, datatype=XSD.boolean)))

            if meta["cckp_join"]:
                target_cls, target_field = meta["cckp_join"].split(".")
                index = join_indices.get((target_cls, target_field), {})
                ref_predicate = CCKP[field_slug(f"{field}Ref")]
                for v in values:
                    target_iri = index.get(v)
                    if target_iri:
                        g.add((subject, ref_predicate, target_iri))
    return g


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, help="cckp_portal.linkml.yaml")
    parser.add_argument("--mc2-schema", required=True, help="mc2_model.linkml.yaml (for CURIE prefix expansion)")
    parser.add_argument("--harmonized-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--merge-with", nargs="*", default=[], help="Additional Turtle files to merge into the final graph (e.g. the two schema TBoxes)")
    parser.add_argument("--merged-out", required=True)
    parser.add_argument("--confirmed-unmappable", default="mappings/confirmed_unmappable.tsv",
                         help="TSV of (table, field, value) a human has confirmed has no external ontology term - "
                              "minted as a provisional local IRI instead of a bare literal. Missing file is fine "
                              "(no provisional terms get minted).")
    parser.add_argument("--classes", nargs="+", default=CLASS_ORDER,
                         help=f"Schema classes to build (default: {' '.join(CLASS_ORDER)}) - the MC2 "
                              "assay-metadata pipeline passes its own class list here")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    schema_meta = get_schema_metadata(args.schema, class_order=args.classes)
    mc2_prefixes = load_prefixes(args.mc2_schema)
    join_indices = build_join_indices(schema_meta, args.harmonized_dir)
    confirmed_unmappable = load_confirmed_unmappable(args.confirmed_unmappable)

    merged = rdflib.Graph()
    for path in args.merge_with:
        merged.parse(path, format="turtle")

    for cls_name in args.classes:
        g = build_class_graph(cls_name, schema_meta, args.harmonized_dir, join_indices, mc2_prefixes,
                               confirmed_unmappable=confirmed_unmappable)
        out_path = os.path.join(args.out_dir, f"{cls_name}.ttl")
        g.serialize(destination=out_path, format="turtle")
        print(f"{cls_name}: {len(g)} triples -> {out_path}")
        merged += g

    merged.serialize(destination=args.merged_out, format="turtle")
    print(f"Merged graph: {len(merged)} triples -> {args.merged_out}")


if __name__ == "__main__":
    main()
