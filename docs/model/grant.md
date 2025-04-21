A **Grant** entry captures essential details about funded research projects. Grants support various scientific studies, often involving multiple institutions, investigators, and funding agencies. Accurate grant records facilitate resource tracking, collaboration, and compliance with funding requirements.

This section outlines how to create a valid grant entry by defining key metadata, including grant type, institution, investigator, and project duration. Proper grant documentation ensures projects can be easily identified, referenced, and managed across research initiatives.


## Why You Should Contribute Grant Entries

Grant information is maintained by the MC2 Center to ensure accurate tracking of funding sources, research objectives, and project details. This helps stakeholders monitor research progress, facilitates collaboration across funded initiatives, and supports compliance with reporting and accountability requirements.

At this time, grant entries are curated exclusively by MC2 Center staff and are not open for external contributions. If broader contribution access is introduced in the future, updated guidelines will be provided.


### Who Should Be Contributing Grant Entries?

1. **Principal Investigators (PIs)** – Document your funded projects to highlight ongoing research, objectives, and collaborations for visibility and accountability.  
2. **Research Administrators** – Maintain accurate grant records for compliance, progress monitoring, and reporting purposes.  
3. **Data Managers** – Link datasets, publications, and other project outputs to their corresponding funding sources to improve data traceability.  
4. **Grant Writers and Project Coordinators** – Provide detailed grant descriptions and metadata to showcase successful projects and support future funding proposals.  
5. **Consortia and Collaborative Project Leads** – Share grant details to foster transparency and facilitate multi-institutional research efforts across teams and disciplines.  

## Download Template

Use the [grant entry template](https://github.com/mc2-center/data-models/raw/main/templates/GrantView.csv) to streamline your data entry process. The template contains pre-defined required fields.


## Example Data Entry

The table below includes sample values to demonstrate proper attribute usage.
It is important to note that where these examples can generally guide you on the structure of the Grant entry, these fields will generally be curated by a member of the MC2 personnel near the beginning of the grant funding period and will be made available via Synapse. 

| **Attribute** | **Example Value** |
|---|---|
| Grant Name | Research Grant for Cancer Genomics |
| Grant Number | CA209971 |
| Grant Abstract | This grant funds research into genetic mutations contributing to aggressive cancers, focusing on tumor sequencing and gene expression analysis. |
| Grant Type | R37 |
| Grant View | Public |
| Grant Theme Name | Cancer Genomics, Precision Medicine |
| Grant Institution Name | Stanford University |
| Grant Institution Alias | Stanford |
| Grant Investigator | Dr. John Smith |
| Grant Consortium Name | HTAN |
| GrantView_id | GV12345 |
| Grant Synapse Team | Team: Project Management, Permission: Edit |
| Grant Synapse Project | Synapse_ID: syn123456789, Grant_Name: NIH Brain Initiative Grant |
| Grant Start Date | 2022-01-01 |
| NIH RePORTER Link | [NIH Reporter Project Info](https://projectreporter.nih.gov/project_info_description.cfm?aid=9813521) |
| Duration of Funding | 5 years |
| Embargo End Date | 2023-12-31 |


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('grant/reference.csv') }}
