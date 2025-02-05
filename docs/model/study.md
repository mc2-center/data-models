This section provides detailed guidance for creating and maintaining a study entry in compliance with data model standards. It is essential to follow these specifications to ensure accuracy, consistency, and usability of study-related data.

## Required Fields 
Certain attributes, such as 'Study Name', 'Study Description', 'Study Investigator', 'Study_id', 'Study Number of Participants', and 'Study De-identification Method Type', are marked as mandatory. Completing these fields ensures a comprehensive and standardized data entry.  


## Download Template
To streamline the process, download the [study entry template](https://github.com/mc2-center/data-models/raw/main/templates/Study.csv) for standardized data entry.


## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**                       | **Example Value**                                                                                                    |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| Study                                | Biology                                                                                                               |
| Study Name                           | Effects of Diet and Exercise on Obesity                                                                               |
| Study Description                    | Analysis of Cardiovascular Response during Exercise                                                                   |
| Study Investigator                   | Dr. Jane Doe, PhD in Nutrition Science, University of Texas                                                           |
| Study Reuse Statement                | Data from this study may be reused under conditions of proper citation and ethical approval.                           |
| Study_id                             | STUDY_2024_OBESITY_EXERCISE                                                                                           |
| Study Number of Participants         | 5000                                                                                                                  |
| Study De-identification Method Type  | Manual                                                                                                                |
| Study De-identification Method Description | Personal identifiers such as names and dates were removed, and randomization techniques were applied.               |
| Study De-identification Method Software | Safe Harbor Privacy Software                                                                                          |
| Study dbGaP Accession Id             | phs000424.v7.p2                                                                                                       |
| Study License                        | CC BY-NC 4.0                                                                                                          |
| Study Data Use Codes                 | IRB, PUB, HMB                                                                                                         |


## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/Study.csv)

{{ read_csv('study/template.csv') }}