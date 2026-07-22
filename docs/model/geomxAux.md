A **NanoString GeoMx Auxiliary Files** entry documents the supporting, non-image and non-count files that accompany a NanoString GeoMx Digital Spatial Profiler (DSP) experiment. Rather than describing the imaging or expression data itself, this module tracks the auxiliary artifacts needed to fully interpret and reproduce a GeoMx run: the ROI/segment annotation file, the PKC probe kit configuration file, the lab worksheet(s) generated during the run, and the DSP `config.ini` file.

These files are typically produced automatically by the GeoMx DSP instrument and software alongside the imaging and sequencing/count data, but they are easy to overlook when depositing a dataset. Capturing their Synapse identifiers here ensures that anyone reusing the imaging or expression data (Levels 1–3) can also locate the exact probe configuration, worksheet, and run settings that produced it.


## Why You Should Contribute NanoString GeoMx Auxiliary Files Entries

Contributing auxiliary file entries ensures that the configuration and worksheet files needed to interpret or reproduce a GeoMx DSP run are not lost or disconnected from the primary imaging and expression data, making the full experiment traceable and reusable by others.


### Who Should Be Contributing NanoString GeoMx Auxiliary Files Entries?

1. **Core Facility Staff** – Deposit the PKC, config, and worksheet files generated directly by the GeoMx DSP instrument.
2. **Spatial Biology Researchers** – Ensure auxiliary files are linked to the correct experiment and biospecimens they support.
3. **Computational Analysts** – Confirm that the probe kit and configuration files needed to reprocess or validate results are available and correctly referenced.
4. **Data Managers** – Track auxiliary file completeness alongside the imaging and expression data deposited for a study.


## Download Template

You can download the [NanoStringGeoMxAuxiliaryFiles CSV template](https://github.com/mc2-center/data-models/raw/main/templates/NanoStringGeoMxAuxiliaryFiles.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('geomxAux/reference.csv', keep_default_na=False) }}
