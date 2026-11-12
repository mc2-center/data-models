# Draft attribute crosswalks: MC2 → export targets

These are field inventories for four export targets. Each target field is
listed with the MC2 attribute that would fill it. They are the seed for the
SSSOM files described in `plans/metadata_export_pipeline.md` (Part A).
**They are drafts. Nobody has reviewed them, and no pipeline code reads them.**

| File | Target | Source read (2026-11-12) | Rows |
|---|---|---|---|
| `c2m2.tsv` | CFDE C2M2 | `C2M2_datapackage.json` (nih-cfde/published-documentation, `stable`) | 262 |
| `geo.tsv` | NCBI GEO, high-throughput sequencing. Covers the Sequencing, Visium and GeoMx families. | `seq_template.xlsx` (GEO update of 2026-10-28) and the GEO seq and validation pages | 43 |
| `dbgap.tsv` | dbGaP | Submission guide and the 2026-04-07 template package | 39 |
| `crdc.tsv` | CRDC General Commons (CDS) 13.0.1 | CBIIT/cds-model `13.0.1-GC_Release`, checked against the portal's `GC_Dictionary_All_v13.0.1.json` and controlled-vocabulary export | 291 |

## Columns

| Column | Meaning |
|---|---|
| `target_table` | The target's table, node or file. |
| `target_field` | The target's field name. |
| `target_required` | `required`, `conditional` or `optional`. `conditional` means the field is required only when its table or node is submitted, or under the condition given in `notes`. |
| `target_value_constraint` | An ontology, an enum or CDE ID, or a type. |
| `mc2_class` | The MC2 class that supplies the value. |
| `mc2_attribute` | The exact `mc2.model.csv` attribute name. Several attributes are separated by `\|`. |
| `match` | `exact`, `close`, `broad`, `narrow` or `none`, from MC2's perspective. |
| `value_crosswalk` | The value crosswalk the field needs, if any. |
| `notes` | Anything else about the field. |

Every `mc2_attribute` value resolves to an attribute in `mc2.model.csv`.
