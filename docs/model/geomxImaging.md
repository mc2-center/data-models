A **NanoString GeoMx Imaging** entry documents the images acquired directly by the GeoMx Digital Spatial Profiler (DSP) instrument during a spatial profiling run. This includes the standard file-level descriptors (format, species, design, assay) shared across the data model, along with GeoMx-specific attributes such as the imaging channel names captured and the Synapse ID(s) of tabular files containing the coordinate points for each Area of Illumination (AOI) found in the image.

Because GeoMx images can vary widely in acquisition hardware and configuration, this module also captures detailed instrument- and file-format-level imaging metadata: platform model and manufacturer, acquisition software, objective and magnification, working distance, immersion type, field-of-view size and index, physical pixel size and dimension order, bit depth, plane count, and timepoint/z-stack structure. Imaging entries link forward to the sequencing outputs derived from the same run (Level 1 and Level 2) and to the ROI/segment annotations and biospecimen that were imaged, anchoring the full GeoMx data provenance chain.


## Why You Should Contribute NanoString GeoMx Imaging Entries

Contributing imaging entries ensures that the raw scan images underlying a GeoMx DSP experiment are properly cataloged with the acquisition and instrument details needed to interpret them, and are traceable to the ROIs, segments, and downstream expression data they informed.


### Who Should Be Contributing NanoString GeoMx Imaging Entries?

1. **Core Facility Staff** – Record the instrument, software, and acquisition settings used to capture GeoMx scan images.
2. **Spatial Biology Researchers** – Confirm imaging metadata accurately reflects the tissue, channels, and regions profiled.
3. **Computational Imaging Analysts** – Ensure channel names and AOI coordinate files are correctly linked so downstream expression data can be traced back to specific image regions.
4. **Data Managers** – Track imaging files as they are deposited alongside sequencing and annotation data for a study.


## Download Template

You can download the [NanoStringGeoMxDSPImaging CSV template](https://github.com/mc2-center/data-models/raw/main/templates/NanoStringGeoMxDSPImaging.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('geomxImaging/reference.csv', keep_default_na=False) }}
