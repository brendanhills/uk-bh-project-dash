# 🚀 Work Handover & Launchpad

> **Active Focus**: Project Dash (Executive Risk & Horizon Dashboard)
> **Branch**: `fix/ci-secrets-syntax` | **Last Synced**: 2026-09-11 14:00

## 🎯 Immediate Starting Point
*Where to pick up work when you return:*
- **Next Command / Action**: `uv run pytest` (112 tests, ~73s) or `./run_server.sh`
- **Primary File to Open**: [`.github/workflows/ci.yml`](file:///usr/local/google/home/brendanhills/dev/apps/project_dash/.github/workflows/ci.yml)
- **Active State / Handover Notes**: All 112 unit tests passing; Depot CI workflow configured for dev/main auto-deployment.

## 📋 Actionable TODOs

### Active (Current In-Flight Work)
- [ ] **CI Validation**: Verify Depot GitHub Actions runner executes `deploy` job cleanly on `dev` push
- [ ] **PR Merge**: Open and merge Depot PR for `fix/ci-secrets-syntax` into `main`

### Code Improvements & Tech Debt (Not Bugs)
- [ ] **Track Review**: Evaluate status of Track `ondemand_podcast_generation_20260820` against current codebase
- [ ] **Test Performance**: Profile long-running podcast generation test cases in `tests/test_sync_podcast_generation.py`

### Demo Scope & Next Phases (Deferred Milestones)
- [ ] **Stakeholder Views**: Implement tailored stakeholder views (Exec, PM, and Tech URL-driven views)

### Done Recently (Pruned on Next Checkpoint)
- [x] **Depot CI Fix**: Fixed secrets `if` condition and enabled auto-deploy on `dev` branch
- [x] **Test Verification**: 112/112 pytest unit tests passing cleanly in standalone workspace

## ⚠️ Watch-outs & Blockers
- Depot requires SSH signed commits (`auto_init_ed25519.pub`). Direct pushes to `main` are restricted by branch protections; use PRs.
