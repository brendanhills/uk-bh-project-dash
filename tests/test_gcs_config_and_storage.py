import json
import os
from unittest.mock import patch
import pytest

from scripts.security_utils import (
    validate_google_sheet_url,
    validate_drive_folder_id,
)
from scripts.pipeline import (
    validate_and_normalize_config,
    pull_project_config,
    push_project_config,
    update_project_config,
    load_json_file,
    save_json_file,
)


def test_validate_google_sheet_url_accepts_valid_urls_and_ids():
    valid_id = "1s2fd-fK8E-N9tM2nF0n-a-bC3dE4fG5hI6jK7lM8nO"
    assert validate_google_sheet_url(valid_id) == f"https://docs.google.com/spreadsheets/d/{valid_id}/edit"

    full_url = f"https://docs.google.com/spreadsheets/d/{valid_id}/edit?gid=12345#gid=12345"
    normalized = validate_google_sheet_url(full_url)
    assert normalized == f"https://docs.google.com/spreadsheets/d/{valid_id}/edit#gid=12345"


def test_validate_google_sheet_url_rejects_ssrf_and_malicious_schemes():
    for bad_input in [
        "http://169.254.169.254/latest/meta-data/",
        "https://evil.example.com/spreadsheets/d/1s2fd-fK8E-N9tM2nF0n-a-bC3dE4fG5hI6jK7lM8nO/edit",
        "javascript:alert(1)",
        "file:///etc/passwd",
        "short_id",
    ]:
        with pytest.raises(ValueError):
            validate_google_sheet_url(bad_input)


def test_validate_drive_folder_id_accepts_valid_urls_and_ids():
    folder_id = "1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C"
    assert validate_drive_folder_id(folder_id) == folder_id
    assert (
        validate_drive_folder_id(f"https://drive.google.com/drive/folders/{folder_id}?usp=drive_link")
        == folder_id
    )


def test_validate_drive_folder_id_rejects_invalid_hosts():
    with pytest.raises(ValueError):
        validate_drive_folder_id("https://attacker.com/drive/folders/1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C")


def test_validate_and_normalize_config_normalizes_both_sheets():
    s1_id = "111111111111111111111111111111111"
    s2_id = "222222222222222222222222222222222"
    raw_cfg = {
        "project": {
            "links": {
                "primaryRegisterSheet": s1_id,
                "teamGoogleSheet": f"https://docs.google.com/spreadsheets/d/{s2_id}/edit#gid=99",
                "driveFolder": "https://drive.google.com/drive/folders/1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C",
            }
        }
    }
    norm = validate_and_normalize_config(raw_cfg)
    assert norm["project"]["links"]["primaryRegisterSheet"] == f"https://docs.google.com/spreadsheets/d/{s1_id}/edit"
    assert norm["project"]["links"]["teamGoogleSheet"] == f"https://docs.google.com/spreadsheets/d/{s2_id}/edit#gid=99"
    assert "sheets" not in norm["project"]["links"]
    assert "primarySheet" not in norm["project"]["links"]
    assert norm["project"]["links"]["driveFolder"] == "https://drive.google.com/drive/folders/1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C"
    assert norm["sources"]["googleDrive"]["folderId"] == "1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C"


def test_pull_and_push_project_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_BUCKET", "test-risk-data-bucket")
    s1_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz012345"
    s2_id = "1ZyXwVuTsRqPoNmLkJiHgFeDcBa543210"
    remote_cfg = {
        "project": {
            "name": "Project Monaro",
            "links": {
                "primaryRegisterSheet": f"https://docs.google.com/spreadsheets/d/{s1_id}/edit",
                "teamGoogleSheet": f"https://docs.google.com/spreadsheets/d/{s2_id}/edit",
            },
        }
    }

    with patch("scripts.gemini_generator.download_bytes_from_gcs") as mock_dl, patch(
        "scripts.gemini_generator.upload_bytes_to_gcs"
    ) as mock_ul:
        mock_dl.return_value = json.dumps(remote_cfg).encode("utf-8")
        mock_ul.return_value = "gs://test-risk-data-bucket/monaro/config.json"

        pulled = pull_project_config("monaro", data_root=str(tmp_path))
        assert pulled["bucket"] == "test-risk-data-bucket"
        local_cfg_file = tmp_path / "monaro" / "config.json"
        assert local_cfg_file.is_file()

        # Simulate user editing both sheets in vi and pushing back
        edited = json.loads(local_cfg_file.read_text(encoding="utf-8"))
        new_s2_id = "199999999999999999999999999999999"
        edited["project"]["links"]["teamGoogleSheet"] = new_s2_id
        local_cfg_file.write_text(json.dumps(edited), encoding="utf-8")

        pushed = push_project_config("monaro", data_root=str(tmp_path))
        assert (
            pushed["config"]["project"]["links"]["teamGoogleSheet"]
            == f"https://docs.google.com/spreadsheets/d/{new_s2_id}/edit"
        )
        assert "sheets" not in pushed["config"]["project"]["links"]
        assert mock_ul.called


def test_update_project_config_updates_both_sheets(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_BUCKET", "test-risk-data-bucket")
    s1_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz012345"
    s2_id = "1ZyXwVuTsRqPoNmLkJiHgFeDcBa543210"

    with patch("scripts.gemini_generator.download_bytes_from_gcs") as mock_dl, patch(
        "scripts.gemini_generator.upload_bytes_to_gcs"
    ) as mock_ul:
        mock_dl.return_value = json.dumps({"project": {"links": {}}}).encode("utf-8")
        mock_ul.return_value = "gs://test-risk-data-bucket/monaro/config.json"

        updated = update_project_config(
            project_name="monaro",
            primary_sheet=s1_id,
            team_google_sheet=s2_id,
            data_root=str(tmp_path),
        )
        assert updated["project"]["links"]["primaryRegisterSheet"] == f"https://docs.google.com/spreadsheets/d/{s1_id}/edit"
        assert updated["project"]["links"]["teamGoogleSheet"] == f"https://docs.google.com/spreadsheets/d/{s2_id}/edit"
        assert "sheets" not in updated["project"]["links"]
        assert mock_ul.called


def test_cloud_run_web_service_mounts_gcs_read_only():
    tf_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deploy",
        "terraform",
        "modules",
        "cloud_run",
        "main.tf",
    )
    with open(tf_path, "r", encoding="utf-8") as f:
        content = f.read()
    web_service_block = content.split('resource "google_cloud_run_v2_job" "sync_job"')[0]
    assert "read_only = true" in web_service_block
