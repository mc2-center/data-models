# CCKP Data Model 14.0.0

This is a **major, breaking release**. It consolidates dozens of per-entity attributes into shared attributes, replaces several closed value lists with ontology reference validation, revises multiple controlled vocabularies, moves the model-generation tooling off `schematicpy` and onto `synapseclient.extensions.curator`, and renames the Visium (`10x Visium`) templates. Contributors, curators, and anyone with scripts or saved manifests that reference the old column names should read this before submitting new data.

## Breaking changes summary

- **~70 per-entity attributes were merged into shared attributes** (e.g. `Biospecimen Sex` / `Individual Sex` / `Model Sex` → `Sex`; `Dataset Assay` / `File Assay` / `Publication Assay` → `Assay`). See [Consolidated attributes](#consolidated-attributes) below.
- **Several closed picklists were replaced with ontology reference validation** (NCIt concept names / UBERON identifiers), loosening validation on those fields rather than tightening it. See [Fields moved to reference validation](#fields-moved-to-reference-validation).
- **Several controlled vocabularies were narrowed, re-cased, or restructured** against CDE/ontology sources — old values that curators may still be using will no longer validate. See [Value-set narrowings](#value-set-narrowings).
- **License values are now SPDX identifiers**, not the old internal tokens. See [License values are now SPDX](#license-values-are-now-spdx).
- **The `10x Visium` templates were renamed to `Visium`** (class labels, JSON Schema file names, and `_id`/`Key` attribute names). See [Visium template renames](#visium-template-renames).
- **New foreign keys**: `Consortium Key` and `Institution Key` replace the old `*Consortium Name` value lists on `Grant View`, `Person View`, and `Project View`.
- **Model generation no longer uses `schematicpy`**; `mc2.model.jsonld` and `json_schemas/*.json` are now produced via `synapseclient.extensions.curator`. `make all` now regenerates `mc2.model.jsonld` again (it did not on the previous release).

- **All manifest templates in `templates/` were regenerated** with the new column names (29 of 33 have changed headers).

## Consolidated attributes

These per-entity attributes were retired in favor of a single shared attribute, defined once and reused across templates via `DependsOn`. Old values survive wherever the new shared CV's value set was a superset; narrower cases are called out separately below.

| New shared attribute | Retired per-entity attributes |
|---|---|
| `Assay` | `Dataset Assay`, `File Assay`, `Publication Assay` |
| `Species` | `Biospecimen Species`, `Dataset Species`, `File Species`, `Model Species`, DataCatalog's `species` |
| `Tissue` | `Dataset Tissue`, `File Tissue`, `Publication Tissue` |
| `Tumor Type` | `Dataset Tumor Type`, `File Tumor Type`, `Publication Tumor Type` |
| `Data Use Codes` | `File Data Use Codes`, `Study Data Use Codes` (Dataset View keeps its own `Dataset Data Use Codes`; see [Other schema changes](#other-schema-changes)) |
| `License` | `Resource License` (Educational Resource), `Tool License`, Study's `license`/`DUOPlus6` |
| `Investigator` | `Grant Investigator`, `Project Investigator`, `Study Investigator` |
| `Sex` | `Biospecimen Sex`, `Individual Sex`, `Model Sex` |
| `Disease Type` | `Biospecimen Disease Type`, `Individual Disease Type`, `Model Disease Type` |
| `Primary Diagnosis` | `Biospecimen/Individual/Model Primary Diagnosis` |
| `Primary Site` | `Biospecimen/Individual/Model Primary Site` |
| `Site of Origin` | `Biospecimen/Individual/Model Site of Origin` |
| `Tumor Subtype` | `Biospecimen/Individual/Model Tumor Subtype` |
| `Tumor Grade` | `Biospecimen Tumor Grade`, `Individual Tumor Grade` |
| `Known Metastasis Sites` | `Biospecimen Known Metastasis Sites`, `Individual Known Metastasis Sites` |
| `Treatment Type` | `Biospecimen/Individual/Model Treatment Type` |
| `Therapeutic Agent` | `Biospecimen/Individual/Model Therapeutic Agent` |
| `Treatment Response` | `Biospecimen/Individual/Model Treatment Response` |
| `Last Known Disease Status` | `Biospecimen Last Known Disease Status`, `Individual Last Known Disease Status` |
| `Days to Treatment` | `Individual Days to Treatment`, `Model Days to Treatment` |
| `Consortium Key` | `Grant Consortium Name`, `Person Consortium Name` (backed by a new `consortium_id.csv`, replacing `consortium_name.csv`) |
| `Institution Key` | new — `Grant View` and `Person View` now take an institution foreign key (backed by a new `institution_id.csv`) |

A handful of other duplicate/unused rows were also retired as part of this cleanup: `Project Consortium Name`, `Project Grant Number`, and `Person Grant Number` were defined but not actually wired into any template and were removed outright.

### DataCatalog changes

DataCatalog's own camelCase attributes collided with shared attributes and CV values once the model generator normalizes labels, so several were merged or renamed:

| 13.1.0 DataCatalog attribute | 14.0.0 attribute |
|---|---|
| `species` | `Species` (shared) |
| `contributors` | `dataCatalogContributor` |
| `license` | `dataCatalogLicense` (SPDX list; distinct from the shared `License`) |
| `individuals` | `individualCount` |
| `dataUseModifiersCatalog` | `dataCatalogDataUseModifiers` |

DataCatalog also gains attributes for the other annotations found on live Dataset entities, including `dataCatalogStudyId` (the Synapse ID of the grant's project, `^syn\d{7,8}$`). The grant number annotation is carried in the existing `GrantView Key`.

The live Synapse annotation **keys** on Dataset entities are unchanged by this rename — only this repo's model-side attribute names changed; the extraction/sync step maps the live key onto the new name.

## Fields moved to reference validation

These sample/assay-template fields dropped their closed `shared/*.csv` picklist in favor of free-text NCIt-concept-name or UBERON-identifier reference validation (the backing CV files were deleted, not renamed). Portal/resource templates (Dataset, Study, Publication, Tool, etc.) are unaffected — this change is scoped to Biospecimen/Individual/Model/File-level fields.

| Attribute | New validation | Used by |
|---|---|---|
| `Therapeutic Agent` | NCI Thesaurus concept name, reference-validated (no fixed list) | Biospecimen, Individual, Model |
| `Primary Diagnosis` | NCI Thesaurus concept name, reference-validated | Biospecimen, Individual, Model |
| `Primary Site` | UBERON identifier, `^UBERON:\d+$` | Biospecimen, Individual, Model |
| `Site of Origin` | UBERON identifier, `^UBERON:\d+$` | Biospecimen, Individual, Model |
| `Known Metastasis Sites` | UBERON identifier(s), `^UBERON:\d+$` | Biospecimen, Individual |
| `Biospecimen Anatomic Site` | UBERON identifier, `^UBERON:\d+$` | Biospecimen |
| `Biospecimen Site of Resection or Biopsy` | UBERON identifier, `^UBERON:\d+$` | Biospecimen |
| `File Longitudinal Event Type` | Free text (no fixed list; previously `Enrollment, Baseline`) | File View, NanoString GeoMx, Imaging, Sequencing, Visium templates |

`File Anatomic Site` also had its closed list replaced with a UBERON-identifier pattern, but as verified against the current model it is not currently referenced by any template's `DependsOn` (it wasn't in the previous release either — this is a pre-existing, unused definition, not a new gap).

## Value-set narrowings

- **Sex** (`shared/biologicalSex.csv`): narrowed from 9 values to 3 — `Female`, `Male`, `Unknown`. Removed: `Decline to answer`, `Don't know`, `Intersex`, `None of these describe me`, `Prefer not to answer`, `X`. No replacement mapping is recorded for the removed values.
- **Tumor Grade** (`shared/tumorGrade.csv`): values were renamed to fuller display labels and two new values added (`GB Borderline`, `GX Grade Cannot Be Assessed`), e.g. `G1`→`G1 Low Grade`, `G2`→`G2 Intermediate Grade`, `G3`→`G3 High Grade`, `G4`→`G4 Anaplastic`. Net broadened, not narrowed, but every value is now spelled differently than before.
- **Biospecimen Acquisition Method** (`biospecimen/acquisitionMethod.csv`): narrowed from 18 values to 10, restricted to CRDC_CDE 15115495's real permissible-value list. Several old values are recorded as `Nonpreferred Terms` on their replacement, so curators have a direct mapping: `Core needle biopsy` / `Fine needle aspirate` → **`Needle Biopsy`**; `Not reported` / `Not applicable` / `Not specified` / `Unknown` → **`Not Reported`**; `Lymphadenectomy (regional nodes)` / `Pancreaticoduodenectomy` / `Re-excision` / `Sentinel node biopsy` / `Shave biopsy` / `Punch biopsy` → **`Surgical Resection`**; `Blood draw` → **`Blood Draw`**. `Autopsy` was dropped outright with no mapping.
- **Biospecimen Composition** (`biospecimen/specimenComp.csv`): narrowed from 20 values to 11 (e.g. `Additional Primary`, `Atypia or hyperplasia`, `Local recurrence`, `Normal`, `Normal adjacent`, `Normal distant`, `NOS`, `Tissue`, the `Tumor post-*` variants were dropped; `Prior Primary`, `Progression`, `Synchronous Primary` were added). No Nonpreferred Terms recorded for the dropped values.
- **Biospecimen Preservation Method** (`biospecimen/preservation.csv`): narrowed from 19 values to 13, re-cased and consolidated (e.g. the three separate "Cryopreservation in..." variants collapsed to one `Cryopreserved`); new additions include `Cytospin Slide`, `Fixation`, `Refrigerated`, `Refrigerated Vacuum Chamber`. No Nonpreferred Terms recorded.
- **Biospecimen Preservation Medium** (formerly `Biospecimen Fixative`, now backed by `biospecimen/fixative.csv` under the renamed attribute): this is both a rename and a CV overhaul — old values like `Acetone`, `Saline`, `Diimidoester`, `Carbodiimide`, `Dimethylacetamide`, `Para-benzoquinone`, `Carnoy's Solution`, `Poloxamer`, `None` were dropped, replaced with a 17-value NCIt-backed list (`Desiccant`, `EDTA`, `FFPE`, `Formalin Fixed - Buffered`, `Formalin Fixed - Unbuffered`, `Glutaraldehyde`, `RNALater`, `TRIzol`, `OCT`, `Paraffin Block`, `Isopentane`, `Liquid Nitrogen`, `Liquid Nitrogen Vapor`, etc.). No Nonpreferred Terms recorded.
- **File Format** (`shared/fileFormat.csv`): this is a new, independently-curated CV, not a simple narrowing — 81 old values (`shared/dataset_file_format.csv`) became 97 new values. It is heavily **re-cased** (e.g. `xlsx`→`XLSX`, `docx`→`DOCX`, `maf`→`MAF`, `cel`→`CEL`) and many formats were added (`DICOM`, `CRAM`, `gVCF`, `HIC`, `OME-TIFF`, `Parquet`, `YAML`, etc.). Some older values have no case-only counterpart and were dropped outright, including `Pending Annotation`, `Unspecified`, `SRA`, `FCS`, `H5`, `H5AD`, `MSF`, `PKL`. No Nonpreferred Terms are recorded, so there is no in-CV mapping for the dropped values.

## License values are now SPDX

`License` (and DataCatalog's `dataCatalogLicense`) now validate against SPDX license identifiers instead of the old internal tokens. Legacy tokens are preserved as `Nonpreferred Terms` on the matching SPDX row in `modules/shared/license.csv`, so lookups/crosswalks can still resolve them:

| Legacy token | SPDX identifier |
|---|---|
| `CC0` | `CC0-1.0` |
| `CC_BY` | `CC-BY-4.0` |
| `CC_BY_NC` | `CC-BY-NC-4.0` |
| `CC_BY_ND` | `CC-BY-ND-4.0` |
| `CC_BY_SA` | `CC-BY-SA-4.0` |
| `CC_BY_NC_ND` | `CC-BY-NC-ND-4.0` |
| `CC_BY_NC_SA` | `CC-BY-NC-SA-4.0` |
| `Apache_2` | `Apache-2.0` |
| `MIT` | `MIT` |
| `GPL_3` | `GPL-3.0` |
| `BSD_3_Clause` | `BSD-3-Clause` |

## Visium template renames

The `10x Visium` templates were renamed to drop the vendor prefix:

- `10x Visium Auxiliary Files` → `Visium Auxiliary Files`
- `10x Visium RNA Level 1` → `Visium RNA Level 1`
- `10x Visium RNA Level 2` → `Visium RNA Level 2`
- `10x Visium RNA Level 3` → `Visium RNA Level 3`
- `10x Visium RNA Level 4` → `Visium RNA Level 4`

This applies to the model class labels, the generated JSON Schema file names (`json_schemas/10xVisium*.json` → `json_schemas/Visium*.json`), and the `*_id`/`* Key` attributes (e.g. `10xVisiumRNALevel1_id` → `VisiumRNALevel1_id`, `10xVisiumAuxiliaryFiles Key` → `VisiumAuxiliaryFiles Key`). 

## New and newly generated schemas

The following JSON Schemas are new in this release (none existed at `13.1.0`): `ImagingChannel.json`, `PersonView.json`, `ProjectView.json`, `Consortium.json`, `Institution.json`, `Theme.json`.

## Other schema changes

- **Enum values in generated JSON Schemas are now display labels**, not squashed class labels — e.g. `RNA Sequencing` rather than `RNASequencing`. Property *keys* are still class labels (no spaces); only the enum *values* were affected.
- **`Species` is now required** wherever a template includes it, including `DataCatalog` and `File View` (previously not required on `DataCatalog`'s own definition).
- **Conditional DUO fields are limited to file-level schemas**, plus Study and DataDSP. Selecting codes such as `DUO:0000007` there still adds the follow-up fields (`Disease Specific Research`, ...). Dataset View's `Dataset Data Use Codes` and DataCatalog's `dataCatalogDataUseModifiers` no longer use the controlled list, so they don't pull those fields in. Each value must still look like a DUO code (`DUO:0000042`, `DUOPlus3`) or be `Pending Annotation`.
- **`Grant Number` / `GrantView Key`** now accept `Affiliated/Non-Grant Associated` in addition to the `CA\d{6}` pattern, for records not tied to a specific grant.

## Tooling

- Model generation has moved off `schematicpy` (removed from `requirements.txt`) onto `synapseclient[curator]>=4.13.0`. `convert_model_to_jsonld.py` now calls `synapseclient.extensions.curator` directly.
- `make all` now runs `collate → convert → generate-json → templates`; the new `make templates` target writes `templates/*.csv` from the model. Previously it only ran `collate → generate-json` and never actually regenerated `mc2.model.jsonld` — anyone relying on `make all` to keep `mc2.model.jsonld` current on the prior release was getting a stale file; that's fixed here.
- `qc_model/mc2_qc.model.csv` and `.jsonld`, and the `make qc` target, have been removed. `qc_model/qc_attribute_mapping.csv` stays; it configures how portal-table QC merges duplicate rows.
- The Data Curator App configuration (`dca_config/`) and related docs references have been removed, as the DCA is deprecated.
- New verification scripts: `scripts/check_json_schemas.py` and `scripts/check_template_list.py`.

## Templates

All 33 files in `templates/` are now generated from the model (`make templates`), so their columns match the JSON Schemas. 29 have changed headers relative to 13.1.0, reflecting the consolidated attributes and the Visium renames above. Saved manifests built from the old templates need their columns renamed using the [Consolidated attributes](#consolidated-attributes) table.

---

**Full Changelog**: https://github.com/mc2-center/data-models/compare/13.1.0...14.0.0
