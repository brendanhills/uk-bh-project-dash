# 🚀 Work Handover & Launchpad

> **Active Focus**: Project Dash (Executive Risk & Horizon Dashboard)
> **Branch**: `feat/prompt-eval-and-ui-harness` | **Last Synced**: 2026-09-22 11:00

## 🎯 Immediate Starting Point
*Where to pick up work when you return:*
- **Next Command / Action**: `uv run pytest tests/test_prompt_integrity.py` or `npm run verify`
- **Primary File to Open**: [`scripts/gemini_generator.py:192`](file:///usr/local/google/home/brendanhills/dev/apps/project_dash/scripts/gemini_generator.py#L192) (`build_podcast_prompt`)
- **Active State / Handover Notes**: Prompts standardized on RASCEF XML; prompt decoupling resolved via `build_podcast_prompt`; Tier 1 prompt integrity suite passing; 122/122 pytest unit tests & 6/6 Vitest UX tests passing.

## 📋 Actionable TODOs

### Active (Current In-Flight Work)
- [ ] **CI Validation**: Verify Depot GitHub Actions runner executes `deploy` job cleanly on `dev` push
- [ ] **PR Merge**: Open and merge Depot PR for `fix/ci-secrets-syntax` into `main`

### Code Improvements & Tech Debt (Not Bugs)
- [ ] **Track Review**: Evaluate status of Track `ondemand_podcast_generation_20260820` against current codebase
- [ ] **Test Performance**: Profile long-running podcast generation test cases in `tests/test_sync_podcast_generation.py`

### Demo Scope & Next Phases (Deferred Milestones)
- [ ] **Stakeholder Views**: Implement tailored stakeholder views (Exec, PM, and Tech URL-driven views)

## ⚠️ Watch-outs & Blockers
- Depot requires SSH signed commits (`auto_init_ed25519.pub`). Direct pushes to `main` are restricted by branch protections; use PRs.
