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
