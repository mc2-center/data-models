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

## How to Contribute

### Development process

To edit the data model, modify the project in your own fork or in a feature
branch, then issue a PR once you are ready for the MC2 Center internal data
team to review and discuss.

Generally, you should:

1. **Branch off `main` and develop your contribution(s)**. Ensure `main` is
   up-to-date in your local project before creating a new feature branch.

2. Push changes to the feature branch (or fork, if that's the route you chose).

3. **Open a PR to (upstream) `main` once ready.**  Follow our PR template.
   Someone from the MC2 Center internal data team will then review, and either
   approve + merge or ask for futher discussion.

4. Once the branch is merged into `main` (pending approval), a workflow will
   run to generate a new `mc2.model.csv` and `mc2.model.jsonld`.


### Releasing a new version

This repository has a workflow in-place that will auto-update the next
release draft.  Whenever a PR is merged, the workflow will run and add the
PR to the draft.

For versioning, this project adopts [Semantic Versioning] (SemVer), which the
workflow will also determine, based on the PR(s) included in the next planned
release. Specifically:
   * any PR labeled with `major` will increment `x`
   * any PR labeled with `minor` will increment `y`
   * any PR labeled with `patch` will increment `z`

  > [!NOTE]
  > Only _one_ number will increment, where `x` will take precedence, followed
  > by `y`, then finally `z`.

To release a new version, go to [Releases] > edit the release draft > **Publish release**


### Updating documentation

The Data Models Explorer uses [MkDocs], [mkdocs-table-reader-plugin], and the
[Material theme] (as well as [pandas] for the `hooks.py` script).

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
    pip install mkdocs mkdocs-material mkdocs-table-reader-plugin pandas
    ```



[Cancer Complexity Knowledge Portal]: https://cancercomplexity.synapse.org/
[open a ticket]: https://github.com/mc2-center/data-models/issues/new?assignees=aditigopalan&labels=bug&projects=&template=bug-report.md&title=%5Bbug%5D+
[Data Curator App (DCA)]: https://dca.app.sagebionetworks.org/
[Semantic Versioning]: https://semver.org/
[Release]: https://github.com/mc2-center/data-models/releases
[MKDocs]: https://www.mkdocs.org/
[mkdocs-table-reader-plugin]: https://timvink.github.io/mkdocs-table-reader-plugin/
[Material theme]: https://squidfunk.github.io/mkdocs-material/
[pandas]: https://pandas.pydata.org/docs/index.html
