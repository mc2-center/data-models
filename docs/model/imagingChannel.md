An **Imaging Channel** entry describes the channel-level metadata for a single detection channel within a multiplexed or multi-channel imaging experiment, such as a cycle in CODEX/CyCIF, a fluorescence channel in MxIF, or a metal-tagged channel in Imaging Mass Cytometry (IMC). Rather than describing an image file itself, this module captures the reagents, targets, and physical detection parameters (fluorophore, metal isotope, oligo barcode, excitation/emission wavelengths) associated with one channel, along with the antibody or probe used to generate signal in that channel.

Because a single imaging experiment can involve dozens of channels across multiple staining cycles, Imaging Channel entries are typically submitted as a table with one row per channel per assay, and are then linked from the imaging file-level modules (Imaging Level 1 and Imaging Level 2) via the `ImagingChannel Key`. This separation keeps channel/antibody metadata reusable and consistent across the many image files that share the same channel configuration.


## Why You Should Contribute Imaging Channel Entries

Contributing Imaging Channel entries ensures that the antibodies, probes, and detection parameters behind each signal in a multiplexed image are fully traceable — which is essential for reproducing staining panels, troubleshooting failed channels, and enabling downstream re-analysis of multiplexed imaging data by other groups.


### Who Should Be Contributing Imaging Channel Entries?

1. **Imaging Scientists** – Document the antibody panel, fluorophore, or isotope assignments used to generate each channel of a multiplexed imaging experiment.
2. **Core Facility Staff** – Record the reagent lot numbers, vendors, and detection settings applied during acquisition on shared imaging instrumentation.
3. **Computational Imaging Analysts** – Ensure channel metadata is complete and consistent so that channel-to-marker mappings can be programmatically resolved during analysis.
4. **Lab Managers** – Maintain a durable record of antibody clones, dilutions, and QC outcomes across staining cycles and experiments.


## Download Template

You can download the [ImagingChannel CSV template](https://github.com/mc2-center/data-models/raw/main/templates/ImagingChannel.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('imagingChannel/reference.csv', keep_default_na=False) }}
