from pathlib import Path

import pytest
import rdflib
from rdflib.namespace import SH

import validate_graph

SHAPES_PATH = str(Path(__file__).resolve().parent.parent / "schema" / "cckp_portal.shacl.ttl")
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SHAPE_NS = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/shapes#")


def test_conforming_fixture_passes():
    assert validate_graph.shacl_validate(SHAPES_PATH, [str(FIXTURES_DIR / "shacl_conforming.ttl")]) is True


def test_violating_fixture_fails():
    assert validate_graph.shacl_validate(SHAPES_PATH, [str(FIXTURES_DIR / "shacl_violating.ttl")]) is False


# One fixture per *structural* (default sh:Violation severity) shape, each
# with exactly one violation. Checking sh:sourceShape (not just
# conforms=False) stops a fixture passing because some other shape fired.
# ToolShape/EducationalResourceShape/PublicationShape are sh:Warning now
# (literal data-quality checks, not structural graph damage - see
# cckp_portal.shacl.ttl §1) and are covered by
# test_warning_severity_shape_reports_but_does_not_fail below instead.
@pytest.mark.parametrize("fixture, shape", [
    ("shacl_violating_publication_id_iri.ttl", "PublicationIdIriShape"),
    ("shacl_violating_datasets_ref.ttl", "DatasetsRefShape"),
    ("shacl_violating_institution_ref.ttl", "InstitutionRefShape"),
    ("shacl_violating_consortium_ref.ttl", "ConsortiumRefShape"),
    ("shacl_violating_investigator_ref.ttl", "InvestigatorRefShape"),
    ("shacl_violating_contributor_ref.ttl", "ContributorRefShape"),
])
def test_each_shape_fires(fixture, shape):
    conforms, results_graph, _, _, shapes_graph = validate_graph.run_shacl(SHAPES_PATH, [str(FIXTURES_DIR / fixture)])
    assert conforms is False
    results = list(results_graph.subjects(rdflib.RDF.type, SH.ValidationResult))
    assert len(results) == 1
    # sh:sourceShape is the property shape (a blank node); walk back to the
    # named node shape that owns it.
    prop_shape = results_graph.value(results[0], SH.sourceShape)
    assert shapes_graph.value(predicate=SH.property, object=prop_shape) == SHAPE_NS[shape]
    assert validate_graph.shacl_validate(SHAPES_PATH, [str(FIXTURES_DIR / fixture)]) is False


# ToolShape.toolName, EducationalResourceShape.title, and
# PublicationShape.pubMedId are sh:severity sh:Warning: a fixture that only
# trips one of these should still be reported (grouped, with a count) but
# must not fail shacl_validate() / carry a non-conforming result, since
# nothing sh:Violation-level fired.
@pytest.mark.parametrize("fixture, shape", [
    ("shacl_violating_tool.ttl", "ToolShape"),
    ("shacl_violating_educational_resource.ttl", "EducationalResourceShape"),
    ("shacl_violating_publication.ttl", "PublicationShape"),
])
def test_warning_severity_shape_reports_but_does_not_fail(fixture, shape, capsys):
    conforms, results_graph, _, _, shapes_graph = validate_graph.run_shacl(SHAPES_PATH, [str(FIXTURES_DIR / fixture)])
    results = list(results_graph.subjects(rdflib.RDF.type, SH.ValidationResult))
    assert len(results) == 1
    assert results_graph.value(results[0], SH.resultSeverity) == SH.Warning
    prop_shape = results_graph.value(results[0], SH.sourceShape)
    assert shapes_graph.value(predicate=SH.property, object=prop_shape) == SHAPE_NS[shape]

    violations, warnings = validate_graph.partition_shacl_results(results_graph)
    assert violations == []
    assert len(warnings) == 1

    assert validate_graph.shacl_validate(SHAPES_PATH, [str(FIXTURES_DIR / fixture)]) is True
    out = capsys.readouterr().out
    assert "OK" in out
    assert "1 SHACL warning(s)" in out
