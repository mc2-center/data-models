A **Sequencing Level 3** entry documents further-processed sequencing data derived from a Sequencing Level 2 alignment, such as count matrices or probe-level summaries. This level captures matrix-type metadata (raw, normalized, scaled, or batch-corrected counts), unique probe and target counts, and the workflow, software, and parameters used to generate the processed output.

Level 3 entries represent the analysis-ready data products most commonly used for downstream statistical analysis, while still preserving a clear lineage back to the Level 2 alignment and Level 1 raw reads that produced them.

## Why You Should Contribute Sequencing Level 3 Entries

Contributing Sequencing Level 3 entries ensures that processed count data is documented with enough workflow and provenance detail for others to understand exactly how it was derived, and to confidently reuse it in downstream analyses shared through the CCKP.

### Who Should Be Contributing Sequencing Level 3 Entries?

1. **Computational Genomics Analysts** – Document the workflow, parameters, and matrix type used to generate processed count data.
2. **Bioinformatics Pipeline Developers** – Record the software and workflow versions that produced the processed outputs, supporting reproducibility.
3. **Research Staff** – Track which processed data products correspond to which raw and aligned files.
4. **Data Managers** – Maintain consistent, portal-ready metadata for processed sequencing outputs shared through the CCKP.

## Download Template

You can download the [SequencingLevel3 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/SequencingLevel3.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('sequencingLevel3/reference.csv', keep_default_na=False) }}
