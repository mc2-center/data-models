# Schematic CSV → LinkML mapping rules

> Vendored from the `csv-to-linkml` Claude Code skill's `references/mapping-rules.md`
> alongside `../csv_to_linkml.py`, so this repo's copy of the script is reproducible
> without that skill installed.

This describes exactly what `scripts/csv_to_linkml.py` does and why, so you can judge
whether its output is right for a given model. The target format is
[LinkML](https://github.com/linkml/linkml-model) — a schema language built around
**classes** (record types), **slots** (fields, reusable across classes), **enums**
(controlled vocabularies), and **types**.

## Input formats

### schematic CSV (Sage Bionetworks `schematic`)

One row per attribute, columns: `Attribute`, `Description`, `Valid Values`,
`DependsOn`, `Required`, `Properties`, `Validation Rules`, `columnType`, `Format`,
`Pattern`, `Minimum`, `Maximum`, `IsTemplate`, `Source`. This is the shape of
`mc2.model.csv` and every `modules/*/annotationProperty.csv`. Controlled-vocabulary
CSVs (e.g. `modules/biospecimen/specimenType.csv`) are a different shape — one row per
*term*, with `Attribute` (the term), `Description`, `Parent` (the attribute it's a
valid value of), and — if OLS-annotated — `Ontology Identifier` / `Ontology Url`.
These CV CSVs aren't passed directly to `convert`; they're read indirectly via
`--mapping`/`--modules-dir` to enrich enums (see below).

### Exported JSON Schema (`json_schemas/*.json`)

One file per component/class, produced by `create_json_from_model.py` from the CSV.
Each file has `title` (the class name), `description`, `properties` (one entry per
field, keyed by a sanitized CamelCase name with the original name in `title`),
`required` (list of sanitized keys), and sometimes `allOf` (conditional-requirement
blocks — see "JSON-derived rules" below). The script treats each file as one class,
using each property's `title` as the canonical attribute name so it lines up with the
same attribute's row in the CSV if both are converted together.

This format is **lossier** than the CSV for plain fields — `Properties` (CDE/DUO
tags, `primary_key`/`foreign_key`), `Source`, `Format`, `Minimum`/`Maximum`, and the
CSV's exact enum-value spelling (the exporter strips spaces and punctuation from enum
values — e.g. `"Not applicable"` becomes `"Notapplicable"`, `"Blood draw"` becomes
`"Blooddraw"`) are all gone or degraded. But it's **richer** in one respect: the
CSV's ambiguous single-entry `DependsOn` sibling-conditionals are already compiled
here into explicit `allOf`/`if`/`then` blocks with the triggering value spelled out
— see "JSON-derived rules" below for what the script does with that.

## Classifying a row: class or slot?

A row is a **class** if:
- `IsTemplate == True` (schematic's own marker for a component/template), **or**
- its `DependsOn` list has more than one entry.

The second rule matters: in this model there are template-like rows (e.g. `10x Visium
RNA Level 1`) that list dozens of fields in `DependsOn` but were never marked
`IsTemplate=True` — almost certainly a curation gap, not intent. Treating only
`IsTemplate=True` rows as classes silently drops these from the schema. The script
flags every row it classifies this way as a **note** so you can confirm it's really a
component and not a one-off dependency list.

A row with **exactly one** `DependsOn` entry is a **slot**, and that single entry is
almost never "this is a component made of one field" — in this model it's schematic's
sibling-conditional-requirement pattern: e.g. `USE` (a DUO permission code) has
`DependsOn: userSpecificRestriction`, meaning "if USE is set, also expect
`userSpecificRestriction`." LinkML has no direct equivalent to schematic's
`DependsOn`-as-conditional-rule; the script preserves it as a `comments` entry on the
slot and a report note suggesting a LinkML
[`rules:`](https://linkml.io/linkml-model/docs/rules/) block if you need it enforced.

Every other row is a plain **slot**.

## Class fields

| Schematic column | LinkML field | Notes |
|---|---|---|
| `Attribute` | class name | kept verbatim, spaces included |
| `Description` | `description` | — |
| `DependsOn` | `slots` | list of slot (or nested-class) names |
| `IsTemplate=True` | `tree_root: true` | marks it as a top-level/root class |

Missing `DependsOn` targets (a class references a slot name with no row of its own —
this happens once in the current model, `Study` → `Study Number of Samples`) get a
stub slot plus a warning, rather than being silently dropped, since dropping would
make the class incomplete without anyone noticing.

When a class of the same name is defined by more than one input file (e.g. `Study`
appears in both `mc2.model.csv` and `json_schemas/Study.json`), its `DependsOn`/slot
lists are **unioned**, not overwritten — so combining a CSV and a narrower or
differently-ordered JSON definition doesn't silently drop fields either way round.

## JSON-derived rules

For each JSON Schema file's `allOf` entries, the script expects (and everywhere in
the current model, finds) the shape:
```json
{"if": {"properties": {"<PrecondSlot>": {"enum": ["<value>"]}}, "required": ["<PrecondSlot>"]},
 "then": {"properties": {"<PostcondSlot>": {"not": {"type": "null"}}}, "required": ["<PostcondSlot>"]}}
```
i.e. "if `<PrecondSlot>` equals `<value>`, then `<PostcondSlot>` is required." This is
translated directly into a LinkML class-level rule:
```yaml
rules:
- preconditions:
    slot_conditions:
      <PrecondSlot>: {equals_string: <value>}     # or equals_string_in: [...] for a multi-value enum
  postconditions:
    slot_conditions:
      <PostcondSlot>: {required: true}
```
This is exactly the schematic `DependsOn` sibling-conditional pattern described above
(`USE`/`COL`/`DSR`/`DUOPlus*`), but now with the triggering value known, so it can be
compiled instead of just flagged. If an `allOf` entry doesn't match this shape
(multiple preconditions, no enum, etc.), it's skipped with a warning rather than
guessed at.

## Slot fields

| Schematic column/value | LinkML field | Notes |
|---|---|---|
| `Description` | `description` | — |
| `Required == True` | `required: true` | omitted (not `false`) otherwise |
| `columnType == string_list` | `multivalued: true` | |
| `columnType == number` | `range: float` | schematic doesn't distinguish int/float |
| `columnType == boolean` | `range: boolean` | |
| `columnType == string` / blank | *(no range set)* | falls back to schema `default_range: string` |
| `Valid Values` non-empty | `range: "<Attribute> Enum"` | generates/points to an enum, see below |
| `Pattern` | `pattern` | regex, passed through as-is |
| `Minimum` / `Maximum` | `minimum_value` / `maximum_value` | parsed as int, then float |
| `Format` | `comments` entry | LinkML has no direct analog; kept as a note |
| `Source` | `comments` entry | provenance note |
| `Validation Rules` | `comments` entry + **warning** | schematic's rule DSL (e.g. custom regex/list rules) isn't translated — surfaced for manual review, not silently dropped |
| single-entry `DependsOn` | `comments` entry + **note** | see "sibling conditional requirement" above |

### `Properties` column tokens

`Properties` is a comma-separated bag of tags. Each token is classified:

- `primary_key` → slot `identifier: true`
- `foreign_key` → slot `annotations: {foreign_key: true}` (LinkML has no native FK
  concept; this is a plain tag, not a resolvable relationship)
- `CDE:<publicId>` → slot `annotations: {cde_id: "<publicId>"}` — kept as an opaque tag
  rather than `exact_mappings`, because a caDSR public ID isn't a real resolvable CURIE
  (there's no clean `CDE:` namespace URI to expand it into)
- Any other token matching `PREFIX:LOCAL` (e.g. `DUO:0000026`, `NCIT:C12434`) →
  `exact_mappings: [...]`, and `PREFIX` is registered in the schema's `prefixes:` block.
  Known OBO Foundry prefixes (`DUO`, `NCIT`, `UBERON`, `CL`, `MONDO`, `OBI`, `CHEBI`,
  `BTO`) get their real `http://purl.obolibrary.org/obo/<PREFIX>_` namespace.
  Anything else gets a placeholder `https://example.org/UNKNOWN_PREFIX_<PREFIX>/` and a
  **warning** — fill in the real namespace before treating the schema as final.
- Anything else → kept as a `comments` entry plus a warning (unrecognized token).

## Enums

For every slot with non-empty `Valid Values`, the script creates an enum named
`"<Attribute> Enum"` and points the slot's `range` at it. Permissible values default to
bare strings (no metadata) **unless** you pass `--mapping modules/mapping.yaml
--modules-dir modules`, in which case the script:

1. Looks up which CV CSV supplies this attribute's values (`modules/mapping.yaml`,
   the same registry `update_valid_values.py` uses).
2. Reads that CV CSV and, for each value, pulls `description` (its `Description`
   column) and `meaning` (its `Ontology Identifier` column, if it's a well-formed
   CURIE) into the permissible value.

This is where OLS-annotated vocabularies (e.g. `modules/biospecimen/biospecimenCategory.csv`,
produced by the `ols-term-annotator` skill) pay off directly — their NCIT/UBERON
identifiers land in the LinkML enum's `meaning` field, which is exactly what LinkML
expects for ontology-backed enums. If a CV file is listed in `mapping.yaml` but can't
be read, or an attribute has no mapping entry, its enum is still generated — just
without the extra metadata — and a warning is raised only for the read-failure case.

## Prefixes and schema header

`id` and `name` default to placeholders (`https://w3id.org/mc2-center/mc2-model` /
`mc2_model`) — override with `--schema-id` / `--schema-name`. The `mc2:` default
prefix is derived from `--schema-id`. `linkml:` (for the `linkml:types` import) is
always present. Everything else is added only as needed by the `Properties` CURIEs
actually seen.

## Merging multiple input files

Rows/properties for the same `Attribute` across input files are merged field by
field: a blank field is filled in from whichever file supplies it, a field populated
in both is kept from whichever file was read first, and a **warning** is raised only
when both files populate the same field with genuinely different values — this can
be a real data-quality finding (e.g. `Individual_id`'s `Pattern` and `Description`
differ between `mc2.model.csv` and `json_schemas/Individual.json` in the current
model — one of them is stale). `Valid Values` is exempt from this conflict check
(handled by the separate JSON-provenance warning above) and `DependsOn` is unioned
rather than compared (see "Class fields" above) — everything else is a real conflict
if it fires.

If you have both formats and want the CSV's richer fields to win by default, list
the CSV path(s) before the JSON path(s) in the `convert` command (this is also the
order used in the examples above).

## Known limitations (by design, not bugs)

- Schematic's `Validation Rules` mini-language (CSV path only) is not translated into
  LinkML constructs (`pattern`, `structured_pattern`, `rules`) — it's preserved
  verbatim as a comment and flagged. Translating it correctly requires knowing the
  exact rule grammar in use, which varies; do this by hand per flagged slot.
- Sibling-conditional `DependsOn` **from the CSV alone** (the `USE`/`COL`/`DUOPlus*`-
  style single-entry case) is not compiled into LinkML `rules:` — only flagged,
  because the CSV alone doesn't state the triggering value. Pass the matching
  `json_schemas/*.json` file alongside the CSV to get real `rules:` blocks instead
  (see "JSON-derived rules" above) — this is the recommended path whenever both are
  available.
