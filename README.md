<h1 align="center">
  MC<sup>2</sup> Center Data Models
</h1>

<h3 align="center">
  Data models and standard terms used by MC2 Center
</h3>
<br/>

<p align="center">
  <img 
    alt="GitHub release (latest by date)" 
    src="https://img.shields.io/github/release/mc2-center/mc2-data-models?label=latest%20release&display_name=release&style=flat-square"
  >
  <img 
    alt="GitHub Release Date" 
    src="https://img.shields.io/github/release-date/mc2-center/mc2-data-models?style=flat-square&color=green"
  >
  <img 
    alt="GitHub" 
    src="https://img.shields.io/github/license/mc2-center/mc2-data-models?style=flat-square&color=orange"
  >
</p>

---

🔎 **Data Models Explorer**: https://mc2-center.github.io/data-models/

📊 **Data Curator App**: https://dca.app.sagebionetworks.org/

---

## Overview

This project contains the released versions of the JSON-LD schemas for the
[Cancer Complexity Knowledge Portal] (CCKP), and more broadly, MC2 Center.
You can learn more about the schemas/data models and other aspects of this
project in our portal documentation - coming soon! The MC2 Center data model
is in both CSV and JSON-LD format.

## Folder Structure

```
.
├── dca_config/
├── docs/
├── modules/
├── scripts/
└── templates/
```

### DCA Configuration

MC2 Center's configurations for the DCA is located in `./dca_config`.

### Documentation

All docs are located in the `./docs` directory and are written in Markdown
format. Some docs are generated before the site is built, which is handled
by the `hooks.py` script in `./scripts`.

### Valid Values

Valid values are separated into modules (located in `./modules`), where
various pieces of the data model can be updated, including the standard
terms/valid values.

#### Add a new valid value
 
When a new valid value needs to be added to the data model:

1. Research the term and make sure we do not already have a synonym for it
   that exists. Using NCIt is excellent for this, though sometimes looking
   outside of NCIt is necessary. If we do currently have a synonym in use,
   add the valid value as a "non preferred term" in the applicable attribute
   CSV in `./modules`. If not:

2. Add the valid value in the "attribute" column of the applicable csv in
   the appropriate module folder. E.g. if a new tumor type needs to be added
   go to `tumorType.csv` and add the new term in the attribute column). Fill
   out the rest of the columns as completely as possible, this includes the
   description, the required column, parent column, source column, non-preferred
   terms column, the ontology identifier, url, NCIt Code, and any notes.
   Please make a note of who added it and the date.

3. Be sure to look up any synonyms and add to the "non preferred terms"
   column. This will make annotating easier in the future.

#### Update a valid value

Please [open a ticket] and let the MC2 Center internal data team know the
reasoning behind why a valid value should be updated/removed.

### Annotation Templates

A collection of ready-for-use templates are available in `./templates`, that
can be used with the [Data Curator App (DCA)] to add/update entities on the
CCKP.



[Cancer Complexity Knowledge Portal]: https://cancercomplexity.synapse.org/
[open a ticket]: https://github.com/mc2-center/data-models/issues/new?assignees=aditigopalan&labels=bug&projects=&template=bug-report.md&title=%5Bbug%5D+
[Data Curator App (DCA)]: https://dca.app.sagebionetworks.org/