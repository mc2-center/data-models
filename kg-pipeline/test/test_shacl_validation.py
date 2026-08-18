from pathlib import Path

import validate_graph

SHAPES_PATH = str(Path(__file__).resolve().parent.parent / "schema" / "cckp_portal.shacl.ttl")
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_conforming_fixture_passes():
    assert validate_graph.shacl_validate(SHAPES_PATH, [str(FIXTURES_DIR / "shacl_conforming.ttl")]) is True


def test_violating_fixture_fails():
    assert validate_graph.shacl_validate(SHAPES_PATH, [str(FIXTURES_DIR / "shacl_violating.ttl")]) is False
