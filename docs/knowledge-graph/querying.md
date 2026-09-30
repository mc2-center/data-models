# Querying the graph

A cookbook of example SPARQL from `queries/examples/*.rq` — domain
questions, not the pass/fail checks in [Build and validation](build.md).
Run with `make query-examples`; each was re-run against the live build
(see the Overview's last verified build table for graph size).

**Datasets tagged with a specific ontology-resolved tumor type** (breast
carcinoma, `NCIT:C4872`), with their DOI — answered via the resolved term
rather than a free-text guess at how "breast cancer" is spelled in the
source data (174 rows):

```sparql
PREFIX cckp: <https://w3id.org/mc2-center/cckp-portal/>

SELECT ?dataset ?name ?doi WHERE {
  ?dataset a cckp:Dataset ;
           cckp:tumorTypeTerm <http://purl.obolibrary.org/obo/NCIT_C4872> ;
           cckp:datasetName ?name .
  OPTIONAL { ?dataset cckp:doi ?doi }
}
```

**Every Publication linked to a Dataset**, with the Publication's resolved
PubMed IRI — a real resolvable link instead of a bare numeric PubMed ID
(394 rows):

```sparql
PREFIX cckp: <https://w3id.org/mc2-center/cckp-portal/>

SELECT ?pub ?title ?pubmedIri ?dataset WHERE {
  ?pub a cckp:Publication ;
       cckp:datasetRef ?dataset ;
       cckp:publicationTitle ?title .
  OPTIONAL { ?pub cckp:pubMedIdIri ?pubmedIri }
}
```

**Per-SCDM-Program output rollup**, via the `cckp:consortiumRef`
federation edges `link_scdm.py` mints — a cross-silo question the base
portal tables alone can't answer (26 rows, one per Program × class with at
least one row):

```sparql
PREFIX cckp: <https://w3id.org/mc2-center/cckp-portal/>
PREFIX sagecdm: <https://sage-bionetworks.github.io/SageCommonDataModel/>

SELECT ?programName ?type (COUNT(?s) AS ?n) WHERE {
  ?program a sagecdm:Program ;
           sagecdm:name ?programName .
  ?s cckp:consortiumRef ?program ;
     a ?type .
  VALUES ?type { cckp:Dataset cckp:Publication cckp:Tool }
} GROUP BY ?programName ?type ORDER BY ?programName ?type
```

> A performance note: rdflib's engine handles several independent
> `OPTIONAL` blocks badly at this graph's size. The single-join-plus-
> `VALUES` form above runs in well under a second.
