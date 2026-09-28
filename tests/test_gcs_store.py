"""Unit tests for the centralized in-memory GCS ProjectDataStore (scripts/gcs_store.py)."""

import json
import time
from typing import Any, Dict, Optional
import pytest

from scripts.gcs_store import ProjectDataStore, get_project_data_store


class MockGCSBlob:
    """Fake GCS Blob for testing ProjectDataStore without network round-trips."""

    def __init__(self, name: str, payload: Optional[bytes] = None):
        self.name = name
        self._payload = payload
        self.download_calls = 0

    def exists(self, *args, **kwargs) -> bool:
        return self._payload is not None

    def download_as_bytes(self, *args, **kwargs) -> bytes:
        self.download_calls += 1
        if self._payload is None:
            raise FileNotFoundError(f"Blob {self.name} not found in mock bucket")
        return self._payload


class MockGCSBucket:
    """Fake GCS Bucket holding blobs in memory."""

    def __init__(self, name: str, blobs: Dict[str, bytes]):
        self.name = name
        self.blobs: Dict[str, MockGCSBlob] = {
            k: MockGCSBlob(k, v) for k, v in blobs.items()
        }

    def blob(self, blob_name: str) -> MockGCSBlob:
        if blob_name not in self.blobs:
            self.blobs[blob_name] = MockGCSBlob(blob_name, None)
        return self.blobs[blob_name]


class MockGCSClient:
    """Fake google.cloud.storage.Client for hermetic unit testing."""

    def __init__(self, buckets: Dict[str, MockGCSBucket]):
        self._buckets = buckets
        self.bucket_calls = 0

    def bucket(self, bucket_name: str) -> MockGCSBucket:
        self.bucket_calls += 1
        if bucket_name not in self._buckets:
            raise PermissionError(f"Bucket '{bucket_name}' is inaccessible or missing")
        return self._buckets[bucket_name]


@pytest.fixture
def mock_monaro_blobs() -> Dict[str, bytes]:
    """Provides mock JSON and MP3 payloads for project 'monaro' in GCS."""
    return {
        "monaro/config.json": json.dumps({
            "project": {"name": "Monaro", "slug": "monaro", "title": "Monaro Risk Platform"}
        }).encode("utf-8"),
        "monaro/snapshots.json": json.dumps({
            "current_week": "w33",
            "snapshots": {
                "w33": {
                    "week": "Week 33",
                    "date": "18 Sep 2026",
                    "overallStatus": "🟢 GREEN"
                }
            }
        }).encode("utf-8"),
        "monaro/risks.json": json.dumps([
            {"id": "R-01", "title": "Supply Chain Delay", "residualRiskScore": 8}
        ]).encode("utf-8"),
        "monaro/issues.json": json.dumps([
            {"id": "I-01", "title": "Firewall Port Approval"}
        ]).encode("utf-8"),
        "monaro/driver_tree.json": json.dumps({"root": "Monaro Program"}).encode("utf-8"),
        "monaro/knowledge.json": json.dumps({"sources": [{"id": "nb-1", "title": "Blueprint"}]}).encode("utf-8"),
        "monaro/podcast_w33.mp3": b"ID3_MOCK_MONARO_PODCAST_MP3_STREAM",
    }


def test_singleton_initialization_and_connection_pooling():
    """Verifies get_project_data_store() returns a thread-safe singleton instance with pooled session."""
    store1 = get_project_data_store()
    store2 = get_project_data_store()
    assert store1 is store2
    assert store1.http_session is not None


def test_prewarm_projects_and_submillisecond_get_json(mock_monaro_blobs: Dict[str, bytes]):
    """Verifies startup hydration loads GCS datasets into RAM and serves get_json() in < 0.1ms."""
    bucket = MockGCSBucket("monaro-risk-dev-data", mock_monaro_blobs)
    client = MockGCSClient({"monaro-risk-dev-data": bucket})

    store = ProjectDataStore(
        bucket_name="monaro-risk-dev-data",
        storage_client=client,
        allow_local_fallback=False,
    )
    summary = store.prewarm_projects(projects=["monaro", "sample"], bucket_name="monaro-risk-dev-data")

    assert summary["warm"] is True
    assert "monaro" in summary["loaded_projects"]
    assert "sample" in summary["loaded_projects"]
    assert summary["project_counts"]["monaro"] >= 6

    # Measure get_json latency from warm cache (must be < 0.1ms average, zero extra GCS downloads)
    initial_downloads = bucket.blobs["monaro/snapshots.json"].download_calls
    assert initial_downloads == 1

    start = time.perf_counter()
    iterations = 100
    for _ in range(iterations):
        snaps = store.get_json("monaro", "snapshots.json")
    elapsed_ms_per_call = ((time.perf_counter() - start) * 1000.0) / iterations

    assert snaps is not None
    assert snaps["current_week"] == "w33"
    assert elapsed_ms_per_call < 0.1, f"Expected < 0.1ms cache read, got {elapsed_ms_per_call:.4f}ms"
    assert bucket.blobs["monaro/snapshots.json"].download_calls == initial_downloads


def test_cache_miss_fetches_from_gcs_and_caches_subsequent_reads(mock_monaro_blobs: Dict[str, bytes]):
    """Verifies ad-hoc cache misses fetch from GCS once and populate the in-memory cache."""
    mock_monaro_blobs["monaro/extra_audit.json"] = json.dumps({"audit": "passed"}).encode("utf-8")
    bucket = MockGCSBucket("monaro-risk-dev-data", mock_monaro_blobs)
    client = MockGCSClient({"monaro-risk-dev-data": bucket})

    store = ProjectDataStore(
        bucket_name="monaro-risk-dev-data",
        storage_client=client,
        allow_local_fallback=False,
    )

    # Not pre-warmed yet -> cache miss fetches from GCS
    data1 = store.get_json("monaro", "extra_audit.json")
    assert data1 == {"audit": "passed"}
    assert bucket.blobs["monaro/extra_audit.json"].download_calls == 1

    # Second read -> served from memory cache without hitting GCS
    data2 = store.get_json("monaro", "extra_audit.json")
    assert data2 == {"audit": "passed"}
    assert bucket.blobs["monaro/extra_audit.json"].download_calls == 1


def test_reload_project_invalidates_and_refreshes_ram_cache(mock_monaro_blobs: Dict[str, bytes]):
    """Verifies reload_project() evicts stale entries and pulls updated blobs from GCS."""
    bucket = MockGCSBucket("monaro-risk-dev-data", mock_monaro_blobs)
    client = MockGCSClient({"monaro-risk-dev-data": bucket})

    store = ProjectDataStore(
        bucket_name="monaro-risk-dev-data",
        storage_client=client,
        allow_local_fallback=False,
    )
    store.prewarm_projects(projects=["monaro"], bucket_name="monaro-risk-dev-data")
    assert store.get_json("monaro", "snapshots.json")["current_week"] == "w33"

    # Mutate GCS blob to simulate new weekly report sync
    bucket.blobs["monaro/snapshots.json"] = MockGCSBlob(
        "monaro/snapshots.json",
        json.dumps({"current_week": "w34", "snapshots": {"w34": {"week": "Week 34"}}}).encode("utf-8"),
    )

    # Before reload, RAM still serves w33
    assert store.get_json("monaro", "snapshots.json")["current_week"] == "w33"

    # After reload_project('monaro'), RAM immediately serves w34
    store.reload_project("monaro")
    assert store.get_json("monaro", "snapshots.json")["current_week"] == "w34"


def test_immutable_sample_project_loads_from_package_without_gcs(mock_monaro_blobs: Dict[str, bytes]):
    """Verifies 'sample' showcase dataset loads from local package data/sample/ and never hits GCS."""
    bucket = MockGCSBucket("monaro-risk-dev-data", mock_monaro_blobs)
    client = MockGCSClient({"monaro-risk-dev-data": bucket})

    store = ProjectDataStore(
        bucket_name="monaro-risk-dev-data",
        storage_client=client,
        allow_local_fallback=False,
    )
    sample_snaps = store.get_json("sample", "snapshots.json")
    assert isinstance(sample_snaps, dict)
    assert len(sample_snaps) > 0
    assert client.bucket_calls == 0


def test_get_audio_bytes_caches_mp3_in_memory(mock_monaro_blobs: Dict[str, bytes]):
    """Verifies get_audio_bytes() fetches MP3 from GCS and caches bytes in RAM."""
    bucket = MockGCSBucket("monaro-risk-dev-data", mock_monaro_blobs)
    client = MockGCSClient({"monaro-risk-dev-data": bucket})

    store = ProjectDataStore(
        bucket_name="monaro-risk-dev-data",
        storage_client=client,
        allow_local_fallback=False,
    )
    audio1 = store.get_audio_bytes("monaro", "podcast_w33.mp3")
    assert audio1 == b"ID3_MOCK_MONARO_PODCAST_MP3_STREAM"
    assert bucket.blobs["monaro/podcast_w33.mp3"].download_calls == 1

    audio2 = store.get_audio_bytes("monaro", "podcast_w33.mp3")
    assert audio2 == b"ID3_MOCK_MONARO_PODCAST_MP3_STREAM"
    assert bucket.blobs["monaro/podcast_w33.mp3"].download_calls == 1


def test_startup_failure_reporting_when_gcs_inaccessible():
    """Verifies explicit error reporting and status telemetry when GCS bucket or credentials fail."""
    client = MockGCSClient({})  # Empty -> raises PermissionError on bucket access
    store = ProjectDataStore(
        bucket_name="inaccessible-bucket",
        storage_client=client,
        allow_local_fallback=False,
    )

    summary = store.prewarm_projects(projects=["monaro"], bucket_name="inaccessible-bucket")
    assert summary["project_counts"].get("monaro", 0) == 0
    assert summary["errors"].get("monaro") is not None
    status = store.get_status()
    assert status["last_error"] is not None

    with pytest.raises(RuntimeError):
        store.prewarm_projects(projects=["monaro"], bucket_name="inaccessible-bucket", strict=True)


# --- GCS Config Validation, Pull/Push Sync & Read-Only Mount Contracts ---

import os
from unittest.mock import patch
from scripts.security_utils import validate_drive_folder_id, validate_google_sheet_url
from scripts.pipeline import (
    pull_project_config,
    push_project_config,
    update_project_config,
    validate_and_normalize_config,
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

