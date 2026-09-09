import suggest_mappings


def test_choose_registry_institution_src_uses_ror():
    assert suggest_mappings.choose_registry("institution/institution_name.csv", []) == "ror"
    assert suggest_mappings.choose_registry("institution/institution_alias.csv", ["ncit"]) == "ror"


def test_choose_registry_spdx_hint_uses_spdx():
    assert suggest_mappings.choose_registry("tool/tool_license.csv", ["spdx"]) == "spdx"


def test_choose_registry_defaults_to_ols():
    assert suggest_mappings.choose_registry("shared/tumorType.csv", ["ncit"]) == "ols"
    assert suggest_mappings.choose_registry("shared/tumorType.csv", []) == "ols"


FAKE_SPDX_LICENSES = [
    {"licenseId": "MIT", "name": "MIT License"},
    {"licenseId": "Apache-2.0", "name": "Apache License 2.0"},
    {"licenseId": "GPL-3.0-only", "name": "GNU General Public License v3.0 only"},
]


def test_spdx_search_matches_on_name_or_id():
    hits = suggest_mappings.spdx_search("Apache 2.0", FAKE_SPDX_LICENSES, rows=1)
    assert len(hits) == 1
    assert hits[0]["curie"] == "SPDX:Apache-2.0"
    assert hits[0]["label"] == "Apache License 2.0"
    assert hits[0]["url"] == "https://spdx.org/licenses/Apache-2.0.html"
    assert hits[0]["source"] == "spdx"


def test_spdx_search_respects_rows_limit_and_ranks_by_similarity():
    hits = suggest_mappings.spdx_search("MIT", FAKE_SPDX_LICENSES, rows=2)
    assert len(hits) == 2
    assert hits[0]["curie"] == "SPDX:MIT"  # exact id match ranks first
    assert hits[0]["score"] == 1.0


def test_spdx_search_empty_license_list_returns_no_hits():
    assert suggest_mappings.spdx_search("MIT", [], rows=3) == []
