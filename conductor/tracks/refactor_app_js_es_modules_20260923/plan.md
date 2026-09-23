# Implementation Plan: Refactor Monolithic `src/js/app.js` into Google-Standard ES6 Modules

## Phase 1: Shared State Store (`state.js`), Pure Analytics (`analytics.js`) & Data/Sync API Client (`api.js`)
- [ ] Task: Write Module Contract & State Propagation Tests (TDD)
  - [ ] Add assertions in `tests/test_frontend_contracts.py` verifying that `src/js/app.js` is under 250 lines, loaded via `<script type="module" src="src/js/app.js"></script>`, and imports domain modules from `src/js/` and `src/js/modules/`
  - [ ] Add unit test cases in `tests/frontend/dashboard_ux.test.js` verifying shared state access and `window` controller bridge exports
- [ ] Task: Refactor `src/js/state.js` into the Authoritative Shared Runtime State & Temporal Engine
  - [ ] Export mutable `appState` container holding all runtime dataset and UI filter state (`CURRENT_PROJECT`, `CONFIG`, `NOTEBOOK_CATALOG`, `BUNDLE_ANNEX_MAPPING`, `LIVE_RISKS`, `LIVE_TEAM_GOOGLE_RISKS`, `LIVE_ISSUES`, `TIME_MACHINE_SNAPSHOTS`, `DRIVER_TREE`, `DRIVER_TREE_ITEMS`, `DRIVE_REPORTS`, `NOTEBOOK_REGISTRY`, `ACTIVE_NOTEBOOK_SLUG`, matrix ratings/statuses, active cell filters, `activeTimeMachineWeek`, `selectedDiffBaseline`, `currentQuickFilter`, `explorerViewMode`, `expandedRiskIds`, `expandedCardIds`, `currentAiTone`, `isPodcastPlaying`, `podcastPlaybackSpeed`, `PODCAST_AUDIO_CACHE`)
  - [ ] Extract and export `cleanField()`, `getLatestWeekKey()`, `getSystemTimeContext()`, `evaluateTargetStaleness()`, and `updateSystemTimeBadges()`
- [ ] Task: Refactor `src/js/api.js` into the Data Loader, Branding & Workspace Sync Module
  - [ ] Extract and export `loadDashboardData()`, `renderProjectBranding()`, `renderFeatureTabs()`, `checkUrlViewParameters()`, and `updateAllDynamicCounters()`
  - [ ] Extract and export Workspace Sync & NotebookLM controllers (`openSheetsModal`, `closeSheetsModal`, `checkForUpdates`, `checkDriveSyncStatus`, `renderDriveReportsInModal`, `ingestReport`, `syncAllWorkspaceSources`, `syncGoogleSheet`, `showSyncToast`, `initNotebookRegistry`, `renderNotebookDropdown`, `switchActiveNotebook`, `triggerNotebookSync`, `toggleSheetDropdown`)
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 2: Executive Cockpit, Podcast Audio Player & Time Machine Modules
- [ ] Task: Write Unit Tests for Executive Briefing, Audio Player & Time Machine Modules (TDD)
  - [ ] Verify tone switching (`setAiTone`), baseline diff selector (`setDiffBaseline`), podcast playback/transcript gating (`togglePodcastPlayback`, `toggleTranscriptModal`), and time travel (`activateTimeMachine`, `returnToPresent`) in `tests/frontend/dashboard_ux.test.js`
- [ ] Task: Implement `src/js/modules/exec_briefing.js`
  - [ ] Extract and export `renderExecBriefing()`, `setAiTone()`, `getGeminiParagraphsForWeek()`, `copyGeminiParagraph()`, `copyExecSummaryNote()`, and `updateAtoGateKpi()`
  - [ ] Extract and export `renderDiffBaselineSelector()`, `setDiffBaseline()`, `renderExecGapClosePlans()`, `toggleShowAllGapPlans()`, `toggleResolvedGapPlans()`, `renderTop5Risks()`, and `renderTop5Issues()`
- [ ] Task: Implement `src/js/modules/podcast_player.js`
  - [ ] Extract and export `getPodcastScriptForWeek()`, `resolvePodcastAudioSrc()`, `hasAudioForWeek()`, `updatePodcastAudioForWeek()`, `togglePodcastPlayback()`, `setPodcastSpeed()`, `formatAudioTime()`, `playPodcastFromIndex()`, `animateWaveform()`, `toggleTranscriptModal()`, `renderPodcastTranscript()`, `copyPodcastScript()`, `togglePodcastPlay()`, and `openTranscriptModal()`
- [ ] Task: Implement `src/js/modules/time_machine.js`
  - [ ] Extract and export `toggleTimeMachineModal()`, `closeTimeMachineModal()`, `renderTimeMachineModalList()`, `activateTimeMachine()`, and `returnToPresent()`
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: Risk Heatmaps, Explorers, Team Google, Blueprints, Driver Tree, Issues, Trends & Modals
- [ ] Task: Write Unit Tests for Domain Renderers & Cross-Tab Citations (TDD)
  - [ ] Verify 5×5 heatmap cell filtering (`highlightHeatmapCell`, `filterTeamGoogleMatrixCell`), quick filter pills, driver tree level filters, and universal item detail modal (`openItemDetailModal`)
- [ ] Task: Implement `src/js/modules/risk_heatmap.js` & `src/js/modules/risk_explorer.js`
  - [ ] Implement `src/js/modules/risk_heatmap.js` (`MATRIX_SCORES_TABLE`, `CONSEQUENCE_NAMES`, `setRiskRating`, `setRiskStatusFilter`, `renderRiskHeatmap`, `highlightHeatmapCell`, `clearActiveCellFilter`, `renderMatrix`)
  - [ ] Implement `src/js/modules/risk_explorer.js` (`renderRiskExplorer`, `renderSingleRiskCard`, `renderExplorerTableMarkup`, `setExplorerViewMode`, `setQuickFilter`, `resetAllFilters`, `updateQuickFilterButtonsUI`, `toggleCardExpansion`, `toggleRiskCardExpand`, `isUnactionedRisk`, `renderRiskSeverityProfile`, `drillDownToCategory`, `drillDownToScoreBand`)
- [ ] Task: Implement `src/js/modules/team_google.js` & `src/js/modules/blueprint_knowledge.js`
  - [ ] Implement `src/js/modules/team_google.js` (`setTeamGoogleRating`, `setTeamGoogleStatusFilter`, `renderTeamGoogleHeatmap`, `filterTeamGoogleMatrixCell`, `filterTeamGoogleMatrixCell_legacy`, `clearTeamGoogleActiveCellFilter`, `clearTeamGoogleMatrixCellFilter`, `renderTeamGoogleRiskExplorer`, `highlightTeamGoogleHeatmapCell`)
  - [ ] Implement `src/js/modules/blueprint_knowledge.js` (`renderBlueprintKnowledge`, `renderBlueprintBundleCards`, `renderResearchDocsCards`, `filterRiskExplorerByBundle`, `jumpToBlueprintBundle`)
- [ ] Task: Implement `src/js/modules/driver_tree.js`, `src/js/modules/issue_register.js`, `src/js/modules/performance_trends.js` & `src/js/modules/modals.js`
  - [ ] Implement `src/js/modules/driver_tree.js` (`setDriverTreeLevelFilter`, `renderDriverTree`, `jumpToDriverRef`, `jumpToGapClose`, `jumpToRiskExplorer`, `filterByDriverTreeDeliverable`)
  - [ ] Implement `src/js/modules/issue_register.js` (`renderIssueTable`, `filterAndRenderIssues`, `renderLedger`, `exportCSV`, `exportDeckPDF`, `exportExecutiveDeck`)
  - [ ] Implement `src/js/modules/performance_trends.js` (`setTrendsGranularity`, `computeTimelineMetrics`, `renderTrendsCharts`, `openTimelineDrilldownModal`, `closeTimelineDrilldownModal`)
  - [ ] Implement `src/js/modules/modals.js` (`openRiskModal`, `openItemDetailModal`, `closeItemDetailModal`)
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 4: Lean ES6 Bootstrapper (`app.js`), `<script type="module">`, ESLint & Vitest Suite Verification
- [ ] Task: Refactor `src/js/app.js` (<250 lines) & Update `index.html`
  - [ ] Replace the 4,266-line `src/js/app.js` with a lean ~180-line ES6 coordinator importing all domain modules, implementing `initApp()`, `switchTab()`, `popstate` history router, and binding public handlers to `window` and `window.app`
  - [ ] Update `index.html` script tag from `<script src="src/js/app.js" defer></script>` to `<script type="module" src="src/js/app.js"></script>`
- [ ] Task: Enforce Strict ES Module Linting (`eslint.config.js`) & Update Vitest Harness (`dashboard_ux.test.js`)
  - [ ] Remove the `sourceType: "script"` override for `src/js/app.js` in `eslint.config.js`
  - [ ] Update `tests/frontend/dashboard_ux.test.js` to load `src/js/app.js` via ES module import rather than classic `window.eval()`
- [ ] Task: Full End-to-End Verification (`node --check`, `npm run verify`, `uv run pytest`)
  - [ ] Verify 0 syntax or lint warnings via `npm run verify`
  - [ ] Verify 100% pass rate across all Python unit and contract tests via `uv run pytest`
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
