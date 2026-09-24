---
track_id: gcs_in_memory_cache_unification_20260923
type: refactor
focus: robustness
status: ACTIVE
bug_id: null
target_sdd_sections:
  - "2.1 Technology Stack & Architectural Decisions"
  - "2.2 Server Runtime & CLI Tooling"
  - "2.3 Dual-Environment Matrix & Cloud Run Security Architecture"
---

# Specification: GCS In-Memory Cache Unification & Dev/Prod Parity (Delta RFC)

## 1. Overview & Objectives
1. **100% Dev vs Prod Parity**: Eliminate data and environment divergence between local development and Cloud Run production by ensuring that both environments use the **exact same code path** to pull authoritative project data directly from Google Cloud Storage (`gs://${DATA_BUCKET}/{project}/`).
2. **One-Time Startup In-Memory Hydration**: When `server.py` starts up, it initializes a pooled `google.cloud.storage.Client` session, connects to the configured data bucket, and pre-warms an in-memory dictionary cache of all active project datasets (`config.json`, `snapshots.json`, `risks.json`, `issues.json`, `driver_tree.json`, `knowledge.json`).
3. **Sub-Millisecond Read Latency (< 1ms)**: All subsequent HTTP requests for `/data/<project>/<file>.json` serve directly out of in-memory RAM. No end-user in local dev or Cloud Run ever waits for a GCS network round-trip.
4. **Zero Local FUSE Requirement**: Does not require `gcsfuse` or kernel mount tools to be installed on developer workstations (e.g. Cloudtop).
5. **No Local File Drift or Stale Data Masking**: Prevents local disk files from masking missing, malformed, or out-of-date assets in production GCS. If an asset is missing or malformed in GCS, it fails immediately on server boot in both dev and prod.
6. **Immutable Sample Dataset Preservation**: Preserves the built-in, sanitized public showcase dataset (`data/sample/*.json`) in memory with strict confidentiality isolation.

## 2. Proposed Architectural Amendments

### 2.1 In-Memory Project Data Store (`scripts/gcs_store.py` / `server.py`)
- Introduce a centralized `ProjectDataStore` class responsible for:
  - Maintaining an in-memory cache: `_cache: Dict[str, Dict[str, Any]]` mapping `"{project}/{filename}"` to parsed JSON structures or raw bytes (for podcast audio).
  - Establishing a singleton `google.cloud.storage.Client` with connection pooling.
  - Executing a pre-warm hydration routine on server startup for all configured projects (`DEFAULT_PROJECTS=monaro,sample`):
    - Reads `gs://${DATA_BUCKET}/{project}/*.json` in parallel or batched fetch.
    - Loads `sample` data from local package `data/sample/*.json` as an immutable fallback.
  - Exposing `get_json(project: str, filename: str) -> Optional[Dict[str, Any]]`:
    - Checks `_cache` first (returns in < 0.1ms).
    - If a cache miss occurs (e.g., newly ingested snapshot or ad-hoc project query), falls back to fetching from GCS, storing in `_cache`, and returning.
  - Exposing an on-demand invalidation / reload hook: `reload_project(project: str)` to refresh the in-memory cache when a sync or ingest operation occurs.

### 2.2 Unify `server.py` Data Route Serving
- Refactor `server.py`'s `/data/<project>/<filename>.json` route handler:
  - Replace direct `load_json_file(target_path, ...)` disk I/O with `store.get_json(req_proj, req_file)`.
  - Serve directly via `self.send_json(payload)`.
- For podcast audio (`/data/<project>/podcast_w*.mp3`):
  - Stream audio directly via GCS blob streaming or cached bytes with proper `Content-Range` and `Content-Type: audio/mpeg` headers.

### 2.3 Align `scripts/pipeline.py` Data Loading
- Update `load_json_file()`:
  - If running within the server context or when `DATA_BUCKET` is configured, query the unified GCS data store.
  - Avoid redundant per-request REST round-trips by checking the warm in-memory cache.

## 3. Data Contracts & Interfaces
- **Environment Variables**:
  - `GCP_PROJECT_ID`: GCP Project ID hosting GCS.
  - `DATA_BUCKET`: Target bucket (e.g. `monaro-risk-dev-data` or `monaro-risk-prod-data`). Defaults to `f"{GCP_PROJECT_ID}-data"` if unset.
  - `DEFAULT_PROJECTS`: Comma-separated list of projects to pre-warm on boot (default: `monaro`).
- **REST Endpoints**:
  - `GET /data/<project>/<file>.json`: Returns authoritative dataset from memory in < 1ms.
  - `GET /api/status`: Includes GCS cache warm status, loaded projects, and dataset timestamps.

## 4. Acceptance Criteria & Invariants
1. On boot (`python3 server.py` or `./run.sh`), `server.py` logs explicit GCS hydration:
   `[GCS Store] Pre-warmed N datasets for project 'monaro' from gs://... in <XXX>ms.`
2. `curl http://localhost:9000/data/monaro/snapshots.json` returns HTTP 200 with response time < 5ms.
3. No local filesystem read occurs for `monaro` datasets; deleting or renaming `data/monaro` locally does not prevent `server.py` from serving `monaro` data loaded from GCS.
4. Automated unit tests verify:
   - In-memory cache hit rates and sub-millisecond retrieval.
   - Graceful fallback for `sample` project.
   - Parity between dev and prod bucket retrieval logic.
5. All existing pytest unit/contract tests (`uv run pytest`) and frontend verification (`npm run verify`) pass 100%.

## 5. Out of Scope
- Local offline mode without internet connection (explicitly rejected by user).
- GCS FUSE kernel mounts on local Cloudtop workstations (rejected due to missing OS packages).
- Dynamic Google Sheets parsing (handled in separate ingestion jobs).
