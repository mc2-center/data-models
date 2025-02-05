This section explains how to create a valid grant entry, focusing on required fields, template usage, and an example for reference.

## Required Fields 
Fields like 'Grant Name', 'Grant Number', 'Grant Abstract', 'Grant Type', 'Grant Institution Name', 'Grant Investigator', 'Grant Consortium Name', 'GrantView_id', and 'Grant Start Date' are mandatory to ensure each grant is uniquely identifiable and properly categorized.



## Download Template
Use the [grant entry template](https://github.com/mc2-center/data-models/raw/main/templates/GrantView.csv) to streamline your data entry process. The template contains pre-defined required fields.

## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**              | **Example Value**                                                                                           |
|----------------------------|-------------------------------------------------------------------------------------------------------------|
| Grant Name                 | Research Grant for Cancer Genomics                                                                           |
| Grant Number               | CA209971                                                                                                     |
| Grant Abstract             | This grant funds research into genetic mutations contributing to aggressive cancers, focusing on tumor sequencing and gene expression analysis. |
| Grant Type                 | R37                                                                                                          |
| Grant View                 | Public                                                                                                       |
| Grant Theme Name           | Cancer Genomics, Precision Medicine                                                                          |
| Grant Institution Name      | Stanford University                                                                                         |
| Grant Institution Alias    | Stanford                                                                                                     |
| Grant Investigator         | Dr. John Smith                                                                                               |
| Grant Consortium Name      | HTAN                                                                                                         |
| GrantView_id               | GV12345                                                                                                      |
| Grant Synapse Team         | Team: Project Management, Permission: Edit                                                                   |
| Grant Synapse Project      | Synapse_ID: syn123456789, Grant_Name: NIH Brain Initiative Grant                                             |
| Grant Start Date           | 2022-01-01                                                                                                   |
| NIH RePORTER Link          | [NIH Reporter Project Info](https://projectreporter.nih.gov/project_info_description.cfm?aid=9813521)         |
| Duration of Funding        | 5 years                                                                                                      |
| Embargo End Date           | 2023-12-31                                                                                                   |



## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/GrantView.csv)

{{ read_csv('grant/template.csv') }}
