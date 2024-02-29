---
name: ⭐ Release preparation
about: Prepare a release of the data model
title: '[release] CURRENT_SPRINT_MONTH'
labels: release
assignees: 
  - bankso
  - aditigopalan
  - vpchung

---

## Checklist
This checklist covers the post-curation steps that should be performed
when releasing a new data model version and syncing content to the Cancer
Complexity Knowledge Portal (CCKP).

> [!NOTE]
> Closing this ticket will create a new release!  Before closing, ensure
> that all relevent PRs have been merged into `main` and that each PR has
> been labeled with either `major`, `minor` or `patch`.

### Data model
- [ ] Add updates to a new branch in the data-models repo
- [ ] Make a PR to merge updates into main
- [ ] Verify CSV and JSON-LD were updated and added to branch or build and add manually
- [ ] Build manifest templates in xlsx format and store in "templates" folder
- [ ] Review and merge PR to main

### Data Curator Config
- [ ] Update data model and dca-template-config.json version number in data_curator_config/MC2/dca_config.json
- [ ] Copy templates to display in DCA from data-models/templates to data_curator_config/MC2/templates
- [ ] Ensure any templates that should be listed in the DCA are provided in data-models/dca_config/dca-template-config.json

### Synapse
- [ ] Process and upload metadata to grant-based Synapse projects (if needed)
- [ ] Validate and filter the union tables
- [ ] Upload CSVs of the final data to be synced
- [ ] Sync CSVs to the portal tables
 
## Additional comments

