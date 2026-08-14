import sys
from collections import defaultdict
from pathlib import Path

import pytest

KG_PIPELINE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = KG_PIPELINE_DIR.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(KG_PIPELINE_DIR / "scripts"))

import build_triples  # noqa: E402
import harmonize  # noqa: E402

SCHEMA_PATH = str(KG_PIPELINE_DIR / "schema" / "cckp_portal.linkml.yaml")
MC2_SCHEMA_PATH = str(KG_PIPELINE_DIR / "schema" / "mc2_model.linkml.yaml")
MAPPING_PATH = str(REPO_ROOT / "modules" / "mapping.yaml")
MODULES_DIR = str(REPO_ROOT / "modules")

CLASS_ORDER = ["Dataset", "Publication", "Tool", "Grant", "EducationalResource"]


@pytest.fixture(scope="session")
def harmonized_dir(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("harmonized")
    malformed_rows = []
    field_lookups = harmonize.build_field_lookups(SCHEMA_PATH, MAPPING_PATH, MODULES_DIR, malformed_rows)

    unmapped_rows = []
    sssom_rows = defaultdict(set)
    for cls_name in CLASS_ORDER:
        raw_path = FIXTURES_DIR / f"{cls_name}.csv"
        out_path = out_dir / f"{cls_name}_harmonized.csv"
        harmonize.harmonize_table(cls_name, str(raw_path), str(out_path), field_lookups, unmapped_rows, sssom_rows)

    return {"dir": out_dir, "unmapped_rows": unmapped_rows, "malformed_rows": malformed_rows}


@pytest.fixture(scope="session")
def rdf_graphs(harmonized_dir):
    schema_meta = build_triples.get_schema_metadata(SCHEMA_PATH)
    mc2_prefixes = build_triples.load_prefixes(MC2_SCHEMA_PATH)
    join_indices = build_triples.build_join_indices(schema_meta, str(harmonized_dir["dir"]))

    graphs = {}
    for cls_name in CLASS_ORDER:
        graphs[cls_name] = build_triples.build_class_graph(
            cls_name, schema_meta, str(harmonized_dir["dir"]), join_indices, mc2_prefixes
        )
    return graphs
