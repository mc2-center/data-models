Thank you for contributing to the MC2 Center data models project! This page
will guide you through our development workflow, data model release process, 
and how to update this docs site.

### Development process

To edit the data model, modify the project in your own fork or in a feature
branch, then issue a PR once you are ready for the MC2 Center internal data
team to review and discuss.

Generally, you should:

1. **(If you're a first time contributor)** Create your own copy of the 
    project by either cloning or forking the [data-models repo].

2. **Branch off `main` and develop your contribution(s)**. Ensure `main` is
   up-to-date in your local project before creating a new feature branch.

3. **Push changes** to the feature branch.  For best practice:
      - commit related changes together
      - commit often
      - avoid committing half-done work
      - write git messages that are brief enough to read but detailed
        enough to understand

4. **Open a PR to (upstream) `main` once ready.** Follow our PR template.
   Someone from the MC2 Center internal data team will then review, and either
   approve + merge or ask for futher discussion.

5. Once the changes are merged into `main`, a workflow will run to auto-generate
   a new `mc2.model.csv` and `mc2.model.jsonld` directly into the main project.

### Releasing a new version

This repository has a workflow in-place that will auto-update the next
release draft. Whenever a PR is merged, the workflow will run and add the
PR to the draft.

For versioning, this project adopts [Semantic Versioning] (SemVer), which the
workflow will also determine, based on the PR(s) included in the next planned
release. Specifically:

- any PR labeled with `major` will increment `x`
- any PR labeled with `minor` will increment `y`
- any PR labeled with `patch` will increment `z`

!!!note
    Only _one_ number will increment, where `x` will take precedence, followed
    by `y`, then finally `z`.

Publishing a release can only be done by the MC2 Center internal data team. To
release a new version, go to [Releases] > edit the release draft > **Publish release**.

### Updating documentation

The Data Models Explorer uses [MkDocs], [mkdocs-table-reader-plugin], and the
[Material theme] (as well as [pandas] for the `hooks.py` script).

- **Update the docs site:**

    The docs site is configured to rebuild automatically whenever a change
    is found in the `docs` folder, `mc2.model.csv`, or `mkdocs.yml`
    (the MkDocs configuration file). No further manual steps are required.

- **To add a new page:**

    Create a Markdown file in `docs`, then add the page to the `nav`
    setting in `mkdocs.yml`.

- **To test your changes:**

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

    Before you can test locally, you will first need to install the dependencies
    (ideally in a virtual environment), e.g.

    ```console
    conda create -n mc2-data-docs python=3.12
    conda activate mc2-data-docs
    pip install mkdocs mkdocs-material mkdocs-table-reader-plugin pandas
    ```

### I want to contribute something else...

If there is something you'd like to contribute that was not covered on this page,
please reach out to us on the [Discussions board]!

[data-models repo]: https://github.com/mc2-center/data-models
[Semantic Versioning]: https://semver.org/
[Releases]: https://github.com/mc2-center/data-models/releases
[MKDocs]: https://www.mkdocs.org/
[mkdocs-table-reader-plugin]: https://timvink.github.io/mkdocs-table-reader-plugin/
[Material theme]: https://squidfunk.github.io/mkdocs-material/
[pandas]: https://pandas.pydata.org/docs/index.html
[Discussion board]: https://github.com/mc2-center/data-models/discussions
