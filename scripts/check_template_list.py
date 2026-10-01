#!/usr/bin/env python3
"""Check that the Makefile's ``DATA`` list matches the set of templates
(IsTemplate == true) defined across modules/*/annotationProperty.csv.

A class's label is its Attribute name with spaces removed (e.g.
"Imaging Channel" -> "ImagingChannel"), matching the convention
create_json_from_model.py/synapseclient.extensions.curator use to name
exported JSON Schemas / registered Synapse schemas.

Usage: python scripts/check_template_list.py

Exits non-zero (and prints both set differences) if DATA and the
IsTemplate-derived label set disagree, except for labels listed in
EXCLUDED below (each with a reason this script doesn't treat it as a
real mismatch).
"""
import glob
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent

# Label -> reason this known mismatch is not (yet) treated as an error.
# The orchestrator owns this list; leave it to them to finalize.
EXCLUDED = {
    "Collection": "Not a portal table or curation manifest; it groups other records for sharing, so no schema is registered for it.",
}


def get_makefile_data(makefile_path: Path) -> set:
    """Parse the DATA := ... line out of the Makefile."""
    text = makefile_path.read_text()
    match = re.search(r"^DATA\s*:=\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find a DATA := ... line in {makefile_path}")
    return set(match.group(1).split())


def get_template_labels(modules_glob: str) -> set:
    """Compute class labels for every IsTemplate==true row across
    modules/*/annotationProperty.csv."""
    labels = set()
    for csv_path in sorted(glob.glob(modules_glob)):
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        if "IsTemplate" not in df.columns:
            continue
        is_template = df["IsTemplate"].str.strip().str.lower() == "true"
        for attribute in df.loc[is_template, "Attribute"]:
            labels.add(attribute.replace(" ", ""))
    return labels


def main() -> int:
    makefile_path = REPO_ROOT / "Makefile"
    modules_glob = str(REPO_ROOT / "modules" / "*" / "annotationProperty.csv")

    data_set = get_makefile_data(makefile_path)
    template_labels = get_template_labels(modules_glob)

    missing_from_data = (template_labels - data_set) - set(EXCLUDED)
    extra_in_data = (data_set - template_labels) - set(EXCLUDED)

    print(f"Makefile DATA entries: {len(data_set)}")
    print(f"IsTemplate-derived labels: {len(template_labels)}")
    print()

    print(f"In IsTemplate labels but missing from Makefile DATA ({len(missing_from_data)}):")
    for label in sorted(missing_from_data):
        print(f"  {label}")
    print()

    print(f"In Makefile DATA but no matching IsTemplate row ({len(extra_in_data)}):")
    for label in sorted(extra_in_data):
        print(f"  {label}")
    print()

    if EXCLUDED:
        print("Excluded from the comparison above (see EXCLUDED at top of script):")
        for label, reason in EXCLUDED.items():
            in_templates = label in template_labels
            in_data = label in data_set
            print(f"  {label}: {reason} (in templates={in_templates}, in DATA={in_data})")
        print()

    if missing_from_data or extra_in_data:
        print("MISMATCH: Makefile DATA and IsTemplate-derived labels disagree.")
        return 1

    print("OK: Makefile DATA matches IsTemplate-derived labels (modulo EXCLUDED).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
