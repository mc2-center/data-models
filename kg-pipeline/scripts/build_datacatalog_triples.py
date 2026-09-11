"""Stage: merge harmonized DataCatalog annotations onto the existing
cckp:Dataset subject - see plans/datacatalog_kg_integration.md for the full
design.

DataCatalog_id always equals the CCKP Dataset row's own datasetId (confirmed
on every entity that carries a real DataCatalog_id annotation) - these are
two metadata facets of the *same* real-world dataset, not two entities to
join. So this script does NOT mint a separate sagecdm-style node the way
scripts/link_scdm.py mints Organization/Program nodes; it adds triples
directly onto build_triples.py's own mint_iri("Dataset", datasetId) subject,
the same IRI schema/cckp_portal.linkml.yaml's own Dataset class pass already
uses in data/rdf/Dataset.ttl.

Predicate choice: this vocabulary was deliberately modeled on schema.org
Dataset/CreativeWork terms, so real https://schema.org/ properties are used
wherever one exists (SCHEMA_ORG_FIELDS below) rather than inventing a new
cckp:-namespaced predicate for a concept that already has a standard
equivalent - this also sidesteps any collision with cckp_portal.linkml.yaml's
own same-named-but-differently-sourced Dataset fields (cckp:description,
cckp:species, ...), since the two metadata layers live under different
namespaces on the same subject. Fields with no real schema.org equivalent
get a cckp:-namespaced predicate, same as everywhere else in this pipeline.
`doi` reuses build_triples.py's own external_iri()/doiIri templating
convention directly, rather than a schema:identifier predicate, for
consistency with how cckp_portal's own Dataset.doi is already handled.
CV-backed fields (license, measurementTechnique, species, funder, dataType,
accessType, downloadType, manifestation) additionally emit a resolved
cckp:{field}Term edge to the real ontology IRI, mirroring build_triples.py's
own {field}Term convention for its Dataset class.
"""

import argparse
import os
import sys

import rdflib
from rdflib.namespace import RDF, XSD

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_triples import (  # noqa: E402
    LIST_DELIMITER, expand_curie_or_url, external_iri, field_slug,
    get_schema_metadata, load_prefixes, mint_iri, read_harmonized, xsd_datatype,
)

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
SCHEMA = rdflib.Namespace("https://schema.org/")

# Real schema.org Dataset/CreativeWork properties - attribute name -> schema.org
# local name (identity mapping unless noted). See module docstring.
SCHEMA_ORG_FIELDS = {
    # Keyed by the DataCatalog class's own field name (dataCatalogLicense,
    # renamed from the model's generic "license" - see
    # extract_datacatalog.py's SCHEMA_FIELD_RENAMES) - not the schema.org
    # local name, which stays "license" on the right.
    "dataCatalogLicense": "license",
    "creator": "creator",
    "contributor": "contributor",
    "keywords": "keywords",
    "citation": "citation",
    "measurementTechnique": "measurementTechnique",
    "includedInDataCatalog": "includedInDataCatalog",
    "datePublished": "datePublished",
    "alternateName": "alternateName",
    "funder": "funder",
    "description": "description",
    "title": "name",
}


def build_datacatalog_graph(harmonized_dir, mc2_schema_path):
    schema_meta = get_schema_metadata(mc2_schema_path, class_order=["DataCatalog"])["DataCatalog"]
    mc2_prefixes = load_prefixes(mc2_schema_path)

    g = rdflib.Graph()
    g.bind("cckp", CCKP)
    g.bind("schema", SCHEMA)

    n_triples_by_predicate_kind = {"schema": 0, "cckp": 0, "term": 0, "doi": 0}

    for row in read_harmonized(harmonized_dir, "DataCatalog"):
        dataset_id = (row.get("DataCatalog_id") or "").strip()
        if not dataset_id:
            continue
        subject = mint_iri("Dataset", dataset_id)

        for field, meta in schema_meta.items():
            if field == "DataCatalog_id":
                continue
            raw_value = (row.get(field) or "").strip()
            values = [v.strip() for v in raw_value.split(LIST_DELIMITER)] if meta["multivalued"] else [raw_value]
            values = [v for v in values if v]
            if not values:
                continue

            if field == "doi":
                for v in values:
                    iri = external_iri("doi", v)
                    if iri:
                        g.add((subject, CCKP.doiIri, rdflib.URIRef(iri)))
                        n_triples_by_predicate_kind["doi"] += 1
                continue

            if field in SCHEMA_ORG_FIELDS:
                predicate = SCHEMA[SCHEMA_ORG_FIELDS[field]]
                kind = "schema"
            else:
                predicate = CCKP[field_slug(field)]
                kind = "cckp"

            datatype = xsd_datatype(meta["range"])
            for v in values:
                if datatype:
                    try:
                        g.add((subject, predicate, rdflib.Literal(v, datatype=datatype)))
                    except Exception:  # noqa: BLE001 - malformed source value, keep as plain literal
                        g.add((subject, predicate, rdflib.Literal(v)))
                else:
                    g.add((subject, predicate, rdflib.Literal(v)))
                n_triples_by_predicate_kind[kind] += 1

            if meta["mc2_enum"]:
                iri_cell = (row.get(f"{field}_ontology_iri") or "").strip()
                term_predicate = CCKP[field_slug(f"{field}Term")]
                for entry in iri_cell.split(LIST_DELIMITER):
                    entry = entry.strip()
                    if not entry:
                        continue
                    expanded = expand_curie_or_url(entry, mc2_prefixes)
                    if expanded:
                        g.add((subject, term_predicate, rdflib.URIRef(expanded)))
                        n_triples_by_predicate_kind["term"] += 1

    return g, n_triples_by_predicate_kind


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--harmonized-dir", default="data/harmonized")
    parser.add_argument("--mc2-schema", default="schema/mc2_model.linkml.yaml")
    parser.add_argument("--out", default="data/rdf/DataCatalog.ttl")
    args = parser.parse_args()

    g, stats = build_datacatalog_graph(args.harmonized_dir, args.mc2_schema)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    g.serialize(destination=args.out, format="turtle")
    print(f"{len(g)} triple(s) -> {args.out}")
    print(f"  schema.org: {stats['schema']}, cckp: {stats['cckp']}, "
          f"resolved-term: {stats['term']}, doiIri: {stats['doi']}")


if __name__ == "__main__":
    main()
