# Implementation Plan: Consolidate Depot CI/CD, Folder Structure & Isolated Project Aurora Demo

## Overview
De-risked 4-phase plan to:
1. Lock in `depot` (`sovops-au/monaro-dash.git`) and verify `monaro-risk-dev` Cloud Run with zero refactoring.
2. Create an isolated `demo/aurora` branch with mechanical sanitization (`0` occurrences of `monaro`) and a 1-command mirror script to `~/dev/uk-bh-demos/project_dash`.
3. Push the sanitized Project Aurora demo to `cloud-gtm/uk-bh-demos` (`origin/dev`) and verify GitHub Actions CI.
4. Deploy and verify `project-dash-demo` on Cloud Run in `uk-bh-experiments-argolis` (`australia-southeast1` with IAP).

---

## Phase 1: Lock In `depot` & Verify Monaro Cloud Run (Objectives a & b — Zero Refactoring)
- [ ] **Task 1.1: Reconcile and commit simplification & CI/CD fixes in `~/dev/apps/project_dash`**
  - [ ] Verify `.github/workflows/ci.yml` removes `cache: 'pip'`, sets `permissions: { contents: 'read', id-token: 'write' }`, guards `GCP_SA_KEY`, and passes `--service-account="projects/monaro-risk-dev/serviceAccounts/github-deployer@monaro-risk-dev.iam.gserviceaccount.com"` and `_COMMIT_SHA=${GITHUB_SHA}` to `gcloud builds submit`.
  - [ ] Verify `deploy/cloudbuild.yaml` tags both `:${_COMMIT_SHA}` and `:latest` in Step #3 (`build-image`) and runs `pytest -v -m "not live"` in Step #4 (`run-tests`).
  - [ ] Run `npm run verify && uv run pytest` to confirm all 116 pytest and 21 Vitest tests pass.
- [ ] **Task 1.2: Sync with `depot/main` and push `main` to `depot`**
  - [ ] Reconcile local `main` with `depot/main` (`4099a65`) and merge/cherry-pick the simplification + CI/CD commit onto `main`.
  - [ ] Push `main` to `depot` (`git push depot main`).
- [ ] **Task 1.3: Verify Cloud Build & Cloud Run in `monaro-risk-dev` (`australia-southeast1`)**
  - [ ] Inspect the triggered (or manually submitted) Cloud Build via `python3 scripts/check_build_status.py --project monaro-risk-dev --region australia-southeast1 --limit 1`.
  - [ ] Confirm Step #0 through Step #6 (`deploy-web` and `update-job` for `monaro-risk-sync-job`) succeed and `https://monaro-risk-dash-dev-525025654699.australia-southeast1.run.app` is healthy.
- [ ] **Task 1.4: Phase 1 Verification & Checkpoint**

---

## Phase 2: Create Isolated `demo/aurora` Branch & Consolidate Disk Sync (Objectives c & d)
- [ ] **Task 2.1: Branch `demo/aurora` from verified `main`**
  - [ ] Create branch `demo/aurora` from `main` (leaving `main` / `depot` 100% untouched).
  - [ ] Update `index.html` on `demo/aurora` to set `<script>window.DEFAULT_PROJECT = 'sample';</script>` and replace static header fallback text (`PROJECT MONARO`) with `PROJECT AURORA` (`Aurora Health Cloud Modernization • Executive Risk & Delivery Portfolio`).
- [ ] **Task 2.2: Mechanical sanitization of `monaro` references on `demo/aurora`**
  - [ ] Remove Monaro-only Terraform environments (`deploy/terraform/environments/{dev,prod}`) and Depot-specific `.github/workflows/ci.yml` on `demo/aurora`.
  - [ ] Mechanically replace remaining `monaro` / `Monaro` strings in docs, comments, and default literals with `aurora` / `Aurora` / `sample`.
  - [ ] Verify `! git grep -i "monaro"` returns `0` matches across the entire `demo/aurora` branch.
  - [ ] Run `npm run verify && uv run pytest` on `demo/aurora` to confirm 100% test pass rate.
- [ ] **Task 2.3: Add 1-command sync script (`scripts/demo/sync_to_demos.sh`)**
  - [ ] Create `scripts/demo/sync_to_demos.sh` to deterministically mirror the `demo/aurora` working tree into `/usr/local/google/home/brendanhills/dev/uk-bh-demos/project_dash` so the two directories never drift manually.
- [ ] **Task 2.4: Phase 2 Verification & Checkpoint**

---

## Phase 3: Push Clean Demo to `uk-bh-demos` & Verify GitHub Actions CI (Objectives e & f)
- [ ] **Task 3.1: Mirror `demo/aurora` into `~/dev/uk-bh-demos/project_dash`**
  - [ ] Run `scripts/demo/sync_to_demos.sh` and verify `! git -C /usr/local/google/home/brendanhills/dev/uk-bh-demos grep -i "monaro" -- project_dash/` passes with `0` matches.
- [ ] **Task 3.2: Update `uk-bh-demos/.github/workflows/ci.yml` for `project_dash`**
  - [ ] Configure `.github/workflows/ci.yml` in `uk-bh-demos` to run `project_dash` automated tests (`pytest -v -m "not live"` + Node syntax/ESLint/Vitest) on `ubuntu-latest` for pushes and PRs on `dev` and `main`.
- [ ] **Task 3.3: Commit, push to `origin/dev` (`cloud-gtm/uk-bh-demos`), and verify GitHub CI**
  - [ ] Stage `project_dash/` and `.github/workflows/ci.yml` in `uk-bh-demos`, commit, and push to `origin/dev`.
  - [ ] Verify the GitHub Actions workflow run completes with green status.
- [ ] **Task 3.4: Phase 3 Verification & Checkpoint**

---

## Phase 4: Deploy & Verify Demo on Cloud Run in `uk-bh-experiments-argolis` (Objective g)
- [ ] **Task 4.1: Configure `deploy/cloudbuild.yaml` on `demo/aurora` for `uk-bh-experiments-argolis`**
  - [ ] Configure `deploy/cloudbuild.yaml` for service `project-dash-demo` in `australia-southeast1` with IAP (`--no-allow-unauthenticated --iap`) and `DEFAULT_PROJECTS=sample,STRICT_READ_ONLY=true` (omitting the Monaro-only sync job step).
- [ ] **Task 4.2: Deploy to Cloud Run in `uk-bh-experiments-argolis` & verify live service**
  - [ ] Submit Cloud Build / Cloud Run deployment using `--project=uk-bh-experiments-argolis --account=brendan@brendanhills.altostrat.com`.
  - [ ] Verify `project-dash-demo` is active in `australia-southeast1` with IAP enabled and serves Project Aurora (`🌌 PROJECT AURORA`).
- [ ] **Task 4.3: Phase 4 Verification & Final Handover**
