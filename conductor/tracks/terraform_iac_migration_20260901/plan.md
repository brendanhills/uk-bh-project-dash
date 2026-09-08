# Implementation Plan: Terraform Infrastructure as Code (IaC) Migration

**Track ID:** `terraform_iac_migration_20260901`  
**Status:** `[ ] In Progress`  

## Implementation Roadmap

- [x] **Phase 1: Module Scaffolding & Foundation (Bootstrap, APIs, Storage, Artifact Registry, IAM)**
  - [x] Task: Refactor root `setup.sh` developer cockpit:
    - [x] Preserve sub-5s parallel health audit (`--status`, `-l`, `-m`, `--state-only`)
    - [x] Implement explicit auditing for manual checkpoints (GitHub connection, OAuth Consent Screen, Drive access, Billing expiration, Google Groups) showing `[✓] COMPLETE` vs `[!] OUTSTANDING` with 1-click console URLs
    - [x] Implement pre-flight bootstrap (APIs, state bucket, data seeding) and wire provisioning to Terraform
  - [x] Task: Create `deploy/terraform/` directory structure and module skeletons
  - [x] Task: Implement `modules/apis` declaring all 16 required GCP services in `australia-southeast1`
  - [x] Task: Implement `modules/storage` declaring GCS data persistence bucket (`${PROJECT_ID}-data`) and state bucket
  - [x] Task: Implement `modules/artifact_registry` with native cleanup policies (`cleanup_policies`) matching `cleanup-policy.json`
  - [x] Task: Implement `modules/iam` for `github-deployer` and least-privilege role bindings
  - [x] Task: Phase Verification & Checkpoint (Validate syntax with `terraform fmt` and `terraform validate`)

- [ ] **Phase 2: Compute, Scheduling & Ingestion Pipeline Modules**
  - [ ] Task: Implement `modules/cloud_run` for static web service and sync job (Gen2 execution environment + GCS volume mount)
  - [ ] Task: Implement `modules/ingestion_pipeline` for Cloud Tasks queue (`monaro-sync-queue`) and Cloud Scheduler cron (`monaro-sync-schedule`)
  - [ ] Task: Implement `modules/cloud_build` for GitHub triggers (`brendanhills/uk-bh-project-dash`, `main` branch and `^project_dash/prod-.*$` tags)
  - [ ] Task: Implement `modules/monitoring` for alert policies and email notification channels (`brendanhills@google.com`, `allins@google.com`)
  - [ ] Task: Phase Verification & Checkpoint (Verify plan generation on dummy/staging vars)

- [ ] **Phase 3: Environment Composition (`dev` and `prod`) & Import Runbook**
  - [ ] Task: Configure `environments/dev` root module, `backend.tf`, and `terraform.tfvars` (`monaro-risk-dev`)
  - [ ] Task: Configure `environments/prod` root module, `backend.tf`, and `terraform.tfvars` (`monaro-risk-prod`)
  - [ ] Task: Author `import.sh` script to import existing live GCP resources (`monaro-risk-dev`) without service disruption
  - [ ] Task: Execute `terraform plan` against `monaro-risk-dev` and verify zero-destructive diffs
  - [ ] Task: Verify `./setup.sh --status` reports 100% healthy (0 missing items) against imported Terraform infrastructure
  - [ ] Task: Phase Verification & Checkpoint (Dry-run plan validation)

- [ ] **Phase 4: Documentation & Operations Transition**
  - [ ] Task: Update `conductor/spec.md` (Master Specification) and `conductor/tech-stack.md` establishing Terraform modules as the canonical infrastructure standard and documenting the `./setup.sh` developer cockpit
  - [ ] Task: Update `docs/DEPLOYMENT_GUIDE.md` with comprehensive Terraform operator manual (`init`, `plan`, `apply`, `import`), manual checkpoints guide, and `./setup.sh --status` audit instructions
  - [ ] Task: Update `README.md` to document `./setup.sh --status`, manual checkpoints reporting, and Terraform IaC architecture
  - [ ] Task: Deprecate `deploy/enable_apis.sh` in favor of root `./setup.sh`
  - [ ] Task: Verify `tests/test_frontend_contracts.py` passes syntax and contract checks for refactored `setup.sh` (including `--status`, `-l`, and `-m`)
  - [ ] Task: Final Track Verification & Checkpoint
