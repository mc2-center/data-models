"""Publish a built knowledge-graph tree to its Synapse staging location.

Two named profiles, one per pipeline this repo builds:

  portal      The public CCKP portal KG (Dataset/Publication/Tool/Grant/
              EducationalResource) - `data/raw|harmonized|rdf/`. Public data,
              so no ACL check is required before publishing - this profile
              is not a "safe by construction" claim about the target, just a
              reflection of the fact the source data is meant to be public.
  mc2-assay   The MC2 assay-metadata KG (biospecimen/individual/model/
              sequencing/imaging, via `File View`) - `data/mc2_assay/raw|
              harmonized|rdf/`. This data may be access-restricted (it
              originates from per-file Synapse annotations that can require
              login), so this profile *requires* verifying the target's ACL
              is actually restricted before every upload - see
              `assert_target_is_restricted` below.

Neither tree is ever committed to GitHub (see .gitignore) - this script is
the intended publish path for both, to their own private-vs-public Synapse
container.

For a profile with `require_restricted_acl=True`, this script verifies the
target's *effective* ACL (its own, or its nearest ACL-owning ancestor's,
per Synapse's "benefactor" model) grants no read/download access to PUBLIC
or AUTHENTICATED_USERS - and refuses to upload if it does, rather than
silently trusting whatever synId it's pointed at. This check runs against
whatever entity actually governs permissions at upload time, not a
one-time assumption baked in when the target was first configured.

Mirrors the local `{data_dir}/{raw,harmonized,rdf}/` directory structure as
Synapse subfolders under the target container, and re-running this script
uploads new File *versions* in place (`store()` finds an existing File by
(parent, name) and versions it automatically - no extra logic needed here
for "upload as new versions on build").

A third, narrower mode - `--deploy-kg` (see `deploy_full_kg` below) -
uploads the single final merged graph, `data/rdf/cckp_kg_full.ttl`, plus its
small `data/rdf/manifest.ttl` PROV companion (see scripts/build_manifest.py),
directly into their own dedicated distribution folder (not nested under an
`rdf/` subfolder the way the two tree-mirroring profiles above are): other
systems pull straight from these files - manifest.ttl as the lightweight
new-version trigger, cckp_kg_full.ttl as the payload it points at - so this
gets its own simple, single-purpose publish path (`make deploy-kg`) rather
than being folded into the portal profile's directory-tree upload.
"""

import argparse
import asyncio
import os

import synapseclient
from synapseclient.api import get_children
from synapseclient.models import File, Folder
from synapseclient.operations import store

PUBLIC_PRINCIPAL_ID = 273949
AUTHENTICATED_USERS_PRINCIPAL_ID = 273948
OPEN_PRINCIPAL_IDS = {PUBLIC_PRINCIPAL_ID, AUTHENTICATED_USERS_PRINCIPAL_ID}
READ_LIKE_ACCESS_TYPES = {"READ", "DOWNLOAD"}
SUBDIRS = ["raw", "harmonized", "rdf"]

PROFILES = {
    "portal": {
        "target": "syn76958235",  # "portal-ttl-builds"
        "data_dir": "data",
        "require_restricted_acl": False,
    },
    "mc2-assay": {
        "target": "syn76957723",  # "data-ttl-builds" under "CCKP Knowledge Graph - Staging"
        "data_dir": "data/mc2_assay",
        "require_restricted_acl": True,
    },
}

# --deploy-kg's target/sources - see the module docstring's third paragraph.
FULL_KG_TARGET = "syn77443315"
FULL_KG_PATH = os.path.join("data", "rdf", "cckp_kg_full.ttl")
MANIFEST_PATH = os.path.join("data", "rdf", "manifest.ttl")


def effective_acl(syn, entity_id):
    """The ACL actually governing `entity_id` right now - its own if it has
    a local override, otherwise its nearest ACL-owning ancestor's (Synapse's
    "benefactor"). Resolved fresh on every call, not cached/assumed."""
    benefactor = syn.restGET(f"/entity/{entity_id}/benefactor")
    return syn.restGET(f"/entity/{benefactor['id']}/acl"), benefactor["id"]


def find_open_grants(acl):
    """resourceAccess entries that grant PUBLIC/AUTHENTICATED_USERS any
    read-like access - the thing that must be absent for a target used by
    the `require_restricted_acl` profile."""
    open_grants = []
    for entry in acl.get("resourceAccess", []):
        if entry.get("principalId") in OPEN_PRINCIPAL_IDS and \
                READ_LIKE_ACCESS_TYPES & set(entry.get("accessType", [])):
            open_grants.append(entry)
    return open_grants


def assert_target_is_restricted(syn, target_id):
    acl, benefactor_id = effective_acl(syn, target_id)
    open_grants = find_open_grants(acl)
    if open_grants:
        principal_names = {PUBLIC_PRINCIPAL_ID: "PUBLIC", AUTHENTICATED_USERS_PRINCIPAL_ID: "AUTHENTICATED_USERS"}
        grants_desc = ", ".join(
            f"{principal_names.get(g['principalId'], g['principalId'])}:{g['accessType']}" for g in open_grants
        )
        raise SystemExit(
            f"REFUSING TO PUBLISH: {target_id}'s effective ACL (governed by {benefactor_id}) grants "
            f"open read/download access ({grants_desc}) - this must be a private/team-restricted "
            f"location before any potentially access-restricted data is uploaded to it."
        )
    print(f"OK: {target_id}'s effective ACL (governed by {benefactor_id}) has no PUBLIC/AUTHENTICATED_USERS "
          f"read/download grant.")


async def _find_child_folder_id(parent_id, name, syn):
    async for child in get_children(parent=parent_id, include_types=["folder"], synapse_client=syn):
        if child["name"] == name:
            return child["id"]
    return None


def get_or_create_folder(syn, name, parent_id):
    existing_id = asyncio.run(_find_child_folder_id(parent_id, name, syn))
    if existing_id:
        return existing_id
    folder = store(Folder(name=name, parent_id=parent_id), synapse_client=syn)
    return folder.id


def upload_directory(syn, local_dir, target_folder_id):
    if not os.path.isdir(local_dir):
        print(f"  (skip: {local_dir} does not exist)")
        return []
    uploaded = []
    for filename in sorted(os.listdir(local_dir)):
        if filename.startswith("."):
            continue
        local_path = os.path.join(local_dir, filename)
        if not os.path.isfile(local_path):
            continue
        stored = store(File(path=local_path, parent_id=target_folder_id), synapse_client=syn)
        uploaded.append((filename, stored.id, stored.version_number))
        print(f"  {filename} -> {stored.id} (version {stored.version_number})")
    return uploaded


def deploy_full_kg(syn, path=FULL_KG_PATH, manifest_path=MANIFEST_PATH, target=FULL_KG_TARGET):
    """Upload the single final merged graph, plus its manifest.ttl PROV
    companion, directly into `target` as two File entities - see the module
    docstring's third paragraph for why this is a separate, narrower path
    from upload_directory()'s tree mirroring. manifest.ttl is optional (a
    pre-existing deployment predates it) - warn and skip rather than fail
    the whole deploy if it's missing."""
    if not os.path.isfile(path):
        raise SystemExit(f"{path} not found - run `make full-kg` first")
    stored = store(File(path=path, parent_id=target), synapse_client=syn)
    print(f"{path} -> {stored.id} (version {stored.version_number})")

    if os.path.isfile(manifest_path):
        stored_manifest = store(File(path=manifest_path, parent_id=target), synapse_client=syn)
        print(f"{manifest_path} -> {stored_manifest.id} (version {stored_manifest.version_number})")
    else:
        print(f"WARNING: {manifest_path} not found - skipping (run `make full-kg` to generate it)")
    return stored


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", choices=sorted(PROFILES), default=None,
                         help="Which pipeline's output to publish - sets --target/--data-dir/ACL-check "
                              "defaults below, each individually overridable. Mutually exclusive with "
                              "--deploy-kg.")
    parser.add_argument("--target", default=None,
                         help="Synapse container (Project/Folder) to publish into - defaults to the "
                              "profile's own designated staging location")
    parser.add_argument("--data-dir", default=None,
                         help="Local mirror of raw/harmonized/rdf - defaults to the profile's own tree")
    parser.add_argument("--skip-acl-check", action="store_true",
                         help="Danger: for a require_restricted_acl profile, upload without verifying "
                              "the target's ACL is restricted first")
    parser.add_argument("--deploy-kg", action="store_true",
                         help=f"Upload {FULL_KG_PATH} directly to its distribution folder "
                              f"({FULL_KG_TARGET}) instead of running a --profile publish")
    args = parser.parse_args()

    if args.deploy_kg == bool(args.profile):
        parser.error("pass exactly one of --profile or --deploy-kg")

    syn = synapseclient.Synapse()
    syn.login(silent=True)

    if args.deploy_kg:
        deploy_full_kg(syn)
        return

    profile = PROFILES[args.profile]
    target = args.target or profile["target"]
    data_dir = args.data_dir or profile["data_dir"]

    if not profile["require_restricted_acl"]:
        print(f"Profile '{args.profile}' publishes intentionally public data - no ACL check needed.")
    elif args.skip_acl_check:
        print("WARNING: --skip-acl-check passed - uploading without verifying the target is restricted.")
    else:
        assert_target_is_restricted(syn, target)

    for subdir in SUBDIRS:
        print(f"{subdir}/")
        folder_id = get_or_create_folder(syn, subdir, target)
        upload_directory(syn, os.path.join(data_dir, subdir), folder_id)


if __name__ == "__main__":
    main()
