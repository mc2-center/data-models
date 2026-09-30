import os

import pytest
import rdflib

import build_manifest
import upload_sagebrain_s3 as up

CCKP = build_manifest.CCKP
VOID = rdflib.Namespace("http://rdfs.org/ns/void#")

# One real triple - not a comment-only placeholder. upload() parses every
# file it's about to place under data/ and refuses one that parses to zero
# triples, so a fixture has to actually carry a triple to
# stand in for a built schema/graph file.
MINIMAL_TURTLE = "<urn:example:s> <urn:example:p> <urn:example:o> .\n"


def _write(path, content=MINIMAL_TURTLE):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _rig_aws(monkeypatch, occupied=False, recursive_listing=None):
    """Fake aws_s3_ls/run_aws that never shell out for real, recording
    every call (in order) as (kind, ...) tuples for assertions.

    `occupied` controls the non-recursive `ls {prefix}/` guard-1 check.
    `run_aws("sync", ...)` walks its real local source directory (still on
    disk at call time, inside upload()'s own tempfile.TemporaryDirectory
    block) and remembers that file list, so the guard-3 `ls --recursive`
    call reports back exactly what was "uploaded" - unless
    `recursive_listing` is given to simulate a corrupted/stray load path
    instead.
    """
    calls = []
    state = {"listing": ""}

    def fake_ls(prefix, region, recursive=False):
        calls.append(("ls", recursive, prefix))
        if recursive:
            return recursive_listing if recursive_listing is not None else state["listing"]
        return "PRE data/\n" if occupied else ""

    def fake_run(*args, region):
        calls.append(("run", args))
        if args[0] == "sync":
            src_dir = args[1].rstrip("/")
            # Real `aws s3 ls --recursive` prints keys relative to the
            # bucket ("<portal>/<date>/data/..."), not to the sync source.
            key_root = args[2].split("/", 3)[3]
            keys = []
            for root, _, files in os.walk(src_dir):
                for name in files:
                    rel = os.path.relpath(os.path.join(root, name), src_dir)
                    keys.append(key_root + rel.replace(os.sep, "/"))
            state["listing"] = "\n".join(f"2026-09-29 00:00:00 100 {key}" for key in keys)

    monkeypatch.setattr(up, "aws_s3_ls", fake_ls)
    monkeypatch.setattr(up, "run_aws", fake_run)
    return calls


def test_upload_refuses_when_full_kg_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="run `make full-kg` first"):
        up.upload("some-bucket", "cckp", "us-east-1")


def test_upload_refuses_when_schema_dir_has_no_ttls(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    with pytest.raises(SystemExit, match="run `make schema` first"):
        up.upload("some-bucket", "cckp", "us-east-1")


def test_upload_refuses_when_aws_cli_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: None)
    with pytest.raises(SystemExit, match="aws.*not on PATH"):
        up.upload("some-bucket", "cckp", "us-east-1")


def test_upload_refuses_when_a_data_file_parses_to_zero_triples(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl", content="# just a comment, no triples\n")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    _rig_aws(monkeypatch)
    with pytest.raises(SystemExit, match="parsed to zero triples"):
        up.upload("some-bucket", "cckp", "us-east-1")


def test_upload_refuses_when_the_date_is_already_occupied(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    calls = _rig_aws(monkeypatch, occupied=True)
    with pytest.raises(SystemExit, match="already holds a snapshot"):
        up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))
    # Refused before ever staging/syncing anything.
    assert not any(call[0] == "run" for call in calls)


def test_upload_allow_overwrite_proceeds_despite_an_occupied_date(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    calls = _rig_aws(monkeypatch, occupied=True)

    prefix = up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path),
                        allow_overwrite=True)

    assert prefix == "s3://some-bucket/cckp/2026-09-15"
    # The occupied-date ls is skipped entirely when overwriting is allowed.
    assert not any(call[0] == "ls" and call[1] is False for call in calls)
    assert any(call[0] == "run" and call[1][0] == "cp" for call in calls)


def test_upload_dry_run_proceeds_regardless_of_an_occupied_date(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    calls = _rig_aws(monkeypatch, occupied=True)

    dry_run_dir = tmp_path / "mirror"
    prefix = up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path),
                        dry_run_dir=str(dry_run_dir))

    assert prefix == "s3://some-bucket/cckp/2026-09-15"
    assert calls == []  # dry run never calls aws at all, occupied or not


def test_upload_sync_targets_data_with_delete_then_cp_uploads_manifest_last(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    _write("schema/cckp_portal.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    calls = _rig_aws(monkeypatch)

    prefix = up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))

    assert prefix == "s3://some-bucket/cckp/2026-09-15"
    kinds = [call[0] for call in calls]
    # Call order: occupied-date ls, sync, post-sync ls --recursive, then cp
    # manifest.ttl last - matching nf-osi's own deposit-sagebrain.yml order.
    assert kinds == ["ls", "run", "ls", "run"]
    assert calls[0] == ("ls", False, f"{prefix}/")
    sync_call = calls[1][1]
    assert sync_call[0] == "sync"
    assert sync_call[1].endswith(os.sep + "data" + os.sep) or sync_call[1].endswith("/data/")
    assert sync_call[2] == f"{prefix}/data/"
    assert "--delete" in sync_call
    assert calls[2] == ("ls", True, f"{prefix}/data/")
    cp_call = calls[3][1]
    assert cp_call[0] == "cp"
    assert cp_call[2] == f"{prefix}/manifest.ttl"

    assert os.path.isfile(tmp_path / "manifest.ttl")
    assert os.path.isfile(tmp_path / "_provenance.ttl")
    with open(tmp_path / "manifest.ttl") as f:
        manifest_content = f.read()
    with open(tmp_path / "_provenance.ttl") as f:
        provenance_content = f.read()
    assert manifest_content == provenance_content
    assert f"{prefix}/data/" in manifest_content  # void:dataDump points at the load path, not the bare prefix


def test_upload_refuses_when_load_path_has_a_stray_non_ttl_key_and_never_uploads_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    calls = _rig_aws(monkeypatch, recursive_listing="2026-09-15 00:00:00 10 data/schema/README.md")

    with pytest.raises(SystemExit, match="non-Turtle objects"):
        up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))

    assert not any(call[0] == "run" and call[1][0] == "cp" for call in calls)


def test_upload_refuses_when_the_object_count_does_not_match_what_was_staged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    # Only one key reported back, but 3 files were staged (schema + rdf + _provenance.ttl).
    calls = _rig_aws(monkeypatch, recursive_listing="2026-09-15 00:00:00 10 cckp/2026-09-15/data/schema/mc2_model.ttl")

    with pytest.raises(SystemExit, match="doesn't match what was staged"):
        up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))

    assert not any(call[0] == "run" and call[1][0] == "cp" for call in calls)


def test_upload_refuses_when_the_load_path_is_empty_after_the_sync(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    calls = _rig_aws(monkeypatch, recursive_listing="")

    with pytest.raises(SystemExit, match="is empty after the upload"):
        up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))

    assert not any(call[0] == "run" and call[1][0] == "cp" for call in calls)


def test_upload_manifest_triple_count_matches_the_placed_data_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH, content="<urn:a> <urn:b> <urn:c> .\n<urn:a> <urn:b> <urn:d> .\n")
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    _rig_aws(monkeypatch)

    up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))

    g = rdflib.Graph()
    g.parse(tmp_path / "manifest.ttl", format="turtle")
    activity = next(g.subjects(rdflib.RDF.type, VOID.Dataset))
    # 1 triple in schema/mc2_model.ttl + 2 in cckp_kg_full.ttl = 3.
    assert (activity, VOID.triples, rdflib.Literal(3, datatype=rdflib.XSD.integer)) in g
    assert (activity, CCKP.snapshotDate, rdflib.Literal("2026-09-15", datatype=rdflib.XSD.date)) in g
    assert next(g.objects(activity, CCKP.depositedAtTime), None) is not None


def test_dry_run_mirrors_the_upload_layout_locally_without_aws(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))

    calls = []
    monkeypatch.setattr(up.subprocess, "run", lambda *a, **k: calls.append((a, k)))
    # aws doesn't need to be on PATH at all for a dry run.
    monkeypatch.setattr(up.shutil, "which", lambda _: None)

    dry_run_dir = tmp_path / "mirror"
    prefix = up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15",
                        tmp_root=str(tmp_path), dry_run_dir=str(dry_run_dir))

    assert calls == []  # never shells out to aws
    assert prefix == "s3://some-bucket/cckp/2026-09-15"
    mirrored = dry_run_dir / "cckp" / "2026-09-15"
    assert (mirrored / "data" / "schema" / "mc2_model.ttl").is_file()
    assert (mirrored / "data" / "rdf" / "cckp_kg_full.ttl").is_file()
    assert (mirrored / "data" / "_provenance.ttl").is_file()
    assert (mirrored / "manifest.ttl").is_file()


@pytest.mark.parametrize("returncode, stdout, stderr, expected", [
    (0, "PRE data/\n", "", "PRE data/\n"),
    # `aws s3 ls` on a prefix with no objects exits 1 and prints nothing -
    # that must read as "date is free", not crash the first deposit.
    (1, "", "", ""),
])
def test_aws_s3_ls_treats_an_empty_prefix_as_empty_not_an_error(monkeypatch, returncode, stdout, stderr, expected):
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], returncode, stdout, stderr))
    assert up.aws_s3_ls("s3://bucket/cckp/2026-09-29/", region="us-east-1") == expected


def test_aws_s3_ls_raises_on_a_real_failure(monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 254, "", "An error occurred (InvalidToken) when calling the ListObjectsV2 operation"))
    with pytest.raises(SystemExit, match=r"failed \(exit 254\): An error occurred \(InvalidToken\)"):
        up.aws_s3_ls("s3://bucket/cckp/2026-09-29/", region="us-east-1")


def test_upload_void_triples_counts_distinct_triples_across_overlapping_files(tmp_path, monkeypatch):
    # cckp_kg_full.ttl already merges the schema, so a schema triple appears
    # in two files - Neptune stores it once, and void:triples must too.
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH, content=MINIMAL_TURTLE + "<urn:a> <urn:b> <urn:c> .\n")
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    _rig_aws(monkeypatch)

    up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))

    g = rdflib.Graph()
    g.parse(tmp_path / "manifest.ttl", format="turtle")
    assert next(g.objects(None, VOID.triples)) == rdflib.Literal(2, datatype=rdflib.XSD.integer)


@pytest.mark.parametrize("bad_date", ["2026-9-15", "20260915", "2026-02-30", "latest"])
def test_upload_refuses_a_malformed_date_before_touching_s3(tmp_path, monkeypatch, bad_date):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    calls = _rig_aws(monkeypatch)

    with pytest.raises(SystemExit, match="YYYY-MM-DD"):
        up.upload("some-bucket", "cckp", "us-east-1", date=bad_date, tmp_root=str(tmp_path))
    assert calls == []


def test_upload_refuses_a_stray_ttl_that_balances_a_missing_staged_file(tmp_path, monkeypatch):
    # Same object count as staged, but one expected key is missing and an
    # unexpected .ttl took its place - a count-only check would pass this.
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    listing = "\n".join(f"2026-09-15 00:00:00 10 cckp/2026-09-15/data/{key}" for key in
                        ["schema/mc2_model.ttl", "rdf/cckp_kg_full.ttl", "rdf/stale_from_last_run.ttl"])
    calls = _rig_aws(monkeypatch, recursive_listing=listing)

    with pytest.raises(SystemExit, match="unexpected: \\['cckp/2026-09-15/data/rdf/stale_from_last_run.ttl'\\]"):
        up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))
    assert not any(call[0] == "run" and call[1][0] == "cp" for call in calls)


def test_dry_run_clears_files_left_by_an_earlier_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))
    mirror = tmp_path / "mirror"
    stale = mirror / "cckp" / "2026-09-15" / "data" / "rdf" / "dropped_since.ttl"
    _write(str(stale))

    up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path),
              dry_run_dir=str(mirror))

    assert not stale.exists()
    assert (mirror / "cckp" / "2026-09-15" / "data" / "rdf" / "cckp_kg_full.ttl").exists()


def test_aws_s3_ls_raises_on_exit_1_with_an_error_message(monkeypatch):
    # Exit 1 alone means "nothing under the prefix"; exit 1 *with* stderr
    # is a real failure and must not read as a free date.
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 1, "", "Could not connect to the endpoint URL"))
    with pytest.raises(SystemExit, match="Could not connect to the endpoint URL"):
        up.aws_s3_ls("s3://bucket/cckp/2026-09-29/", region="us-east-1")
