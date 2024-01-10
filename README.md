<h1 align="center">
  MC<sup>2</sup> Center Data Models
</h1>

<h3 align="center">
  Data models and standard terms used by the
  <a href="https://cancercomplexity.synapse.org/" target="_blank">Cancer Complexity Knowledge Portal</a> 
  (CCKP)
</h3>
<br/>

<p align="center">
  <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/release/mc2-center/mc2-data-models?label=latest%20release&display_name=release&style=flat-square">
  <img alt="GitHub Release Date" src="https://img.shields.io/github/release-date/mc2-center/mc2-data-models?style=flat-square&color=green">
  <img alt="GitHub" src="https://img.shields.io/github/license/mc2-center/mc2-data-models?style=flat-square&color=orange">
</p>

## Overview

This repository contains the released versions of the JSON-LD schemas for the CCKP, and more broadly, MC2 Center. You can learn more about the schemas/data models and other aspects of this project in our portal documentation - coming soon! The MC2 Center data model is in both a csv and jsonld format. It is separated into modules (see the module folder) where various peices of the data model can be updated, including the standard terms/valid values (please see "Adding a new valid value" below). To edit the data model, create a new branch, make edits, and when ready, create a pull request. Once the new branch is merged with the main, a new mc2.model.csv and mc2.model.jsonld will automatically update. See documentation below for more information.


## Updating the Data Model


### Adding a new valid value
 
When a new valid value needs to be added to the data model:

1. Research the term and make sure we do not already have a synonym for it that exists. Using NCIt is excellent for this, though sometimes looking outside of NCIt is necessary. If we do currently have a synonym in use, add the valid value as a "non preferred term" in the applicable attribute csv in the modules folder. If not:

2. Add the valid value in the "attribute" column of the applicable csv in the appropriate module folder. E.g. if a new tumor type needs to be added go to the tumorType.csv and add the new term in the attribute column). Fill out the rest of the columns as completely as possible, this includes the description, the required column, parent column, source column, non preferred terms column, the ontology identifier, url, NCIt Code, and any notes. Please make a note of who added it and the date.

3. Be sure to look up any synonyms and add to the "non preferred terms" column. This will make annotating easier in the future.

4. When ready to release a new version of the data model and a pull request is made, the valid values will automatically get added to `mc2.model.csv` and its JSON-LD file.

## Release Notes 

The latest version release is v23.12.1. Moving forward, this repository will adopt <a href="https://semvar.org/" target="_blank"> Semanting Versioning</a>  (SemVar), which provides a standard way of versioning software based on meaningful changes in functionality.

