"""Stage 3.5: suggest ontology mappings for values harmonize.py could not resolve.

harmonize.py (see scripts/harmonize.py) does exact-match-only lookups against
each field's backing MC2 controlled-vocabulary (CV) CSV and logs every miss to
data/harmonized/unmapped_terms.csv. That log conflates three very different
situations:

  curation_gap    the raw value already exists as a CV Attribute (or one of
                   its Nonpreferred Terms), but that CV row's own Ontology
                   Identifier column is blank - harmonize.py's load_cv_lookup
                   skips such rows entirely, so they can never match even
                   though the picklist term itself is valid.
  possible_typo    the raw value doesn't exist in the CV, but is a close
                   fuzzy match (ratio >= TYPO_THRESHOLD) to one that does -
                   most likely raw-data noise (a typo, a stray character)
                   rather than a genuinely new concept.
  novel_term       the raw value doesn't match anything in the CV at all -
                   either a genuinely new concept the CV hasn't been
                   extended to cover yet, or (for identifier-style fields
                   such as grantNumber) not something that was ever meant to
                   carry an ontology mapping.

For curation_gap and novel_term, this script queries an external registry for
candidate matches - the EBI OLS4 REST API by default, or the ROR API for
CVs whose `src` path contains "institution" - and writes every candidate to
data/harmonized/mapping_suggestions.csv for a human to review.

This script never writes back into a CV CSV or SSSOM file itself: it only
proposes. Applying a suggestion is a deliberate follow-up edit to the
relevant modules/*/annotationProperty.csv-style CV file.
"""

import argparse
import csv
import json
import os
import re
import subprocess
import time
import urllib.parse
from collections import Counter, defaultdict
from difflib import SequenceMatcher

CURIE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]*:\S+$")
TYPO_THRESHOLD = 0.84

OLS_SEARCH_URL = "https://www.ebi.ac.uk/ols4/api/search"
# The plain `query` endpoint scores on a full-text match across every field
# (aliases, city names, etc.) and returns near-arbitrary organizations at
# 0.9+ "relevance" for an input like an institution name; ROR's dedicated
# `affiliation` endpoint is built for exactly this string-to-org matching
# task and returns a real 0-1 confidence score, e.g. 1.0 for an exact name.
ROR_AFFILIATION_URL = "https://api.ror.org/organizations"

# Accession-number / free-identifier fields that were never meant to carry an
# ontology mapping (confirmed by inspecting their backing CV: every row is an
# allowlisted ID with zero populated Ontology Identifier values). Skipped
# without a network call so a large identifier CV doesn't burn OLS quota on
# lookups that can't possibly succeed. See kg-pipeline/README.md.
EXCLUDED_FIELDS = {
    ("Publication", "grantNumber"),
    ("Dataset", "grantNumber"),
    ("Tool", "grantNumber"),
}

# CURIE prefix -> OLS4 ontology id, when they differ. SPDX license IDs aren't
# indexed in OLS at all, so a CV backed by SPDX is skipped for OLS search.
PREFIX_TO_OLS_ONTOLOGY = {"ncbitaxon": "ncbitaxon"}
FALLBACK_ONTOLOGIES = ["ncit", "obi", "edam", "duo", "doid"]
NON_OLS_PREFIXES = {"spdx"}


def normalize(label):
    return " ".join(label.strip().casefold().split())


def http_get_json(url, timeout=15, retries=2):
    """Shell out to curl (matches ols-term-annotator's approach) rather than
    depend on requests/httpx being importable in every environment this
    script runs in. One retry with backoff absorbs the OLS4 API's occasional
    transient timeout without mistaking a blip for a real empty result."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            out = subprocess.run(
                ["curl", "-s", "--max-time", str(timeout), url],
                capture_output=True, text=True, timeout=timeout + 5,
            ).stdout
            return json.loads(out)
        except Exception as e:  # noqa: BLE001 - report and let caller decide
            last_err = e
            if attempt < retries:
                time.sleep(1.0)
    return {"error": str(last_err)}


def load_attribute_to_src(mapping_path):
    import yaml

    with open(mapping_path) as f:
        mapping = yaml.safe_load(f)
    attr_to_src = {}
    for entries in mapping.values():
        for entry in entries:
            attr_to_src[entry["name"]] = entry["src"]
    return attr_to_src


def build_field_srcs(schema_path, mapping_path):
    """{ClassName: {field: (enum_name, cv_src, multivalued)}} - the same
    schema/mapping.yaml resolution harmonize.py's build_field_lookups does,
    without also building a lookup dict (this script wants every CV row,
    including ones with a blank Ontology Identifier, so it re-reads the CSVs
    itself in load_cv_rows instead)."""
    from linkml_runtime import SchemaView

    sv = SchemaView(schema_path)
    attr_to_src = load_attribute_to_src(mapping_path)
    field_srcs = defaultdict(dict)
    for cls_name in ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]:
        cls = sv.induced_class(cls_name)
        for field, slot in cls.attributes.items():
            ann = slot.annotations
            if "mc2_enum" not in ann:
                continue
            enum_name = ann["mc2_enum"].value
            attr_name = enum_name[: -len(" Enum")] if enum_name.endswith(" Enum") else enum_name
            src = attr_to_src.get(attr_name)
            if src:
                field_srcs[cls_name][field] = (enum_name, src, bool(slot.multivalued))
    return field_srcs


def load_cv_rows(modules_dir, src):
    path = os.path.join(modules_dir, src)
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cv_attribute_index(cv_rows):
    """normalized-term -> CV row, covering both Attribute and each
    Nonpreferred Term alias (mirrors harmonize.py's load_cv_lookup key
    space, but keeps every row regardless of whether Ontology Identifier is
    populated)."""
    index = {}
    for row in cv_rows:
        term = (row.get("Attribute") or "").strip()
        if term:
            index[normalize(term)] = row
        for alias in (row.get("Nonpreferred Terms") or "").split(","):
            alias = alias.strip()
            if alias:
                index[normalize(alias)] = row
    return index


def cv_ontology_hints(cv_rows):
    """The ontology prefix(es) already in use among this CV's populated
    rows - used to bias the OLS search toward the same vocabulary the CV's
    existing curation already committed to, rather than guessing cold."""
    prefixes = Counter()
    for row in cv_rows:
        ident = (row.get("Ontology Identifier") or "").strip()
        if CURIE_RE.match(ident):
            prefixes[ident.split(":", 1)[0].lower()] += 1
    return [p for p, _ in prefixes.most_common(3)]


def guess_ontologies(hints):
    ontologies = [PREFIX_TO_OLS_ONTOLOGY.get(h, h) for h in hints if h not in NON_OLS_PREFIXES]
    for o in FALLBACK_ONTOLOGIES:
        if o not in ontologies:
            ontologies.append(o)
    return ontologies[:4]


def ols_search(query, ontologies, rows=3):
    params = {"q": query, "rows": rows,
              "fieldList": "iri,label,short_form,obo_id,ontology_name,description"}
    if ontologies:
        params["ontology"] = ",".join(ontologies)
    data = http_get_json(OLS_SEARCH_URL + "?" + urllib.parse.urlencode(params))
    docs = ((data.get("response") or {}).get("docs") or [])[:rows]
    hits = []
    for d in docs:
        obo_id = d.get("obo_id") or d.get("short_form") or ""
        curie = obo_id if (":" in obo_id) else (obo_id.replace("_", ":", 1) if obo_id else None)
        hits.append({"source": "ols", "curie": curie, "label": d.get("label"),
                     "ontology": d.get("ontology_name"), "url": d.get("iri")})
    return hits


def ror_display_name(org):
    for n in org.get("names") or []:
        if "ror_display" in (n.get("types") or []):
            return n.get("value")
    return org.get("id")


def ror_search(query, rows=3):
    data = http_get_json(ROR_AFFILIATION_URL + "?" + urllib.parse.urlencode({"affiliation": query}))
    items = (data.get("items") or [])[:rows]
    hits = []
    for it in items:
        org = it.get("organization") or {}
        ror_id = (org.get("id") or "").rsplit("/", 1)[-1]
        hits.append({"source": "ror", "curie": f"ROR:{ror_id}" if ror_id else None,
                     "label": ror_display_name(org), "ontology": "ror", "url": org.get("id"),
                     "score": it.get("score")})
    return hits


def classify(value, attr_index):
    norm_value = normalize(value)
    row = attr_index.get(norm_value)
    if row is not None:
        ident = (row.get("Ontology Identifier") or "").strip()
        if not ident:
            return "curation_gap", None
        return "already_mapped", None  # shouldn't occur if unmapped_terms.csv is fresh

    best_ratio, best_key = 0.0, None
    for term_norm in attr_index:
        ratio = SequenceMatcher(None, norm_value, term_norm).ratio()
        if ratio > best_ratio:
            best_ratio, best_key = ratio, term_norm
    if best_ratio >= TYPO_THRESHOLD:
        canonical = attr_index[best_key].get("Attribute")
        return "possible_typo", {"likely_canonical_term": canonical, "similarity": round(best_ratio, 2)}
    return "novel_term", None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--modules-dir", required=True)
    parser.add_argument("--unmapped-csv", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-values-per-field", type=int, default=200,
                         help="Cap distinct values looked up per (table, field) - a safety valve against "
                              "burning the whole run on one enormous free-text field (default 200)")
    parser.add_argument("--no-lookup", action="store_true",
                         help="Classify only (curation_gap/possible_typo/novel_term); skip all network calls")
    parser.add_argument("--only-field", nargs="+", metavar="TABLE.FIELD",
                         help="Restrict to these table.field pairs, e.g. Tool.license Publication.tumorType")
    args = parser.parse_args()

    field_srcs = build_field_srcs(args.schema, args.mapping)
    src_to_class_field = {}
    for cls_name, fields in field_srcs.items():
        for field, (enum_name, src, _multivalued) in fields.items():
            src_to_class_field.setdefault((cls_name, field), src)

    only = set(args.only_field) if args.only_field else None

    with open(args.unmapped_csv, newline="") as f:
        rows = list(csv.DictReader(f))

    by_field = defaultdict(Counter)
    for r in rows:
        by_field[(r["table"], r["field"])][r["value"]] += 1

    cv_rows_cache, attr_index_cache, ontologies_cache = {}, {}, {}
    lookup_cache = {}
    suggestions = []
    n_excluded = n_looked_up = 0

    for (table, field), value_counts in sorted(by_field.items()):
        if only and f"{table}.{field}" not in only:
            continue
        src = src_to_class_field.get((table, field))
        if src is None:
            print(f"WARNING: no CV src resolved for {table}.{field} - skipping")
            continue
        if (table, field) in EXCLUDED_FIELDS:
            n_excluded += len(value_counts)
            for value, count in value_counts.most_common():
                suggestions.append({
                    "table": table, "field": field, "value": value, "count": count,
                    "cv_file": src, "category": "identifier_not_ontology_mappable",
                    "suggestion_detail": "", "candidate_curie": "", "candidate_label": "",
                    "candidate_url": "", "candidate_source": "",
                })
            continue

        if src not in cv_rows_cache:
            cv_rows_cache[src] = load_cv_rows(args.modules_dir, src)
            attr_index_cache[src] = cv_attribute_index(cv_rows_cache[src])
            ontologies_cache[src] = guess_ontologies(cv_ontology_hints(cv_rows_cache[src]))
        attr_index = attr_index_cache[src]
        use_ror = "institution" in src.lower()

        for i, (value, count) in enumerate(value_counts.most_common()):
            if i >= args.max_values_per_field:
                print(f"  ! {table}.{field}: {len(value_counts) - args.max_values_per_field} more distinct "
                      f"value(s) beyond --max-values-per-field={args.max_values_per_field} not looked up")
                break
            category, detail = classify(value, attr_index)
            candidates = []
            if not args.no_lookup and category in ("curation_gap", "novel_term"):
                cache_key = f"{'ror' if use_ror else src}:{normalize(value)}"
                if cache_key in lookup_cache:
                    candidates = lookup_cache[cache_key]
                else:
                    if use_ror:
                        candidates = ror_search(value)
                    else:
                        candidates = ols_search(value, ontologies_cache[src])
                    lookup_cache[cache_key] = candidates
                    n_looked_up += 1
                    time.sleep(0.2)
            if candidates:
                for c in candidates:
                    suggestions.append({
                        "table": table, "field": field, "value": value, "count": count,
                        "cv_file": src, "category": category,
                        "suggestion_detail": json.dumps(detail) if detail else "",
                        "candidate_curie": c.get("curie") or "", "candidate_label": c.get("label") or "",
                        "candidate_url": c.get("url") or "", "candidate_source": c.get("source") or "",
                        "candidate_score": c.get("score", ""),
                    })
            else:
                suggestions.append({
                    "table": table, "field": field, "value": value, "count": count,
                    "cv_file": src, "category": category,
                    "suggestion_detail": json.dumps(detail) if detail else "",
                    "candidate_curie": "", "candidate_label": "", "candidate_url": "", "candidate_source": "",
                    "candidate_score": "",
                })

    fieldnames = ["table", "field", "value", "count", "cv_file", "category", "suggestion_detail",
                  "candidate_curie", "candidate_label", "candidate_url", "candidate_source", "candidate_score"]
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(suggestions)

    by_category = Counter(s["category"] for s in suggestions)
    print(f"Wrote {len(suggestions)} suggestion row(s) -> {args.out}")
    for cat, n in sorted(by_category.items(), key=lambda kv: -kv[1]):
        print(f"  {cat}: {n}")
    print(f"  {n_excluded} value(s) skipped as known non-ontology-mappable identifier fields")
    print(f"  {n_looked_up} external registry lookup(s) performed (OLS4 / ROR)")
    print("This script only proposes candidates - review mapping_suggestions.csv and apply "
          "accepted mappings by hand-editing the relevant CV CSV's Ontology Identifier/Url columns.")


if __name__ == "__main__":
    main()
