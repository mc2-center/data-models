# CCKP Data Model 14.1.1

This is a **patch release** on top of 14.1.0. It makes one change. See `release_14.1.0_notes.md` for the 14.1.0 changes.

## Portal Display is a true/false field

- **`Portal Display`** (PersonView) is now `"type": "boolean"` in the JSON Schema. It was a text enum of `"FALSE"` and `"TRUE"`. Its column type was already `boolean`; the `FALSE, TRUE` valid-values list is what made it an enum, so that list is removed (`modules/person/annotationProperty.csv`, the `modules/mapping.yaml` entry, `modules/person/portal_display.csv`). It now matches other boolean attributes with no valid-values list, such as `Image Z stack`.
- **Why:** Synapse Curator's Grid stores the text `TRUE` as `true`, which the old enum rejected, so every PersonView row failed validation. With a boolean field, the value Grid stores validates.
- **Portal unaffected:** the People and Tools portal tables already store `portalDisplay` as a BOOLEAN column.
- The example value is now `true` (`modules/person/exampleColumn.csv`, `docs/model/person.md`).
- Regenerated: `mc2.model.csv`, `mc2.model.jsonld`, `all_valid_values.csv`, `json_schemas/PersonView.json` (no other JSON Schema changes), and `kg-pipeline/schema/mc2_model.linkml.yaml` / `mc2_model.ttl` (`Portal Display` has range `boolean`; `Portal Display Enum` removed).
