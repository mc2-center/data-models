A **10x Visium RNA Level 2** entry documents the alignment workflow outputs downstream of a 10x Visium RNA Level 1 file. This level captures the SAM tags used for the unique molecular identifier (UMI) and spatial barcode fields, a link to the spatial barcode whitelist file, whether hard trimming was applied, and the genomic reference, genome annotation, and workflow version used to perform the alignment.

Level 2 entries make explicit how raw spatial reads were mapped and tagged with their spatial barcodes, preserving the technical details needed to reproduce or audit the alignment step before expression quantification.

## Why You Should Contribute 10x Visium RNA Level 2 Entries

Contributing 10x Visium RNA Level 2 entries ensures that the alignment and barcode-tagging workflow applied to spatial sequencing reads is documented with enough detail for others to reproduce or evaluate the analysis shared through the CCKP.

### Who Should Be Contributing 10x Visium RNA Level 2 Entries?

1. **Computational Genomics Analysts** – Record alignment tags, genomic reference, and workflow versions used to process spatial reads.
2. **Bioinformatics Pipeline Developers** – Document the spatial barcode whitelist and trimming parameters applied during alignment.
3. **Spatial Biology Researchers** – Confirm that aligned outputs are correctly linked back to the raw Visium run they originated from.
4. **Data Managers** – Maintain consistent, portal-ready metadata for aligned Visium sequencing outputs shared through the CCKP.

## Download Template

You can download the [VisiumRNALevel2 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/VisiumRNALevel2.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('visiumRNALevel2/reference.csv', keep_default_na=False) }}
