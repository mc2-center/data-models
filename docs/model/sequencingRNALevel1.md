A **Sequencing RNA Level 1** entry documents raw, unaligned RNA sequencing data, extending the general Sequencing Level 1 structure with RNA-specific library metadata. In addition to standard NGS library and platform fields, this level captures RNA-specific details such as end bias (3 prime, 5 prime, or full-length transcript coverage), reverse transcription primer type, RNA integrity number (RIN), and DV200, which describe the quality and construction of the RNA library before sequencing.

These RNA-specific quality metrics are critical for interpreting downstream expression results, since RNA degradation or library construction choices can significantly affect quantification accuracy.

## Why You Should Contribute Sequencing RNA Level 1 Entries

Contributing Sequencing RNA Level 1 entries ensures that raw RNA sequencing outputs carry the library construction and RNA quality metadata needed to properly interpret and reproduce downstream expression analyses shared through the CCKP.

### Who Should Be Contributing Sequencing RNA Level 1 Entries?

1. **Sequencing Core Staff** – Record RNA library preparation details and quality metrics (RIN, DV200) at the point of library construction.
2. **Computational Genomics Analysts** – Ensure RNA-specific metadata is available before it is used in expression quantification pipelines.
3. **Research Staff and Lab Managers** – Track which raw RNA sequencing files correspond to which biospecimens and studies.
4. **Data Managers** – Maintain consistent, portal-ready metadata for raw RNA sequencing outputs shared through the CCKP.

## Download Template

You can download the [SequencingRNALevel1 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/SequencingRNALevel1.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('sequencingRNALevel1/reference.csv', keep_default_na=False) }}
