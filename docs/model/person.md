This section explains how to create a valid person entry in the database, with a focus on required fields, template usage, and a practical example to ensure data consistency and accuracy.

## Required Fields 
Certain fields like 'Name', 'Last Known Institution', 'Working Group Participation', 'Chair Roles', 'Consent For Portal Display', 'Portal Display', 'Person Grant Number', 'Person Consortium Name', and 'PersonView_id' are mandatory to ensure that each entry provides sufficient detail for identification and categorization.


## Download Template
Download the [person entry template](https://github.com/mc2-center/data-models/raw/main/templates/PersonView.csv) for streamlined data entry, ensuring that all required fields are filled out.

## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**               | **Example Value**                                                                                     |
|-----------------------------|--------------------------------------------------------------------------------------------------------|
| Name                        | Dr. Jane Smith                                                                                        |
| Alternative Names           | Jane Doe, J. Smith                                                                                    |
| Email                       | janesmith@example.com                                                                                 |
| Url                         | [Professional Profile](https://www.example.com/janesmith)                                             |
| Orcid Id                    | 0000-0002-1825-0097                                                                                   |
| Synapse Profile Id          | SP98765432                                                                                            |
| Last Known Institution      | Stanford University                                                                                   |
| Working Group Participation | Cancer Metabolism, Genomic Data Integration                                                           |
| Chair Roles                 | Steering Committee, Ethics Review Panel                                                               |
| Consent For Portal Display  | Yes                                                                                                    |
| Portal Display              | TRUE                                                                                                   |
| Person View                 | Public Profile View                                                                                    |
| Person Grant Number         | CA202177, CA304599                                                                                     |
| Person Consortium Name      | HTAN, PDMC                                                                                            |
| Person Publications         | 25700473, 31245678                                                                                     |
| Person Datasets             | GSE12345, DOI:10.1000/sampledataset                                                                   |
| Person Tools                | R Studio, Python, Jupyter Notebook                                                                    |
| Person Educational Resources | Advanced Cancer Research Training, NIH Data Science Workshop                                           |
| PersonView_id               | PersonView_12345                                                                                       |

## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/PersonView.csv)

{{ read_csv('person/template.csv') }}