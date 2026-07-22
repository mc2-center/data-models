An **Individual** entry documents a human participant (or the source patient behind a derived model) from whom biospecimens were collected for MC<sup>2</sup> Center-supported research. Individual metadata captures demographic information (sex, gender), diagnosis and staging at the individual level, and longitudinal clinical outcomes such as treatment history, recurrence, and vital status.

This model outlines the key attributes needed to describe an individual independent of any single specimen or assay, so that clinical context collected once can be linked across every biospecimen, model, and dataset derived from that individual.


## Why You Should Contribute Individual Entries

Contributing individual entries ensures that clinical and demographic context is recorded once and consistently reused across every biospecimen and downstream dataset tied to that person, rather than being duplicated or left out of assay-level metadata. This supports accurate cohort analysis, reduces re-collection of the same clinical details, and helps ensure patient privacy is respected through consistent de-identified identifiers.


### Who Should Be Contributing Individual Entries?

1. **Clinical Research Coordinators** – Ensure demographic and diagnosis information is accurately captured at enrollment.
2. **Data Managers** – Maintain the individual-level record that biospecimen and model entries key off of.
3. **Principal Investigators (PIs)** – Ensure longitudinal outcomes (treatment response, recurrence, vital status) are kept up to date as a study progresses.
4. **Biobank Coordinators** – Link individuals to the biospecimens collected from them.


## Download Template

You can download the [Individual entry template](https://github.com/mc2-center/data-models/raw/main/templates/Individual.csv), which includes all required fields, to streamline the data entry process.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('individual/reference.csv', keep_default_na=False) }}
