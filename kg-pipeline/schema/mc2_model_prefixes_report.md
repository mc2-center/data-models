# Prefix resolution report

Patched `kg-pipeline/schema/mc2_model.linkml.yaml` — added 38 prefixes derived from real `Ontology Url` data, plus 4 from a known-ontology fallback table.

## Added (derived from Ontology Url in the CV CSVs)

| Prefix | Base IRI | Rows matched |
|---|---|---|
| BAO | `http://www.bioassayontology.org/bao#BAO_` | 21/23 ⚠️ 2 row(s) had an unrelated Ontology Url, excluded from the vote |
| BTO | `http://purl.obolibrary.org/obo/BTO_` | 2/2 |
| CHEBI | `http://purl.obolibrary.org/obo/CHEBI_` | 1/1 |
| CHMO | `http://purl.obolibrary.org/obo/CHMO_` | 29/32 ⚠️ 3 row(s) had an unrelated Ontology Url, excluded from the vote |
| DOID | `http://purl.obolibrary.org/obo/DOID_` | 1/1 |
| ECO | `http://purl.obolibrary.org/obo/ECO_` | 2/6 ⚠️ 4 row(s) had an unrelated Ontology Url, excluded from the vote |
| EDAM | `http://edamontology.org/` | 135/139 ⚠️ 4 row(s) had an unrelated Ontology Url, excluded from the vote |
| EFO | `http://www.ebi.ac.uk/efo/EFO_` | 77/85 ⚠️ 8 row(s) had an unrelated Ontology Url, excluded from the vote |
| EMAPA | `http://purl.obolibrary.org/obo/EMAPA_` | 1/1 |
| ERO | `http://purl.obolibrary.org/obo/ERO_` | 7/8 ⚠️ 1 row(s) had an unrelated Ontology Url, excluded from the vote |
| EVORAO | `https://w3id.org/evorao/` | 2/2 |
| FBbi | `http://purl.obolibrary.org/obo/FBbi_` | 2/4 ⚠️ 2 row(s) had an unrelated Ontology Url, excluded from the vote |
| FBcv | `http://purl.obolibrary.org/obo/FBcv_` | 2/2 |
| FOODON | `http://purl.obolibrary.org/obo/FOODON_` | 1/1 |
| GENEPIO | `http://purl.obolibrary.org/obo/GENEPIO_` | 45/45 |
| GSSO | `http://purl.obolibrary.org/obo/GSSO_` | 1/1 |
| MESH | `http://id.nlm.nih.gov/mesh/` | 15/15 |
| MI | `http://purl.obolibrary.org/obo/MI_` | 1/2 ⚠️ 1 row(s) had an unrelated Ontology Url, excluded from the vote |
| MMO | `http://purl.obolibrary.org/obo/MMO_` | 4/4 |
| MONDO | `http://purl.obolibrary.org/obo/MONDO_` | 1/1 |
| MSIO | `http://purl.obolibrary.org/obo/MSIO_` | 1/1 |
| MeSH | `http://id.nlm.nih.gov/mesh/` | 1/1 |
| NCBITaxon | `http://purl.obolibrary.org/obo/NCBITaxon_` | 3/3 |
| NCIT | `http://purl.obolibrary.org/obo/NCIT_` | 793/926 ⚠️ 133 row(s) had an unrelated Ontology Url, excluded from the vote |
| OBI | `http://purl.obolibrary.org/obo/OBI_` | 20/24 ⚠️ 4 row(s) had an unrelated Ontology Url, excluded from the vote |
| OCCO | `http://purl.obolibrary.org/obo/OCCO_` | 1/1 |
| OMIT | `http://purl.obolibrary.org/obo/OMIT_` | 1/1 |
| PRIDE | `http://purl.obolibrary.org/obo/PRIDE_` | 2/2 |
| SIO | `http://semanticscience.org/resource/SIO_` | 1/1 |
| SNOMED | `http://snomed.info/id/` | 7/9 ⚠️ 2 row(s) had an unrelated Ontology Url, excluded from the vote |
| SWO | `http://www.ebi.ac.uk/swo/SWO_` | 28/30 ⚠️ 2 row(s) had an unrelated Ontology Url, excluded from the vote |
| T4FS | `http://purl.obolibrary.org/obo/T4FS_` | 1/1 |
| UBERON | `http://purl.obolibrary.org/obo/UBERON_` | 3/3 |
| UMLS | `http://purl.obolibrary.org/obo/UMLS_` | 1/1 |
| UO | `http://purl.obolibrary.org/obo/UO_` | 5/5 |
| mesh | `http://id.nlm.nih.gov/mesh/` | 4/7 ⚠️ 3 row(s) had an unrelated Ontology Url, excluded from the vote |
| operation | `http://edamontology.org/operation_` | 1/1 |
| schema | `https://schema.org/` | 1/1 |

## Added from known-ontology fallback (zero clean matches in source data)

| Prefix | Base IRI | Rows affected |
|---|---|---|
| ENVO | `http://purl.obolibrary.org/obo/ENVO_` | 1 |
| OBCS | `http://purl.obolibrary.org/obo/OBCS_` | 1 |
| PMID | `https://pubmed.ncbi.nlm.nih.gov/` | 32 |
| pmid | `https://pubmed.ncbi.nlm.nih.gov/` | 2 |

## Already declared in the schema (left untouched)

- `DUO` -> `http://purl.obolibrary.org/obo/DUO_`

Note: case-variant prefixes (e.g. `mesh`/`MeSH`/`MESH`, `PMID`/`pmid`) are registered separately rather than merged, since LinkML/OWL CURIE prefixes are case-sensitive and `meaning:` values in the schema use the source CSVs' exact casing — merging would require rewriting every `meaning:` value, which this script deliberately does not do.
