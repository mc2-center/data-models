This page outlines the attributes used to document and share dataset plans within MC2 Center-supported Synapse projects. The DataDSP model ensures that datasets are well-organized, traceable, and meet compliance requirements for data storage, sharing, and use.


## Required Fields 
Mandatory fields like 'DSP Dataset Name,' 'DSP Dataset Assay,' 'DSP Dataset Species,' and 'DataDSP_id' are essential for uniquely identifying and categorizing datasets. These attributes ensure completeness and help users locate or reference datasets within repositories.

## Download Template
To streamline data entry, you can download the [DataDSP CSV template](https://github.com/mc2-center/data-models/raw/main/templates/DataDSP.csv).


## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**               | **Example Value**                                                                                                      |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------|
| DSP Dataset Name            | DSP_Dataset_Sales_Analysis_2020                                                                                          |
| DSP Dataset Alias           | Sales_Data_2020                                                                                                          |
| DSP Dataset Assay           | Flow Cytometry                                                                                                           |
| DSP Dataset Species         | Asian Elephant                                                                                                           |
| DSP Dataset File Formats    | CSV, JSON                                                                                                                |
| DSP Planned Upload Date     | 2022-12-01                                                                                                               |
| DSP Dataset Grant Number    | CA209971                                                                                                                  |
| DSP Dataset Description     | "Preprocessed audio data for machine learning models, including frequency components, spectral analysis, etc."            |
| DSP Dataset Destination     | "/home/user/datasets/dsp_output"                                                                                          |
| DSP Dataset Url             | https://www.example.com/dataset/dsp1234                                                                                   |


## Full Field Reference


[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/DataDSP.csv)

{{ read_csv('sharingPlans/template.csv') }}