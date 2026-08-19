A **Biospecimen** entry documents a tissue, tumor, fluid, or other physical sample collected from an individual or a model organism/cell line for use in MC<sup>2</sup> Center-supported research. Biospecimen metadata captures how and when a specimen was acquired, its composition and preservation, and clinically relevant context such as disease type, tumor grade, morphology, and treatment history at the time of collection.

This model outlines the key attributes needed to track a biospecimen from acquisition through processing, including its relationship to a parent individual, model, or another biospecimen (for derived specimens), as well as the pathology and preservation details that downstream assays depend on.


## Why You Should Contribute Biospecimen Entries

Contributing biospecimen entries ensures that every downstream dataset (imaging, sequencing, spatial transcriptomics, etc.) can be traced back to a well-documented physical sample. Complete biospecimen metadata makes it possible to reproduce experiments, correctly interpret assay results in their clinical context, and avoid ambiguity when the same specimen is used across multiple studies or assay types.


### Who Should Be Contributing Biospecimen Entries?

1. **Biobank and Specimen Coordinators** – Ensure specimens are consistently tracked from acquisition through distribution to assay cores.
2. **Pathologists and Histology Staff** – Provide accurate morphology, tumor status, and preservation details that inform downstream analysis.
3. **Research Staff and Lab Managers** – Maintain the link between specimens, the individuals/models they were derived from, and the assays performed on them.
4. **Data Managers** – Ensure biospecimen records are complete before associated assay-level data (imaging, sequencing, etc.) is submitted.


## Download Template

You can download the [Biospecimen entry template](https://github.com/mc2-center/data-models/raw/main/templates/Biospecimen.csv), which includes all required fields, to streamline the data entry process.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('biospecimen/reference.csv', keep_default_na=False) }}
