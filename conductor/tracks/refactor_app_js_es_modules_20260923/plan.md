# Implementation Plan: Refactor Monolithic `src/js/app.js` into Google-Standard ES6 Modules & De-Bloat Platform

## Phase 0: Backend, Server & Tracked Asset De-Bloating (`server.py`, `scripts/`, `assets/`, `data/`)
- [x] Task: Remove Uncompressed Audio Bloat & Obsolete Local Data Dumps
  - [x] Delete 9.4 MB uncompressed `.wav` audio duplicates (`assets/podcast_w26.wav`, `assets/podcast_w27.wav`) while retaining `.mp3` assets
  - [x] Remove obsolete local sync dumps (`data/sheets/live_synced_data.json`, `data/drive/weekly_snapshots.json`, `data/notebooks/registry.json`, `backup.json`) superseded by GCS `ProjectDataStore`
- [x] Task: Streamline `server.py` & Consolidate GCS Helper Plumbing
  - [x] Simplify `server.py` by removing dead filesystem fallback paths (`src/data/live_synced_data.json`, `data/notebook/sources_catalog.json`) and consolidating route aliases while preserving strict read-only `403 Forbidden` security invariants and unit test contracts
  - [x] Delegate default project resolution in `server.py` through `resolve_configured_projects()` in `scripts/gcs_store.py`

## Phase 1: Shared State Store (`state.js`), Pure Analytics (`analytics.js`) & Data/Sync API Client (`api.js`) (With Dead-Code Pruning)
- [x] Task: Write Module Contract & State Propagation Tests (TDD)
  - [x] Add assertions in `tests/test_frontend_contracts.py` verifying that `src/js/app.js` is under 220 lines, loaded via `<script type="module" src="src/js/app.js"></script>`, imports domain modules from `src/js/` and `src/js/modules/`, and omits dead legacy symbols (`PODCAST_TRANSCRIPT`, `togglePodcastPlay`, `filterTeamGoogleMatrixCell_legacy`)
  - [x] Add unit test cases in `tests/frontend/dashboard_ux.test.js` verifying shared state access and `window` controller bridge exports
- [x] Task: Refactor `src/js/state.js` into the Authoritative Shared Runtime State & Temporal Engine
  - [x] Export mutable `appState` container holding all runtime dataset and UI filter state (`CURRENT_PROJECT`, `CONFIG`, `NOTEBOOK_CATALOG`, `BUNDLE_ANNEX_MAPPING`, `LIVE_RISKS`, `LIVE_TEAM_GOOGLE_RISKS`, `LIVE_ISSUES`, `TIME_MACHINE_SNAPSHOTS`, `DRIVER_TREE`, `DRIVER_TREE_ITEMS`, `DRIVE_REPORTS`, matrix ratings/statuses, active cell filters, `activeTimeMachineWeek`, `selectedDiffBaseline`, `currentQuickFilter`, `explorerViewMode`, `expandedRiskIds`, `expandedCardIds`, `currentAiTone`, `isPodcastPlaying`, `podcastPlaybackSpeed`, `PODCAST_AUDIO_CACHE`)
  - [x] Extract and export `cleanField()`, `getLatestWeekKey()`, `getSystemTimeContext()`, `evaluateTargetStaleness()`, and `updateSystemTimeBadges()`
- [x] Task: Refactor `src/js/api.js` into the Read-Only Data Loader, Branding & Provenance Module
  - [x] Extract and export `initApp()`, `loadDashboardData()`, `loadProjectData()`, `renderProjectBranding()`, `renderFeatureTabs()`, `checkUrlViewParameters()`, and `updateAllDynamicCounters()`
  - [x] Extract and export read-only provenance & modal helpers (`openSheetsModal`, `closeSheetsModal`, `checkForUpdates`, `checkDriveSyncStatus`, `renderDriveReportsInModal`, `syncAllWorkspaceSources`, `syncGoogleSheet`, `showSyncToast`, `refreshNotebookSources`, `toggleSheetDropdown`), pruning dead `/api/notebooks` and `/api/ingest` mutations
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 2: Executive Cockpit, Podcast Audio Player & Time Machine Modules
- [x] Task: Write Unit Tests for Executive Briefing, Audio Player & Time Machine Modules (TDD)
  - [x] Verify tone switching (`setAiTone`), baseline diff selector (`setDiffBaseline`), podcast playback/transcript gating (`togglePodcastPlayback`, `toggleTranscriptModal`), and time travel (`activateTimeMachine`, `returnToPresent`) in `tests/frontend/dashboard_ux.test.js`
- [x] Task: Implement `src/js/modules/exec_briefing.js`
  - [x] Extract and export `renderExecBriefing()`, `setAiTone()`, `getGeminiParagraphsForWeek()`, `copyGeminiParagraph()`, `copyExecSummaryNote()`, and `updateAtoGateKpi()`
  - [x] Extract and export `renderDiffBaselineSelector()`, `setDiffBaseline()`, `renderExecGapClosePlans()`, `toggleShowAllGapPlans()`, `toggleResolvedGapPlans()`, `renderTop5Risks()`, and `renderTop5Issues()`
- [x] Task: Implement `src/js/modules/podcast_player.js` (Pruning Dead Legacy Audio Code)
  - [x] Extract and export `getPodcastScriptForWeek()`, `resolvePodcastAudioSrc()`, `hasAudioForWeek()`, `updatePodcastAudioForWeek()`, `togglePodcastPlayback()`, `setPodcastSpeed()`, `formatAudioTime()`, `playPodcastFromIndex()`, `animateWaveform()`, `toggleTranscriptModal()`, `renderPodcastTranscript()`, and `copyPodcastScript()` (deleting dead `PODCAST_TRANSCRIPT`, `togglePodcastPlay`, and `openTranscriptModal`)
- [x] Task: Implement `src/js/modules/time_machine.js`
  - [x] Extract and export `toggleTimeMachineModal()`, `closeTimeMachineModal()`, `renderTimeMachineModalList()`, `activateTimeMachine()`, and `returnToPresent()`
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: Risk Heatmaps, Explorers, Team Google, Blueprints, Driver Tree, Issues, Trends & Modals
- [x] Task: Write Unit Tests for Domain Renderers & Cross-Tab Citations (TDD)
  - [x] Verify 5×5 heatmap cell filtering (`highlightHeatmapCell`, `filterTeamGoogleMatrixCell`), quick filter pills, driver tree level filters, and universal item detail modal (`openItemDetailModal`)
- [x] Task: Implement `src/js/modules/risk_heatmap.js` & `src/js/modules/risk_explorer.js`
  - [x] Implement `src/js/modules/risk_heatmap.js` (`MATRIX_SCORES_TABLE`, `CONSEQUENCE_NAMES`, `setRiskRating`, `setRiskStatusFilter`, `renderRiskHeatmap`, `highlightHeatmapCell`, `clearActiveCellFilter`, `renderMatrix`)
  - [x] Implement `src/js/modules/risk_explorer.js` (`renderRiskExplorer`, `setExplorerViewMode`, `setQuickFilter`, `resetAllFilters`, `updateQuickFilterButtonsUI`, `toggleCardExpansion`, `toggleRiskCardExpand`, `isUnactionedRisk`, `renderRiskSeverityProfile`, `drillDownToCategory`, `drillDownToScoreBand`)
- [x] Task: Implement `src/js/modules/team_google.js` & `src/js/modules/blueprint_knowledge.js`
  - [x] Implement `src/js/modules/team_google.js` (`setTeamGoogleRating`, `setTeamGoogleStatusFilter`, `renderTeamGoogleHeatmap`, `filterTeamGoogleMatrixCell`, `clearTeamGoogleActiveCellFilter`, `clearTeamGoogleMatrixCellFilter`, `renderTeamGoogleRiskExplorer`, `highlightTeamGoogleHeatmapCell`)
  - [x] Implement `src/js/modules/blueprint_knowledge.js` (`renderBlueprintKnowledge`, `renderBlueprintBundleCards`, `renderResearchDocsCards`, `filterRiskExplorerByBundle`, `jumpToBlueprintBundle`)
- [x] Task: Implement `src/js/modules/driver_tree.js`, `src/js/modules/issue_register.js`, `src/js/modules/performance_trends.js` & `src/js/modules/modals.js`
  - [x] Implement `src/js/modules/driver_tree.js` (`setDriverTreeLevelFilter`, `renderDriverTree`, `jumpToDriverRef`, `jumpToGapClose`, `jumpToRiskExplorer`, `filterByDriverTreeDeliverable`)
  - [x] Implement `src/js/modules/issue_register.js` (`renderIssueTable`, `filterAndRenderIssues`, `renderLedger`, `exportCSV`, `exportDeckPDF`, `exportExecutiveDeck`)
  - [x] Implement `src/js/modules/performance_trends.js` (`setTrendsGranularity`, `computeTimelineMetrics`, `renderTrendsCharts`, `openTimelineDrilldownModal`, `closeTimelineDrilldownModal`)
  - [x] Implement `src/js/modules/modals.js` (`openRiskModal`, `openItemDetailModal`, `closeItemDetailModal`)
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 4: Lean ES6 Bootstrapper (`app.js`), `<script type="module">`, ESLint & Vitest Suite Verification
- [x] Task: Refactor `src/js/app.js` (<220 lines) & Update `index.html`
  - [x] Replace the 4,269-line `src/js/app.js` with a lean 92-line ES6 coordinator importing all domain modules, implementing `initApp()`, `switchTab()`, and binding public handlers to `window` and `window.app`
  - [x] Update `index.html` script tag from `<script src="src/js/app.js" defer></script>` to `<script type="module" src="src/js/app.js"></script>`
- [x] Task: Enforce Strict ES Module Linting (`eslint.config.js`) & Update Vitest Harness (`dashboard_ux.test.js`)
  - [x] Remove the `sourceType: "script"` override for `src/js/app.js` in `eslint.config.js`
  - [x] Update `tests/frontend/dashboard_ux.test.js` to load `src/js/app.js` via ES module import rather than classic `window.eval()`
- [x] Task: Full End-to-End Verification (`node --check`, `npm run verify`, `uv run pytest`)
  - [x] Verify 0 syntax or lint warnings via `npm run verify`
  - [x] Verify 100% pass rate across all Python unit and contract tests via `uv run pytest`
- [~] Task: User Verification & Sign-Off
