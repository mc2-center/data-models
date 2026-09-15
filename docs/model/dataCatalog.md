A **Data Catalog** entry captures the schema.org/Bioschemas-flavored dataset-cataloging metadata that Synapse's own Data Catalog feature stores directly on a Dataset entity — fields like `measurementTechnique`, `license`, `accessType`, `conditionsOfAccess`, `funder`, and `includedInDataCatalog`. It describes the same real-world dataset as a portal [Dataset](dataset.md) entry, but as a second, complementary metadata facet rather than a duplicate record: `DataCatalog_id` always equals the corresponding Dataset entry's own dataset ID.

This model applies only to datasets backed by a real Synapse Dataset entity (i.e., hosted or indexed directly on Synapse, as opposed to externally hosted datasets described only through a portal Dataset entry).

## Where Data Catalog Metadata Comes From

Unlike the other models on this site, Data Catalog fields are **not** submitted through this repo's manifest/template process. They are populated directly on the Synapse Dataset entity itself, through Synapse's own Data Catalog UI and metadata assistant, at the time the dataset is created or curated on Synapse.

The Cancer Complexity Knowledge Portal (CCKP)'s knowledge-graph pipeline reads these annotations directly from the Dataset entity and merges them onto the same subject as the entity's portal Dataset metadata, so the two facets end up describing one unified dataset in the CCKP knowledge graph.

## Who Maintains Data Catalog Annotations?

Whoever manages the corresponding Synapse Dataset entity — typically the same Principal Investigators, Data Managers, and Research Staff who host or index the dataset's files on Synapse. Keeping these annotations current on the Dataset entity (rather than in a separate submission) ensures the CCKP knowledge graph reflects accurate licensing, access, and provenance information for the dataset.

## Full Field Reference

Below is the full field reference table with attributes and their descriptions.

{{ read_csv('dataCatalog/reference.csv', keep_default_na=False) }}
