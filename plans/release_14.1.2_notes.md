# CCKP Data Model 14.1.2

This is a **patch release** on top of 14.1.1. It makes one change. See `release_14.1.1_notes.md` for the 14.1.1 change.

## Five true/false attributes are now boolean fields

- These attributes are now `"type": "boolean"` in the JSON Schema. They were text enums of `"False"` and `"True"`. Their column type was already `boolean`; the `True, False` valid-values list is what made them enums, so that list is removed.
  - `Tool Package Dependencies Present` (ToolView)
  - `Image Pixels BigEndian` and `Image Pyramidal` (ImagingLevel2, ImagingLevel3Image, NanoStringGeoMxDSPImaging)
  - `Visium Image Re-orientation` (VisiumRNALevel1)
  - `Visium Applied Hard Trimming` (VisiumRNALevel2)
- **Why:** Synapse Curator's Grid stores these cells as JSON booleans, which the old enum rejected. A boolean field validates the value Grid stores (same fix as `Portal Display` in 14.1.1).
- The valid-values list is removed in each `annotationProperty.csv` and the five `shared/boolean.csv` entries are removed from `modules/mapping.yaml`.
- Regenerated: `mc2.model.csv`, `mc2.model.jsonld`, `all_valid_values.csv` and the six JSON Schemas above (no other JSON Schema changes).
- Also in 14.1.2: the `Tool Package Dependencies Present` example in `modules/tool/exampleColumn.csv` is now `true` (was `True`); `kg-pipeline/schema/mc2_model.linkml.yaml`, its conversion report, prefixes report and `mc2_model.ttl` are regenerated (the five attributes have range `boolean`, their Enum classes are gone); `modules/shared/boolean.csv` is deleted; and the stale `mc2_enum` annotation on `Tool.toolPackageDependenciesPresent` is removed from `kg-pipeline/schema/cckp_portal.linkml.yaml` and `cckp_portal.ttl`.
