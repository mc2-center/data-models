import suggest_mappings


def test_choose_registry_reads_dominant_prefix_not_src_path():
    # Driven by the CV's own existing curation, not a path heuristic - an
    # institution CV with no ROR-prefixed rows yet (e.g. a brand-new one)
    # gets no special treatment just because "institution" is in the path.
    assert suggest_mappings.choose_registry(["ror"], src="institution/institution_name.csv") == "ror"
    assert suggest_mappings.choose_registry(["ror"], src="grant/some_other_cv.csv") == "ror"
    assert suggest_mappings.choose_registry([], src="institution/institution_name.csv") == "ols"


def test_choose_registry_spdx_hint_uses_spdx():
    assert suggest_mappings.choose_registry(["spdx"], src="tool/tool_license.csv") == "spdx"


def test_choose_registry_defaults_to_ols_for_real_ols_ontologies():
    assert suggest_mappings.choose_registry(["ncit"], src="shared/tumorType.csv") == "ols"
    assert suggest_mappings.choose_registry([], src="shared/tumorType.csv") == "ols"


def test_choose_registry_warns_on_confirmed_non_ols_prefix_with_no_backend(capsys):
    # Simulate the exact SPDX-before-the-fix situation with a second
    # confirmed-non-OLS prefix that (deliberately) has no registered
    # backend, to prove the warning path actually fires instead of
    # silently defaulting to a doomed OLS search.
    suggest_mappings.NON_OLS_PREFIXES.add("madeupprefix")
    try:
        registry = suggest_mappings.choose_registry(["madeupprefix"], src="fake/fake_cv.csv")
    finally:
        suggest_mappings.NON_OLS_PREFIXES.discard("madeupprefix")
    assert registry == "ols"
    captured = capsys.readouterr()
    assert "fake/fake_cv.csv" in captured.out
    assert "madeupprefix" in captured.out
    assert "PREFIX_TO_REGISTRY" in captured.out


def test_choose_registry_no_warning_for_ordinary_unrecognized_prefix(capsys):
    # A prefix with no prior "confirmed not in OLS" signal is just an
    # ordinary OLS lookup, not a known-doomed one - no warning expected.
    suggest_mappings.choose_registry(["uberon"], src="shared/tissue.csv")
    assert capsys.readouterr().out == ""


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
