An **Imaging Level 3 (Image)** entry describes quality-controlled or co-registered image data — imagery that has been processed beyond the raw and pre-processed stages to correct artifacts, align channels or cycles, and confirm suitability for downstream analysis. It carries the same detailed image-format metadata as Imaging Level 2 (optical parameters, pixel dimensions, pyramid/Z-stack/timeseries flags, and pixel encoding), reflecting the state of the image after QC and/or co-registration have been applied.

Imaging Level 3 (Image) entries link back to the pre-processed image via `ImagingLevel2 Key` and to the relevant channel via `ImagingChannel Key`, preserving a clear processing lineage from raw acquisition through to analysis-ready imagery. This level typically serves as the direct input to segmentation (Imaging Level 3 Segments) and downstream feature extraction (Imaging Level 4).


## Why You Should Contribute Imaging Level 3 (Image) Entries

Contributing Imaging Level 3 (Image) entries ensures that quality-controlled and co-registered imagery is clearly distinguished from raw data, with full traceability back to its source image — supporting confident reuse of processed images in downstream segmentation and analysis.


### Who Should Be Contributing Imaging Level 3 (Image) Entries?

1. **Computational Imaging Analysts** – Document QC and co-registration outcomes and the resulting processed image files.
2. **Imaging Scientists** – Verify that processing steps applied to raw images are accurately reflected in the metadata.
3. **Core Facility Staff** – Confirm image quality metrics and processing parameters used prior to downstream analysis.
4. **Data Managers** – Track processed image files to maintain a complete and auditable imaging data lineage.


## Download Template

You can download the [ImagingLevel3Image CSV template](https://github.com/mc2-center/data-models/raw/main/templates/ImagingLevel3Image.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('imagingLevel3Image/reference.csv', keep_default_na=False) }}
