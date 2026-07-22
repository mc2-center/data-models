A **Sequencing Level 2** entry documents sequencing data that has been aligned to a reference genome. This level builds directly on a Sequencing Level 1 file and adds alignment-specific metrics, such as aligned reads, deduplicated reads, trimmed reads, mapping quality (MapQ30), and the genomic reference and software version used to perform the alignment.

Level 2 entries make explicit the connection between a raw sequencing file and the processed alignment derived from it, while also capturing the tools and parameters that produced the alignment, which is essential for evaluating data quality and reproducing analyses.

## Why You Should Contribute Sequencing Level 2 Entries

Contributing Sequencing Level 2 entries ensures that alignment outputs are traceable to their raw source files and are documented with the quality metrics and software versions needed for others to assess, reproduce, or build on the analysis.

### Who Should Be Contributing Sequencing Level 2 Entries?

1. **Computational Genomics Analysts** – Record alignment metrics and software versions immediately after processing pipelines complete.
2. **Sequencing Core Staff** – Confirm that aligned outputs are correctly linked back to the raw files and biospecimens they originated from.
3. **Bioinformatics Pipeline Developers** – Document the genomic reference and workflow versions used, supporting reproducibility across pipeline updates.
4. **Data Managers** – Maintain consistent, portal-ready metadata for aligned sequencing outputs shared through the CCKP.

## Download Template

You can download the [SequencingLevel2 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/SequencingLevel2.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('sequencingLevel2/reference.csv', keep_default_na=False) }}
