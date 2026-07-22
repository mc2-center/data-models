A **Sequencing Level 1** entry documents the raw, unaligned sequencing reads produced directly by a sequencer, before any downstream processing or alignment has been applied. This level captures the file itself (e.g., a FASTQ file) alongside the biospecimen, dataset, and study context it belongs to, along with next-generation sequencing (NGS) library and platform metadata such as library strategy, selection method, read length, raw read counts, and sequencing coverage.

Because Level 1 files represent the earliest, most foundational data product of a sequencing experiment, complete and accurate metadata at this level is what makes every downstream processing step (alignment, quantification, variant calling) traceable back to its source. Missing or incomplete library and platform details at this stage are difficult to reconstruct later.

## Why You Should Contribute Sequencing Level 1 Entries

Contributing Sequencing Level 1 entries ensures that raw sequencing outputs are properly linked to their originating biospecimens and are described with enough library preparation and platform detail to support reproducible reprocessing, reanalysis, and integration with other datasets on the Cancer Complexity Knowledge Portal (CCKP).

### Who Should Be Contributing Sequencing Level 1 Entries?

1. **Sequencing Core Staff** – Capture library preparation and instrument run details at the point of generation, when they are most accurate.
2. **Computational Genomics Analysts** – Ensure raw file metadata is complete before it feeds into alignment and processing pipelines.
3. **Research Staff and Lab Managers** – Track which raw sequencing files correspond to which biospecimens and studies.
4. **Data Managers** – Maintain consistent, portal-ready metadata for raw sequencing outputs shared through the CCKP.

## Download Template

You can download the [SequencingLevel1 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/SequencingLevel1.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('sequencingLevel1/reference.csv', keep_default_na=False) }}
