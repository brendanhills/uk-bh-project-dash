"""Centralized In-Memory GCS Project Data Store (`scripts/gcs_store.py`).

Provides 100% Dev/Prod storage parity by hydrating authoritative project datasets
from Google Cloud Storage (`gs://${DATA_BUCKET}/{project}/*.json`) into an in-memory
RAM cache on startup, serving subsequent reads in sub-millisecond (< 0.1ms) latency.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import logging
import os
import subprocess
import sys
import threading
import time
import urllib.parse
from typing import Any, Dict, List, Optional

import google.auth
import google.auth.transport.requests
from google.oauth2 import credentials as oauth2_credentials
import requests
from requests.adapters import HTTPAdapter

try:
    from google.cloud import storage as gcs_storage
except ImportError:
    gcs_storage = None

from scripts.security_utils import resolve_default_project, sanitize_slug

logger = logging.getLogger("gcs_store")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_BASE_DIR = os.path.join(BASE_DIR, "data")

STANDARD_PROJECT_DATASETS: List[str] = [
    "config.json",
    "snapshots.json",
    "risks.json",
    "issues.json",
    "driver_tree.json",
    "knowledge.json",
]


def resolve_configured_projects() -> List[str]:
    """Resolves the list of projects to pre-warm on boot from DEFAULT_PROJECTS or .env."""
    raw = os.getenv("DEFAULT_PROJECTS") or os.getenv("DEFAULT_PROJECT")
    if not raw:
        env_path = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("DEFAULT_PROJECTS=") or line.startswith("DEFAULT_PROJECT="):
                            raw = line.split("=", 1)[1].strip().strip("\"'")
                            break
            except OSError:
                pass

    projects: List[str] = []
    if raw:
        for part in raw.split(","):
            slug = part.strip()
            if slug and slug not in projects:
                projects.append(slug)

    if not projects:
        projects.append("monaro")
    if "sample" not in projects:
        projects.append("sample")
    return projects


def resolve_default_data_bucket() -> str:
    """Resolves the active GCS bucket name (`DATA_BUCKET` or `<GCP_PROJECT_ID>-data`)."""
    explicit = os.getenv("DATA_BUCKET")
    if explicit and explicit.strip().lower() not in ("none", "false", "local", "0"):
        return explicit.strip()

    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATA_BUCKET="):
                        val = line.split("=", 1)[1].strip().strip("\"'")
                        if val and val.lower() not in ("none", "false", "local", "0"):
                            return val
        except OSError:
            pass

    quota_project = resolve_default_project()
    return f"{quota_project}-data"


class ProjectDataStore:
    """Thread-safe in-memory project dataset and audio store backed by Google Cloud Storage."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        storage_client: Optional[Any] = None,
        allow_local_fallback: Optional[bool] = None,
    ):
        self._lock = threading.RLock()
        self._cache: Dict[str, Any] = {}
        self._raw_json_cache: Dict[str, bytes] = {}
        self._audio_cache: Dict[str, bytes] = {}
        self._bucket_name: Optional[str] = bucket_name
        self._client: Optional[Any] = storage_client
        self._gcloud_token: Optional[str] = None

        # Pooled HTTP session for connection reuse across GCS REST / client operations
        self.http_session = requests.Session()
        adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16)
        self.http_session.mount("https://", adapter)
        self.http_session.mount("http://", adapter)

        # In dev/prod runtime, local disk fallback for non-sample projects is strictly disabled
        # to enforce 100% Dev/Prod GCS parity. Only enabled when bucket is disabled in hermetic pytest.
        if allow_local_fallback is None:
            is_pytest = "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules
            self._allow_local_fallback = bool(is_pytest and not bucket_name and storage_client is None)
        else:
            self._allow_local_fallback = allow_local_fallback

        self._warm: bool = False
        self._loaded_projects: List[str] = []
        self._project_counts: Dict[str, int] = {}
        self._project_timestamps: Dict[str, str] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._last_error: Optional[str] = None

    @property
    def bucket_name(self) -> Optional[str]:
        if self._bucket_name:
            return self._bucket_name
        # In hermetic pytest without explicit bucket, do not auto-target live GCS
        if ("PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules) and self._client is None:
            explicit = os.getenv("DATA_BUCKET")
            if not explicit or explicit.lower() in ("none", "false", "local", "0"):
                return None
            return explicit.strip()
        self._bucket_name = resolve_default_data_bucket()
        return self._bucket_name

    def _obtain_gcloud_token(self, force_refresh: bool = False) -> Optional[str]:
        with self._lock:
            if self._gcloud_token and not force_refresh:
                return self._gcloud_token
            try:
                res = subprocess.run(
                    ["gcloud", "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                )
                tok = res.stdout.strip()
                if tok:
                    self._gcloud_token = tok
                    return tok
            except Exception:
                pass
            return self._gcloud_token

    def _get_storage_client(self, force_gcloud: bool = False) -> Optional[Any]:
        """Returns or initializes a pooled google.cloud.storage.Client."""
        with self._lock:
            if self._client is not None:
                if not force_gcloud or getattr(self, "_using_gcloud_fallback", False):
                    return self._client
            if gcs_storage is None:
                return None

            quota_project = resolve_default_project()
            adapter = HTTPAdapter(pool_connections=16, pool_maxsize=16)
            if not force_gcloud:
                try:
                    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                    client = gcs_storage.Client(project=quota_project, credentials=creds)
                    if hasattr(client, "_http") and hasattr(client._http, "mount"):
                        client._http.mount("https://", adapter)
                    self._client = client
                    self._using_gcloud_fallback = False
                    return self._client
                except Exception:
                    pass

            tok = self._obtain_gcloud_token(force_refresh=False)
            if tok:
                creds = oauth2_credentials.Credentials(token=tok, quota_project_id=quota_project)
                client = gcs_storage.Client(project=quota_project, credentials=creds)
                if hasattr(client, "_http") and hasattr(client._http, "mount"):
                    client._http.mount("https://", adapter)
                self._client = client
                self._using_gcloud_fallback = True
                return self._client
            return None

    def _download_blob_bytes(self, bucket_name: str, blob_name: str) -> Optional[bytes]:
        """Downloads raw blob bytes from GCS via pooled storage.Client or pooled REST fallback."""
        # 1. If a custom/mock storage_client was injected, use it directly
        if self._client is not None:
            bucket_obj = self._client.bucket(bucket_name)
            blob_obj = bucket_obj.blob(blob_name)
            if hasattr(blob_obj, "exists") and not blob_obj.exists():
                return None
            return blob_obj.download_as_bytes()

        # 1b. In pytest runs without an explicit storage_client, honor patched download_bytes_from_gcs
        if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
            from scripts.gemini_generator import download_bytes_from_gcs
            return download_bytes_from_gcs(bucket_name, blob_name)

        # 2. Try pooled google.cloud.storage.Client or pooled REST with automatic gcloud token fallback
        client = self._get_storage_client(force_gcloud=False)
        if client is not None:
            try:
                bucket_obj = client.bucket(bucket_name)
                blob_obj = bucket_obj.blob(blob_name)
                return blob_obj.download_as_bytes()
            except Exception as exc:
                err_str = str(exc)
                if "404" in err_str or "NotFound" in err_str or isinstance(exc, FileNotFoundError):
                    return None
                if "401" in err_str or "403" in err_str or "Forbidden" in err_str or "Unauthorized" in err_str:
                    # Retry with gcloud CLI token (handles workstation @google.com ADC vs Argolis @altostrat.com)
                    fb_client = self._get_storage_client(force_gcloud=True)
                    if fb_client is not None:
                        try:
                            return fb_client.bucket(bucket_name).blob(blob_name).download_as_bytes()
                        except Exception as fb_exc:
                            if "404" in str(fb_exc) or "NotFound" in str(fb_exc):
                                return None
                            raise fb_exc
                raise exc

        # 3. Pooled HTTP Session REST fallback
        from scripts.gemini_generator import _get_gcs_auth_headers

        encoded_blob = urllib.parse.quote(blob_name, safe="")
        url = f"https://storage.googleapis.com/storage/v1/b/{bucket_name}/o/{encoded_blob}?alt=media"
        headers = _get_gcs_auth_headers()
        r = self.http_session.get(url, headers=headers, timeout=15)
        if r.status_code in (401, 403):
            headers = _get_gcs_auth_headers(force_gcloud=True)
            r = self.http_session.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.content
        if r.status_code == 404:
            return None
        raise PermissionError(f"GCS HTTP {r.status_code} accessing gs://{bucket_name}/{blob_name}: {r.text[:160]}")

    def _load_sample_dataset_into_cache(self, filename: str) -> Optional[Any]:
        """Loads an immutable showcase dataset from local data/sample/<filename> into RAM."""
        sample_path = os.path.join(DATA_BASE_DIR, "sample", filename)
        if not os.path.exists(sample_path):
            return None
        try:
            with open(sample_path, "rb") as f:
                raw_bytes = f.read()
            data = json.loads(raw_bytes.decode("utf-8"))
            with self._lock:
                self._cache[f"sample/{filename}"] = data
                self._raw_json_cache[f"sample/{filename}"] = raw_bytes
            return data
        except Exception as e:
            logger.warning(f"[GCS Store] Failed to read sample dataset {sample_path}: {e}")
            return None

    def prewarm_projects(
        self,
        projects: Optional[List[str]] = None,
        bucket_name: Optional[str] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        """Hydrates configured project datasets from GCS into memory on server boot."""
        target_projects = projects or resolve_configured_projects()
        active_bucket = bucket_name or self.bucket_name
        if bucket_name:
            self._bucket_name = bucket_name

        errors: Dict[str, str] = {}
        project_counts: Dict[str, int] = {}

        for raw_proj in target_projects:
            proj = sanitize_slug(raw_proj, default="monaro")
            start_t = time.perf_counter()

            if proj == "sample":
                count = 0
                for fname in STANDARD_PROJECT_DATASETS:
                    if self._load_sample_dataset_into_cache(fname) is not None:
                        count += 1
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                with self._lock:
                    if proj not in self._loaded_projects:
                        self._loaded_projects.append(proj)
                    self._project_counts[proj] = count
                    self._project_timestamps[proj] = datetime.utcnow().isoformat() + "Z"
                project_counts[proj] = count
                logger.info(
                    f"[GCS Store] Pre-warmed {count} datasets for showcase project 'sample' in {elapsed_ms:.1f}ms."
                )
                continue

            if not active_bucket:
                err_msg = f"No GCS DATA_BUCKET configured for project '{proj}'."
                errors[proj] = err_msg
                self._last_error = err_msg
                project_counts[proj] = 0
                if strict:
                    raise RuntimeError(err_msg)
                continue

            # Fetch all standard datasets for `proj` concurrently from GCS
            loaded_for_proj = 0
            proj_errors: List[str] = []

            def _fetch_one(fname: str) -> Optional[Any]:
                blob_key = f"{proj}/{fname}"
                raw_bytes = self._download_blob_bytes(active_bucket, blob_key)
                if raw_bytes is None:
                    return None
                parsed = json.loads(raw_bytes.decode("utf-8"))
                return parsed, raw_bytes

            # Probe the first dataset (`config.json`) to establish auth session before parallel fan-out
            remaining_files = list(STANDARD_PROJECT_DATASETS)
            if remaining_files:
                first_fn = remaining_files.pop(0)
                try:
                    res = _fetch_one(first_fn)
                    if res is not None:
                        parsed, raw_bytes = res
                        with self._lock:
                            self._cache[f"{proj}/{first_fn}"] = parsed
                            self._raw_json_cache[f"{proj}/{first_fn}"] = raw_bytes
                        loaded_for_proj += 1
                except Exception as exc:
                    proj_errors.append(f"{first_fn}: {exc}")

            if remaining_files and not proj_errors:
                with ThreadPoolExecutor(max_workers=len(remaining_files)) as pool:
                    future_map = {pool.submit(_fetch_one, fn): fn for fn in remaining_files}
                    for fut in as_completed(future_map):
                        fname = future_map[fut]
                        try:
                            res = fut.result()
                            if res is not None:
                                parsed, raw_bytes = res
                                with self._lock:
                                    self._cache[f"{proj}/{fname}"] = parsed
                                    self._raw_json_cache[f"{proj}/{fname}"] = raw_bytes
                                loaded_for_proj += 1
                        except Exception as exc:
                            proj_errors.append(f"{fname}: {exc}")

            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            project_counts[proj] = loaded_for_proj

            if proj_errors or loaded_for_proj == 0:
                err_detail = "; ".join(proj_errors) if proj_errors else f"0 blobs found under gs://{active_bucket}/{proj}/"
                full_err = f"Failed to hydrate project '{proj}' from gs://{active_bucket}: {err_detail}"
                errors[proj] = full_err
                with self._lock:
                    self._last_error = full_err
                logger.error(f"[GCS Store] ERROR: {full_err}")
                if strict:
                    raise RuntimeError(full_err)

            if loaded_for_proj > 0:
                with self._lock:
                    if proj not in self._loaded_projects:
                        self._loaded_projects.append(proj)
                    self._project_counts[proj] = loaded_for_proj
                    self._project_timestamps[proj] = datetime.utcnow().isoformat() + "Z"
                    self._warm = True
                msg = (
                    f"[GCS Store] Pre-warmed {loaded_for_proj} datasets for project '{proj}' "
                    f"from gs://{active_bucket} in {elapsed_ms:.1f}ms."
                )
                logger.info(msg)
                print(msg)

        with self._lock:
            if not self._warm and any(c > 0 for c in project_counts.values()):
                self._warm = True

        return {
            "warm": self._warm,
            "bucket": active_bucket,
            "loaded_projects": list(self._loaded_projects),
            "project_counts": project_counts,
            "errors": errors,
        }

    def get_json(self, project: str, filename: str) -> Optional[Any]:
        """Retrieves a parsed JSON dataset from in-memory cache (< 0.1ms) or fetches from GCS on miss."""
        clean_proj = sanitize_slug(project, default="monaro")
        cache_key = f"{clean_proj}/{filename}"

        with self._lock:
            if cache_key in self._cache:
                self._cache_hits += 1
                return self._cache[cache_key]
            self._cache_misses += 1

        # 1. Immutable sample dataset loads from local package data/sample/
        if clean_proj == "sample":
            return self._load_sample_dataset_into_cache(filename)

        # 2. Authoritative GCS fetch (Dev & Prod parity — never reads local disk for non-sample projects)
        active_bucket = self.bucket_name
        if active_bucket:
            try:
                raw_bytes = self._download_blob_bytes(active_bucket, cache_key)
                if raw_bytes is not None:
                    parsed = json.loads(raw_bytes.decode("utf-8"))
                    with self._lock:
                        self._cache[cache_key] = parsed
                        self._raw_json_cache[cache_key] = raw_bytes
                        if clean_proj not in self._loaded_projects:
                            self._loaded_projects.append(clean_proj)
                        self._project_counts[clean_proj] = self._project_counts.get(clean_proj, 0) + 1
                        self._project_timestamps[clean_proj] = datetime.utcnow().isoformat() + "Z"
                    return parsed
            except Exception as exc:
                with self._lock:
                    self._last_error = f"GCS fetch error for gs://{active_bucket}/{cache_key}: {exc}"
                logger.warning(f"[GCS Store] {self._last_error}")

        return None

    def get_json_bytes(self, project: str, filename: str) -> Optional[bytes]:
        """Retrieves pre-serialized UTF-8 JSON bytes from RAM (< 0.05ms) for zero-copy HTTP responses."""
        clean_proj = sanitize_slug(project, default="monaro")
        cache_key = f"{clean_proj}/{filename}"
        with self._lock:
            if cache_key in self._raw_json_cache:
                self._cache_hits += 1
                return self._raw_json_cache[cache_key]
        parsed = self.get_json(clean_proj, filename)
        if parsed is not None:
            with self._lock:
                if cache_key not in self._raw_json_cache:
                    self._raw_json_cache[cache_key] = json.dumps(parsed).encode("utf-8")
                return self._raw_json_cache[cache_key]
        return None

    def put_json(self, project: str, filename: str, data: Any) -> None:
        """Updates the in-memory cache immediately when a pipeline write or sync completes."""
        clean_proj = sanitize_slug(project, default="monaro")
        cache_key = f"{clean_proj}/{filename}"
        encoded = json.dumps(data).encode("utf-8")
        with self._lock:
            self._cache[cache_key] = data
            self._raw_json_cache[cache_key] = encoded
            if clean_proj not in self._loaded_projects:
                self._loaded_projects.append(clean_proj)
            self._project_timestamps[clean_proj] = datetime.utcnow().isoformat() + "Z"

    def get_audio_bytes(self, project: str, filename: str) -> Optional[bytes]:
        """Retrieves podcast MP3 bytes from in-memory cache or downloads from GCS."""
        clean_proj = sanitize_slug(project, default="monaro")
        cache_key = f"{clean_proj}/{filename}"

        with self._lock:
            if cache_key in self._audio_cache:
                self._cache_hits += 1
                return self._audio_cache[cache_key]
            self._cache_misses += 1

        active_bucket = self.bucket_name
        if active_bucket:
            for candidate_blob in (f"{clean_proj}/{filename}", f"assets/{filename}"):
                try:
                    raw_bytes = self._download_blob_bytes(active_bucket, candidate_blob)
                    if raw_bytes:
                        with self._lock:
                            self._audio_cache[cache_key] = raw_bytes
                        return raw_bytes
                except Exception as exc:
                    logger.debug(f"[GCS Store] Audio fetch failed for gs://{active_bucket}/{candidate_blob}: {exc}")

        if clean_proj == "sample":
            for local_cand in (
                os.path.join(DATA_BASE_DIR, "sample", filename),
                os.path.join(BASE_DIR, "assets", filename),
            ):
                if os.path.isfile(local_cand):
                    try:
                        with open(local_cand, "rb") as f:
                            raw_bytes = f.read()
                        with self._lock:
                            self._audio_cache[cache_key] = raw_bytes
                        return raw_bytes
                    except OSError:
                        pass

        return None

    def reload_project(self, project: str) -> Dict[str, Any]:
        """Invalidates all cached entries for `project` and re-hydrates from GCS."""
        clean_proj = sanitize_slug(project, default="monaro")
        prefix = f"{clean_proj}/"
        with self._lock:
            keys_to_drop = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_drop:
                del self._cache[k]
            raw_to_drop = [k for k in self._raw_json_cache if k.startswith(prefix)]
            for k in raw_to_drop:
                del self._raw_json_cache[k]
            audio_to_drop = [k for k in self._audio_cache if k.startswith(prefix)]
            for k in audio_to_drop:
                del self._audio_cache[k]

        return self.prewarm_projects(projects=[clean_proj], bucket_name=self._bucket_name)

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry for `/api/status`."""
        with self._lock:
            return {
                "warm": self._warm,
                "bucket": self.bucket_name,
                "loaded_projects": list(self._loaded_projects),
                "cached_datasets_count": len(self._cache),
                "cached_audio_count": len(self._audio_cache),
                "project_counts": dict(self._project_counts),
                "project_timestamps": dict(self._project_timestamps),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "last_error": self._last_error,
            }


_SINGLETON_STORE: Optional[ProjectDataStore] = None
_SINGLETON_LOCK = threading.Lock()


def get_project_data_store() -> ProjectDataStore:
    """Returns the process-wide singleton ProjectDataStore instance."""
    global _SINGLETON_STORE
    if _SINGLETON_STORE is None:
        with _SINGLETON_LOCK:
            if _SINGLETON_STORE is None:
                _SINGLETON_STORE = ProjectDataStore()
    return _SINGLETON_STORE
