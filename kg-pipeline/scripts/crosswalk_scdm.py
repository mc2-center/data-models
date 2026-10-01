"""Crosswalks from MC2 controlled vocabularies to Sage Common Data Model
(SCDM) entities - see plans/scdm_alignment.md (steps 2-3) for the design.

Two crosswalks, deliberately different trust levels:

  - institution -> sagecdm:Organization (--organization-out): a ROR ID
    already *is* an organization's identity, so this is a deterministic
    join, not a judgment call - every row with a well-formed ROR
    Ontology Url in modules/institution/institution_name.csv gets a minted
    org.<slug> id, joined against modules/institution/institution_alias.csv
    on the shared ROR identifier for an acronym where one exists. No human
    review column - this crosswalk is trustworthy as generated.

  - consortium -> sagecdm:Program (--program-out): SCDM's Program class
    requires `description` and `status` (see
    schema/vendor/sagecdm/props.yaml), neither of which is recoverable from
    modules/consortium/consortium_id.csv - and `funding_source` can't be
    reliably attributed per-consortium from
    modules/consortium/consortium_funding_agency.csv (a single unlinked
    "NIH" row, not a per-consortium mapping). So a *new* row ships with
    `reviewed=false` and those three columns blank - a human fills them in
    and flips `reviewed` to `true` before scripts/link_scdm.py will mint
    that row. A rerun preserves any row a human has already curated
    (matched on `scdm_program_id`) rather than overwriting it with a blank
    one - see `load_existing_program_rows`. Never guessed here.

    Consortium_id (modules/consortium/consortium_id.csv) is this model's
    primary-key CV for the Consortium entity - `Attribute` is already the
    `program.<slug>` id `scripts/link_scdm.py`/`build_triples.py` mint
    against (Consortium_id is `primary_key`), while the bare acronym real
    CCKP `consortium` values actually store (CCBIR, HTAN, ...) lives in the
    CV's own `Notes` column (its `NCIt Code` column is blank for every row -
    verified directly against the file, not assumed from the column name).
    Reusing `Attribute` directly as `scdm_program_id` (rather than
    re-slugifying the acronym) guarantees this crosswalk's ids always match
    Consortium_id's own values exactly, with no risk of two
    independently-derived slugs drifting apart.

    A prior CV, modules/consortium/consortium_name.csv (bare acronym as
    `Attribute`, no `program.*` id), is what this script originally read -
    retired in commit 6552e4d ("Retire redundant FK-shadowing attributes +
    naming fixes") without updating this script, which broke `make
    crosswalk-scdm` (FileNotFoundError) until this fix.

Both are generated-but-committed, like mappings/crosswalks/*.sssom.tsv -
re-run this script after modules/institution|consortium/*.csv changes and
commit the result.
"""

import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_triples import normalize, slugify  # noqa: E402

ROR_ID_RE = re.compile(r"^https://ror\.org/0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$")


def load_cv_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_organization_crosswalk(institution_csv, institution_alias_csv):
    institution_rows = load_cv_rows(institution_csv)
    alias_rows = load_cv_rows(institution_alias_csv) if institution_alias_csv else []

    acronym_by_ror = {}
    for row in alias_rows:
        ror_id = (row.get("Ontology Url") or "").strip()
        alias = (row.get("Attribute") or "").strip()
        if ROR_ID_RE.match(ror_id) and alias:
            acronym_by_ror.setdefault(ror_id, alias)

    seen_ids = {}
    out_rows = []
    skipped = []
    for row in institution_rows:
        name = (row.get("Attribute") or "").strip()
        ror_id = (row.get("Ontology Url") or "").strip()
        if not name:
            continue
        if not ROR_ID_RE.match(ror_id):
            skipped.append(name)
            continue
        org_id = f"org.{slugify(name)}"
        if org_id in seen_ids:
            # Two different institution names slugifying to the same id -
            # a real collision to surface, not silently overwrite.
            raise ValueError(f"org id collision: '{org_id}' from both "
                              f"'{seen_ids[org_id]}' and '{name}'")
        seen_ids[org_id] = name
        out_rows.append({
            "institution_name": name,
            "scdm_organization_id": org_id,
            "scdm_name": name,
            "scdm_ror_id": ror_id,
            "scdm_acronym": acronym_by_ror.get(ror_id, ""),
        })
    return out_rows, skipped


def load_existing_program_rows(path):
    """{scdm_program_id: row dict} from a previously-written program
    crosswalk at `path`, if one exists - so re-running this script (e.g.
    after a consortium_id.csv edit) never silently discards a human's
    curated description/status/funding_source/reviewed=true. Keyed on
    scdm_program_id, which is derived from Consortium_id's own stable
    `Attribute` primary key, not row order."""
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {row["scdm_program_id"]: row for row in csv.DictReader(f, delimiter="\t")}


def build_program_crosswalk(consortium_csv, existing_rows=None):
    """Consortium_id's own CV: `Attribute` is already the program.<slug> id
    (Consortium_id is primary_key), the bare acronym real CCKP `consortium`
    values store (CCBIR, HTAN, ...) lives in the CV's own `Notes` column
    (its `NCIt Code` column is blank for every row) - see module docstring."""
    rows = load_cv_rows(consortium_csv)
    existing_rows = existing_rows or {}
    out_rows = []
    for row in rows:
        program_id = (row.get("Attribute") or "").strip()
        acronym = (row.get("Notes") or "").strip()
        if not program_id or not acronym:
            continue
        if program_id in existing_rows:
            out_rows.append(existing_rows[program_id])
            continue
        out_rows.append({
            "consortium_name": acronym,
            "scdm_program_id": program_id,
            "scdm_name": acronym,
            "scdm_description": "",
            "scdm_status": "",
            "scdm_funding_source": "",
            "reviewed": "false",
        })
    return out_rows


def write_tsv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--institution-cv", default="../modules/institution/institution_name.csv")
    parser.add_argument("--institution-alias-cv", default="../modules/institution/institution_alias.csv")
    parser.add_argument("--consortium-cv", default="../modules/consortium/consortium_id.csv")
    parser.add_argument("--organization-out", default="mappings/crosswalks/institution_to_scdm_organization.tsv")
    parser.add_argument("--program-out", default="mappings/crosswalks/consortium_to_scdm_program.tsv")
    args = parser.parse_args()

    org_rows, skipped = build_organization_crosswalk(args.institution_cv, args.institution_alias_cv)
    write_tsv(args.organization_out,
              ["institution_name", "scdm_organization_id", "scdm_name", "scdm_ror_id", "scdm_acronym"],
              org_rows)
    print(f"{args.institution_cv}: {len(org_rows)} institution(s) with a well-formed ROR id -> "
          f"{args.organization_out}")
    if skipped:
        print(f"  skipped (no well-formed ROR Ontology Url, not guessed): {', '.join(sorted(skipped))}")

    existing_program_rows = load_existing_program_rows(args.program_out)
    program_rows = build_program_crosswalk(args.consortium_cv, existing_program_rows)
    write_tsv(args.program_out,
              ["consortium_name", "scdm_program_id", "scdm_name", "scdm_description", "scdm_status",
               "scdm_funding_source", "reviewed"],
              program_rows)
    n_reviewed = sum(1 for r in program_rows if (r.get("reviewed") or "").strip().lower() == "true")
    print(f"{args.consortium_cv}: {len(program_rows)} consortium(a) -> {args.program_out} "
          f"({n_reviewed} already reviewed=true and preserved, "
          f"{len(program_rows) - n_reviewed} need human curation before scripts/link_scdm.py will mint them)")


if __name__ == "__main__":
    main()
