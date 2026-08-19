An **Imaging Level 3 (Segments)** entry describes image segmentation mask information — the output of algorithms that delineate objects of interest (such as nuclei, cytoplasm, plasma membrane, or whole cells) within a processed image. Rather than pixel intensity data, this module captures how segmentation results are stored (mask, outline, polygon, probability map, or point representation), the object class being segmented, the number of objects identified, and a pointer to the parameter file needed to reproduce the segmentation.

Imaging Level 3 (Segments) entries link to both the pre-processed image (`ImagingLevel2 Key`) and the QC'd/co-registered image (`ImagingLevel3Image Key`) that the segmentation was derived from. Segmentation results documented here are typically the direct input to object-level feature extraction and summary statistics captured in Imaging Level 4.


## Why You Should Contribute Imaging Level 3 (Segments) Entries

Contributing Imaging Level 3 (Segments) entries ensures that segmentation outputs — and the parameters used to generate them — are documented clearly enough for others to reproduce, validate, or build on object-level analyses without re-running segmentation from scratch.


### Who Should Be Contributing Imaging Level 3 (Segments) Entries?

1. **Computational Imaging Analysts** – Document segmentation algorithms, parameters, and resulting object classes and counts.
2. **Imaging Scientists** – Confirm that the object classes and segmentation representations accurately reflect the underlying biology.
3. **Core Facility Staff** – Provide context on the imaging assay driving segmentation choices (e.g. nuclear vs. whole-cell masks).
4. **Data Managers** – Track segmentation output files and their associated parameter files for reproducibility.


## Download Template

You can download the [ImagingLevel3Segments CSV template](https://github.com/mc2-center/data-models/raw/main/templates/ImagingLevel3Segments.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('imagingLevel3Segments/reference.csv', keep_default_na=False) }}
