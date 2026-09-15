import os

import pytest

import upload_sagebrain_s3 as up


def _write(path, content="# fake turtle\n"):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


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


def test_upload_uploads_schema_rdf_provenance_then_manifest_last(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(up.FULL_KG_PATH)
    _write("schema/mc2_model.ttl")
    _write("schema/cckp_portal.ttl")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/usr/bin/aws")
    monkeypatch.setattr(up, "git_info", lambda: (None, None))

    calls = []
    monkeypatch.setattr(up.subprocess, "run", lambda cmd, check: calls.append(cmd))

    prefix = up.upload("some-bucket", "cckp", "us-east-1", date="2026-09-15", tmp_root=str(tmp_path))

    assert prefix == "s3://some-bucket/cckp/2026-09-15"
    # cmd shape: ["aws", "s3", "cp", src, dst, "--region", region]
    dests = [cmd[4] for cmd in calls]
    assert dests[0] == f"{prefix}/data/schema/cckp_portal.ttl"
    assert dests[1] == f"{prefix}/data/schema/mc2_model.ttl"
    assert dests[2] == f"{prefix}/data/rdf/cckp_kg_full.ttl"
    assert dests[3] == f"{prefix}/data/_provenance.ttl"
    assert dests[-1] == f"{prefix}/manifest.ttl"  # sentinel uploaded last

    assert os.path.isfile(tmp_path / "manifest.ttl")
    assert os.path.isfile(tmp_path / "_provenance.ttl")
    with open(tmp_path / "manifest.ttl") as f:
        manifest_content = f.read()
    with open(tmp_path / "_provenance.ttl") as f:
        provenance_content = f.read()
    assert manifest_content == provenance_content
    assert f"{prefix}/" in manifest_content  # void:dataDump points at this build's prefix


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
