"""Stage 2: extract CCKP source tables from Synapse into raw CSVs.

Uses synapseclient (already a repo dependency, already used by
create_json_from_model.py at the repo root) rather than raw REST calls, so
pagination/async-query polling is handled for us. Auth follows the same
pattern as create_json_from_model.py: prefer SYNAPSE_AUTH_TOKEN (for CI),
fall back to a cached/interactive synapseclient session (for local use).

v1 scope is the 5 confirmed-live View tables documented by the cckp-search
skill (~/.claude/skills/cckp-search/references/backend_tables.md).
Person/PersonView is out of scope (unconfirmed table ID + consent-gating
logic) - see kg-pipeline/README.md.
"""

import argparse
import csv
import os
from datetime import datetime, timezone

import synapseclient
import yaml

TABLES = {
    "Dataset": "syn21897968",
    "Publication": "syn21868591",
    "Tool": "syn26127427",
    "Grant": "syn21918972",
    "EducationalResource": "syn51497305",
}

# Synapse STRING_LIST columns come back from asDataFrame() as native Python
# lists already (not delimited strings) - written out here pipe-delimited
# for a stable, git-diffable CSV representation. "|" is chosen because none
# of the controlled-vocabulary term labels in the MC2 model contain it
# (checked against modules/*/*.csv), unlike "," which appears in some
# free-text descriptions.
LIST_DELIMITER = "|"


def login():
    syn = synapseclient.Synapse()
    token = os.environ.get("SYNAPSE_AUTH_TOKEN")
    if token:
        syn.login(authToken=token, silent=True)
    else:
        syn.login(silent=True)
    return syn


def flatten_cell(value):
    if isinstance(value, list):
        return LIST_DELIMITER.join(str(v) for v in value)
    if value is None:
        return ""
    return value


def extract_table(syn, name, synid, out_dir):
    query = f"SELECT * FROM {synid}"
    results = syn.tableQuery(query)
    df = results.asDataFrame()
    df = df.map(flatten_cell)

    out_path = os.path.join(out_dir, f"{name}.csv")
    df.to_csv(out_path, index=False, quoting=csv.QUOTE_MINIMAL)
    return len(df), out_path


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--data-sources", required=True)
    parser.add_argument("--tables", nargs="+", choices=list(TABLES.keys()), default=list(TABLES.keys()),
                         help="Subset of tables to extract (default: all in-scope tables)")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    syn = login()

    run_info = {}
    for name in args.tables:
        synid = TABLES[name]
        n_rows, out_path = extract_table(syn, name, synid, args.out_dir)
        print(f"{name} ({synid}): {n_rows} rows -> {out_path}")
        run_info[name] = {
            "synapse_id": synid,
            "row_count": n_rows,
            "queried_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    update_data_sources(args.data_sources, run_info)
    print(f"Provenance recorded in {args.data_sources}")


if __name__ == "__main__":
    main()
