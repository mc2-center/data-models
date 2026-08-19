A **10x Visium RNA Level 1** entry documents raw RNA sequencing data associated with a Visium spatial transcriptomics spot/slide experiment. In addition to standard NGS library and platform fields, this level captures Visium-specific slide and library metadata, including the Visium run ID, spatial read content (spatial barcode and UMI vs. cDNA), spatial library construction method, capture area, slide version and ID, image re-orientation, and permeabilization time, along with RNA quality metrics such as RIN and DV200.

Because Visium data links sequencing reads to a specific physical location on a slide, accurate capture of the slide, capture area, and read-structure metadata at this level is essential for correctly reconstructing the spatial context of the data in downstream processing.

## Why You Should Contribute 10x Visium RNA Level 1 Entries

Contributing 10x Visium RNA Level 1 entries ensures that raw spatial sequencing reads are documented with the slide, capture area, and library metadata needed to correctly reconstruct spatial context in downstream alignment and analysis shared through the CCKP.

### Who Should Be Contributing 10x Visium RNA Level 1 Entries?

1. **Spatial Biology Researchers** – Record slide, capture area, and permeabilization details from the Visium experiment.
2. **Sequencing Core Staff** – Capture library preparation and platform metadata for the spatial sequencing run.
3. **Computational Genomics Analysts** – Ensure raw file and slide metadata is complete before spatial alignment pipelines are run.
4. **Data Managers** – Maintain consistent, portal-ready metadata for raw Visium sequencing outputs shared through the CCKP.

## Download Template

You can download the [VisiumRNALevel1 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/VisiumRNALevel1.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('visiumRNALevel1/reference.csv', keep_default_na=False) }}
