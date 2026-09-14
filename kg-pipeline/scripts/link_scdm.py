"""Stage: link the public CCKP-portal RDF graph to Sage Common Data Model
(SCDM) entities - see plans/scdm_alignment.md for the full design.

Reads the same harmonized CSVs build_triples.py builds cckp_kg.ttl from
(data/harmonized/<Class>_harmonized.csv) and mints/links:

  - sagecdm:Organization, one per row in the institution->SCDM crosswalk
    (scripts/crosswalk_scdm.py's --organization-out) - always minted, since
    a ROR id already *is* the organization's identity (no review gate).
    Grant.grantInstitution/institutionAlias values that resolve get a
    cckp:institutionRef edge to the matching Organization.
  - sagecdm:Program, one per **reviewed** row in the consortium->SCDM
    crosswalk (--program-out) - unreviewed rows (missing the
    human-curated description/status SCDM's Program class requires) are
    skipped, not asserted. Dataset/Publication/Tool/Grant.consortium
    values that resolve to a reviewed row get a cckp:consortiumRef edge.
  - Provisional sagecdm:Person stubs from Grant.investigator (scalar) and
    EducationalResource.contributors (free text, no controlled
    vocabulary) - one stub per distinct person, flagged cckp:provisional
    (same tier-3 discipline build_triples.py already uses for
    confirmed-unmappable CV terms), explicitly not claiming a resolved
    identity. "Distinct person" merges same first/last name entries whose
    middle name/initial matches or is missing from one of them (see
    _find_or_mint_person()'s docstring), and every display name is
    normalized to proper capitalization (see proper_case_name()) before
    being stored. Linked back via cckp:investigatorRef/cckp:contributorRef.
    Deliberately does NOT try to match an investigator/contributor string
    against any existing Person registry - this pipeline has no Person
    data in scope (see cckp_portal.linkml.yaml's own v1-scope note) and
    SCDM Person's own design principle is "capture, don't resolve."

All four edge predicates (institutionRef/consortiumRef/investigatorRef/
contributorRef) live in this pipeline's own `cckp:` namespace, not
sagebrain's or SCDM's - neither schema defines an inverse property for
"this CCKP row relates to that SCDM entity", so these are this pipeline's
own extensions, the same way cckp:doiIri/cckp:pubMedIdIri are.

Organization/Program instance IRIs reuse build_triples.py's own
DATA_NS-under-cckp-portal minting scheme (mint_iri("Organization", org_id))
rather than SCDM's own namespace - this pipeline doesn't own
sage-bionetworks.github.io and isn't claiming to be an authoritative SCDM
data source, only a derived/provisional one (tier 2 of the identifier
policy in README.md).

Output stays a separate file (data/rdf/scdm_links.ttl), not merged into
cckp_kg.ttl - matching how data/mc2_assay/rdf/sagebrain_links.ttl stays
separate from mc2_assay_kg.ttl rather than being folded in. Grant/Dataset/
Publication/Tool/EducationalResource are public CCKP portal data, not the
access-controlled MC2 assay-metadata domain scripts/link_sagebrain.py
operates in.

Known data-quality caveat, surfaced not hidden (confirmed against live
data, not assumed): Grant.investigator is genuinely a scalar STRING column
in the live Synapse table (per cckp_portal.linkml.yaml's own header
comment), but its raw values are sometimes several PI names crammed into
one comma-separated string (e.g. "Nevan Krogan, Trey Ideker, ..." for one
Grant row). split_person_names() below splits these into one Person stub
per real person, disambiguated from a single "Last, First MI" name (which
also contains a comma) by word count - see its own docstring for the
heuristic and its known false-positive case. EducationalResource.contributors
(a real `|`-delimited list) sometimes has a degree suffix like "MS"/"PhD"
show up as its own list entry, separate from the name it modifies - a raw
data-entry inconsistency in the live table, not a bug in this script's
delimiter handling, and not something a comma-based heuristic can fix (no
comma survives the upstream `|`-split by the time this script sees each
entry) - not silently cleaned up here.
"""

import argparse
import csv
import os
import sys

import rdflib
from rdflib.namespace import RDF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_triples import IDENTIFIER_FIELD, LIST_DELIMITER, mint_id, mint_iri, normalize, read_harmonized  # noqa: E402


def _has_identifier(cls_name, row):
    """False for a row whose declared identifier field is blank (e.g. the
    live Dataset table's placeholder/deleted-row remnants) - mirrors
    build_triples.py's build_class_graph() skip so this script doesn't
    crash on the same rows."""
    return cls_name not in IDENTIFIER_FIELD or (row.get(IDENTIFIER_FIELD[cls_name]) or "").strip()

SAGECDM = rdflib.Namespace("https://sage-bionetworks.github.io/SageCommonDataModel/")
CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")

# Only Grant carries grantInstitution/institutionAlias (confirmed against
# cckp_portal.linkml.yaml - Dataset/Publication/Tool/EducationalResource
# don't have an institution-shaped field of their own).
INSTITUTION_FIELDS = {"Grant": ("grantInstitution", "institutionAlias")}
# EducationalResource has no `consortium` field (confirmed absent from
# cckp_portal.linkml.yaml) - the other four all do.
CONSORTIUM_CLASSES = ("Dataset", "Publication", "Tool", "Grant")
# field -> multivalued? (Grant.investigator is scalar; contributors is a
# free-text list - both per cckp_portal.linkml.yaml).
INVESTIGATOR_FIELDS = {"Grant": ("investigator", False), "EducationalResource": ("contributors", True)}


def load_tsv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load_organization_crosswalk(path):
    """{normalized institution name or acronym: (org_id, name, ror_id, acronym)}."""
    by_key = {}
    for row in load_tsv(path):
        entry = (row["scdm_organization_id"], row["scdm_name"], row["scdm_ror_id"], row["scdm_acronym"])
        by_key[normalize(row["institution_name"])] = entry
        if row["scdm_acronym"]:
            by_key.setdefault(normalize(row["scdm_acronym"]), entry)
    return by_key


def load_program_crosswalk(path):
    """{normalized consortium name: (program_id, name, description, status, funding_source)} -
    reviewed rows only; an unreviewed row is skipped entirely, not just its missing fields."""
    by_key = {}
    for row in load_tsv(path):
        if (row.get("reviewed") or "").strip().lower() != "true":
            continue
        by_key[normalize(row["consortium_name"])] = (
            row["scdm_program_id"], row["scdm_name"], row["scdm_description"],
            row["scdm_status"], row["scdm_funding_source"],
        )
    return by_key


def split_values(raw_value, multivalued):
    values = raw_value.split(LIST_DELIMITER) if multivalued else [raw_value]
    return [v.strip() for v in values if v.strip()]


# Lowercase surname particles that can make a single last name span 2+
# words (e.g. "Van't Veer, Laura", "De La Cruz, Maria") - checked by exact
# match on the first word before the first comma, not by prefix, so a
# genuine first name that merely starts with the same letters (e.g.
# "Vanessa") isn't caught by mistake. Not exhaustive - a multi-word surname
# using some other, rarer particle still falls through to the word-count
# heuristic below.
SURNAME_PARTICLES = {
    "van", "van't", "vander", "vanden", "von", "der", "den", "de", "des",
    "du", "da", "di", "del", "della", "dos", "das", "la", "le", "mac", "mc",
    "st", "st.", "o'",
}


def split_person_names(raw_value):
    """Split a free-text scalar like Grant.investigator into individual
    person names.

    Two real formats show up in the live data, indistinguishable without a
    heuristic: multiple people already in "First [MI] Last" order, joined
    by commas (e.g. "Amy Brock, Thomas E. Yankeelov" - two people); or a
    single person in "Last, First MI" order (e.g. "Krogan, Nevan"). Told
    apart by the text before the first comma: a single word there reads as
    a last name (LAST, FIRST MI - one person, put back in First MI Last
    order below) rather than the first person's full name in a comma-joined
    list (two-plus words - FIRST MI LAST, FIRST MI LAST, ...) - unless that
    first word is a known surname particle (SURNAME_PARTICLES above), in
    which case the whole multi-word segment is still read as one last name
    (e.g. "Van't Veer, Laura" - one person, not two). Still a heuristic,
    not infallible: a multi-word surname using some other, rarer particle
    not in that list still gets treated as a list instead - a known,
    accepted false positive, not silently hidden.
    """
    raw_value = (raw_value or "").strip()
    if not raw_value:
        return []
    parts = [p.strip() for p in raw_value.split(",")]
    if len(parts) == 1:
        return [parts[0]] if parts[0] else []
    first_words = parts[0].split()
    starts_with_particle = bool(first_words) and first_words[0].casefold() in SURNAME_PARTICLES
    if len(first_words) < 2 or starts_with_particle:
        # LAST, FIRST MI - one person, not a comma-joined list of names.
        last = parts[0]
        first_mi = " ".join(p for p in parts[1:] if p)
        name = f"{first_mi} {last}".strip()
        return [name] if name else []
    return [p for p in parts if p]


def add_organizations(g, organization_crosswalk):
    seen = set()
    for org_id, name, ror_id, acronym in organization_crosswalk.values():
        if org_id in seen:
            continue
        seen.add(org_id)
        subject = mint_iri("Organization", org_id)
        g.add((subject, RDF.type, SAGECDM.Organization))
        g.add((subject, SAGECDM.name, rdflib.Literal(name)))
        if ror_id:
            g.add((subject, SAGECDM.ror_id, rdflib.URIRef(ror_id)))
        if acronym:
            g.add((subject, SAGECDM.acronym, rdflib.Literal(acronym)))
    return len(seen)


def add_programs(g, program_crosswalk):
    seen = set()
    for program_id, name, description, status, funding_source in program_crosswalk.values():
        if program_id in seen:
            continue
        seen.add(program_id)
        subject = mint_iri("Program", program_id)
        g.add((subject, RDF.type, SAGECDM.Program))
        g.add((subject, SAGECDM.name, rdflib.Literal(name)))
        if description:
            g.add((subject, SAGECDM.description, rdflib.Literal(description)))
        if status:
            g.add((subject, SAGECDM.status, rdflib.Literal(status)))
        if funding_source:
            g.add((subject, SAGECDM.funding_source, rdflib.Literal(funding_source)))
    return len(seen)


def link_institutions(g, harmonized_dir, organization_crosswalk):
    n_edges = 0
    for cls_name, fields in INSTITUTION_FIELDS.items():
        for row in read_harmonized(harmonized_dir, cls_name):
            if not _has_identifier(cls_name, row):
                continue
            subject = mint_iri(cls_name, mint_id(cls_name, row))
            targets = set()
            for field in fields:
                for value in split_values(row.get(field) or "", multivalued=True):
                    hit = organization_crosswalk.get(normalize(value))
                    if hit:
                        targets.add(hit[0])
            for org_id in targets:
                g.add((subject, CCKP.institutionRef, mint_iri("Organization", org_id)))
                n_edges += 1
    return n_edges


def link_consortia(g, harmonized_dir, program_crosswalk):
    n_edges = 0
    for cls_name in CONSORTIUM_CLASSES:
        for row in read_harmonized(harmonized_dir, cls_name):
            if not _has_identifier(cls_name, row):
                continue
            subject = mint_iri(cls_name, mint_id(cls_name, row))
            for value in split_values(row.get("consortium") or "", multivalued=True):
                hit = program_crosswalk.get(normalize(value))
                if hit:
                    g.add((subject, CCKP.consortiumRef, mint_iri("Program", hit[0])))
                    n_edges += 1
    return n_edges


def _parse_first_middle_last(display_name):
    """(first, middle, last), all casefolded - or None if display_name has
    fewer than 2 words and first/last can't be told apart (e.g. a mononym,
    or a non-person string like "MC2 Center" that slipped into a
    Person-shaped field). middle is "" when there isn't one; a trailing
    "." is stripped so an initial matches with or without it ("E."/"E")."""
    tokens = normalize(display_name).split(" ")
    if len(tokens) < 2:
        return None
    first, last = tokens[0], tokens[-1]
    middle = " ".join(tokens[1:-1]).rstrip(".")
    return first, middle, last


def _proper_case_word(word):
    """Title-case a single shouted ("EUN") or all-lowercase ("van") word.
    Left untouched if it's already mixed-case (e.g. "McDonald", an
    already-deliberate casing) or contains a digit (e.g. "MC2", not a name
    word at all) - str.title() would mangle either (McDonald -> Mcdonald,
    MC2 -> Mc2)."""
    if any(ch.isdigit() for ch in word):
        return word
    if word.isupper() or word.islower():
        return word.title()
    return word


def proper_case_name(display_name):
    """Normalize a name to proper capitalization for display (e.g. "EUN
    HYUN AHN" -> "Eun Hyun Ahn"). Word-by-word via _proper_case_word(), so
    already mixed-case or digit-bearing words are left alone. Still
    imperfect for a few specific particles - str.title() capitalizes after
    an apostrophe, so "van't" (correctly lowercase-t) comes out "Van'T" -
    a known, accepted limitation, not silently hidden."""
    return " ".join(_proper_case_word(w) for w in display_name.split())


def _mint_person(g, display_name):
    display_name = proper_case_name(display_name)
    person_iri = mint_iri("Person", "investigator-" + normalize(display_name).replace(" ", "-"))
    g.add((person_iri, RDF.type, SAGECDM.Person))
    g.add((person_iri, SAGECDM.display_name, rdflib.Literal(display_name)))
    g.add((person_iri, CCKP.provisional, rdflib.Literal(True)))
    return person_iri


def _find_or_mint_person(g, groups, ungrouped, display_name):
    """Return display_name's sagecdm:Person IRI, reusing an existing one
    where it's the same person under this module's name-matching rule:
    same first and last name, and a middle name/initial that either
    matches exactly (case/period-insensitive) or is missing from one of
    the two - e.g. "Thomas Yankeelov" and "Thomas E. Yankeelov" merge, but
    "Thomas E. Yankeelov" and "Thomas J. Yankeelov" don't. A missing-middle
    name that could equally belong to 2+ already-distinguished full names
    for the same first/last is left unmerged (and, if repeated, reuses its
    own single stub rather than re-guessing or re-minting) - ambiguous,
    not silently resolved either way.

    `groups` is {(first, last): [[middle, iri], ...]} for names successfully
    parsed by _parse_first_middle_last(); `ungrouped` is a plain
    normalize(display_name) -> iri map for names that aren't (both dicts
    mutated in place, shared across calls for one link_investigators() run).
    """
    parsed = _parse_first_middle_last(display_name)
    if parsed is None:
        key = normalize(display_name)
        if key not in ungrouped:
            ungrouped[key] = _mint_person(g, display_name)
        return ungrouped[key]

    first, middle, last = parsed
    bucket = groups.setdefault((first, last), [])
    matches = [entry for entry in bucket if entry[0] == middle or not entry[0] or not middle]
    if len(matches) == 1:
        entry = matches[0]
        if not entry[0] and middle:
            # Upgrade the stored middle (and display name) now that a
            # fuller version of the same person has shown up.
            entry[0] = middle
            g.set((entry[1], SAGECDM.display_name, rdflib.Literal(proper_case_name(display_name))))
        return entry[1]
    if len(matches) > 1:
        exact = [entry for entry in bucket if entry[0] == middle]
        if exact:
            return exact[0][1]
    person_iri = _mint_person(g, display_name)
    bucket.append([middle, person_iri])
    return person_iri


def link_investigators(g, harmonized_dir):
    """Mint one provisional sagecdm:Person stub per distinct person seen
    across Grant.investigator/EducationalResource.contributors (see
    _find_or_mint_person()'s docstring for how "distinct person" is
    decided), linking each source row to it via
    cckp:investigatorRef/contributorRef. Grant.investigator (scalar) is
    split into individual names via split_person_names()'s comma
    heuristic; EducationalResource.contributors (already a real
    `|`-delimited list) still uses the plain pipe split - see this
    module's docstring for both fields' caveats."""
    groups = {}
    ungrouped = {}
    n_edges = 0
    predicate_by_class = {"Grant": CCKP.investigatorRef, "EducationalResource": CCKP.contributorRef}
    for cls_name, (field, multivalued) in INVESTIGATOR_FIELDS.items():
        predicate = predicate_by_class[cls_name]
        for row in read_harmonized(harmonized_dir, cls_name):
            if not _has_identifier(cls_name, row):
                continue
            subject = mint_iri(cls_name, mint_id(cls_name, row))
            raw = row.get(field) or ""
            candidates = split_values(raw, multivalued) if multivalued else split_person_names(raw)
            for display_name in candidates:
                person_iri = _find_or_mint_person(g, groups, ungrouped, display_name)
                g.add((subject, predicate, person_iri))
                n_edges += 1
    n_persons = len(ungrouped) + sum(len(bucket) for bucket in groups.values())
    return n_persons, n_edges


def build_scdm_links(harmonized_dir, organization_crosswalk_path, program_crosswalk_path):
    organization_crosswalk = load_organization_crosswalk(organization_crosswalk_path)
    program_crosswalk = load_program_crosswalk(program_crosswalk_path)

    g = rdflib.Graph()
    g.bind("sagecdm", SAGECDM)
    g.bind("cckp", CCKP)

    n_orgs = add_organizations(g, organization_crosswalk)
    n_programs = add_programs(g, program_crosswalk)
    n_institution_edges = link_institutions(g, harmonized_dir, organization_crosswalk)
    n_consortium_edges = link_consortia(g, harmonized_dir, program_crosswalk)
    n_persons, n_investigator_edges = link_investigators(g, harmonized_dir)

    stats = {
        "organizations": n_orgs, "programs": n_programs,
        "institution_edges": n_institution_edges, "consortium_edges": n_consortium_edges,
        "person_stubs": n_persons, "investigator_edges": n_investigator_edges,
    }
    return g, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--harmonized-dir", default="data/harmonized")
    parser.add_argument("--organization-crosswalk", default="mappings/crosswalks/institution_to_scdm_organization.tsv")
    parser.add_argument("--program-crosswalk", default="mappings/crosswalks/consortium_to_scdm_program.tsv")
    parser.add_argument("--out", default="data/rdf/scdm_links.ttl")
    args = parser.parse_args()

    g, stats = build_scdm_links(args.harmonized_dir, args.organization_crosswalk, args.program_crosswalk)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    g.serialize(destination=args.out, format="turtle")
    print(f"{len(g)} triple(s) -> {args.out}")
    print(f"  {stats['organizations']} Organization(s), {stats['programs']} Program(s) "
          f"(reviewed rows only), {stats['person_stubs']} provisional Person stub(s)")
    print(f"  {stats['institution_edges']} institutionRef edge(s), "
          f"{stats['consortium_edges']} consortiumRef edge(s), "
          f"{stats['investigator_edges']} investigatorRef/contributorRef edge(s)")


if __name__ == "__main__":
    main()
