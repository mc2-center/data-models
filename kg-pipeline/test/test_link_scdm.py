import csv

import rdflib

import link_scdm

SAGECDM = rdflib.Namespace("https://sage-bionetworks.github.io/SageCommonDataModel/")
CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")


def write_tsv(path, header, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)


ORG_HEADER = ["institution_name", "scdm_organization_id", "scdm_name", "scdm_ror_id", "scdm_acronym"]
PROGRAM_HEADER = ["consortium_name", "scdm_program_id", "scdm_name", "scdm_description", "scdm_status",
                  "scdm_funding_source", "reviewed"]


def test_load_organization_crosswalk_indexes_by_name_and_acronym(tmp_path):
    path = tmp_path / "org.tsv"
    write_tsv(path, ORG_HEADER, [
        ["Sage Bionetworks", "org.sage-bionetworks", "Sage Bionetworks", "https://ror.org/049ncjx51", "Sage"],
    ])
    index = link_scdm.load_organization_crosswalk(str(path))
    assert index["sage bionetworks"][0] == "org.sage-bionetworks"
    assert index["sage"][0] == "org.sage-bionetworks"


def test_load_program_crosswalk_skips_unreviewed_rows(tmp_path):
    path = tmp_path / "program.tsv"
    write_tsv(path, PROGRAM_HEADER, [
        ["HTAN", "program.htan", "HTAN", "Human Tumor Atlas Network", "active", "", "true"],
        ["CSBC", "program.csbc", "CSBC", "", "", "", "false"],
    ])
    index = link_scdm.load_program_crosswalk(str(path))
    assert list(index) == ["htan"]
    assert index["htan"][0] == "program.htan"


def test_add_organizations_dedupes_by_org_id():
    g = rdflib.Graph()
    crosswalk = {
        "sage bionetworks": ("org.sage-bionetworks", "Sage Bionetworks", "https://ror.org/049ncjx51", "Sage"),
        "sage": ("org.sage-bionetworks", "Sage Bionetworks", "https://ror.org/049ncjx51", "Sage"),  # same org, alias key
    }
    n = link_scdm.add_organizations(g, crosswalk)
    assert n == 1
    subject = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Organization/org.sage-bionetworks")
    assert (subject, rdflib.RDF.type, SAGECDM.Organization) in g
    assert (subject, SAGECDM.name, rdflib.Literal("Sage Bionetworks")) in g
    assert (subject, SAGECDM.acronym, rdflib.Literal("Sage")) in g


def test_link_institutions_resolves_grant_institution_and_alias(tmp_path):
    harmonized_dir = tmp_path
    with open(harmonized_dir / "Grant_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["grantId", "grantInstitution", "institutionAlias"])
        writer.writerow(["syn1", "Sage Bionetworks", "Sage"])

    g = rdflib.Graph()
    crosswalk = {"sage bionetworks": ("org.sage-bionetworks", "Sage Bionetworks", "", ""),
                 "sage": ("org.sage-bionetworks", "Sage Bionetworks", "", "")}
    n_edges = link_scdm.link_institutions(g, str(harmonized_dir), crosswalk)
    # Same org resolved via both grantInstitution and institutionAlias - deduped to one edge.
    assert n_edges == 1
    subject = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Grant/syn1")
    target = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Organization/org.sage-bionetworks")
    assert (subject, CCKP.institutionRef, target) in g


def test_link_consortia_only_uses_reviewed_programs(tmp_path):
    harmonized_dir = tmp_path
    with open(harmonized_dir / "Grant_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["grantId", "consortium"])
        writer.writerow(["syn1", "HTAN"])
    for cls in ("Dataset", "Publication", "Tool"):
        with open(harmonized_dir / f"{cls}_harmonized.csv", "w", newline="") as f:
            csv.writer(f).writerow(["consortium"])  # empty tables

    g = rdflib.Graph()
    reviewed_crosswalk = {"htan": ("program.htan", "HTAN", "", "", "")}
    n_edges = link_scdm.link_consortia(g, str(harmonized_dir), reviewed_crosswalk)
    assert n_edges == 1

    unreviewed_crosswalk = {}  # load_program_crosswalk would have excluded HTAN here
    g2 = rdflib.Graph()
    assert link_scdm.link_consortia(g2, str(harmonized_dir), unreviewed_crosswalk) == 0


def test_link_investigators_mints_one_stub_per_distinct_name_and_flags_provisional(tmp_path):
    harmonized_dir = tmp_path
    with open(harmonized_dir / "Grant_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["grantId", "investigator"])
        writer.writerow(["syn1", "Jane Doe"])
        writer.writerow(["syn2", "Jane Doe"])  # same investigator, different grant
    with open(harmonized_dir / "EducationalResource_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["internalIdentifier", "alias", "contributors"])
        writer.writerow(["", "syn3", "John Smith|Jane Doe"])

    g = rdflib.Graph()
    n_persons, n_edges = link_scdm.link_investigators(g, str(harmonized_dir))
    assert n_persons == 2  # "Jane Doe" and "John Smith", deduped across both classes
    assert n_edges == 4  # syn1->Jane, syn2->Jane, syn3->John, syn3->Jane

    jane = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Person/investigator-jane-doe")
    assert (jane, rdflib.RDF.type, SAGECDM.Person) in g
    assert (jane, SAGECDM.display_name, rdflib.Literal("Jane Doe")) in g
    assert (jane, CCKP.provisional, rdflib.Literal(True)) in g


def test_build_scdm_links_end_to_end(tmp_path):
    harmonized_dir = tmp_path / "harmonized"
    harmonized_dir.mkdir()
    with open(harmonized_dir / "Grant_harmonized.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["grantId", "grantInstitution", "institutionAlias", "consortium", "investigator"])
        writer.writerow(["syn1", "Sage Bionetworks", "Sage", "HTAN", "Jane Doe"])
    for cls in ("Dataset", "Publication", "Tool", "EducationalResource"):
        with open(harmonized_dir / f"{cls}_harmonized.csv", "w", newline="") as f:
            csv.writer(f).writerow(["placeholder"])

    org_cw = tmp_path / "org.tsv"
    write_tsv(org_cw, ORG_HEADER, [
        ["Sage Bionetworks", "org.sage-bionetworks", "Sage Bionetworks", "https://ror.org/049ncjx51", "Sage"],
    ])
    program_cw = tmp_path / "program.tsv"
    write_tsv(program_cw, PROGRAM_HEADER, [
        ["HTAN", "program.htan", "HTAN", "Human Tumor Atlas Network", "active", "", "true"],
    ])

    g, stats = link_scdm.build_scdm_links(str(harmonized_dir), str(org_cw), str(program_cw))
    assert stats == {
        "organizations": 1, "programs": 1,
        "institution_edges": 1, "consortium_edges": 1,
        "person_stubs": 1, "investigator_edges": 1,
    }
    grant = rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Grant/syn1")
    assert (grant, CCKP.institutionRef,
            rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Organization/org.sage-bionetworks")) in g
    assert (grant, CCKP.consortiumRef,
            rdflib.URIRef("https://w3id.org/mc2-center/cckp-portal/data/Program/program.htan")) in g
