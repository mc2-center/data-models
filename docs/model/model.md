A **Model** entry documents a non-human organism (e.g. mouse, zebrafish) or a cell line/organoid used as an experimental stand-in for human disease in MC<sup>2</sup> Center-supported research. Model metadata captures how the model was derived or acquired (e.g. patient-derived xenograft, cell line, genetically engineered model), its genotype, and the treatment history applied to it during experiments.

This model outlines the key attributes needed to describe a model system, including its link back to the individual it was derived from (when applicable), so that biospecimens and assay data collected from the model can be traced to both the model itself and its clinical origin.


## Why You Should Contribute Model Entries

Contributing model entries ensures that experimental findings generated from mouse models, cell lines, organoids, and other model systems can be correctly attributed to a well-documented source, including how faithfully the model represents the original patient disease. This supports reproducibility and allows other researchers to evaluate whether a given model system is appropriate for their own experiments.


### Who Should Be Contributing Model Entries?

1. **Model System Core Staff** – Document how a model was generated, acquired, and maintained (e.g. PDX, cell line, genetically engineered model).
2. **Research Staff and Lab Managers** – Track treatment and experimental history applied to a model over time.
3. **Principal Investigators (PIs)** – Ensure model provenance and its relationship to the source individual is properly documented.
4. **Data Managers** – Maintain the model-level record that biospecimen entries derived from the model key off of.


## Download Template

You can download the [Model entry template](https://github.com/mc2-center/data-models/raw/main/templates/Model.csv), which includes all required fields, to streamline the data entry process.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('model/reference.csv', keep_default_na=False) }}
