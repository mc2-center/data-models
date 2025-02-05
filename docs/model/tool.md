This section outlines the data attributes for registering and documenting a software tool in a structured and standardized manner. Each attribute in the table below has a distinct purpose, helping improve the usability, traceability, and functionality of the tool in research or technical environments.


## Required Attributes
Mandatory attributes such as 'Tool Name', 'Tool Description', 'Tool Entity Role', 'Tool Entity Type', 'Tool Release Date', and others are necessary for completeness and usability. These attributes provide essential data points for tool identification, description, and functionality.


## Download Template
You can download the [ToolView CSV template](https://github.com/mc2-center/data-models/raw/main/templates/ToolView.csv) to streamline data entry.


## Example Data Entry
The table below includes sample values to demonstrate proper attribute usage.

| **Attribute**                 | **Example Value**                                                                                                    |
|-------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| Tool Name                     | Adobe Photoshop                                                                                                         |
| Tool Description              | "A photo editing tool with advanced image manipulation features, supporting multiple file formats and layers."          |
| Tool Release Date             | January 5, 2022                                                                                                        |
| Tool Entity Role              | Developer, Maintainer                                                                                                  |
| Tool Entity Type              | Organization                                                                                                           |
| Tool Input Data               | DNA Sequence                                                                                                           |
| Tool Output Data              | Gene ID (NCBI): NM_001282392.1                                                                                         |
| Tool Grant Number             | CA209975                                                                                                                |
| Tool Documentation Url        | https://docs.example.com/tool-guide.html                                                                               |
| Tool Operating System         | Windows, MacOS                                                                                                          |
| Tool Version                  | 3.2.1                                                                                                                  |
| Tool View                     | Detail View                                                                                                             |
| Tool Pubmed Id                | 26760201                                                                                                                |
| Tool License                  | Apache-2.0                                                                                                              |

## Full Field Reference

[⤓ Download template](https://github.com/mc2-center/data-models/raw/main/templates/ToolView.csv)

{{ read_csv('tool/template.csv') }}
