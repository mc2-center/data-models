# CCKP Data Model 14.1.3

This is a **patch release** on top of 14.1.2. It makes five changes. See `release_14.1.2_notes.md` for the 14.1.2 change.

## Resource Doi is optional

- `Resource Doi` (EducationalResource) is no longer required. Many educational resources do not have a DOI.

## Tool Release Date accepts "No Release Available"

- `Tool Release Date` (ToolView) is now text with this pattern: `^(\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])|No Release Available)$`. The `date` format is removed.
- **Why:** many tools have no release. The `date` format rejected the value "No Release Available".
- **Note:** the pattern does not reject an impossible date such as 2024-02-31. The `date` format did.

## 16 new Assay terms

- 16 terms are added at the end of `modules/shared/assay.csv`. Curated records use them. Ten have an ontology identifier (OBI, EDAM, BAO, NCIT or EFO). Six have no ontology term and have a description written by the CCKP team.

## Assay descriptions

- 24 Assay terms had the ChIP-Seq description, copied by mistake. Each now has its own description. 15 come from the ontology term of the row (or a matching OLS term), and 9 are written by the CCKP team.

## Spatial Profiling working group

- `Spatial Profiling` is a new value of `Working Group Participation` (PersonView).

## Regenerated files

- `mc2.model.csv`, `mc2.model.jsonld`, `all_valid_values.csv`, the JSON Schemas that have the changed attributes or enums, `kg-pipeline/schema/mc2_model.linkml.yaml` and `mc2_model.ttl` (the large ttl diff is mostly reordering).
- `cckp_portal.ttl` is not changed. Regenerating it only reorders triples.
