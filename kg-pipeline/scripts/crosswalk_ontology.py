"""Cross-vocabulary crosswalks for federating with sagebrain-model.

kg-pipeline's own harmonization (scripts/harmonize.py) anchors CVs in
whatever ontology the MC2 model already curated them against - mostly NCIT,
plus BTO/DOID for a few fields. sagebrain-model (a sibling Sage Bionetworks
ontology meant to integrate data *across* Synapse portals) anchors the same
kind of concepts differently: `biolink:Disease` in MONDO, and its worked
example instantiates `sagebrain:Tissue`/`Organ` in UBERON. Without a
crosswalk, a CCKP/MC2 NCIT-anchored disease or tissue term and a sagebrain
MONDO/UBERON-anchored one for the same real-world concept can't be joined in
a federated query even though they mean the same thing.

This script does NOT change how kg-pipeline harmonizes its own data (that
stays NCIT/BTO/DOID-anchored, unchanged) - it produces a *supplementary*
crosswalk: for every CV row that already has a curated source-ontology
`Ontology Identifier`, look up the same label in a target ontology and
record the hit for human review. Kept in mappings/crosswalks/, deliberately
separate from mappings/sssom/ (which records what harmonize.py resolves
against) so "the mapping we harmonize on" and "a supplementary federation
crosswalk" are never conflated. Like suggest_mappings.py, this script only
ever proposes - a crosswalk hit is never written back into a CV's own
Ontology Identifier/Url columns automatically.
"""

import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suggest_mappings import normalize, ols_search  # noqa: E402

CURIE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]*:\S+$")


def load_cv_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def crosswalk(cv_rows, target_ontology, rows=3):
    """For every row with a populated, well-formed source Ontology
    Identifier, search target_ontology for an exact label match. Returns a
    list of dicts: source term/CURIE, candidate target CURIE/label/url (best
    hit only - kept to one row per source term since this is a proposal
    list, not an exhaustive search dump)."""
    results = []
    for row in cv_rows:
        term = (row.get("Attribute") or "").strip()
        source_ident = (row.get("Ontology Identifier") or "").strip()
        if not term or not source_ident or not CURIE_RE.match(source_ident):
            continue
        hits = ols_search(term, [target_ontology], rows=rows)
        exact = [h for h in hits if h.get("label") and normalize(h["label"]) == normalize(term)]
        best = exact[0] if exact else (hits[0] if hits else None)
        results.append({
            "source_term": term,
            "source_curie": source_ident,
            "target_curie": (best or {}).get("curie") or "",
            "target_label": (best or {}).get("label") or "",
            "target_url": (best or {}).get("url") or "",
            "exact_label_match": bool(exact),
        })
    return results


def write_sssom(path, source_prefix, target_ontology, results):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        f.write("# curie_map:\n#   skos: http://www.w3.org/2004/02/skos/core#\n"
                "#   semapv: https://w3id.org/semapv/vocab/\n")
        f.write(f"# mapping_set_id: https://w3id.org/mc2-center/cckp-portal/crosswalks/"
                f"{os.path.basename(path)}\n")
        f.write(f"# comment: supplementary {source_prefix}->{target_ontology.upper()} crosswalk for "
                "federation with sagebrain-model - NOT the mapping harmonize.py resolves against; "
                "review before treating any row as confirmed.\n")
        f.write("# license: https://creativecommons.org/publicdomain/zero/1.0/\n")
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["subject_id", "subject_label", "predicate_id", "object_id", "object_label",
                          "mapping_justification", "confidence"])
        for r in results:
            if not r["target_curie"]:
                continue
            justification = "semapv:LexicalMatching"
            confidence = "high" if r["exact_label_match"] else "low"
            writer.writerow([r["source_curie"], r["source_term"], "skos:exactMatch",
                              r["target_curie"], r["target_label"], justification, confidence])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cv", required=True, help="Path to the MC2 CV CSV to crosswalk, "
                         "e.g. ../modules/shared/tumorType.csv")
    parser.add_argument("--target-ontology", required=True, help="OLS4 ontology id to search, e.g. mondo, uberon")
    parser.add_argument("--out", required=True, help="Output SSSOM-style TSV path, "
                         "e.g. mappings/crosswalks/tumorType_ncit_to_mondo.sssom.tsv")
    parser.add_argument("--rows", type=int, default=3)
    args = parser.parse_args()

    cv_rows = load_cv_rows(args.cv)
    results = crosswalk(cv_rows, args.target_ontology, rows=args.rows)
    source_prefix = next((r["source_curie"].split(":", 1)[0] for r in results if r["source_curie"]), "unknown")
    write_sssom(args.out, source_prefix, args.target_ontology, results)

    n_hit = sum(1 for r in results if r["target_curie"])
    n_exact = sum(1 for r in results if r["exact_label_match"])
    print(f"{args.cv}: {len(results)} curated row(s) checked against {args.target_ontology} -> "
          f"{n_hit} candidate(s) found ({n_exact} exact label match) -> {args.out}")
    print("This is a proposal list for human review - no CV file was modified.")


if __name__ == "__main__":
    main()
