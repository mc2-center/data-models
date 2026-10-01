"""Tests for validate_graph.py's --queries mode (queries/*.rq sanity
checks - see the module docstring's --queries section). The generic
engine (header parsing, expectation checking, running a query set against
a graph) is tested here against small test/fixtures/queries/*.rq files,
the same way test_shacl_validation.py tests shacl_validate() against tiny
fixtures rather than the real, live-built cckp_kg_full.ttl - the real
queries/*.rq files run against the real graph via `make full-kg`/`make
validate`, not in this fixture-based pytest suite. A lighter check here
confirms every real queries/*.rq file at least has a valid header and
syntactically valid SPARQL, without asserting anything about live data."""

import glob
from pathlib import Path

import pytest
import rdflib
import validate_graph

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
QUERY_FIXTURES_DIR = FIXTURES_DIR / "queries"
REPO_QUERIES_DIR = Path(__file__).resolve().parent.parent / "queries"


def test_parse_query_file_reads_header_and_body():
    name, expect, description, sparql = validate_graph.parse_query_file(str(QUERY_FIXTURES_DIR / "has_people.rq"))
    assert name == "has_people"
    assert expect == "min_count 1"
    assert description
    assert "ex:Person" in sparql


def test_parse_query_file_requires_name_and_expect_headers(tmp_path):
    bad = tmp_path / "bad.rq"
    bad.write_text("# description: missing name/expect headers\nSELECT * WHERE { ?s ?p ?o }")
    with pytest.raises(ValueError):
        validate_graph.parse_query_file(str(bad))


def test_check_expectation_empty():
    assert validate_graph.check_expectation("empty", 0) is True
    assert validate_graph.check_expectation("empty", 3) is False


def test_check_expectation_min_count():
    assert validate_graph.check_expectation("min_count 2", 2) is True
    assert validate_graph.check_expectation("min_count 2", 1) is False


def test_check_expectation_rejects_unknown_expectation():
    with pytest.raises(ValueError):
        validate_graph.check_expectation("bogus", 0)


def test_run_query_checks_conforming_fixture_all_pass():
    results = validate_graph.run_query_checks(
        str(QUERY_FIXTURES_DIR), [str(FIXTURES_DIR / "query_checks_conforming.ttl")]
    )
    assert len(results) == 2
    assert all(r["passed"] for r in results)


def test_run_query_checks_violating_fixture_reports_the_failure():
    results = validate_graph.run_query_checks(
        str(QUERY_FIXTURES_DIR), [str(FIXTURES_DIR / "query_checks_violating.ttl")]
    )
    by_name = {r["name"]: r for r in results}
    assert by_name["no_untyped_people"]["passed"] is False
    assert by_name["no_untyped_people"]["n_rows"] == 1
    # bob still satisfies the unrelated "at least one Person exists" floor check.
    assert by_name["has_people"]["passed"] is True


def test_print_query_check_results_returns_overall_pass_fail(capsys):
    conforming = validate_graph.run_query_checks(
        str(QUERY_FIXTURES_DIR), [str(FIXTURES_DIR / "query_checks_conforming.ttl")]
    )
    assert validate_graph.print_query_check_results(conforming) is True
    assert "2/2 query check(s) passed" in capsys.readouterr().out

    violating = validate_graph.run_query_checks(
        str(QUERY_FIXTURES_DIR), [str(FIXTURES_DIR / "query_checks_violating.ttl")]
    )
    assert validate_graph.print_query_check_results(violating) is False
    assert "1/2 query check(s) passed" in capsys.readouterr().out


def test_repo_queries_all_have_valid_headers_and_syntactically_valid_sparql():
    paths = sorted(glob.glob(str(REPO_QUERIES_DIR / "*.rq")))
    assert paths, "expected at least one queries/*.rq file in the repo"
    empty_graph = rdflib.Graph()
    for path in paths:
        name, expect, description, sparql = validate_graph.parse_query_file(path)
        assert name, f"{path}: missing '# name: ...'"
        assert description, f"{path}: missing '# description: ...'"
        validate_graph.check_expectation(expect, 0)  # raises on a malformed '# expect: ...'
        empty_graph.query(sparql)  # raises if the SPARQL itself doesn't parse
