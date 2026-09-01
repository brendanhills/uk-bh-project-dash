# Implementation Plan: Terraform Infrastructure as Code (IaC) Migration

**Track ID:** `terraform_iac_migration_20260901`  
**Status:** `[ ] In Progress`  

## Implementation Roadmap

- [ ] **Phase 1: Module Scaffolding & Foundation (APIs, Artifact Registry, IAM)**
  - [ ] Task: Create `deploy/terraform/` directory structure and module skeletons
  - [ ] Task: Implement `modules/apis` declaring all 16 required GCP services
  - [ ] Task: Implement `modules/artifact_registry` for Sydney Docker repository
  - [ ] Task: Implement `modules/iam` for `github-deployer` and least-privilege role bindings
  - [ ] Task: Phase Verification & Checkpoint (Validate syntax with `terraform fmt` and `terraform validate`)

- [ ] **Phase 2: Compute, Scheduling & Ingestion Pipeline Modules**
  - [ ] Task: Implement `modules/cloud_run` for static web service and sync job
  - [ ] Task: Implement `modules/ingestion_pipeline` for Cloud Tasks queue and Cloud Scheduler cron
  - [ ] Task: Implement `modules/cloud_build` for automated CI/CD branch and tag triggers
  - [ ] Task: Implement `modules/monitoring` for alert policies and email notification channels
  - [ ] Task: Phase Verification & Checkpoint (Verify plan generation on dummy/staging vars)

- [ ] **Phase 3: Environment Composition (`dev` and `prod`) & Import Runbook**
  - [ ] Task: Configure `environments/dev` root module and `terraform.tfvars`
  - [ ] Task: Configure `environments/prod` root module and `terraform.tfvars`
  - [ ] Task: Author `import.sh` script to import existing live GCP resources (`monaro-risk-dev`) without service disruption
  - [ ] Task: Execute `terraform plan` against `monaro-risk-dev` and verify zero-destructive diffs
  - [ ] Task: Phase Verification & Checkpoint (Dry-run plan validation)

- [ ] **Phase 4: Documentation & Operations Transition**
  - [ ] Task: Update `docs/DEPLOYMENT_GUIDE.md` with Terraform operator manual (init, plan, apply, import)
  - [ ] Task: Update `README.md` to reference Terraform as the primary IaC standard
  - [ ] Task: Deprecate imperative scripts gracefully while retaining `--apis-only` helper
  - [ ] Task: Final Track Verification & Checkpoint
