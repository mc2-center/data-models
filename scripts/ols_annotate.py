#!/usr/bin/env python3
"""OLS Annotator: prepare worklists and apply decisions for ontology annotation."""

import argparse
import csv
import json
import os
import re
import sys

ONTOLOGY_ID_COL = "Ontology Identifier"
ONTOLOGY_URL_COL = "Ontology Url"
DESCRIPTION_COL = "Description"
NCIT_CODE_COL = "NCIt Code"


def normalize_curie(raw):
    if not raw:
        return ""
    raw = raw.strip()
    if ":" in raw:
        return raw
    m = re.match(r"^([A-Za-z]+)_([A-Za-z0-9]+)$", raw)
    if m:
        return f"{m.group(1).upper()}:{m.group(2)}"
    return raw


def get_ncit_code(curie):
    m = re.match(r"^NCIT:(C\d+)$", curie, re.IGNORECASE)
    return m.group(1) if m else None


def cmd_prepare(args):
    vocab_path = args.vocab
    model_path = args.model
    out_path = args.out or "worklist.json"
    term_col_arg = args.term_column or "Attribute"
    parent_attr = args.parent_attribute

    with open(vocab_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    # Find term column (case-insensitive, strip BOM)
    term_col = next((c for c in fieldnames if c.strip().lstrip("﻿").lower() == term_col_arg.lower()), None)
    if not term_col:
        print(f"ERROR: term column '{term_col_arg}' not found in {fieldnames}", file=sys.stderr)
        sys.exit(1)

    # Detect Parent column
    parent_col = next((c for c in fieldnames if c.strip().lower() == "parent"), None)

    # Infer parent attribute from Parent column if not supplied
    if not parent_attr and parent_col:
        parents = {r[parent_col].strip() for r in rows if r.get(parent_col, "").strip()}
        if len(parents) == 1:
            parent_attr = next(iter(parents))
            print(f"Detected parent attribute: {parent_attr!r}")
        elif parents:
            print(f"Multiple parent values detected: {parents}", file=sys.stderr)

    is_annotation_property = "Valid Values" in fieldnames or "IsTemplate" in fieldnames

    # Look up parent definition from model CSV
    parent_def = ""
    if model_path and os.path.exists(model_path) and parent_attr:
        try:
            with open(model_path, newline="", encoding="utf-8") as mf:
                mr = csv.DictReader(mf)
                mfields = list(mr.fieldnames or [])
                attr_col = next((c for c in mfields if c.strip().lower() == "attribute"), "Attribute")
                desc_col = next((c for c in mfields if c.strip().lower() == "description"), "Description")
                for mrow in mr:
                    if mrow.get(attr_col, "").strip() == parent_attr.strip():
                        parent_def = mrow.get(desc_col, "").strip()
                        break
        except Exception as e:
            print(f"Warning: could not read model: {e}", file=sys.stderr)

    all_terms = [r[term_col].strip() for r in rows if r.get(term_col, "").strip()]

    worklist = []
    for i, row in enumerate(rows):
        term = row.get(term_col, "").strip()
        if not term:
            continue

        existing_desc = row.get(DESCRIPTION_COL, "").strip() if DESCRIPTION_COL in fieldnames else ""
        existing_id = row.get(ONTOLOGY_ID_COL, "").strip() if ONTOLOGY_ID_COL in fieldnames else ""
        existing_url = row.get(ONTOLOGY_URL_COL, "").strip() if ONTOLOGY_URL_COL in fieldnames else ""
        properties = row.get("Properties", "").strip() if "Properties" in fieldnames else ""

        needs = []
        if not existing_id:
            needs.append("ontology_identifier")
        if not existing_url:
            needs.append("ontology_url")
        if not existing_desc:
            needs.append("description")

        if is_annotation_property:
            component = os.path.basename(os.path.dirname(vocab_path)).replace("_", " ").title()
            context = (
                f"This is a data model attribute (property/field) in the {component} metadata schema. "
                f"The term represents a named property used to describe a biospecimen or its associated entity."
            )
            if properties:
                context += f" Existing property identifiers: {properties}."
            suggested = ["NCIT", "OBI", "UBERON"]
        elif parent_attr:
            siblings = [t for t in all_terms if t != term][:10]
            context = f"Parent attribute: {parent_attr!r}. Every term is a valid value (controlled vocabulary) for this attribute."
            if parent_def:
                context += f" Parent definition: {parent_def}"
            if siblings:
                context += f" Sibling values: {', '.join(siblings)}"
                if len(all_terms) - 1 > 10:
                    context += f" (and {len(all_terms) - 11} more)"
                context += "."
            suggested = ["NCIT", "OBI", "UBERON", "BTO", "CHEBI"]
        else:
            context = f"Vocabulary file: {os.path.basename(vocab_path)}."
            suggested = ["NCIT", "OBI", "UBERON"]

        entry = {
            "row_index": i,
            "term": term,
            "existing_description": existing_desc,
            "existing_ontology_identifier": existing_id,
            "existing_ontology_url": existing_url,
            "needs": needs,
            "suggested_ontologies": suggested,
            "context": context,
        }
        if not needs:
            entry["status"] = "already_complete"
        worklist.append(entry)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(worklist, f, indent=2)

    needs_work = [e for e in worklist if e.get("needs")]
    already_done = len(worklist) - len(needs_work)
    print(f"Worklist written to {out_path}")
    print(f"  {len(needs_work)} terms need annotation, {already_done} already complete")
    mode = "annotationProperty (data model attributes)" if is_annotation_property else f"controlled vocabulary (parent: {parent_attr!r})"
    print(f"  Mode: {mode}")


def cmd_apply(args):
    vocab_path = args.vocab
    decisions_path = args.decisions or "decisions.json"
    out_path = args.out or "annotated_vocab.csv"
    term_col_arg = args.term_column or "Attribute"
    overwrite_desc = args.overwrite_description

    with open(vocab_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    with open(decisions_path, encoding="utf-8") as f:
        raw = json.load(f)
    decisions = raw.get("decisions", raw) if isinstance(raw, dict) else raw
    by_index = {d["row_index"]: d for d in decisions}

    # Add missing target columns
    added_cols = []
    for col in [ONTOLOGY_ID_COL, ONTOLOGY_URL_COL]:
        if col not in fieldnames:
            fieldnames.append(col)
            added_cols.append(col)
    if DESCRIPTION_COL not in fieldnames:
        fieldnames.append(DESCRIPTION_COL)
        added_cols.append(DESCRIPTION_COL)
    has_ncit_col = NCIT_CODE_COL in fieldnames

    report = ["# Verification Report\n\n"]
    report.append(f"- Source: `{vocab_path}`\n")
    report.append(f"- Decisions: `{decisions_path}`\n\n")
    report.append("| Row | Term | Identifier | Verdict | Description | Notes |\n")
    report.append("|-----|------|------------|---------|-------------|-------|\n")

    total = matched = desc_added = 0
    derived_urls = []
    review_items = []

    for i, row in enumerate(rows):
        for col in added_cols:
            row.setdefault(col, "")
        if i not in by_index:
            continue

        d = by_index[i]
        total += 1
        term = d.get("term", "")
        ident = normalize_curie(d.get("ontology_identifier", ""))
        url = d.get("ontology_url", "")
        desc = d.get("description", "")
        verdict = d.get("verification", {}).get("verdict", "")
        note = d.get("verification", {}).get("note", "")

        # Derive URL from CURIE as fallback
        if ident and not url:
            m = re.match(r"^([A-Za-z]+):([A-Za-z0-9_]+)$", ident)
            if m:
                prefix, local = m.group(1).upper(), m.group(2)
                url = f"http://purl.obolibrary.org/obo/{prefix}_{local}"
                derived_urls.append(i)

        # Reject malformed identifiers
        if ident and ":" not in ident:
            ident = ""

        if not row.get(ONTOLOGY_ID_COL):
            row[ONTOLOGY_ID_COL] = ident
        if not row.get(ONTOLOGY_URL_COL):
            row[ONTOLOGY_URL_COL] = url

        existing_desc = row.get(DESCRIPTION_COL, "").strip()
        desc_action = "kept"
        if desc and not existing_desc:
            row[DESCRIPTION_COL] = desc
            desc_added += 1
            desc_action = "added"
        elif desc and existing_desc and overwrite_desc and verdict.lower() in ("match", "ok", "verified"):
            row[DESCRIPTION_COL] = desc
            desc_added += 1
            desc_action = "overwritten"

        if has_ncit_col:
            ncit_code = get_ncit_code(ident)
            if ncit_code and not row.get(NCIT_CODE_COL, "").strip():
                row[NCIT_CODE_COL] = ncit_code

        v_lower = verdict.lower()
        if v_lower in ("match", "ok", "verified"):
            matched += 1
        else:
            review_items.append({"row": i, "term": term, "verdict": verdict, "note": note})

        report.append(
            f"| {i} | {term} | {ident or '—'} | {verdict} | {desc_action} | {note[:80]}{'…' if len(note) > 80 else ''} |\n"
        )

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    report.append(f"\n## Summary\n\n")
    report.append(f"- **Total decisions applied:** {total}\n")
    report.append(f"- **Verified matches:** {matched}\n")
    report.append(f"- **Descriptions added:** {desc_added}\n")
    if derived_urls:
        report.append(f"- **URLs derived (not from OLS — verify):** rows {derived_urls}\n")
    if review_items:
        report.append(f"\n## Needs Human Review ({len(review_items)} terms)\n\n")
        for r in review_items:
            report.append(f"- Row {r['row']}: **{r['term']}** — `{r['verdict']}`: {r['note']}\n")

    report_path = "verification_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(report)

    print(f"Annotated CSV → {out_path}")
    print(f"Report → {report_path}")
    print(f"  {total} applied, {matched} verified, {desc_added} descriptions added")
    if review_items:
        print(f"  {len(review_items)} terms need human review — see {report_path}")


def main():
    parser = argparse.ArgumentParser(description="OLS Annotator")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="Build a worklist from a vocabulary CSV")
    p.add_argument("vocab")
    p.add_argument("--model", help="Model CSV for parent attribute context")
    p.add_argument("--out", help="Output path (default: worklist.json)")
    p.add_argument("--term-column", default="Attribute")
    p.add_argument("--parent-attribute", help="Override detected parent attribute")

    a = sub.add_parser("apply", help="Apply decisions to produce annotated CSV")
    a.add_argument("vocab")
    a.add_argument("--decisions", help="Decisions JSON path (default: decisions.json)")
    a.add_argument("--out", help="Output CSV path (default: annotated_vocab.csv)")
    a.add_argument("--term-column", default="Attribute")
    a.add_argument("--overwrite-description", action="store_true")

    args = parser.parse_args()
    if args.command == "prepare":
        cmd_prepare(args)
    else:
        cmd_apply(args)


if __name__ == "__main__":
    main()
