An **Imaging Level 2** entry describes raw or pre-processed image data that carries detailed image-format and acquisition metadata beyond what is captured at Level 1 — including optical parameters (objective, magnification, numerical aperture, working distance, immersion type), pixel and physical dimensions (X/Y/Z size, pixel type, plane count, channel size), and structural properties of the image file (whether it is pyramidal, contains a Z-stack, or a time series). This level is intended to describe the image as a technical object in detail, capturing everything needed to correctly interpret its pixel data.

Imaging Level 2 entries link to the corresponding raw file via `ImagingLevel1 Key` and to channel metadata via `ImagingChannel Key`, tying detailed image structure back to both its originating acquisition and the channel(s) it contains. This level is a key input for any downstream co-registration, segmentation, or feature extraction that depends on precise knowledge of image geometry and pixel encoding.


## Why You Should Contribute Imaging Level 2 Entries

Contributing Imaging Level 2 entries ensures that the technical structure of each image file — its dimensions, pixel encoding, and optical acquisition parameters — is fully documented, which is essential for correctly loading, interpreting, and reprocessing multi-dimensional imaging data.


### Who Should Be Contributing Imaging Level 2 Entries?

1. **Imaging Scientists** – Document detailed acquisition and optical parameters associated with each image file.
2. **Core Facility Staff** – Record instrument-specific settings such as objective, magnification, and immersion type at time of capture.
3. **Computational Imaging Analysts** – Ensure image geometry and pixel encoding metadata is accurate so images can be correctly parsed and processed downstream.
4. **Data Managers** – Track pre-processed image files and their associated technical metadata for reproducibility.


## Download Template

You can download the [ImagingLevel2 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/ImagingLevel2.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('imagingLevel2/reference.csv', keep_default_na=False) }}
