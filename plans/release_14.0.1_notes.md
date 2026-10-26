# CCKP Data Model 14.0.1

This is a **patch release** on top of 14.0.0. It fixes value-set and validation defects found after the 14.0.0 cutover; no attributes were added, removed or renamed. See `release_14.0.0_notes.md` for the full 14.0.0 changes.

## DM-14

- DatasetView attribute `Data Use Codes` is renamed `Dataset Data Use Codes` in `qc_model/qc_attribute_mapping.csv` for clarity and consistency with the model (commit `9c114bc1`).

## DM-16

- **Tumor Type:** removed the duplicate value `Not-Applicable`. `Not Applicable` (with a space) is the correct value and is unchanged. No nonpreferred-term entry was added: nothing in the model referenced `Not-Applicable`.
- **`Immunoassay` casing (known quirk, unchanged):** DataCatalog `dataType` stays lowercase (`immunoassay`) by owner decision. The Assay value `Immunoassay` and the `dataType` value `immunoassay` share one JSON-LD node (`bts:Immunoassay`), so that node's `sms:displayName` in `mc2.model.jsonld` is lowercase. The JSON Schemas are unaffected (Assay enums keep `Immunoassay`, DataCatalog `dataType` keeps `immunoassay`). The node is not split.
- **DOI format:** the `Publication Doi` description now asks for `https://doi.org/{doi}` (was `https://www.doi.org/{doi}`). No other attribute description referenced `www.doi.org` or `dx.doi.org`.
- **DUO shorthands** (`modules/shared/duo.csv`, `Properties`) aligned to official DUO: `USE`->`US` (DUO:0000026), `RST`->`RS` (DUO:0000012), `TSM`->`TS` (DUO:0000025), `IST`->`IS` (DUO:0000028), `GSR`->`GS` (DUO:0000022), `DSR`->`DS` (DUO:0000007).
- **DUO ID pattern:** validation pattern widened from `DUO:\d{7}` to `DUO:\d{7,8}` (full pattern `^(DUO:\d{7,8}|DUOPlus\d+|Pending Annotation)$`) on `Dataset Data Use Codes` and `dataCatalogDataUseModifiers`, so official 8-digit IDs such as `DUO:00000044` validate. `DUO:0000044` remains the term ID in `duo.csv` and still validates.
- **Trailing whitespace removed** from source values (`all_valid_values.csv` previously carried the trailing space; generated schemas already trimmed it):
  - Assay: `"Gene Silencing "` -> `Gene Silencing`
  - Assay nonpreferred term: `"hiPSC-CM "` -> `hiPSC-CM`
  - `indexDate`: `"Diagnosis Date "` -> `Diagnosis Date`
  - `tool_format`: `"Database Hits (Sequence) Format "` -> `Database Hits (Sequence) Format`
  - `Parent` column in `modules/imagingLevel3Segments/segmentType.csv` (5 rows): `"Imaging Segmentation Data Type "` -> `Imaging Segmentation Data Type`
- **`Dataset Doi` is no longer required** in DatasetView (`DatasetDoi` removed from its `required` list). Many datasets have no DOI of their own, and the portal sync fills one from the linked publication.
