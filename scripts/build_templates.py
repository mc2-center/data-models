"""Write blank manifest templates (templates/<Component>.csv) from mc2.model.csv.

Each template has a header row of "Component" followed by the template's
DependsOn attributes, and one row holding the component name. Only templates
that already exist in templates/ are rewritten, unless their names are given
on the command line.

Usage:
    python scripts/build_templates.py              # refresh existing templates
    python scripts/build_templates.py PersonView   # also create/refresh these
"""

import csv
import os
import sys

import pandas as pd

MODEL = "mc2.model.csv"
TEMPLATE_DIR = "templates"


def template_columns(model_path=MODEL):
    df = pd.read_csv(model_path, dtype=str, keep_default_na=False)
    templates = df[df["IsTemplate"].str.upper() == "TRUE"]
    return {
        row["Attribute"].replace(" ", ""): [
            a.strip() for a in row["DependsOn"].split(",") if a.strip()
        ]
        for _, row in templates.iterrows()
    }


def main(extra):
    columns = template_columns()
    existing = {f[:-4] for f in os.listdir(TEMPLATE_DIR) if f.endswith(".csv")}
    names = sorted(existing | set(extra))
    missing = [n for n in names if n not in columns]
    if missing:
        sys.exit(f"No IsTemplate row in {MODEL} for: {', '.join(missing)}")
    for name in names:
        attrs = columns[name]
        with open(os.path.join(TEMPLATE_DIR, f"{name}.csv"), "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["Component"] + attrs)
            writer.writerow([name] + [""] * len(attrs))
    print(f"Wrote {len(names)} templates to {TEMPLATE_DIR}/")


if __name__ == "__main__":
    main(sys.argv[1:])
