A **NanoString GeoMx Level 1** entry describes the raw sequencing files produced from a GeoMx Digital Spatial Profiler (DSP) experiment, prior to alignment or count conversion. This includes the assay type used in the DSP pipeline (RNA or Protein, run via nCounter or NGS) along with detailed next-generation sequencing (NGS) library metadata: library strategy, source material and molecule, selection method, layout, sequencing platform, read length, raw read counts, unique bases, sequencing coverage, and the library preparation kit name, vendor, and version.

Level 1 entries represent the earliest and most complete record of what was sequenced during a GeoMx run, and they anchor the full data provenance chain — every downstream processed file (Level 2 count conversions and Level 3 processed counts) traces back to the raw reads documented here.


## Why You Should Contribute NanoString GeoMx Level 1 Entries

Contributing Level 1 entries ensures that raw GeoMx sequencing outputs are properly cataloged with the library preparation and sequencing details needed to interpret them, and are traceable back to the biospecimen and ROI/segment they were derived from.


### Who Should Be Contributing NanoString GeoMx Level 1 Entries?

1. **Core Facility Staff** – Document the library preparation kit, sequencing platform, and run parameters used to generate raw reads.
2. **Spatial Biology Researchers** – Confirm that raw sequencing files are correctly linked to the biospecimen and segments profiled.
3. **Computational Analysts** – Ensure sequencing metadata is complete so raw files can be correctly processed into Level 2 and Level 3 outputs.
4. **Data Managers** – Track raw sequencing files as they are deposited to ensure completeness of the GeoMx data provenance chain.


## Download Template

You can download the [NanoStringGeoMxDSPLevel1 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/NanoStringGeoMxDSPLevel1.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('geomxLevel1/reference.csv', keep_default_na=False) }}
