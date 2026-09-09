# Prefix resolution report

Patched `schema/mc2_model.linkml.yaml` — added 50 prefixes derived from real `Ontology Url` data, plus 0 from a known-ontology fallback table.

## Added (derived from Ontology Url in the CV CSVs)

| Prefix | Base IRI | Rows matched |
|---|---|---|
| APOLLO_SV | `http://purl.obolibrary.org/obo/APOLLO_SV_` | 1/1 |
| BAO | `http://www.bioassayontology.org/bao#BAO_` | 23/23 |
| BTO | `http://purl.obolibrary.org/obo/BTO_` | 2/2 |
| CHEBI | `http://purl.obolibrary.org/obo/CHEBI_` | 1/1 |
| CHMO | `http://purl.obolibrary.org/obo/CHMO_` | 32/32 |
| CRO | `http://purl.obolibrary.org/obo/CRO_` | 1/1 |
| DCTERMS | `http://purl.org/dc/terms/` | 1/1 |
| DOID | `http://purl.obolibrary.org/obo/DOID_` | 1/1 |
| ECO | `http://purl.obolibrary.org/obo/ECO_` | 6/6 |
| EDAM | `http://edamontology.org/` | 516/519 ⚠️ 3 row(s) had an unrelated Ontology Url, excluded from the vote |
| EFO | `http://www.ebi.ac.uk/efo/EFO_` | 85/85 |
| EMAPA | `http://purl.obolibrary.org/obo/EMAPA_` | 1/1 |
| ENVO | `http://purl.obolibrary.org/obo/ENVO_` | 1/1 |
| ERO | `http://purl.obolibrary.org/obo/ERO_` | 8/8 |
| EVORAO | `https://w3id.org/evorao/` | 2/2 |
| FBbi | `http://purl.obolibrary.org/obo/FBbi_` | 4/4 |
| FBcv | `http://purl.obolibrary.org/obo/FBcv_` | 2/2 |
| FOODON | `http://purl.obolibrary.org/obo/FOODON_` | 1/1 |
| GENEPIO | `http://purl.obolibrary.org/obo/GENEPIO_` | 45/45 |
| GSSO | `http://purl.obolibrary.org/obo/GSSO_` | 2/2 |
| IAO | `http://purl.obolibrary.org/obo/IAO_` | 1/1 |
| MAMO | `http://purl.obolibrary.org/obo/MAMO_` | 1/1 |
| MESH | `http://id.nlm.nih.gov/mesh/` | 16/16 |
| MI | `http://purl.obolibrary.org/obo/MI_` | 2/2 |
| MMO | `http://purl.obolibrary.org/obo/MMO_` | 5/5 |
| MONDO | `http://purl.obolibrary.org/obo/MONDO_` | 1/1 |
| MSIO | `http://purl.obolibrary.org/obo/MSIO_` | 1/1 |
| MeSH | `http://id.nlm.nih.gov/mesh/` | 1/1 |
| NCBITaxon | `http://purl.obolibrary.org/obo/NCBITaxon_` | 6/6 |
| NCIT | `http://purl.obolibrary.org/obo/NCIT_` | 1089/1089 |
| OBCS | `http://purl.obolibrary.org/obo/OBCS_` | 1/1 |
| OBI | `http://purl.obolibrary.org/obo/OBI_` | 26/26 |
| OCCO | `http://purl.obolibrary.org/obo/OCCO_` | 1/1 |
| OMIT | `http://purl.obolibrary.org/obo/OMIT_` | 1/1 |
| PMID | `https://pubmed.ncbi.nlm.nih.gov/` | 33/34 ⚠️ 1 row(s) had an unrelated Ontology Url, excluded from the vote |
| PRIDE | `http://purl.obolibrary.org/obo/PRIDE_` | 2/2 |
| ROR | `https://ror.org/` | 270/270 |
| SIO | `http://semanticscience.org/resource/SIO_` | 2/2 |
| SNOMED | `http://snomed.info/id/` | 10/10 |
| SWO | `http://www.ebi.ac.uk/swo/SWO_` | 49/51 ⚠️ 2 row(s) had an unrelated Ontology Url, excluded from the vote |
| T4FS | `http://purl.obolibrary.org/obo/T4FS_` | 1/1 |
| UBERON | `http://purl.obolibrary.org/obo/UBERON_` | 1/1 |
| UMLS | `https://uts.nlm.nih.gov/uts/umls/concept/` | 1/2 ⚠️ 1 row(s) had an unrelated Ontology Url, excluded from the vote |
| UO | `http://purl.obolibrary.org/obo/UO_` | 5/5 |
| WIKIDATA | `https://www.wikidata.org/wiki/` | 1/1 |
| credit | `https://credit.niso.org/contributor-roles/` | 1/1 |
| mesh | `http://id.nlm.nih.gov/mesh/` | 7/7 |
| operation | `http://edamontology.org/operation_` | 1/1 |
| pmid | `https://pubmed.ncbi.nlm.nih.gov/` | 2/2 |
| schema | `https://schema.org/` | 5/5 |

## Added from known-ontology fallback (zero clean matches in source data)

| Prefix | Base IRI | Rows affected |
|---|---|---|

## STILL UNRESOLVED — needs manual review

- `SPDX` (327 row(s)) — no clean Ontology Url match and no fallback known.

## Already declared in the schema (left untouched)

- `DUO` -> `http://purl.obolibrary.org/obo/DUO_`

Note: case-variant prefixes (e.g. `mesh`/`MeSH`/`MESH`, `PMID`/`pmid`) are registered separately rather than merged, since LinkML/OWL CURIE prefixes are case-sensitive and `meaning:` values in the schema use the source CSVs' exact casing — merging would require rewriting every `meaning:` value, which this script deliberately does not do.
