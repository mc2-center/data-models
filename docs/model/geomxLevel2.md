A **NanoString GeoMx Level 2** entry documents processed count conversion files (DCC/RCC) derived from a GeoMx Level 1 raw sequencing file. This level captures the same core library preparation and sequencing platform metadata as Level 1, along with the read-processing metrics generated during count conversion: stitched reads, aligned reads, deduplicated reads, trimmed reads, percent reads mapping at Q30 (MapQ30), unique bases, sequencing coverage, the genomic reference used, and the software and version that performed the conversion.

Level 2 entries represent the intermediate step between raw sequencing reads and analysis-ready processed counts, preserving a clear lineage back to the Level 1 raw reads that produced them while capturing the alignment and deduplication metrics needed to assess data quality.


## Why You Should Contribute NanoString GeoMx Level 2 Entries

Contributing Level 2 entries ensures that the read-processing and alignment steps between raw reads and final count data are documented with enough detail for others to assess data quality and trace processed counts back to their source reads.


### Who Should Be Contributing NanoString GeoMx Level 2 Entries?

1. **Computational Analysts** – Document the software, genomic reference, and alignment/deduplication metrics used to generate count conversion files.
2. **Core Facility Staff** – Provide the sequencing platform and library details carried through from Level 1.
3. **Bioinformatics Pipeline Developers** – Record workflow and software versions to support reproducibility of the count conversion step.
4. **Data Managers** – Maintain consistent, portal-ready metadata linking Level 1 raw reads to Level 2 processed outputs.


## Download Template

You can download the [NanoStringGeoMxDSPLevel2 CSV template](https://github.com/mc2-center/data-models/raw/main/templates/NanoStringGeoMxDSPLevel2.csv) to streamline data entry.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('geomxLevel2/reference.csv', keep_default_na=False) }}
