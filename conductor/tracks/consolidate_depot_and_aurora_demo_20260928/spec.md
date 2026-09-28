# Specification: Consolidate Depot CI/CD, Folder Structure & Isolated Project Aurora Demo

## 1. Problem Statement & Context
Currently, two copies of `project_dash` exist on disk (`/usr/local/google/home/brendanhills/dev/apps/project_dash` and `/usr/local/google/home/brendanhills/dev/uk-bh-demos/project_dash`):
1. **`~/dev/apps/project_dash`** contains completed test/script simplifications (`scripts/demo/` relocation, `check_build_status.py` and `check_podcast_status.py` streamlining, test consolidation into `test_frontend_contracts.py` and `test_gcs_store.py`) plus fixes for `.github/workflows/ci.yml` and `deploy/cloudbuild.yaml`.
2. **`depot` (`git@depot.code.corp.goog:sovops-au/monaro-dash.git`)** has `feat/prompt-eval-and-ui-harness` squash-merged into `depot/main` (`18968a5`) and `Update ci.yml (#8)` (`4099a65`), but its last Cloud Build (`4863091f`) in `monaro-risk-dev` failed at Step #6 (`update-job`) because `gcloud builds submit` in `depot/main:.github/workflows/ci.yml` omitted `--service-account=projects/monaro-risk-dev/serviceAccounts/github-deployer@monaro-risk-dev.iam.gserviceaccount.com`.
3. **`~/dev/uk-bh-demos/project_dash`** was imported into `cloud-gtm/uk-bh-demos` (`9fd5507`) prior to the simplification commit and still contains 84 files with `monaro` string references.

## 2. Core Objectives & Requirements
- **(a) Monaro Cloud Run Health**: Ensure `monaro-risk-dash-dev` and `monaro-risk-sync-job` build and deploy cleanly in `monaro-risk-dev` (`australia-southeast1`).
- **(b) Depot Lock-In (Zero Refactoring Risk)**: Commit the already-tested simplification and CI/CD fixes directly to `main` and push to `depot` before performing any demo sanitization work.
- **(c) Consolidated Disk Workflow**: Keep `~/dev/apps/project_dash` as the authoritative Git repository (`main` tracking `depot/main` and `demo/aurora` branch for the sanitized demo), using a deterministic sync script (`scripts/demo/sync_to_demos.sh`) to mirror `demo/aurora` into `~/dev/uk-bh-demos/project_dash`.
- **(d) Isolated `demo/aurora` Branch**: Create a `demo/aurora` branch from `main` using mechanical string sanitization (`monaro` -> `aurora`/`sample`, `window.DEFAULT_PROJECT = 'sample'` in `index.html`) without refactoring Python/JS function signatures on `main`.
- **(e) Zero-Leakage Push to `uk-bh-demos`**: Mirror `demo/aurora` into `~/dev/uk-bh-demos/project_dash`, verify `git grep -i "monaro" -- project_dash/` returns `0` matches, and push to `origin/dev` on `cloud-gtm/uk-bh-demos`.
- **(f) GitHub Actions CI Verification**: Update `.github/workflows/ci.yml` in `uk-bh-demos` to run the `project_dash` test suite (`pytest -v -m "not live"` + Node syntax/ESLint/Vitest) on `ubuntu-latest` and confirm green execution on GitHub.
- **(g) Argolis Cloud Run Deployment**: Deploy the demo version (`project-dash-demo`) to Cloud Run in `uk-bh-experiments-argolis` (`australia-southeast1`) with IAP enabled (`--no-allow-unauthenticated --iap`) using account `brendan@brendanhills.altostrat.com`.

## 3. Out-of-Scope / Guardrails
- Do **not** refactor Python/JS function signatures on `main` (`depot`) to avoid regression risk prior to completing Objectives (a) and (b).
- Enforce a hard gate after Phase 1: Phase 2 (`demo/aurora` branch) only begins after `depot/main` is pushed and `monaro-risk-dev` Cloud Build & Cloud Run are verified green.
