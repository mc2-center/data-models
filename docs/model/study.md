A **Study** entry documents key information about research projects, including methodologies, participants, and ethical considerations. Properly maintaining study records ensures that data is compliant with research standards, traceable, and usable across various scientific fields. This section explains how to create and maintain a valid study entry using the required fields, templates, and example data provided.


## Why You Should Contribute Study Entries

Contributing study entries ensures that critical research details such as methodology, investigators, and related datasets are documented and accessible. This fosters transparency, collaboration, and reproducibility in research. A well-maintained study entry also helps stakeholders understand the scope, purpose, and outcomes of research efforts, enabling better data integration and analysis across projects.


### Who Should Be Contributing Study Entries?

1. **Principal Investigators (PIs)** – Provide clear documentation of your studies to enhance visibility and demonstrate research contributions for funding agencies and collaborators.

2. **Research Coordinators and Project Leads** – Ensure proper record-keeping of studies under your supervision, supporting compliance, reporting, and resource allocation.

3. **Data Managers** – Create study entries to link related datasets, publications, and tools, improving data provenance and facilitating cross-references within research ecosystems.

4. **Consortium Participants** – Contribute study information to showcase collaborative research efforts and track joint achievements.

5. **Funding Agencies and Grant Monitors** – Monitor study progress by ensuring that all funded research is accurately documented and accessible.

6. **Ethics and Compliance Officers** – Maintain study entries to verify that all necessary de-identification methods, IRB protocols, and data use policies are in place.


## Download Template

To streamline the process, download the [study entry template](https://github.com/mc2-center/data-models/raw/main/templates/Study.csv) for standardized data entry.


## Example Data Entry

The table below includes sample values to demonstrate proper attribute usage.

| **Attribute** | **Example Value** |
|---|---|
| Study | Biology |
| Study Name | Effects of Diet and Exercise on Obesity |
| Study Description | Analysis of Cardiovascular Response during Exercise |
| Study Investigator | Dr. Jane Doe, PhD in Nutrition Science, University of Texas |
| Study_id | STUDY_2024_OBESITY_EXERCISE |
| Study Number of Participants | 5000 |
| Study Number of Samples | 120 |
| Study Deidentification Method Type | Manual |
| Study Deidentification Method Description | Personal identifiers such as names and dates were removed, and randomization techniques were applied. |
| Study Deidentification Method Software | Safe Harbor Privacy Software |
| Study dbGaP Accession Id | phs000424.v7.p2 |
| Study Project Identifier | syn12345678 |
| Study Data Use Codes | DUO:0000021, DUO:0000019, DUO:0000006 |


## Data Use Ontology (DUO) Implementation

MC<sup>2</sup> Center uses the [Data Use Ontology (DUO)](https://github.com/EBISPOT/DUO) to record the consent permissions and use restrictions that apply to a Study's data and materials. DUO terms are defined once, in the shared vocabulary (`modules/shared/annotationProperty.csv` and `modules/shared/duo.csv`), and are reused by any attribute that needs to describe data use — currently, `Study Data Use Codes` is that attribute for Study entries.

`Study Data Use Codes` is a multi-select, string-list attribute. Its valid values are almost all real DUO term CURIEs (e.g. `DUO:0000006`, `DUO:0000021`), plus a `Pending Annotation` placeholder for studies that have not yet been reviewed for data use restrictions. Full definitions for every valid DUO term are documented on the [Study Standard Terms page](../valid_values/study.md#attribute-study-data-use-codes).

### DUOPlus terms: Sage Bionetworks extensions to DUO

DUO does not have terms for a few governance concepts this model needs to track (deidentification method, data tier, license, etc.), so Sage Bionetworks defined seven extension terms, `DUOPlus1` through `DUOPlus7`, that this model reuses as valid values for `Study Data Use Codes` alongside the real DUO terms:

| DUOPlus Term | Governance Concept | Companion Field |
|---|---|---|
| DUOPlus1 | Source geography | `sourceGeography` |
| DUOPlus2 | Study population | `populationType` |
| DUOPlus3 | Data deidentification | `deidentificationType` |
| DUOPlus4 | Data permission | `dataPermission` |
| DUOPlus5 | Data tier | `dataTier` |
| DUOPlus6 | License | `license` |
| DUOPlus7 | Attribution | `attribution` |

### How conditionally required fields are surfaced

Most DUO terms (e.g. `DUO:0000042`/General Research Use, `DUO:0000006`/Health or Medical or Biomedical Research) are self-contained labels — selecting one doesn't require anything else. A subset of terms, however, indicate that additional detail must be provided alongside the code. For these terms, the model links the code to a **companion field**: a separate attribute where the contributor records that detail. Selecting the code makes its companion field conditionally required; all other companion fields remain optional.

This conditional relationship is declared directly in `modules/shared/annotationProperty.csv`: each of these DUO/DUOPlus terms also appears there as its own `Attribute` row, and that row's `DependsOn` column names the companion field it requires. When the model is compiled to JSON Schema, each of these rows becomes an `if`/`then` rule on `Study Data Use Codes` — e.g. `StudyDataUseCodes` containing `DUO:0000026` requires `UserSpecificRestriction` to be filled in. `json_schemas/Study.json` currently has 15 such rules, one for each DUO/DUOPlus term listed below:

| DUO Term | Meaning | Companion Field (conditionally required) |
|---|---|---|
| DUO:0000007 | Disease-specific research | `diseaseSpecificResearch` (MONDO ID) |
| DUO:0000012 | Research-specific restrictions | `researchSpecificRestrictions` |
| DUO:0000020 | Collaboration required | `collaborationRequired` (PI contact email) |
| DUO:0000022 | Geographical restriction | `geographicalRestriction` (country code) |
| DUO:0000024 | Publication moratorium | `publicationMoratorium` (end date) |
| DUO:0000025 | Time limit on use | `timeLimitOnUse` (number of months) |
| DUO:0000026 | User-specific restriction | `userSpecificRestriction` |
| DUO:0000028 | Institution-specific restriction | `institutionSpecificRestriction` (ROR ID) |
| DUOPlus1–DUOPlus7 | Sage Bionetworks DUOPlus governance extensions (see table above) | `sourceGeography`, `populationType`, `deidentificationType`, `dataPermission`, `dataTier`, `license`, `attribution` |

For example, a Study entry with `Study Data Use Codes` set to `DUO:0000024, DUO:0000022` must also provide values for `publicationMoratorium` (the moratorium end date) and `geographicalRestriction` (the applicable country code(s)) — but can leave every other companion field blank, since none of the other DUO/DUOPlus terms were selected.


## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('study/reference.csv', keep_default_na=False) }}


## Test

..include :: test.md