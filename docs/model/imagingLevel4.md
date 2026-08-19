An **Imaging Level 4** entry describes derived imaging data in the form of an object-by-feature array — the quantitative output produced after segmented objects (e.g. cells) have had their features (e.g. per-channel marker intensities, morphology) extracted and summarized. Rather than image or mask files, this module captures tabular, analysis-ready data: the number of objects and features described, the object class involved, and the summary statistic (mean, median, or otherwise) used to aggregate feature values per object.

Imaging Level 4 entries reference the full processing lineage that produced them, linking back to the pre-processed image (`ImagingLevel2 Key`), the QC'd/co-registered image (`ImagingLevel3Image Key`), and the segmentation used (`ImagingLevel3Segments Key`). This level typically represents the final, most analysis-ready product of the imaging pipeline, suitable for downstream statistical or machine learning analyses.


## Why You Should Contribute Imaging Level 4 Entries

Contributing Imaging Level 4 entries ensures that derived, object-level feature data is documented with a clear link back to the images and segmentations that produced it, making quantitative imaging results reusable and interpretable by other researchers.


### Who Should Be Contributing Imaging Level 4 Entries?

1. **Computational Imaging Analysts** – Document feature extraction pipelines and the resulting object-by-feature arrays.
2. **Imaging Scientists** – Confirm that extracted features and summary statistics align with the biological question being addressed.
3. **Data Scientists** – Ensure derived feature data is complete and well-annotated for downstream statistical or machine learning analyses.
4. **Data Managers** – Track derived data files to maintain a complete record from raw image through to final quantitative output.


## Download Template

You can download the [ImagingLevel4 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/ImagingLevel4.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('imagingLevel4/reference.csv', keep_default_na=False) }}
