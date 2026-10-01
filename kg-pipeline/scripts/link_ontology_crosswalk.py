"""Stage: promote reviewed NCIT->MONDO/UBERON crosswalk rows into a linked
graph - see plans/mondo_uberon_federation_promotion.md for the full design.

scripts/crosswalk_ontology.py already produces supplementary NCIT->MONDO/
UBERON crosswalks for federation with sagebrain-model
(mappings/crosswalks/*_ncit_to_mondo.sssom.tsv, tissue_ncit_to_uberon.sssom.tsv),
gated behind a `reviewed` column (default "false") a human flips to "true"
row-by-row, same pattern as mappings/crosswalks/consortium_to_scdm_program.tsv
+ scripts/link_scdm.py. This script is the corresponding consumer: for every
harmonized CCKP row whose existing NCIT-anchored `_ontology_iri` cell
matches a **reviewed** crosswalk row, mint an additional MONDO/UBERON edge -
`cckp:tumorTypeMondoTerm` or `cckp:tissueUberonTerm` - alongside (never
replacing) the NCIT edge `build_triples.py` already emits as
`cckp:tumorTypeTerm`/`cckp:tissueTerm`.

Only `tumorType` and `tissue` are wired up here, even though
scripts/crosswalk_ontology.py has also produced committed crosswalks for
"Disease Type" and "Last Known Disease Status" (mappings/crosswalks/
diseaseType_ncit_to_mondo.sssom.tsv, diseaseStatus_ncit_to_mondo.sssom.tsv).
Those two are MC2 individual/biospecimen-level attributes
(modules/mapping.yaml), not fields on any of the 5 CCKP portal classes
(schema/cckp_portal.linkml.yaml) and not currently extracted by the
access-controlled mc2-assay stage either - confirmed in
plans/kg_pipeline_architecture_decisions.md's own finding that `File View`
only carries a `Biospecimen Key` foreign key, not the specimen's own detail
fields. No `cckp:diseaseTypeTerm`/`diseaseStatusTerm` edge exists anywhere
in this pipeline's output to attach a MONDO edge to yet. Their crosswalks
stay committed, reviewed rows and all, for whenever a future stage extracts
those fields - this script's own summary output below says so explicitly
rather than silently pretending they were processed.

Output stays a separate file (data/rdf/ontology_crosswalk_links.ttl), not
merged into cckp_kg.ttl in place - same "separate provenance file, same
subject IRIs, combine by simple triple-set union" convention documented in
README.md for scdm_links.ttl/DataCatalog.ttl.
"""

import argparse
import csv
import os
import sys

import rdflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_triples import expand_curie_or_url, load_prefixes, mint_id, mint_iri, read_harmonized  # noqa: E402

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
LIST_DELIMITER = "|"

# field -> (crosswalk TSV path, target-ontology label used in the new
# predicate's name). Restricted to fields that are real cckp_portal.linkml.yaml
# attributes with an mc2_enum on at least one of the 5 CCKP classes - see
# module docstring for why "Disease Type"/"Last Known Disease Status" are
# deliberately excluded here despite having committed crosswalks.
FIELD_CROSSWALKS = {
    "tumorType": ("mappings/crosswalks/tumorType_ncit_to_mondo.sssom.tsv", "Mondo"),
    "tissue": ("mappings/crosswalks/tissue_ncit_to_uberon.sssom.tsv", "Uberon"),
}
# Classes that carry each field, confirmed against cckp_portal.linkml.yaml
# (Tool/Grant/EducationalResource have neither tumorType nor tissue).
FIELD_CLASSES = {"tumorType": ("Dataset", "Publication"), "tissue": ("Dataset", "Publication")}
# Committed but not yet consumable - see module docstring. Reported, not
# silently skipped.
NOT_YET_CONSUMABLE_CROSSWALKS = [
    "mappings/crosswalks/diseaseType_ncit_to_mondo.sssom.tsv",
    "mappings/crosswalks/diseaseStatus_ncit_to_mondo.sssom.tsv",
]


def load_reviewed_crosswalk(path, prefixes):
    """{expanded_source_iri: (target_curie, target_label)} - reviewed=="true"
    rows only. The source side is expanded the same way build_triples.py
    expands a harmonized CSV's `_ontology_iri` cell (bare CURIE or already a
    URL, via the MC2 model schema's own `prefixes:` block), so both sides of
    the join are guaranteed to be the same string for the same real term."""
    index = {}
    if not os.path.isfile(path):
        return index
    with open(path, newline="") as f:
        body = [line for line in f if not line.startswith("#")]
    for row in csv.DictReader(body, delimiter="\t"):
        if (row.get("reviewed") or "").strip().lower() != "true":
            continue
        expanded = expand_curie_or_url(row["subject_id"], prefixes)
        if expanded:
            index[expanded] = (row["object_id"], row["object_label"])
    return index


def link_field(g, harmonized_dir, field, crosswalk_index, target_label, prefixes):
    predicate = CCKP[f"{field}{target_label}Term"]
    n_edges = 0
    n_rows_with_hit = 0
    for cls_name in FIELD_CLASSES[field]:
        for row in read_harmonized(harmonized_dir, cls_name):
            iri_cell = (row.get(f"{field}_ontology_iri") or "").strip()
            if not iri_cell:
                continue
            subject = None
            row_had_hit = False
            for entry in iri_cell.split(LIST_DELIMITER):
                entry = entry.strip()
                if not entry:
                    continue
                hit = crosswalk_index.get(entry)
                if not hit:
                    continue
                target_curie, _target_label = hit
                target_iri = expand_curie_or_url(target_curie, prefixes)
                if not target_iri:
                    continue
                if subject is None:
                    subject = mint_iri(cls_name, mint_id(cls_name, row))
                g.add((subject, predicate, rdflib.URIRef(target_iri)))
                n_edges += 1
                row_had_hit = True
            if row_had_hit:
                n_rows_with_hit += 1
    return n_edges, n_rows_with_hit


def build_ontology_crosswalk_links(harmonized_dir, mc2_schema_path, crosswalk_overrides=None):
    prefixes = load_prefixes(mc2_schema_path)
    g = rdflib.Graph()
    g.bind("cckp", CCKP)

    stats = {}
    for field, (default_path, target_label) in FIELD_CROSSWALKS.items():
        path = (crosswalk_overrides or {}).get(field, default_path)
        crosswalk_index = load_reviewed_crosswalk(path, prefixes)
        n_edges, n_rows = link_field(g, harmonized_dir, field, crosswalk_index, target_label, prefixes)
        stats[field] = {
            "reviewed_rows": len(crosswalk_index), "edges": n_edges, "rows_linked": n_rows,
            "predicate": f"{field}{target_label}Term",
        }
    return g, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--harmonized-dir", default="data/harmonized")
    parser.add_argument("--mc2-schema", default="schema/mc2_model.linkml.yaml")
    parser.add_argument("--tumor-type-crosswalk", default="mappings/crosswalks/tumorType_ncit_to_mondo.sssom.tsv")
    parser.add_argument("--tissue-crosswalk", default="mappings/crosswalks/tissue_ncit_to_uberon.sssom.tsv")
    parser.add_argument("--out", default="data/rdf/ontology_crosswalk_links.ttl")
    args = parser.parse_args()

    overrides = {"tumorType": args.tumor_type_crosswalk, "tissue": args.tissue_crosswalk}
    g, stats = build_ontology_crosswalk_links(args.harmonized_dir, args.mc2_schema, overrides)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    g.serialize(destination=args.out, format="turtle")

    print(f"{len(g)} triple(s) -> {args.out}")
    for field, s in stats.items():
        print(f"  {field}: {s['reviewed_rows']} reviewed crosswalk row(s), "
              f"{s['edges']} cckp:{s['predicate']} edge(s) across {s['rows_linked']} row(s)")
    print(f"  Not yet consumable (no matching CCKP field extracted): {', '.join(NOT_YET_CONSUMABLE_CROSSWALKS)}")


if __name__ == "__main__":
    main()
