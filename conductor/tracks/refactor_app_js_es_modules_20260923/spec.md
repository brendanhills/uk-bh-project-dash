---
track_id: refactor_app_js_es_modules_20260923
type: refactor
focus: foundation
status: ACTIVE
bug_id: null
target_sdd_sections:
  - "2.1 Technology Stack & Architectural Decisions"
  - "3. Data Architecture & Multi-Project Isolation"
  - "6. Frontend Static Analysis & UI Testing Layer (conductor/tech-stack.md)"
---

# Specification: Refactor Monolithic `src/js/app.js` into Google-Standard ES6 Modules (Delta RFC)

## 1. Overview & Objectives
While `conductor/tracks/modularize_frontend_architecture_20260818` previously created initial 80–100 line placeholder modules under `src/js/modules/`, the production dashboard continued to execute a single monolithic `src/js/app.js` file spanning **4,266 lines (255 KB)** loaded as a classic `<script src="src/js/app.js" defer></script>` tag. The files in `src/js/modules/` were never wired into `app.js` or `index.html`, leaving `app.js` exempted as `sourceType: "script"` in `eslint.config.js`.

This **Foundation (`foundation`)** track decomposes `src/js/app.js` into cohesive, single-responsibility ES6 modules (`import`/`export`) adhering to the **Google JavaScript Style Guide (`go/js-practices` / `go/tsstyle`)**, reduces `src/js/app.js` to a lean (~200-line) bootstrapper, router, and explicit `window` controller bridge, and maintains **100% behavioral parity** with zero runtime bundler dependencies.

### Target Outcomes:
1. **Backend, Server & Asset De-Bloating (Pre-Modularization Sweep)**:
   - Prune unreachable/dead web mutation logic and legacy route aliases in `server.py`, retaining strict presentation-tier `403 Forbidden` guards (`_reject_if_read_only`), RAM-cached JSON/MP3 streaming (`ProjectDataStore`), and read-only status/provenance handlers.
   - Unify GCS blob upload/download/metadata helpers in `scripts/gemini_generator.py` and `scripts/pipeline.py` to delegate through `scripts/gcs_store.py`.
   - Remove 9.4 MB of uncompressed `.wav` audio duplicates (`assets/podcast_w26.wav`, `assets/podcast_w27.wav`) and obsolete local sync dumps (`data/sheets/live_synced_data.json`, `data/drive/weekly_snapshots.json`, `data/notebooks/registry.json`, `backup.json`).
2. **Eliminate Frontend Dead Code & Duplicate Handlers (~1,200 lines pruned)**:
   - Do **not** port dead or superseded functions into ES6 modules: delete hardcoded `PODCAST_TRANSCRIPT`, `togglePodcastPlay()`, and `openTranscriptModal()` (which target non-existent DOM IDs), remove `filterTeamGoogleMatrixCell_legacy()`, consolidate `initNotebookRegistry()`/`switchActiveNotebook()`/`ingestReport()` into read-only presentation stubs, and deduplicate overlapping helpers.
3. **Decompose `src/js/app.js` (4,268 lines → <220 lines)**: Extract all live domain logic, state management, and UI renderers from `src/js/app.js` into explicit ES6 modules under `src/js/` and `src/js/modules/`.
4. **Native Browser ES6 Module Execution (`<script type="module">`)**: Load `src/js/app.js` via `<script type="module" src="src/js/app.js"></script>` in `index.html`, eliminating the `sourceType: "script"` exemption in `eslint.config.js`.
5. **100% Inline HTML & Vitest Compatibility via Explicit Controller Bridge**: Register public UI handlers onto `window` (and `window.app`) in `src/js/app.js` and update `tests/frontend/dashboard_ux.test.js` so both browser `onclick="..."` handlers and headless Vitest (`happy-dom`) tests execute the modularized ES6 dependency graph directly.

---

## 2. Proposed Architectural Amendments

### 2.1 Module Decomposition Architecture (`src/js/` & `src/js/modules/`)

| Module Path | Responsibility & Extracted Symbols from `app.js` (Dead Code Pruned) | Est. Lines |
| :--- | :--- | :--- |
| **`src/js/state.js`** | **Shared Runtime State & Temporal Utilities**: Mutable reactive application store (`appState`), project/dataset references (`CURRENT_PROJECT`, `CONFIG`, `LIVE_RISKS`, `LIVE_TEAM_GOOGLE_RISKS`, `LIVE_ISSUES`, `TIME_MACHINE_SNAPSHOTS`, `DRIVER_TREE`, `DRIVER_TREE_ITEMS`, `DRIVE_REPORTS`, `NOTEBOOK_CATALOG`, `BUNDLE_ANNEX_MAPPING`, filter flags), `cleanField()`, `getLatestWeekKey()`, and temporal staleness helpers (`getSystemTimeContext`, `evaluateTargetStaleness`, `updateSystemTimeBadges`). | ~200 |
| **`src/js/api.js`** | **Data Loader, Project Branding & Read-Only Provenance Client**: `loadDashboardData()`, `loadProjectData()`, `renderProjectBranding()`, `renderFeatureTabs()`, `checkUrlViewParameters()`, `updateAllDynamicCounters()`, `openSheetsModal()`, `closeSheetsModal()`, `checkForUpdates()`, `checkDriveSyncStatus()`, `renderDriveReportsInModal()`, `syncAllWorkspaceSources()`, `syncGoogleSheet()`, `showSyncToast()`, `refreshNotebookSources()`, `toggleSheetDropdown()`. *(Prunes dead `/api/notebooks` and `/api/ingest` mutations).* | ~320 |
| **`src/js/modules/exec_briefing.js`** | **Executive Cockpit, Synthesis, Baseline Diffing & Top 5 Lists**: `renderExecBriefing()`, `setAiTone()`, `getGeminiParagraphsForWeek()`, `copyGeminiParagraph()`, `copyExecSummaryNote()`, `updateAtoGateKpi()`, `renderDiffBaselineSelector()`, `setDiffBaseline()`, `renderExecGapClosePlans()`, `toggleShowAllGapPlans()`, `toggleResolvedGapPlans()`, `renderTop5Risks()`, `renderTop5Issues()`. | ~420 |
| **`src/js/modules/podcast_player.js`** | **Executive Audio Briefing Player, Speech Fallback & Transcript Modal**: `getPodcastScriptForWeek()`, `resolvePodcastAudioSrc()`, `hasAudioForWeek()`, `updatePodcastAudioForWeek()`, `togglePodcastPlayback()`, `setPodcastSpeed()`, `formatAudioTime()`, `playPodcastFromIndex()`, `animateWaveform()`, `toggleTranscriptModal()`, `renderPodcastTranscript()`, `copyPodcastScript()`. *(Deletes dead `PODCAST_TRANSCRIPT`, `togglePodcastPlay`, `openTranscriptModal`).* | ~320 |
| **`src/js/modules/time_machine.js`** | **Time Machine Historical Scrubber & Snapshot Switcher**: `toggleTimeMachineModal()`, `closeTimeMachineModal()`, `renderTimeMachineModalList()`, `activateTimeMachine()`, `returnToPresent()`. | ~210 |
| **`src/js/modules/risk_heatmap.js`** | **5×5 Joint Risk Heatmap & Cell Filtering**: `MATRIX_SCORES_TABLE`, `CONSEQUENCE_NAMES`, `setRiskRating()`, `setRiskStatusFilter()`, `renderRiskHeatmap()`, `highlightHeatmapCell()`, `clearActiveCellFilter()`, `renderMatrix()`. | ~210 |
| **`src/js/modules/risk_explorer.js`** | **Live Risk Explorer Cards, Table, Quick Filters & Severity Bands**: `renderRiskExplorer()`, `renderSingleRiskCard()`, `renderExplorerTableMarkup()`, `setExplorerViewMode()`, `setQuickFilter()`, `resetAllFilters()`, `updateQuickFilterButtonsUI()`, `toggleCardExpansion()`, `toggleRiskCardExpand()`, `isUnactionedRisk()`, `renderRiskSeverityProfile()`, `drillDownToCategory()`, `drillDownToScoreBand()`. | ~440 |
| **`src/js/modules/team_google.js`** | **Team Google Secondary Risk Register Heatmap & Explorer**: `setTeamGoogleRating()`, `setTeamGoogleStatusFilter()`, `renderTeamGoogleHeatmap()`, `filterTeamGoogleMatrixCell()`, `clearTeamGoogleActiveCellFilter()`, `clearTeamGoogleMatrixCellFilter()`, `renderTeamGoogleRiskExplorer()`, `highlightTeamGoogleHeatmapCell()`. *(Deletes `filterTeamGoogleMatrixCell_legacy`).* | ~260 |
| **`src/js/modules/blueprint_knowledge.js`** | **Blueprint Bundle Annex Cards & Research Docs**: `renderBlueprintKnowledge()`, `renderBlueprintBundleCards()`, `renderResearchDocsCards()`, `filterRiskExplorerByBundle()`, `jumpToBlueprintBundle()`. | ~190 |
| **`src/js/modules/driver_tree.js`** | **Milestone 2 / CD1 Driver Tree & Cross-Tab Citation Jumps**: `setDriverTreeLevelFilter()`, `renderDriverTree()`, `jumpToDriverRef()`, `jumpToGapClose()`, `jumpToRiskExplorer()`, `filterByDriverTreeDeliverable()`. | ~220 |
| **`src/js/modules/issue_register.js`** | **Issue Register Table, PM Risk Ledger & CSV/PDF/JSON Exports**: `renderIssueTable()`, `filterAndRenderIssues()`, `renderLedger()`, `exportCSV()`, `exportDeckPDF()`, `exportExecutiveDeck()`. | ~210 |
| **`src/js/modules/modals.js`** | **Universal Item Detail Modal (`risk`, `google_risk`, `issue`)**: `openRiskModal()`, `openItemDetailModal()`, `closeItemDetailModal()`. | ~190 |
| **`src/js/modules/performance_trends.js`** | **Performance Trends Chart.js Visualizations & Timeline Drilldown Modal**: `setTrendsGranularity()`, `computeTimelineMetrics()`, `renderTrendsCharts()`, `openTimelineDrilldownModal()`, `closeTimelineDrilldownModal()`. | ~310 |
| **`src/js/app.js`** | **Application Bootstrap Entry Point, Tab Router & `window` Controller Bridge**: Imports all domain modules, implements `initApp()`, `switchTab()`, `popstate` history handler, binds global UI functions to `window` and `window.app`, and registers `DOMContentLoaded`. | ~170 |

---

## 3. Data Contracts & Interface Changes

1. **Shared State Access Contract (`src/js/state.js`)**:
   - Export a mutable `appState` object (and synchronized getter/setter helpers) holding all runtime state properties (`CURRENT_PROJECT`, `CONFIG`, `LIVE_RISKS`, `LIVE_TEAM_GOOGLE_RISKS`, `LIVE_ISSUES`, `TIME_MACHINE_SNAPSHOTS`, `DRIVER_TREE`, `DRIVER_TREE_ITEMS`, `DRIVE_REPORTS`, `NOTEBOOK_CATALOG`, `BUNDLE_ANNEX_MAPPING`, and UI filter variables) so cross-module mutations propagate deterministically without circular dependency deadlocks.
2. **HTML Entry Point (`index.html`)**:
   - Update `<script src="src/js/app.js" defer></script>` to `<script type="module" src="src/js/app.js"></script>` (note: `<script type="module">` is deferred by default per HTML5 spec).
3. **ESLint & Vitest Harness Updates (`eslint.config.js`, `tests/frontend/dashboard_ux.test.js`)**:
   - Remove the `files: ["src/js/app.js"], languageOptions: { sourceType: "script" }` override in `eslint.config.js` so all `src/js/**/*.js` files are linted strictly as ES2022 modules (`sourceType: "module"`).
   - Update `tests/frontend/dashboard_ux.test.js` to import `src/js/app.js` as a native ES module (`await import('../../src/js/app.js')` + `await window.loadDashboardData()`) rather than `window.eval(appJsCode)` on a classic script string.

---

## 4. Acceptance Criteria & Invariants

- [ ] `src/js/app.js` reduced from **4,266 lines** to **< 250 lines**, acting strictly as the ES6 module coordinator, router, and `window` bridge.
- [ ] All 13 domain modules under `src/js/` and `src/js/modules/` use explicit ES6 `import` / `export` statements with zero `sourceType: "script"` exemptions in `eslint.config.js`.
- [ ] `node --check` AST syntax validation passes across 100% of files in `src/js/*.js` and `src/js/modules/*.js`.
- [ ] `npm run verify` (ESLint 9 flat config + Vitest `dashboard_ux.test.js`) passes with 0 errors.
- [ ] Full Python test suite (`uv run pytest`) passes 100% (including `tests/test_frontend_integrity.py` and `tests/test_frontend_contracts.py`).
- [ ] Zero runtime build step required: `server.py` serves `index.html` and `src/js/**/*.js` directly to the browser with 100% feature parity across all 8 tabs (`exec-briefing`, `overview`, `team-google`, `issues`, `trends`, `blueprints`, `driver-tree`, `ledger`) and modals.

---

## 5. Out of Scope (Deferred to Future Tracks)
- **Bundler / Compiler Introduction**: Introducing Vite/Webpack/Rollup build compilation steps into Cloud Run or local runtime is explicitly out of scope (preserving the zero-build native browser ES6 module invariant).
- **Backend & GCS Storage/Config Refactors**: Explicitly deferred to Tracks `gcs_storage_and_config_sync_20260923` and `decouple_hardcoded_values_and_constants_20260923`.
- **Common Project Framework Script Migration**: Explicitly deferred to Track `common_project_framework_migration_20260923`.
- **Net-New UI Features & Stakeholder Views**: Explicitly deferred to Tracks `tailored_stakeholder_views` and `ondemand_podcast_generation_20260820`.
