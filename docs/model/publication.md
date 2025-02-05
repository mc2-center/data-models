This section outlines how to accurately document a publication entry, ensuring compliance with data model specifications. Use the template and example provided to maintain data accuracy and consistency.  

## Required Fields 
Fields such as 'Publication Journal', 'Pubmed Id', 'Pubmed Url', 'Publication Title', 'Publication Year', 'Publication Authors', 'Publication Abstract', 'Publication Assay', 'Publication Tumor Type', 'Publication Tissue', 'Publication Accessibility', 'Publication Grant Number', and 'PublicationView_id' are mandatory to ensure a comprehensive record for each publication.  


## Download Template
Download the [publication entry template](https://github.com/mc2-center/data-models/raw/main/templates/PublicationView.csv) to streamline data entry and ensure required fields are completed.

## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**              | **Example Value**                                                                                                  |
|----------------------------|---------------------------------------------------------------------------------------------------------------------|
| Publication Doi            | [10.1016/j.cell.2016.02.013](https://doi.org/10.1016/j.cell.2016.02.013)                                             |
| Publication Journal        | *Nature Medicine*                                                                                                   |
| Pubmed Id                  | 12345678                                                                                                             |
| Pubmed Url                 | [PubMed Link](https://www.ncbi.nlm.nih.gov/pubmed/12345678)                                                          |
| Publication Title          | Role of Inflammatory Pathways in Cancer Progression                                                                 |
| Publication Year           | 2023                                                                                                                 |
| Publication Keywords       | Cancer Pathways, Inflammation, Tumor Microenvironment                                                               |
| Publication Authors        | Dr. Sarah Johnson, Dr. Michael Lee, Prof. Amanda Carter                                                              |
| Publication Abstract       | This study investigates inflammatory pathways and their impact on tumor progression and metastasis.                   |
| Publication Assay          | RNA Sequencing, In Vivo Bioluminescence                                                                              |
| Publication Tumor Type     | Lung Cancer, Breast Cancer                                                                                           |
| Publication Tissue         | Lung, Breast                                                                                                         |
| Publication Accessibility  | Open Access                                                                                                          |
| Publication View           | Online                                                                                                               |
| Publication Grant Number   | CA302123, CA301987                                                                                                    |
| Publication Dataset Alias  | GSE45678, DOI:10.1000/exampledataset                                                                                 |
| PublicationView_id         | PublicationView_45678                                                                                                |



## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/PublicationView.csv)

{{ read_csv('publication/template.csv') }}