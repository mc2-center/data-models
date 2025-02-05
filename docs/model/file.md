This section explains how to create a valid file entry, focusing on required fields, template usage, and an example for reference.

## Required Fields 
Fields like 'File Url', 'File Assay', 'File Level', 'File Species', 'File Format', and 'File Alias' are mandatory to ensure each file is uniquely identifiable and can be properly categorized and retrieved.


## Download Template
Use the [file entry template](https://github.com/mc2-center/data-models/raw/main/templates/FileView.csv) to streamline your data entry process. The template contains pre-defined required fields.

## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

### Example Data Entry (Biology-Focused)

| **Attribute**                       | **Example Value**                                                                                           |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------|
| File Description                     | CSV file containing gene expression data for breast cancer samples                                           |
| File Design                          | CSV (Comma-separated values)                                                                                 |
| File Url                             | [https://www.example.com/files/breast_cancer_expression_data.csv](https://www.example.com/files/breast_cancer_expression_data.csv) |
| File Assay                           | RNA Sequencing                                                                                               |
| File Level                           | Level 3: Processed summary data, like gene expression counts or coverage statistics (e.g., CSV files)         |
| File Species                         | Human                                                                                                        |
| File Tumor Type                      | Breast Carcinoma                                                                                             |
| File Tissue                          | Breast                                                                                                       |
| File View                            | List View                                                                                                    |
| FileView_id                          | FileView_789012                                                                                              |
| File Format                          | CSV                                                                                                          |
| File Alias                           | Breast_Cancer_Gene_Expression.csv                                                                            |


## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/FileView.csv)



{{ read_csv('file/template.csv') }}