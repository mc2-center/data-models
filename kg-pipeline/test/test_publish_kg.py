import pytest

import publish_kg as publish_mod


def test_find_open_grants_flags_public_read():
    acl = {"resourceAccess": [{"principalId": publish_mod.PUBLIC_PRINCIPAL_ID, "accessType": ["READ", "DOWNLOAD"]}]}
    assert len(publish_mod.find_open_grants(acl)) == 1


def test_find_open_grants_flags_authenticated_users_download():
    acl = {"resourceAccess": [
        {"principalId": publish_mod.AUTHENTICATED_USERS_PRINCIPAL_ID, "accessType": ["DOWNLOAD"]},
    ]}
    assert len(publish_mod.find_open_grants(acl)) == 1


def test_find_open_grants_ignores_restricted_principal():
    acl = {"resourceAccess": [{"principalId": 3458480, "accessType": ["READ", "DOWNLOAD", "CHANGE_PERMISSIONS"]}]}
    assert publish_mod.find_open_grants(acl) == []


def test_find_open_grants_ignores_non_read_access_to_open_principals():
    # e.g. PUBLIC granted only CREATE somehow - not a read/download leak.
    acl = {"resourceAccess": [{"principalId": publish_mod.PUBLIC_PRINCIPAL_ID, "accessType": ["CREATE"]}]}
    assert publish_mod.find_open_grants(acl) == []


class _FakeSynapse:
    def __init__(self, benefactor_id, acl):
        self._benefactor_id = benefactor_id
        self._acl = acl

    def restGET(self, path):  # noqa: N802 - matches synapseclient's real method name
        if path.endswith("/benefactor"):
            return {"id": self._benefactor_id}
        assert path == f"/entity/{self._benefactor_id}/acl"
        return self._acl


def test_assert_target_is_restricted_passes_for_private_acl():
    syn = _FakeSynapse("syn_project", {"resourceAccess": [{"principalId": 3458480, "accessType": ["READ"]}]})
    publish_mod.assert_target_is_restricted(syn, "syn_folder")  # should not raise


def test_assert_target_is_restricted_refuses_for_public_acl():
    syn = _FakeSynapse("syn_project", {"resourceAccess": [
        {"principalId": publish_mod.PUBLIC_PRINCIPAL_ID, "accessType": ["READ", "DOWNLOAD"]},
    ]})
    with pytest.raises(SystemExit):
        publish_mod.assert_target_is_restricted(syn, "syn_folder")


def test_portal_profile_is_public_and_does_not_require_acl_check():
    profile = publish_mod.PROFILES["portal"]
    assert profile["require_restricted_acl"] is False
    assert profile["data_dir"] == "data"


def test_mc2_assay_profile_requires_acl_check():
    profile = publish_mod.PROFILES["mc2-assay"]
    assert profile["require_restricted_acl"] is True
    assert profile["data_dir"] == "data/mc2_assay"
