# Environment Setup & State Inspection Standards

- **Canonical Root-Level Script Placement**:
  - The repository MUST maintain a single, standard entry point script at the repository root: `setup.sh`.
  - **No Redundant Symlinks**: Do NOT generate alias symlinks (e.g. `configure.sh`, `deploy/setup.sh`, `deploy/provision_environment.sh`). All operational documentation and test suites should point directly to `./setup.sh`.
  - The script must reliably resolve the repository root (`PROJECT_ROOT`) regardless of current working directory.

- **Fast Parallel State Inspection (`-l, --list, --status`)**:
  - Environment state checks must be near-instant (< 5 seconds), never taking minutes.
  - State inspection MUST run checks in parallel background subshells with output capturing (`mktemp -d` + background PID tracking).
  - Use structured, predictable state addresses formatted as `<category>.<resource_id>` (e.g. `gcp_api.run.googleapis.com`, `iam_binding.roles/run.invoker`, `secret.gemini_api_key`).

- **Ergonomic Visual Highlighting & Missing-Item Filtering**:
  - **Visual Highlighting**: In tabular outputs of 40+ resources, missing or failed items MUST be visibly highlighted using warm amber/yellow ANSI escape codes (`\033[1;33m[MISSING]\033[0m`) or bold markers so gaps are immediately visible.
  - **Filtering**: Support a `-m, --missing` flag that filters table output to only items requiring attention.
  - Always print an executive summary footer showing total tracked, present/healthy, and missing counts.

- **Zero-Missing-State Guarantee (Self-Healing Provisioning)**:
  - When `./setup.sh` runs to completion in full provisioning mode (without `-l`), it MUST configure and satisfy all tracked assets.
  - Running `./setup.sh -l` immediately after full provisioning MUST report **0 missing items** (100% healthy).
  - If a resource cannot be auto-provisioned due to external governance, the script must check for inherited access (e.g., Google Group permissions) before flagging as missing.

- **GCP Monitoring & Metric Filter Invariants**:
  - In Cloud Monitoring alert policies (`gcloud beta monitoring policies create`), condition threshold filters MUST strictly use metric/resource prefixes:
    - **Valid**: `resource.type = "cloud_run_revision" AND metric.type = "run.googleapis.com/request_count" AND metric.labels.response_code_class = "5xx"`
    - **Invalid**: `severity >= ERROR` (causes `INVALID_ARGUMENT: The lefthand side of each expression must be prefixed with one of {group, metadata, metric, project, resource}`).

- **Inherited Access & Broad Role Recognition**:
  - State checks for IAM and Google Drive MUST evaluate inherited group permissions (e.g., `monaro-risk-dev@google.com`) and parent admin roles (e.g., `roles/storage.admin` satisfying `storage.objectViewer`) before reporting a permission as missing.
