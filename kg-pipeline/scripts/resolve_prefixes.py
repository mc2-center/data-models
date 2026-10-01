"""Patch a LinkML schema's `prefixes:` block with real ontology base IRIs.

The csv-to-linkml skill (~/.claude/skills/csv-to-linkml/) resolves each CV
CSV's `Ontology Identifier` into a LinkML `meaning:` CURIE, but only
registers a handful of prefixes (linkml/mc2/DUO) in the generated schema's
own `prefixes:` block. Any `meaning:` CURIE whose prefix isn't declared
there fails to expand to a real IRI in downstream tools (e.g. `linkml
generate owl` emits a broken `<NCIT:C12345>` instead of
`<http://purl.obolibrary.org/obo/NCIT_C12345>`) - silently defeating the
whole point of carrying ontology mappings through to RDF.

This script derives the correct base IRI per prefix directly from the CV
CSVs' own `Ontology Url` column (real curated data, not a guessed
convention): for a row with `Ontology Identifier` "PREFIX:LOCAL" and
`Ontology Url` ending in "LOCAL", the base is the URL with that suffix
stripped. The majority base across all rows sharing a prefix wins; a
handful of rows have an unrelated citation URL in `Ontology Url` instead of
the term's real purl (a source-data quality issue, not something to fix
here) and are excluded from the vote via a `__NO_MATCH__` bucket so they
don't skew the result.

A small fallback table covers prefixes with zero clean matches (the
`Ontology Url` cells for every row using that prefix happen to be citation
links, not the term's own purl) - currently just PMID/pmid (a literature
identifier, not an ontology, with no purl to derive from) and ENVO/OBCS
(real OBO Foundry ontologies whose only rows in this repo have bad URLs).
"""

import argparse
import csv
import os
from collections import Counter, defaultdict

import yaml

KNOWN_BASE_FALLBACK = {
    "PMID": "https://pubmed.ncbi.nlm.nih.gov/",
    "pmid": "https://pubmed.ncbi.nlm.nih.gov/",
    "ENVO": "http://purl.obolibrary.org/obo/ENVO_",
    "OBCS": "http://purl.obolibrary.org/obo/OBCS_",
}


def collect_cv_files(mapping_path):
    with open(mapping_path) as f:
        mapping = yaml.safe_load(f)
    files = set()
    for entries in mapping.values():
        for entry in entries:
            files.add(entry["src"])
    return sorted(files)


def derive_prefix_bases(modules_dir, cv_files):
    """Return {prefix: (base_uri, matched_rows, total_rows)} plus a report of skipped rows."""
    votes = defaultdict(Counter)
    for src in cv_files:
        path = os.path.join(modules_dir, src)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if "Ontology Identifier" not in (reader.fieldnames or []):
                continue
            for row in reader:
                ident = (row.get("Ontology Identifier") or "").strip()
                url = (row.get("Ontology Url") or "").strip()
                if not ident or ":" not in ident or not url:
                    continue
                prefix, local = ident.split(":", 1)
                if local and url.endswith(local):
                    votes[prefix][url[: -len(local)]] += 1
                else:
                    votes[prefix]["__NO_MATCH__"] += 1

    resolved = {}
    unresolved = []
    for prefix, counter in votes.items():
        total = sum(counter.values())
        clean = Counter({b: c for b, c in counter.items() if b != "__NO_MATCH__"})
        if clean:
            base, matched = clean.most_common(1)[0]
            resolved[prefix] = (base, matched, total)
        else:
            unresolved.append((prefix, total))
    return resolved, unresolved


def patch_schema(schema_path, resolved, unresolved, report_path):
    with open(schema_path) as f:
        raw_lines = f.readlines()
    header_comment_lines = []
    for line in raw_lines:
        if line.startswith("#"):
            header_comment_lines.append(line)
        else:
            break

    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    existing = schema.setdefault("prefixes", {})
    added, skipped_existing, used_fallback, still_unresolved = [], [], [], []

    for prefix, (base, matched, total) in sorted(resolved.items()):
        if prefix in existing:
            skipped_existing.append((prefix, existing[prefix]))
            continue
        existing[prefix] = base
        added.append((prefix, base, matched, total))

    for prefix, total in sorted(unresolved):
        if prefix in existing:
            skipped_existing.append((prefix, existing[prefix]))
            continue
        if prefix in KNOWN_BASE_FALLBACK:
            existing[prefix] = KNOWN_BASE_FALLBACK[prefix]
            used_fallback.append((prefix, KNOWN_BASE_FALLBACK[prefix], total))
        else:
            still_unresolved.append((prefix, total))

    with open(schema_path, "w") as f:
        f.writelines(header_comment_lines)
        f.write(
            "# NOTE: this schema's `prefixes:` block was subsequently patched by "
            "scripts/resolve_prefixes.py to add ontology bases derived from the CV CSVs'\n"
            "# own Ontology Url data - see mc2_model_prefixes_report.md.\n"
        )
        yaml.safe_dump(schema, f, sort_keys=False, allow_unicode=True, width=100)

    with open(report_path, "w") as f:
        f.write("# Prefix resolution report\n\n")
        f.write(
            f"Patched `{schema_path}` — added {len(added)} prefixes derived from "
            f"real `Ontology Url` data, plus {len(used_fallback)} from a known-ontology "
            "fallback table.\n\n"
        )
        f.write("## Added (derived from Ontology Url in the CV CSVs)\n\n")
        f.write("| Prefix | Base IRI | Rows matched |\n|---|---|---|\n")
        for prefix, base, matched, total in added:
            flag = "" if matched == total else f" ⚠️ {total - matched} row(s) had an unrelated Ontology Url, excluded from the vote"
            f.write(f"| {prefix} | `{base}` | {matched}/{total}{flag} |\n")
        f.write("\n## Added from known-ontology fallback (zero clean matches in source data)\n\n")
        f.write("| Prefix | Base IRI | Rows affected |\n|---|---|---|\n")
        for prefix, base, total in used_fallback:
            f.write(f"| {prefix} | `{base}` | {total} |\n")
        if still_unresolved:
            f.write("\n## STILL UNRESOLVED — needs manual review\n\n")
            for prefix, total in still_unresolved:
                f.write(f"- `{prefix}` ({total} row(s)) — no clean Ontology Url match and no fallback known.\n")
        if skipped_existing:
            f.write("\n## Already declared in the schema (left untouched)\n\n")
            for prefix, base in skipped_existing:
                f.write(f"- `{prefix}` -> `{base}`\n")
        f.write(
            "\nNote: case-variant prefixes (e.g. `mesh`/`MeSH`/`MESH`, `PMID`/`pmid`) are "
            "registered separately rather than merged, since LinkML/OWL CURIE prefixes are "
            "case-sensitive and `meaning:` values in the schema use the source CSVs' exact "
            "casing — merging would require rewriting every `meaning:` value, which this "
            "script deliberately does not do.\n"
        )

    return added, used_fallback, still_unresolved, skipped_existing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", help="LinkML schema YAML to patch in place")
    parser.add_argument("--mapping", required=True, help="modules/mapping.yaml")
    parser.add_argument("--modules-dir", required=True, help="modules/ directory")
    parser.add_argument("--report", required=True, help="Where to write the markdown report")
    args = parser.parse_args()

    cv_files = collect_cv_files(args.mapping)
    resolved, unresolved = derive_prefix_bases(args.modules_dir, cv_files)
    added, used_fallback, still_unresolved, skipped = patch_schema(
        args.schema, resolved, unresolved, args.report
    )

    print(f"Added {len(added)} prefixes derived from Ontology Url data")
    print(f"Added {len(used_fallback)} prefixes from the known-ontology fallback table")
    if still_unresolved:
        print(f"WARNING: {len(still_unresolved)} prefix(es) remain unresolved: {still_unresolved}")
    print(f"Report written to {args.report}")


if __name__ == "__main__":
    main()
