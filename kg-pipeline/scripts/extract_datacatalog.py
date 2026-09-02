"""Stage: extract "Data Catalog" annotations from native Synapse Dataset
entities into a `DataCatalog`-shaped raw CSV - see
plans/datacatalog_kg_integration.md for the full design.

These fields (measurementTechnique, license, includedInDataCatalog, ...) are
NOT populated through this repo's own manifest-submission process - they're
native Synapse annotations, populated directly on the Dataset entity itself
(by Synapse's own Data Catalog UI/metadata assistant, confirmed live: only
11 of 966 probed entities carry a `Component: Dataset` schematic-submission
marker alongside them; the rest carry the same key set with no such marker).
This script reads them directly via `syn.get_annotations()`, the same way
extract_mc2_assay_metadata.py reads native per-file annotations rather than
re-deriving anything.

Which CCKP Dataset rows qualify (established live, not assumed): of
`syn21897968` (the CCKP Dataset merged table)'s rows, only those with
`downloadType` in ("Synapse Hosted", "Synapse Indexed") are backed by a real
Synapse `Dataset` entity - confirmed via a 15-entity `concreteType` sample,
all `org.sagebionetworks.repo.model.table.Dataset`. For those rows,
`downloadSynId` is always populated and always equals `datasetId` (checked
across the full qualifying set, zero mismatches) - so `datasetId` alone is
the entity to fetch annotations from. `Externally Hosted`/`Not Available for
Download` rows have a blank `downloadSynId` and are skipped.

Known annotation keys read (see modules/dataCatalog/annotationProperty.csv
for what each means) - every one of these was deliberately named to match
its live Synapse annotation key exactly, so no key-renaming table is needed
here (unlike extract_mc2_assay_metadata.py's File-annotation PascalCase ->
"Title Case" mapping). Keys seen on real entities but NOT in this list are
administrative/technical noise (`entityType`, `newKey`, `Component`) or this
repo's own differently-shaped `Dataset*`/`GrantViewKey`/`duoCodes`-style
bleed-through annotations (a handful of entities carry both key sets) - both
are intentionally ignored, not just unmapped.
"""

import argparse
import csv
import os
from datetime import datetime, timezone

import synapseclient
import yaml

DATASET_TABLE_ID = "syn21897968"
LIST_DELIMITER = "|"

# Matches modules/dataCatalog/annotationProperty.csv's DataCatalog class
# DependsOn list, minus DataCatalog_id (set explicitly from datasetId below)
# and GrantView Key/Study Key/DatasetView Key (pre-existing FK placeholders
# not sourced from these entity annotations - left for a separate join).
KNOWN_ATTRIBUTES = [
    "studyId", "portal", "community", "description", "contributor", "keywords",
    "individualCount", "link", "croissant_s3_file_object", "accessType",
    "alternateName", "conditionsOfAccess", "countryOfOrigin", "creator",
    "authors", "dataUseModifiers", "datePublished", "funder", "grantNumber",
    "includedInDataCatalog", "license", "measurementTechnique", "dataType",
    "species", "subject", "title", "citation", "doi", "visualizeDataOn",
    "yearProcessed", "specimenCount", "series", "downloadType",
    "externalRepositoryUri", "ageGroup", "diseaseFocus", "manifestation",
]


def login():
    syn = synapseclient.Synapse()
    token = os.environ.get("SYNAPSE_AUTH_TOKEN")
    if token:
        syn.login(authToken=token, silent=True)
    else:
        syn.login(silent=True)
    return syn


def find_dataset_entity_ids(syn, dataset_table_id=DATASET_TABLE_ID):
    """{datasetId} for every CCKP Dataset row backed by a real Synapse
    Dataset entity - downloadType in ('Synapse Hosted', 'Synapse Indexed'),
    deduplicated (a datasetId can appear more than once in the merged table,
    e.g. under different grants/themes)."""
    query = (f"SELECT datasetId, downloadSynId FROM {dataset_table_id} "
             "WHERE downloadType IN ('Synapse Hosted', 'Synapse Indexed')")
    df = syn.tableQuery(query).asDataFrame()
    mismatches = df[df["datasetId"] != df["downloadSynId"]]
    if len(mismatches):
        print(f"WARNING: {len(mismatches)} row(s) have downloadSynId != datasetId - "
              "using datasetId, but this contradicts what was verified live 2026-09-01.")
    return sorted(set(df["datasetId"]))


def annotation_value(ann, key, multivalued):
    values = [v for v in (ann.get(key) or []) if str(v).strip()]
    if multivalued:
        return LIST_DELIMITER.join(str(v) for v in values)
    return str(values[0]) if values else ""


# Attributes declared string_list in modules/dataCatalog/annotationProperty.csv -
# everything else is read as a scalar (first value only), matching the live
# cardinality confirmed in plans/datacatalog_kg_integration.md.
MULTIVALUED_ATTRIBUTES = {
    "contributor", "keywords", "creator", "authors", "dataUseModifiers",
    "funder", "includedInDataCatalog", "measurementTechnique", "dataType",
    "species", "subject", "countryOfOrigin", "externalRepositoryUri",
}


def extract_datacatalog_rows(syn, dataset_ids, sleep_s=0.0):
    import time

    rows = []
    n_errors = 0
    for did in dataset_ids:
        try:
            ann = syn.get_annotations(did)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"  ! could not read annotations for {did}: {exc}")
            n_errors += 1
            continue
        row = {"DataCatalog_id": did}
        for attr in KNOWN_ATTRIBUTES:
            row[attr] = annotation_value(ann, attr, attr in MULTIVALUED_ATTRIBUTES)
        rows.append(row)
        if sleep_s:
            time.sleep(sleep_s)
    if n_errors:
        print(f"  {n_errors} entity/entities could not be read (see above)")
    return rows


def update_data_sources(data_sources_path, run_info):
    existing = {}
    if os.path.isfile(data_sources_path):
        with open(data_sources_path) as f:
            existing = yaml.safe_load(f) or {}
    existing.setdefault("tables", {})
    existing["tables"].update(run_info)
    with open(data_sources_path, "w") as f:
        yaml.safe_dump(existing, f, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", required=True, help="data/raw")
    parser.add_argument("--data-sources", default=None, help="data_sources.yaml (optional provenance record)")
    parser.add_argument("--max-datasets", type=int, default=None,
                         help="Cap how many Dataset entities to read - omit for all")
    args = parser.parse_args()

    syn = login()

    dataset_ids = find_dataset_entity_ids(syn)
    if args.max_datasets:
        dataset_ids = dataset_ids[: args.max_datasets]
    print(f"{len(dataset_ids)} native Synapse Dataset entity/entities to read "
          f"(downloadType in Synapse Hosted/Synapse Indexed)")

    rows = extract_datacatalog_rows(syn, dataset_ids)

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "DataCatalog.csv")
    fieldnames = ["DataCatalog_id"] + KNOWN_ATTRIBUTES
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Extracted {len(rows)} DataCatalog row(s) -> {out_path}")

    if args.data_sources:
        update_data_sources(args.data_sources, {
            "DataCatalog": {
                "synapse_id": f"{DATASET_TABLE_ID} (native Dataset entity annotations, not the table itself)",
                "row_count": len(rows),
                "queried_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
        })
        print(f"Provenance recorded in {args.data_sources}")


if __name__ == "__main__":
    main()
