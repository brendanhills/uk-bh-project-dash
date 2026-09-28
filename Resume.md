# 🚀 Work Handover & Launchpad

> **Active Focus**: Project Dash (Executive Risk & Horizon Dashboard) | **Cycle Focus**: 🎬 Demo Prep & Consolidation
> **Branch**: `feat/prompt-eval-and-ui-harness` | **Last Synced**: 2026-09-28 13:14

## 🎯 Immediate Starting Point
*Where to pick up work when you return:*
- **Next Command / Action**: `/conductor-implement consolidate_depot_and_aurora_demo_20260928`
- **Primary File to Open**: [`conductor/tracks/consolidate_depot_and_aurora_demo_20260928/plan.md`](file:///usr/local/google/home/brendanhills/dev/apps/project_dash/conductor/tracks/consolidate_depot_and_aurora_demo_20260928/plan.md)
- **Active State / Handover Notes**: Track `consolidate_depot_and_aurora_demo_20260928` scaffolded and pushed. Ready to execute Phase 1 (lock in `depot/main` & verify `monaro-risk-dev` Cloud Run with zero refactoring) followed by Phase 2–4 (`demo/aurora` branch, `uk-bh-demos` sync + GitHub CI, and `uk-bh-experiments-argolis` Cloud Run deploy in `australia-southeast1` with IAP).

## 📋 Actionable TODOs

### Active (Current In-Flight Work)
- [ ] **#105 [robustness] CI Validation**: Verify Depot GitHub Actions runner executes `deploy` job cleanly on `dev` push
- [ ] **#106 PR Merge**: Open and merge Depot PR for `fix/ci-secrets-syntax` into `main`
- [ ] **#128 Retire legacy STRICT_READ_ONLY=False local-disk mutation ...**: Retire legacy STRICT_READ_ONLY=False local-disk mutation routes in server.py (L455-L885) after GCS ProjectDataStore is fully road-tested
- [ ] **#129 Sanitize and squash git subtree history for project_dash ...**: Sanitize and squash git subtree history for project_dash in cloud-gtm/uk-bh-demos so zero historical depot commits are in the public demo commit graph
- [ ] **#130 Review .agents/backlog_archive.json retention and gitigno...**: Review .agents/backlog_archive.json retention and gitignore policy after road-testing unified backlog workflow

### Code Improvements & Tech Debt (Not Bugs)
- [ ] **#107 Track Review**: Evaluate status of Track `ondemand_podcast_generation_20260820` against current codebase

### Demo Scope & Next Phases (Deferred Milestones)
- [ ] **#109 Stakeholder Views**: Implement tailored stakeholder views (Exec, PM, and Tech URL-driven views)

## ⚠️ Watch-outs & Blockers
- None
