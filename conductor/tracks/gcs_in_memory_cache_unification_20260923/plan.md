# Implementation Plan: GCS In-Memory Cache Unification & Dev/Prod Parity

## Phase 1: In-Memory GCS Data Store Implementation & Unit Tests (`scripts/gcs_store.py`)
- [x] Task 1.1: Write unit tests in `tests/test_gcs_store.py` validating `ProjectDataStore`:
  - Singleton client connection pooling and initialization.
  - In-memory hydration from GCS for configured projects.
  - Sub-millisecond `< 0.1ms` cache retrieval via `get_json()`.
  - Proper handling of cache misses, invalidation (`reload_project`), and fallback for local `sample` dataset.
  - Failure reporting on startup when GCS bucket or credentials are inaccessible.
- [x] Task 1.2: Implement `scripts/gcs_store.py`:
  - Define `ProjectDataStore` with thread-safe `_cache: Dict[str, Dict[str, Any]]` and `google.cloud.storage.Client` session pool.
  - Implement `prewarm_projects(projects: List[str], bucket_name: Optional[str] = None)`.
  - Implement `get_json(project: str, filename: str) -> Optional[Dict[str, Any]]`.
  - Implement `get_audio_bytes(project: str, filename: str) -> Optional[bytes]`.
  - Implement `reload_project(project: str)`.

## Phase 2: Unify `server.py` and `scripts/pipeline.py` to use `ProjectDataStore`
- [x] Task 2.1: In `server.py`:
  - Initialize and pre-warm `ProjectDataStore` during server startup (`main()` or `run_server()`).
  - Refactor `/data/<project>/<file>.json` route handler to retrieve directly from `store.get_json(req_proj, req_file)` in memory.
  - Refactor audio serving to use `store.get_audio_bytes()` with streaming headers.
  - Enhance `/api/status` to report GCS cache warm status, loaded projects, and item counts.
- [x] Task 2.2: In `scripts/pipeline.py`:
  - Hook `load_json_file()` into `ProjectDataStore` to benefit from in-memory cached datasets.
  - When `save_json_file()` writes new data, notify `ProjectDataStore.reload_project(project)` to keep RAM cache immediately synchronized.

## Phase 3: Verification & Parity Audit
- [x] Task 3.1: Run test suite (`uv run pytest` and `npm run verify`) to ensure 100% test pass rate with zero regression.
- [x] Task 3.2: Verify local server startup:
  - Check boot logs confirming GCS pre-warming.
  - Measure curl response time for `/data/monaro/snapshots.json` (< 5ms).
  - Verify that local dev and Cloud Run both pull strictly from GCS with zero dependence on local files.
