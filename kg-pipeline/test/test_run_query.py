"""Tests for scripts/run_query.py - the exploratory/print-results runner
for queries/examples/*.rq (as opposed to validate_graph.py's --queries
pass/fail mode, which requires an `# expect: ...` header these files
deliberately omit). Uses the same test/fixtures/queries/*.rq and
query_checks_*.ttl fixtures test_query_checks.py already relies on, plus
a header-less fixture query to cover run_query.py's more lenient parser."""

from pathlib import Path

import rdflib
import run_query

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
QUERY_FIXTURES_DIR = FIXTURES_DIR / "queries"
REPO_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "queries" / "examples"


def _graph(*fixture_names):
    g = rdflib.Graph()
    for name in fixture_names:
        g.parse(str(FIXTURES_DIR / name), format="turtle")
    return g


def test_parse_query_file_loose_reads_header_and_body():
    name, description, sparql = run_query.parse_query_file_loose(str(QUERY_FIXTURES_DIR / "has_people.rq"))
    assert name == "has_people"
    assert description
    assert "ex:Person" in sparql


def test_parse_query_file_loose_falls_back_to_filename_with_no_header(tmp_path):
    headerless = tmp_path / "headerless.rq"
    headerless.write_text('PREFIX ex: <http://example.org/>\nSELECT ?p WHERE { ?p a ex:Person }\n')
    name, description, sparql = run_query.parse_query_file_loose(str(headerless))
    assert name == "headerless"
    assert description == ""
    assert "ex:Person" in sparql


def test_parse_query_file_loose_joins_multiline_description():
    # queries/examples/*.rq wrap their description across several plain
    # "# ..." comment lines following the "# description: " one.
    multiline = QUERY_FIXTURES_DIR.parent / "run_query_multiline_description.rq"
    multiline.write_text(
        "# name: multiline\n"
        "# description: First line of the description,\n"
        "#   continued onto a second line.\n"
        "SELECT ?p WHERE { ?p a <http://example.org/Person> }\n"
    )
    try:
        name, description, sparql = run_query.parse_query_file_loose(str(multiline))
        assert name == "multiline"
        assert description == "First line of the description, continued onto a second line."
    finally:
        multiline.unlink()


def test_run_and_print_reports_row_count_and_truncates_at_limit(capsys):
    g = _graph("query_checks_conforming.ttl")
    run_query.run_and_print(str(QUERY_FIXTURES_DIR / "has_people.rq"), g, limit=0)
    out = capsys.readouterr().out
    assert "-> 1 row(s)" in out
    assert "1 more row(s) not shown" in out


def test_repo_example_queries_all_parse_and_are_syntactically_valid_sparql():
    paths = sorted(REPO_EXAMPLES_DIR.glob("*.rq"))
    assert paths, "expected at least one queries/examples/*.rq file"
    empty_graph = rdflib.Graph()
    for path in paths:
        name, description, sparql = run_query.parse_query_file_loose(str(path))
        assert name and description
        empty_graph.query(sparql)  # raises if the SPARQL itself doesn't parse
