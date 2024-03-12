<h1 align="center">
  MC<sup>2</sup> Center Data Models
</h1>

<h3 align="center">
  Data models and standard terms used by MC2 Center
</h3>
<br/>

<p align="center">
  <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/release/mc2-center/mc2-data-models?label=latest%20release&display_name=release&style=flat-square">
  <img alt="GitHub Release Date" src="https://img.shields.io/github/release-date/mc2-center/mc2-data-models?style=flat-square&color=green">
  <img alt="GitHub" src="https://img.shields.io/github/license/mc2-center/mc2-data-models?style=flat-square&color=orange">
</p>

---

🔎 **Data Models Explorer**: https://mc2-center.github.io/data-models/

---

## Overview

This repository contains the released versions of the JSON-LD schemas for the
[Cancer Complexity Knowledge Portal] (CCKP), and more broadly, MC2 Center.
You can learn more about the schemas/data models and other aspects of this
project in our portal documentation - coming soon! The MC2 Center data model
is in both a csv and jsonld format. It is separated into modules (see the
module folder) where various peices of the data model can be updated,
including the standard terms/valid values (please see "Adding a new valid
value" below). To edit the data model, create a new branch, make edits, and
when ready, create a pull request. Once the new branch is merged with `main`,
a new `mc2.model.csv`` and `mc2.model.jsonld`` will automatically update. See
documentation below for more information.


## Updating the Data Model

### Adding a new valid value
 
When a new valid value needs to be added to the data model:

1. Research the term and make sure we do not already have a synonym for it that
exists. Using NCIt is excellent for this, though sometimes looking outside of
NCIt is necessary. If we do currently have a synonym in use, add the valid value
as a "non preferred term" in the applicable attribute csv in the modules folder.
If not:

2. Add the valid value in the "attribute" column of the applicable csv in the
appropriate module folder. E.g. if a new tumor type needs to be added go to
the tumorType.csv and add the new term in the attribute column). Fill out the
rest of the columns as completely as possible, this includes the description,
the required column, parent column, source column, non preferred terms column,
the ontology identifier, url, NCIt Code, and any notes. Please make a note of
who added it and the date.

3. Be sure to look up any synonyms and add to the "non preferred terms" column.
This will make annotating easier in the future.

4. When ready to release a new version of the data model and a pull request is
made, the valid values will automatically get added to `mc2.model.csv` and its
JSON-LD file.


## Release Notes 

This repository adopts [Semantic Versioning] (SemVer), which provides a
standard way of versioning software based on meaningful changes in
functionality.


## Documentation

The documentation uses [MkDocs], [mkdocs-table-reader-plugin], and the
[Material theme]. All docs are located in the `docs` directory and
are written in Markdown format.

* **Update the docs site:**

  The docs site is configured to rebuild automatically whenever a change
  is found in the `docs` folder, `mc2.model.csv`, or `mkdocs.yml`
  (the MkDocs configuration file). No further manual steps are required.

* **To add a new page:**

    Create a Markdown file in `docs`, then add the page to the `nav` 
    setting in `mkdocs.yml`.

* **To test your changes:**

    Build a local docs site that will auto-reload with any changes:

    ```console
    $ mkdocs serve
    INFO    -  Building documentation...
    INFO    -  Cleaning site directory
    INFO    -  Documentation built in 0.51 seconds
    INFO    -  [10:20:58] Watching paths for changes: 'docs', 'mkdocs.yml'
    INFO    -  [10:20:58] Serving on http://127.0.0.1:8000/
    ```

    This will serve the documentation on http://127.0.0.1:8000. Enter Ctrl + C
    to close the server.

    Note that to test locally, you will need to install the dependencies
    first (ideally in a virtual environment), e.g.

    ```console
    conda create -n docs python=3.12
    conda activate docs
    pip install mkdocs mkdocs-material mkdocs-table-reader-plugin
    ```



[Cancer Complexity Knowledge Portal]: https://cancercomplexity.synapse.org/
[Semantic Versioning]: https://semver.org/
[MKDocs]: https://www.mkdocs.org/
[mkdocs-table-reader-plugin]: https://timvink.github.io/mkdocs-table-reader-plugin/
[Material theme]: https://squidfunk.github.io/mkdocs-material/

