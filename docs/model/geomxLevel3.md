A **NanoString GeoMx Level 3** entry documents the fully processed count data produced by the NanoString GeoMx DSP pipeline, such as final probe- or target-level expression matrices. This level captures the unique probe and unique target counts represented in the file, the matrix type (e.g. raw, normalized, or background-subtracted counts), and the software, workflow, and parameters used to generate the processed output, including a link to the workflow for reproducibility.

Level 3 entries represent the analysis-ready data products most commonly used for downstream statistical analysis, while still preserving a clear lineage back to the Level 2 count conversion and Level 1 raw reads that produced them.


## Why You Should Contribute NanoString GeoMx Level 3 Entries

Contributing Level 3 entries ensures that processed count data is documented with enough workflow and provenance detail for others to understand exactly how it was derived, and to confidently reuse it in downstream analyses shared through the CCKP.


### Who Should Be Contributing NanoString GeoMx Level 3 Entries?

1. **Computational Analysts** – Document the workflow, parameters, and matrix type used to generate processed count data.
2. **Bioinformatics Pipeline Developers** – Record the software and workflow versions that produced the processed outputs, supporting reproducibility.
3. **Spatial Biology Researchers** – Track which processed data products correspond to which raw reads and ROI/segments.
4. **Data Managers** – Maintain consistent, portal-ready metadata for processed GeoMx outputs shared through the CCKP.


## Download Template

You can download the [NanoStringGeoMxDSPLevel3 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/NanoStringGeoMxDSPLevel3.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('geomxLevel3/reference.csv', keep_default_na=False) }}
