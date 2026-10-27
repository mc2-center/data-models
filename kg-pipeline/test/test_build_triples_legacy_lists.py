"""build_triples for the three slots made multivalued in the data model 14.x
cutover (Tool.license, EducationalResource.license, Grant.investigator): the
legacy comma text and the real "|" list must give the same triples."""

import pytest
import rdflib

from conftest import build_graph_from_rows

CCKP = rdflib.Namespace("https://w3id.org/mc2-center/cckp-portal/")
DATA = "https://w3id.org/mc2-center/cckp-portal/data/"
SPDX = "https://spdx.org/licenses/"


def _objects(g, cls_name, row_id, predicate):
    return set(g.objects(rdflib.URIRef(DATA + f"{cls_name}/{row_id}"), CCKP[predicate]))


@pytest.mark.parametrize("raw", ["GPL-3.0, MIT", "GPL-3.0|MIT"])
def test_tool_license_comma_and_pipe_forms_give_two_literals_and_terms(tmp_path, raw):
    g = build_graph_from_rows("Tool", [{"toolName": "T1", "license": raw}], tmp_path)
    assert _objects(g, "Tool", "T1", "license") == {rdflib.Literal("GPL-3.0"), rdflib.Literal("MIT")}
    assert _objects(g, "Tool", "T1", "licenseTerm") == {
        rdflib.URIRef(SPDX + "GPL-3.0.html"), rdflib.URIRef(SPDX + "MIT.html")}


@pytest.mark.parametrize("raw", ["GPL-3.0, MIT", "GPL-3.0|MIT"])
def test_educational_resource_license_comma_and_pipe_forms_give_two_literals_and_terms(tmp_path, raw):
    g = build_graph_from_rows("EducationalResource", [{"alias": "E1", "license": raw}], tmp_path)
    assert _objects(g, "EducationalResource", "E1", "license") == {
        rdflib.Literal("GPL-3.0"), rdflib.Literal("MIT")}
    assert _objects(g, "EducationalResource", "E1", "licenseTerm") == {
        rdflib.URIRef(SPDX + "GPL-3.0.html"), rdflib.URIRef(SPDX + "MIT.html")}


@pytest.mark.parametrize("raw, expected", [
    ("Amy Brock, Thomas E. Yankeelov", {"Amy Brock", "Thomas E. Yankeelov"}),
    ("PEROU, CHARLES M", {"PEROU, CHARLES M"}),  # one person, text unchanged
    ("PEROU, CHARLES M|Jane Doe", {"PEROU, CHARLES M", "Jane Doe"}),
])
def test_grant_investigator_literals(tmp_path, raw, expected):
    g = build_graph_from_rows("Grant", [{"grantId": "G1", "investigator": raw}], tmp_path)
    assert {str(o) for o in _objects(g, "Grant", "G1", "investigator")} == expected
