A **NanoString GeoMx ROI Segment Annotation** entry documents the Region of Interest (ROI) and Area of Illumination (AOI)/segment metadata generated during a GeoMx Digital Spatial Profiler (DSP) run. Each entry reports one assayed biospecimen per row, together with the ROI and AOI names and coordinates, scan- and slide-level identifiers, and quality control status as reported by the GeoMx DSP application.

Beyond spatial location, this module captures the segment-level quality metrics used to assess and normalize GeoMx data: binding density, positive normalization factor, surface area, nuclei count, tissue stain used to select ROI boundaries, and the negative control, no-template-control, and limit-of-quantification values used for background correction. It also carries the sequencing quality metrics (raw, stitched, aligned, deduplicated, and trimmed read counts, coverage, and MapQ30) associated with each segment, linking spatial and sequencing quality control together in a single record.


## Why You Should Contribute NanoString GeoMx ROI Segment Annotation Entries

Contributing ROI/segment annotation entries ensures that the spatial location, quality control metrics, and normalization factors behind every GeoMx expression measurement are documented and traceable back to the specific biospecimen, ROI, and AOI that produced them.


### Who Should Be Contributing NanoString GeoMx ROI Segment Annotation Entries?

1. **Spatial Biology Researchers** – Confirm that ROI and AOI selections accurately reflect the biological regions of interest being studied.
2. **Core Facility Staff** – Record the scan, slide, and segment QC metrics reported directly by the GeoMx DSP application.
3. **Computational Analysts** – Ensure normalization factors and QC metrics are complete and correctly linked so downstream expression data can be properly background-corrected and interpreted.
4. **Data Managers** – Track ROI/segment annotations alongside the imaging and sequencing data deposited for a study.


## Download Template

You can download the [NanoStringGeoMXROISegmentAnnotation CSV template](https://github.com/mc2-center/data-models/raw/main/templates/NanoStringGeoMXROISegmentAnnotation.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('geomxRoi/reference.csv', keep_default_na=False) }}
