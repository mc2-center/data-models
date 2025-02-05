This section outlines how to create a valid dataset entry, focusing on required fields, usage instructions, and an example to guide users. 

## Required Fields 
Required fields ensure data accuracy, uniqueness, and discoverability. Fields such as 'Dataset Name', 'Dataset Alias', and 'DatasetView_id' must be filled out to submit an entry successfully.


## Download Template
You can download the [dataset entry template](https://github.com/mc2-center/data-models/raw/main/templates/DatasetView.csv), which includes all required fields, to streamline the data entry process.

## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**           | **Example Value**                                                                                       |
|-------------------------|---------------------------------------------------------------------------------------------------------|
| Dataset Name            | U.S. Census Data 2019                                                                                   |
| Dataset Alias           | Census_2019                                                                                             |
| Dataset Description     | This dataset includes demographic and economic statistics collected in the U.S. Census 2019.             |
| Dataset Url             | [https://www.census.gov/data.html](https://www.census.gov/data.html)                                    |
| Dataset Assay           | None                                                                                                    |
| Dataset Species         | Human                                                                                                   |
| Dataset Tumor Type      | Not applicable                                                                                          |
| Dataset Tissue          | Not applicable                                                                                          |
| Dataset File Formats    | CSV, PDF                                                                                                |
| Dataset Grant Number    | CA209971                                                                                                |
| Dataset Pubmed Id       | Not applicable                                                                                          |
| Dataset View            | Table                                                                                                   |
| DatasetView_id          | DatasetView_12345                                                                                       |



## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/DatasetView.csv)

{{ read_csv('dataset/template.csv') }}
