"""MC2 assay-metadata discovery + extraction (Part B, B1+B2).

Reads real per-file Synapse annotations reachable from each already-extracted
CCKP `Dataset.datasetId` and turns them into a `File View`-shaped CSV -
NOT a Biospecimen/Individual/Model extract. See the "Discovery findings"
section of this docstring for why, established by probing live data rather
than assumed:

  1. Identity check first. A `Dataset.datasetId` is NOT always a real Synapse
     `Dataset`/`DatasetCollection` entity - some are plain Folders (confirmed
     live: 2 of the first 15 datasetIds probed). Only `Dataset`/
     `DatasetCollection` entities (`entity.concreteType ==
     "org.sagebionetworks.repo.model.table.Dataset[Collection]"`) are queried
     further - a Folder is skipped, never treated as walkable.
  2. A confirmed Dataset/DatasetCollection entity's membership comes from its
     own `datasetItems` property (a list of `{entityId, versionNumber}`
     dicts) - NOT from listing a folder's children.
  3. Per mc2-center-dcc's own `table_to_annotations.py` (the DCC's write-side
     pipeline that produces these annotations), metadata is pushed down as
     *native Synapse annotations* directly on each member File entity - read
     here via `syn.get_annotations(file_id)`, never re-derived by this
     script. Confirmed live: every File's annotation dict has a **stable**
     key set (`BiospecimenKey`, `Component`, `DataUseCodes`, `DatasetViewKey`,
     `EntityId`, `FileAlias`, `FileAssay`, `FileDescription`, `FileDesign`,
     `FileFormat`, `FileLevel`, `FileSpecies`, `FileTissue`, `FileTumorType`,
     `FileUrl`, `FileViewId`, `Id`, `StudyKey`) across every Dataset probed -
     this is the MC2 model's `File View` class (see `modules/file/
     annotationProperty.csv`, `schema/mc2_model.linkml.yaml`'s `File View`
     class), NOT the full Biospecimen/Individual/Model record: `File View`
     only carries a `Biospecimen Key` **foreign key**, not Biospecimen's own
     detail fields (Type, Species, Preservation Method, Fixative, ...).
     Reaching those requires the DCC's own upstream Biospecimen/Individual/
     Model *tables* (joined via that key) - explicitly out of scope for this
     script per the decision to read only already-resolved per-file
     annotations, not re-derive DCC-internal joins.
  4. `FileTissue`/`FileTumorType` appear in every live annotation dict and do
     have real slot definitions with CV-backed enums in `schema/
     mc2_model.linkml.yaml` (`File Tissue`/`File Tumor Type`, both registered
     in `modules/mapping.yaml`) - but, as of this writing, neither slot is
     attached to any class in the schema (confirmed: not listed under any
     class's `slots:` block). They are extracted into the `File View` CSV
     alongside the class's own declared slots regardless, since the live
     data carries them - but `make harmonize-mc2-assay` won't harmonize them
     until they're attached to a class, which is a real, pre-existing model
     gap worth flagging to the MC2 modeling team, not something to silently
     patch here by inventing a class attachment.

Output: one row per member file, `data/mc2_assay/raw/File View.csv` (matches
the class's real name, spaces included, per harmonize.py's `{cls_name}.csv`
convention), plus a `datasetId` column so a `cckp_join`-style edge back to
the (public) `Dataset` class is possible later - not the DCC's internal
Biospecimen/Individual/Model tables, which this script never touches.
"""

import argparse
import csv
import os
import time

import synapseclient

# Synapse annotation key -> MC2 model attribute name, built from what's
# actually observed on live File View-annotated files (verified against
# several real Datasets, not assumed from the schema alone - see docstring
# point 4 re: FileTissue/FileTumorType). `Component`/`EntityId`/`Id` are
# Synapse/schematic bookkeeping, not modeled MC2 attributes - skipped.
ANNOTATION_KEY_TO_ATTRIBUTE = {
    "FileViewId": "FileView_id",
    "BiospecimenKey": "Biospecimen Key",
    "StudyKey": "Study Key",
    "DatasetViewKey": "DatasetView Key",
    "FileAlias": "File Alias",
    "FileDescription": "File Description",
    "FileDesign": "File Design",
    "FileLevel": "File Level",
    "FileAssay": "File Assay",
    "FileSpecies": "File Species",
    "FileUrl": "File Url",
    "FileFormat": "File Format",
    "DataUseCodes": "File Data Use Codes",
    "FileTissue": "File Tissue",
    "FileTumorType": "File Tumor Type",
}
DATASET_CONCRETE_TYPES = {
    "org.sagebionetworks.repo.model.table.Dataset",
    "org.sagebionetworks.repo.model.table.DatasetCollection",
}
LIST_DELIMITER = "|"


def annotation_values(ann, key):
    """synapseclient annotation values always come back as a list, even for
    a single-valued slot - join multi-valued ones with harmonize.py's own
    LIST_DELIMITER; a single value is returned bare."""
    values = [v for v in (ann.get(key) or []) if v not in (None, "")]
    return LIST_DELIMITER.join(str(v) for v in values)


def discover_dataset_entities(syn, dataset_ids, sleep_s=0.1):
    """Identity-check every candidate id; return only confirmed Dataset/
    DatasetCollection entities. Reports (not silently drops) what else was
    found, since the plan explicitly calls this out as unknown until probed."""
    confirmed, skipped_by_type = [], {}
    for did in dataset_ids:
        try:
            entity = syn.get(did, downloadFile=False)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            skipped_by_type[f"ERROR: {exc}"] = skipped_by_type.get(f"ERROR: {exc}", 0) + 1
            continue
        if entity.concreteType in DATASET_CONCRETE_TYPES:
            confirmed.append(did)
        else:
            skipped_by_type[entity.concreteType] = skipped_by_type.get(entity.concreteType, 0) + 1
        time.sleep(sleep_s)
    return confirmed, skipped_by_type


def extract_file_view_rows(syn, dataset_ids, sleep_s=0.1, max_files_per_dataset=None):
    rows = []
    for did in dataset_ids:
        entity = syn.get(did, downloadFile=False)
        items = entity.properties.get("datasetItems") or []
        if max_files_per_dataset:
            items = items[:max_files_per_dataset]
        for item in items:
            file_id = item["entityId"]
            try:
                ann = syn.get_annotations(file_id)
            except Exception as exc:  # noqa: BLE001 - report and keep going
                print(f"  ! could not read annotations for {file_id}: {exc}")
                continue
            row = {"datasetId": did, "fileEntityId": file_id}
            for key, attr in ANNOTATION_KEY_TO_ATTRIBUTE.items():
                row[attr] = annotation_values(ann, key)
            if any(v for k, v in row.items() if k not in ("datasetId", "fileEntityId")):
                rows.append(row)
            time.sleep(sleep_s)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-csv", required=True, help="data/raw/Dataset.csv (already extracted)")
    parser.add_argument("--out-dir", required=True, help="data/mc2_assay/raw")
    parser.add_argument("--max-datasets", type=int, default=None,
                         help="Cap how many datasetIds to probe/extract - omit for all")
    parser.add_argument("--max-files-per-dataset", type=int, default=None,
                         help="Cap how many member files to read per confirmed Dataset entity")
    parser.add_argument("--discovery-report", default=None,
                         help="Optional path to write the identity-check discovery report as JSON")
    args = parser.parse_args()

    with open(args.dataset_csv, newline="") as f:
        dataset_ids = [r["datasetId"] for r in csv.DictReader(f)]
    if args.max_datasets:
        dataset_ids = dataset_ids[: args.max_datasets]

    syn = synapseclient.Synapse()
    syn.login(silent=True)

    confirmed, skipped_by_type = discover_dataset_entities(syn, dataset_ids)
    print(f"Discovery: {len(confirmed)}/{len(dataset_ids)} datasetId(s) are real Dataset/DatasetCollection entities")
    for concrete_type, n in sorted(skipped_by_type.items(), key=lambda kv: -kv[1]):
        print(f"  skipped {n}: {concrete_type}")

    if args.discovery_report:
        import json

        with open(args.discovery_report, "w") as f:
            json.dump({"n_probed": len(dataset_ids), "n_confirmed": len(confirmed),
                       "skipped_by_type": skipped_by_type}, f, indent=2)
        print(f"Wrote discovery report -> {args.discovery_report}")

    rows = extract_file_view_rows(syn, confirmed, max_files_per_dataset=args.max_files_per_dataset)
    print(f"Extracted {len(rows)} File View row(s) from {len(confirmed)} confirmed Dataset entity/entities")

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "File View.csv")
    fieldnames = ["datasetId", "fileEntityId"] + list(ANNOTATION_KEY_TO_ATTRIBUTE.values())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote -> {out_path}")
    print("Note: this is a File View extract (per-file annotations only) - NOT full Biospecimen/Individual/"
          "Model records, which live in separate DCC-internal tables this script does not query. See the "
          "module docstring's 'Discovery findings'.")


if __name__ == "__main__":
    main()
