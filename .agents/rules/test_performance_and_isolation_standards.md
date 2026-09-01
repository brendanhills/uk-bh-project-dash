# Test Performance, Hermetic Isolation & Project Defaults Standards

- **Zero-Network Invariant & Millisecond Execution**:
  - Automated unit and integration tests (`pytest tests/`) MUST execute near-instantaneously (< 0.1s per unit test, full test suite under 10 seconds).
  - Tests MUST NEVER make unmocked live external API calls (Vertex AI, Gemini, Google Drive, Google Sheets).
  - Never allow tests to block waiting for network timeouts in sandboxed or offline environments; test calls to ingestion pipelines or generators MUST explicitly pass `force_fallback=True` or mock external endpoints.

- **Defensive Sandbox Data Isolation (`tmp_path`)**:
  - Tests executing pipeline ingestion or data serialization (`ingest_report_file`, `ingest_file`, `sync_project_data`, `save_json_file`) MUST NEVER write directly to production or tracked repository directories (`data/monaro/`, `data/sample/`).
  - Tests MUST leverage pytest's `tmp_path` fixture for `data_root` to ensure all generated artifacts and snapshots remain ephemeral, hermetic, and parallel-safe without contaminating git status.

- **Canonical Project Defaults & Graceful Degradation**:
  - Whenever a project is designated as canonical/default (e.g., `monaro`), all tiers—backend server resolution (`get_default_project`), frontend client data loading (`CURRENT_PROJECT`), CLI argument parsers (`--project`), and documentation links—MUST default to this canonical slug.
  - Client and server loaders MUST implement self-healing fallback to demo/sample datasets (`sample`) whenever private project data directories are missing (e.g. clean public git checkouts).
  - Backward-compatibility aliases (e.g. `f-dse` <-> `monaro`) MUST be preserved bidirectionally so existing bookmarks, scripts, and links continue to function seamlessly.

- **Pre-Commit Full Test Suite Verification**:
  - Before closing any bug or declaring a feature track complete, run the full test suite (`pytest tests/`) to ensure 100% pass rate with zero regressions across all parameterized datasets (`sample`, `monaro`, `f-dse`).
