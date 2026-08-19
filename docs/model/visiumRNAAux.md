A **10x Visium Auxiliary Files** entry documents supporting data associated with 10x Genomics Visium spatial transcriptomics experiments, such as aligned tissue images, quality control reports, and other files that accompany the primary sequencing and expression outputs of a Visium run. Rather than representing a sequencing or expression level itself, this module links auxiliary artifacts, such as slide images, scale factor files, and QC reports, back to the Visium RNA Level 1 through 4 files, biospecimen, and study they belong to, along with the run, slide, and capture area they were generated from.

Auxiliary files are often what make a Visium dataset interpretable and reusable: tissue images and QC reports give downstream users the context needed to evaluate spot detection, alignment quality, and tissue morphology alongside the expression data.

## Why You Should Contribute 10x Visium Auxiliary Files Entries

Contributing 10x Visium Auxiliary Files entries ensures that the images, scale factors, and quality control artifacts generated during a Visium run are discoverable and properly linked to the sequencing and expression data they support, giving downstream users full context for interpreting spatial results shared through the CCKP.

### Who Should Be Contributing 10x Visium Auxiliary Files Entries?

1. **Spatial Biology Researchers** – Document tissue images and slide/capture area context generated during a Visium experiment.
2. **Computational Genomics Analysts** – Record QC reports and scale factor files produced alongside spatial expression processing.
3. **Sequencing Core Staff** – Track which auxiliary files correspond to which Visium run and biospecimen.
4. **Data Managers** – Maintain consistent, portal-ready metadata for auxiliary spatial transcriptomics files shared through the CCKP.

## Download Template

You can download the [VisiumAuxiliaryFiles CSV template](https://github.com/mc2-center/data-models/raw/main/templates/VisiumAuxiliaryFiles.csv) to streamline data entry.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('visiumRNAAux/reference.csv', keep_default_na=False) }}
