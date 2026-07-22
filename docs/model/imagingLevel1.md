An **Imaging Level 1** entry describes a raw imaging data file — the unprocessed output of a microscope, scanner, or other imaging platform, prior to any quality control, co-registration, or downstream processing. This is the earliest and most complete record of what was captured during an imaging experiment, and includes the acquisition context (assay type, platform model and manufacturer, acquisition software, protocol link) along with standard file-level descriptors such as file format, species, and design.

Because raw images are typically generated per-channel or per-acquisition, Imaging Level 1 entries link back to the corresponding channel metadata via the `ImagingChannel Key`, and forward to the biospecimen that was imaged via `Biospecimen Key`. This level anchors the full imaging data provenance chain: every downstream processed image, segmentation, or feature array (Imaging Levels 2–4) traces back to the raw file(s) documented here.


## Why You Should Contribute Imaging Level 1 Entries

Contributing Imaging Level 1 entries ensures that raw imaging outputs are properly cataloged, discoverable, and traceable back to the specimen and acquisition settings that produced them — the foundation that all subsequent image processing and analysis depends on.


### Who Should Be Contributing Imaging Level 1 Entries?

1. **Imaging Scientists** – Document raw image files and the acquisition settings used to generate them.
2. **Core Facility Staff** – Record platform, instrument, and software details at the point of image acquisition.
3. **Computational Imaging Analysts** – Ensure raw file metadata is complete so it can be correctly linked to downstream processed and derived imaging products.
4. **Data Managers** – Track raw imaging files as they are deposited to ensure completeness of the imaging data provenance chain.


## Download Template

You can download the [ImagingLevel1 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/ImagingLevel1.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('imagingLevel1/reference.csv', keep_default_na=False) }}
