This section provides a simplified guide on how to create an educational resource entry by focusing on required fields, usage instructions, and an example. 

## Required Fields 
Certain fields, such as 'Resource Title', 'Resource Link', 'Resource Primary Audience', and 'EducationalResource_id', are mandatory to ensure that resources can be uniquely identified, accessed, and categorized effectively.

## Download Template
Use the [educational resource template](https://github.com/mc2-center/data-models/raw/main/templates/EducationalResource.csv) to streamline your data entry process. The template contains pre-defined required fields.

## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**              | **Example Value**                                                                                           |
|----------------------------|-------------------------------------------------------------------------------------------------------------|
| Educational Resource       | Online Tutoring Platform                                                                                    |
| Resource Title             | Introduction to Biology                                                                                     |
| Resource Link              | [https://www.example.com/resource_page.html](https://www.example.com/resource_page.html)                     |
| Resource Topic             | Metabolism                                                                                                  |
| Resource Activity Type     | Simulation                                                                                                  |
| Resource Primary Format    | Video                                                                                                       |
| Resource Intended Use      | Curriculum/Instruction                                                                                      |
| Resource Primary Audience  | Teacher                                                                                                     |
| Resource Educational Level | High School                                                                                                 |
| Resource Description       | This comprehensive e-book offers insights into advanced Python programming techniques.                       |
| Resource Origin Institution| Smithsonian Institution                                                                                      |
| Resource Language          | en                                                                                                          |
| Resource Contributors      | John Smith, Jane Doe, XYZ Corporation                                                                       |
| Resource Grant Number      | CA217655                                                                                                    |
| EducationalResource_id     | ER_4567                                                                                                     |

## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/EducationalResource.csv)

{{ read_csv('education/template.csv') }}
