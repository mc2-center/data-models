"""Link the MC2 assay-metadata graph into sagebrain-model's classes/properties.

The `File View` extraction (extract_mc2_assay_metadata.py, harmonize.py,
build_triples.py) gives us one row per file with a `Biospecimen Key` foreign
key plus a few file-level projections of that specimen's own fields (`File
Species`, `File Tissue`, `File Tumor Type`) - not a fully-populated
Biospecimen entity (that lives in a separate DCC-internal table this
pipeline doesn't query, by design - see extract_mc2_assay_metadata.py's
docstring). This script does the honest thing with what's actually there:

  1. Group harmonized File View rows by `Biospecimen Key` and mint ONE stub
     node per distinct key, typed directly as `biolink:MaterialSample`
     (the same Biolink class sagebrain-model itself reuses by IRI for
     `sagebrain:has_sample`'s range) - not a fabricated `cckp:Biospecimen`
     instance with attributes we don't actually have.
  2. Multiple files can reference the same Biospecimen Key with slightly
     different File Tissue/File Tumor Type/File Species values (e.g. a
     stale annotation on an older file) - aggregate with the same
     "verify consistency, report disagreement, still emit a best-effort
     value" discipline used elsewhere in this pipeline (unmapped_terms.csv,
     malformed_cv_terms.csv): disagreements are written to
     `biospecimen_annotation_conflicts.csv`, not silently resolved.
  3. Read File Tissue/File Tumor Type's already-resolved
     `{field}_ontology_iri` columns from the harmonized File View CSV -
     `File View` is now registered in the Makefile's `MC2_ASSAY_CLASSES`
     list and both slots are attached to the `File View` class in
     mc2_model.linkml.yaml, so harmonize.py's normal class-driven pass
     resolves them the same way it resolves every other CV-backed field.
     This script used to re-harmonize both fields itself (a second,
     duplicate `load_cv_lookup` pass against tissue.csv/tumorType.csv)
     because neither slot used to be attached to any class - that gap is
     fixed now, so the duplicate pass is gone.
  4. Cross-walk the resolved NCIT/BTO term to sagebrain's own anchor
     ontology - UBERON for tissue, MONDO for tumor type - using ONLY
     `confidence: high` (exact label match) rows from
     mappings/crosswalks/*.sssom.tsv (scripts/crosswalk_ontology.py's
     output). A low-confidence crosswalk hit is skipped, not guessed.
  5. Emit `sagebrain:source_tissue` (MaterialSample -> Tissue-as-UBERON-term)
     and `sagebrain:has_pathology` (MaterialSample -> the resolved
     MONDO/NCIT tumor-type term, standing in as the closest available
     sagebrain "Pathology" concept) - reusing sagebrain's own declared
     properties, never inventing a new predicate.

Output stays inside the isolated, gitignored data/mc2_assay/ tree, like
every other MC2 assay-metadata artifact - see README.md.
"""

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

import rdflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_triples import mint_iri, normalize  # noqa: E402
from harmonize import CURIE_RE, URL_RE  # noqa: E402

SAGEBRAIN = rdflib.Namespace("https://w3id.org/synapse/sagebrain#")
BIOLINK = rdflib.Namespace("https://w3id.org/biolink/vocab/")
# Sentinel placeholders seen in live Biospecimen Key values - not a real
# specimen identifier, so not worth minting a MaterialSample stub for (same
# discipline as build_triples.py's external_iri() skipping "Pending
# Annotation"/"DOI Not Available" rather than templating a fake IRI).
SENTINEL_KEYS = {"not applicable", "not-applicable", "pending annotation", "n/a", "na", "unknown"}


def obo_purl(curie):
    """UBERON:0000310 -> http://purl.obolibrary.org/obo/UBERON_0000310 - the
    standard OBO Foundry purl pattern both UBERON and MONDO follow (the
    crosswalk files this script reads only ever contain OBO-style targets)."""
    prefix, local = curie.split(":", 1)
    return f"http://purl.obolibrary.org/obo/{prefix}_{local}"


def curie_from_resolved(value):
    """Reverse of obo_purl(): the harmonized `{field}_ontology_iri` column
    holds `url or ident` per harmonize.py's own convention (it prefers a CV
    row's Ontology Url over its bare Identifier), but the crosswalk TSVs
    below are always keyed by source CURIE, not URL. Every CV this script
    reads (tissue.csv, tumorType.csv) uses the OBO Foundry purl form
    exclusively for its Ontology Url - same assumption obo_purl() already
    makes for crosswalk targets - so this just reads the last path segment
    back into PREFIX:LOCAL. A value that's already a CURIE (no Ontology Url
    was recorded for that CV row) passes through unchanged; anything blank
    or not matching either shape is treated as unresolved.

    Checked in URL-first order deliberately: a URL like
    "http://purl.obolibrary.org/obo/NCIT_C12971" also satisfies CURIE_RE
    (its "http:" scheme prefix alone matches PREFIX:REST), so CURIE_RE can't
    be checked first without misidentifying every URL as an already-bare
    CURIE."""
    if not value:
        return None
    if URL_RE.match(value):
        tail = value.rsplit("/", 1)[-1]
        if "_" in tail:
            prefix, local = tail.split("_", 1)
            return f"{prefix}:{local}"
        return None
    if CURIE_RE.match(value):
        return value
    return None


def load_crosswalk(path, min_confidence="high"):
    """{source_curie: target_curie} from a crosswalk_ontology.py TSV,
    keeping only rows at least as confident as min_confidence."""
    crosswalk = {}
    if not path or not os.path.isfile(path):
        return crosswalk
    with open(path, newline="") as f:
        # SSSOM's leading `# key: value` metadata lines aren't part of the
        # TSV header csv.DictReader should parse - skip them first, same
        # comment convention crosswalk_ontology.py's write_sssom() writes.
        data_lines = (line for line in f if not line.startswith("#"))
        for row in csv.DictReader(data_lines, delimiter="\t"):
            if row.get("confidence") == min_confidence and row.get("object_id"):
                crosswalk[row["subject_id"]] = row["object_id"]
    return crosswalk


def aggregate_by_biospecimen_key(file_view_rows):
    """(resolved, conflicts). resolved: {biospecimen_key: {"File Tissue":
    resolved_curie_or_None, "File Tumor Type": ...}} - one representative
    (most-common) resolved value per field, reading each field's already-
    harmonized `{field}_ontology_iri` column (see module docstring point 3)
    rather than re-resolving the raw label here. Any disagreement across
    the group's member files is reported in `conflicts`, not silently
    resolved."""
    groups = defaultdict(lambda: defaultdict(Counter))
    for row in file_view_rows:
        key = (row.get("Biospecimen Key") or "").strip()
        if not key or normalize(key) in SENTINEL_KEYS:
            continue
        for field in ("File Tissue", "File Tumor Type"):
            curie = curie_from_resolved((row.get(f"{field}_ontology_iri") or "").strip())
            if curie:
                groups[key][field][curie] += 1

    resolved = {}
    conflicts = []
    for key, field_counts in groups.items():
        resolved[key] = {}
        for field, counter in field_counts.items():
            if len(counter) > 1:
                conflicts.append({
                    "biospecimen_key": key, "field": field,
                    "conflicting_values": ";".join(sorted(counter)),
                })
            resolved[key][field] = counter.most_common(1)[0][0]
    return resolved, conflicts


def build_sagebrain_links(file_view_harmonized_csv, tissue_crosswalk_path, tumor_type_crosswalk_path):
    with open(file_view_harmonized_csv, newline="") as f:
        rows = list(csv.DictReader(f))

    tissue_crosswalk = load_crosswalk(tissue_crosswalk_path)
    tumor_type_crosswalk = load_crosswalk(tumor_type_crosswalk_path)

    resolved, conflicts = aggregate_by_biospecimen_key(rows)

    g = rdflib.Graph()
    g.bind("sagebrain", SAGEBRAIN)
    g.bind("biolink", BIOLINK)
    n_source_tissue = n_has_pathology = 0

    for key, fields in resolved.items():
        subject = mint_iri("Biospecimen", key)
        g.add((subject, rdflib.RDF.type, BIOLINK.MaterialSample))

        tissue_ncit = fields.get("File Tissue")
        uberon = tissue_crosswalk.get(tissue_ncit) if tissue_ncit else None
        if uberon:
            g.add((subject, SAGEBRAIN.source_tissue, rdflib.URIRef(obo_purl(uberon))))
            n_source_tissue += 1

        tumor_type_ncit = fields.get("File Tumor Type")
        mondo = tumor_type_crosswalk.get(tumor_type_ncit) if tumor_type_ncit else None
        if mondo:
            g.add((subject, SAGEBRAIN.has_pathology, rdflib.URIRef(obo_purl(mondo))))
            n_has_pathology += 1

    return g, conflicts, n_source_tissue, n_has_pathology


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file-view-harmonized", required=True,
                         help='data/mc2_assay/harmonized/"File View_harmonized.csv"')
    parser.add_argument("--tissue-crosswalk", default="mappings/crosswalks/tissue_ncit_to_uberon.sssom.tsv")
    parser.add_argument("--tumor-type-crosswalk", default="mappings/crosswalks/tumorType_ncit_to_mondo.sssom.tsv")
    parser.add_argument("--out", required=True, help="data/mc2_assay/rdf/sagebrain_links.ttl")
    parser.add_argument("--conflicts-out", default=None,
                         help="data/mc2_assay/harmonized/biospecimen_annotation_conflicts.csv")
    args = parser.parse_args()

    g, conflicts, n_source_tissue, n_has_pathology = build_sagebrain_links(
        args.file_view_harmonized, args.tissue_crosswalk, args.tumor_type_crosswalk,
    )
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    g.serialize(destination=args.out, format="turtle")
    print(f"{len(g)} triple(s) -> {args.out} ({n_source_tissue} source_tissue, {n_has_pathology} has_pathology)")

    if conflicts:
        conflicts_path = args.conflicts_out or os.path.join(
            os.path.dirname(args.file_view_harmonized), "biospecimen_annotation_conflicts.csv")
        with open(conflicts_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["biospecimen_key", "field", "conflicting_values"])
            writer.writeheader()
            writer.writerows(conflicts)
        print(f"WARNING: {len(conflicts)} biospecimen key(s) have disagreeing values across their member "
              f"files - see {conflicts_path}")


if __name__ == "__main__":
    main()
