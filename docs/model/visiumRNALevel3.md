A **10x Visium RNA Level 3** entry documents processed spatial transcriptomics data built from a 10x Visium RNA Level 2 alignment together with its associated auxiliary files. This level captures per-spot summary statistics such as spots under tissue, mean reads per spatial spot, median genes and UMI counts per spot, sequencing coverage, and the proportion of reads mapped overall and to the transcriptome, along with the workflow version and file type generated.

These per-spot quality and summary metrics are what allow downstream users to assess the technical performance of a Visium run (e.g., tissue coverage, sequencing depth per spot) before interpreting the underlying biology.

## Why You Should Contribute 10x Visium RNA Level 3 Entries

Contributing 10x Visium RNA Level 3 entries ensures that per-spot quality and summary metrics from a Visium run are documented, giving downstream users the information needed to assess data quality before further spatial analysis shared through the CCKP.

### Who Should Be Contributing 10x Visium RNA Level 3 Entries?

1. **Computational Genomics Analysts** – Record per-spot summary statistics and workflow versions produced by processing pipelines.
2. **Spatial Biology Researchers** – Confirm that spot-level quality metrics accurately reflect the tissue and capture area analyzed.
3. **Bioinformatics Pipeline Developers** – Document the file types and workflows used to generate processed spatial outputs.
4. **Data Managers** – Maintain consistent, portal-ready metadata for processed Visium sequencing outputs shared through the CCKP.

## Download Template

You can download the [VisiumRNALevel3 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/VisiumRNALevel3.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('visiumRNALevel3/reference.csv', keep_default_na=False) }}
