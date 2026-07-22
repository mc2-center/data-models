A **10x Visium RNA Level 4** entry documents further-processed data built from a 10x Visium RNA Level 3 output, capturing the generic workflow type and workflow parameters used to derive higher-order analysis products (e.g., spatial clustering, differential expression, or other downstream spatial analyses) from the per-spot summary data.

As the most highly processed level in the Visium cluster, Level 4 entries emphasize workflow provenance, ensuring that the analysis choices behind a derived spatial result remain traceable back through Level 3, Level 2, and Level 1 to the original tissue and sequencing run.

## Why You Should Contribute 10x Visium RNA Level 4 Entries

Contributing 10x Visium RNA Level 4 entries ensures that downstream spatial analysis outputs remain traceable to the workflow and parameters that produced them, supporting reproducibility for results shared through the CCKP.

### Who Should Be Contributing 10x Visium RNA Level 4 Entries?

1. **Computational Genomics Analysts** – Document the workflow type and parameters used to generate derived spatial analysis products.
2. **Spatial Biology Researchers** – Confirm that derived results are correctly linked back to the Level 3 data they were built from.
3. **Bioinformatics Pipeline Developers** – Track workflow versions to support reproducibility across pipeline updates.
4. **Data Managers** – Maintain consistent, portal-ready metadata for derived Visium analysis outputs shared through the CCKP.

## Download Template

You can download the [VisiumRNALevel4 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/VisiumRNALevel4.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('visiumRNALevel4/reference.csv', keep_default_na=False) }}
