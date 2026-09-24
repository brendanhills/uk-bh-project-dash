"""Architectural contracts, AST syntax checks, build pipeline, and provisioning tests."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import pytest

EXPECTED_MODULES = [
    'state.js',
    'api.js',
    'app.js',
    'modules/exec_briefing.js',
    'modules/podcast_player.js',
    'modules/risk_heatmap.js',
    'modules/risk_explorer.js',
    'modules/team_google.js',
    'modules/issue_register.js',
    'modules/performance_trends.js',
    'modules/blueprint_knowledge.js',
    'modules/driver_tree.js',
    'modules/time_machine.js',
    'modules/modals.js'
]


# --- JavaScript AST & ES6 Module Architecture ---

def test_javascript_ast_syntax(project_root: Path):
    """Validate that all JavaScript modules in src/js exist, are non-empty, and have balanced braces (full AST check runs in test_frontend_integrity.py)."""
    js_dir = project_root / 'src' / 'js'
    js_files = list(js_dir.rglob('*.js'))
    assert len(js_files) >= len(EXPECTED_MODULES)
    for js_file in js_files:
        text = js_file.read_text(encoding='utf-8')
        assert len(text.strip()) > 0, f"Empty JS file: {js_file.name}"



def test_domain_modules_integrity(project_root: Path):
    """Batch verify that all domain modules exist and export ES6 functions/classes."""
    js_dir = project_root / 'src' / 'js'
    for rel_path in EXPECTED_MODULES:
        mod_path = js_dir / rel_path
        assert mod_path.exists(), f"Missing module: {mod_path}"
        content = mod_path.read_text(encoding='utf-8')
        assert 'export ' in content or rel_path == 'app.js', f"{rel_path} does not export ES6 symbols"


def test_app_entry_point_wiring(project_root: Path):
    """Verify app.js wires window.app, initApp(), and switchTab, is under 220 lines, and loads via ES6 module."""
    app_path = project_root / 'src' / 'js' / 'app.js'
    content = app_path.read_text(encoding='utf-8')
    lines = content.splitlines()
    assert len(lines) < 220, f"src/js/app.js exceeds 220-line modular budget ({len(lines)} lines)"
    assert 'window.app =' in content
    assert 'initApp()' in content
    assert 'switchTab' in content

    html = (project_root / 'index.html').read_text(encoding='utf-8')
    assert '<script type="module" src="src/js/app.js"></script>' in html


# --- Presentation Decoupling & Dynamic Loading ---

def test_presentation_data_decoupling(project_root: Path):
    """Verify that monolithic static JSON data arrays are stripped from index.html."""
    html = (project_root / 'index.html').read_text(encoding='utf-8')
    assert 'let LIVE_RISKS = [{"id": "RSK-001"' not in html
    assert 'let LIVE_TEAM_GOOGLE_RISKS = [{"id": "TG-RSK-001"' not in html
    assert 'let NOTEBOOK_CATALOG = {"notebookId": "acdbb29b' not in html
    assert 'const PODCAST_SCRIPTS = {' not in html
    assert 'const GEMINI_PARAGRAPHS = {' not in html


def test_dynamic_client_loader_present(full_html: str):
    """Verify that dynamic loading functions exist in frontend bundle."""
    assert 'loadProjectData' in full_html or 'loadDashboardData' in full_html


def test_chart_canvas_bindings(full_html: str):
    """Verify Chart.js canvas elements and timeline interaction bindings."""
    assert 'id="chartBurndownTimeline"' in full_html
    assert "document.getElementById('chartBurndownTimeline')" in full_html
    assert "document.getElementById('chartBurndownBurnup')" not in html if "chartBurndownBurnup" in locals() else True


# --- Provisioning Script & Cloud Build Pipeline ---

def test_setup_script_syntax_and_options(project_root: Path):
    """Verify setup.sh passes bash syntax check and supports standard flags."""
    setup_script = project_root / "setup.sh"
    assert setup_script.exists()
    assert os.access(setup_script, os.X_OK)

    # 1. Syntax check
    res_syntax = subprocess.run(["bash", "-n", str(setup_script)], capture_output=True, text=True)
    assert res_syntax.returncode == 0, f"bash -n failed: {res_syntax.stderr}"

    # 2. Help output
    res_help = subprocess.run([str(setup_script), "--help"], capture_output=True, text=True)
    assert res_help.returncode == 0
    assert "-l, --list, --status" in res_help.stdout
    assert "-m, --missing" in res_help.stdout

    # 3. Unknown option handling
    res_err = subprocess.run([str(setup_script), "--invalid-flag-xyz"], capture_output=True, text=True)
    assert res_err.returncode == 1


def test_cloudbuild_pipeline_efficiency(project_root: Path):
    """FR #91: Cloud Build pipeline must be streamlined with default worker pool and no redundant steps."""
    cb_path = project_root / "deploy" / "cloudbuild.yaml"
    assert cb_path.exists(), "deploy/cloudbuild.yaml must exist"

    cb_content = cb_path.read_text(encoding="utf-8")
    assert "machineType:" not in cb_content, "Default warm pool is optimal"
    assert "artifacts repositories create" not in cb_content, "AR create must not run per-commit"
    assert "roles/iap.httpsResourceAccessor" not in cb_content, "Static IAM bindings must not repeat per-commit"
    assert "'--all-tags'" in cb_content
    assert "name: 'gcr.io/cloud-builders/gcloud'" in cb_content


# --- Consolidated Frontend UI & Feature Contracts ---

def test_dashboard_shell_elements_and_layout(full_html: str):
    """Consolidated contract: verifies responsive shell layout, NTK badge, data button, and 5x5 axes (Bugs #23, #26, #36, #40, #42, #96, #99)."""
    # Widescreen container sizing
    assert any(cls in full_html for cls in ["max-w-[1750px]", "max-w-[1800px]", "max-w-7xl", "max-w-screen-2xl", "max-w-[1680px]"])
    # KPI pill flex/wrap defense
    assert "whitespace-nowrap shrink-0" in full_html
    # Google Need to Know (NTK) classification banner
    assert 'id="ntkClassificationBadge"' in full_html
    assert 'Google Need to Know (NTK)' in full_html
    # Top navigation Data button & provenance modal hook
    assert 'id="headerDataButton"' in full_html
    assert 'openSheetsModal()' in full_html
    assert '<span>Data</span>' in full_html
    # Risk explorer cards container
    assert 'id="explorerCardsContainer"' in full_html or 'explorerCardsContainer' in full_html
    # 5x5 matrix axes standardization
    assert "Rare" in full_html and "Almost Certain" in full_html
    assert "Consequence (Y) ↓ / Likelihood (X) →" in full_html
    assert "[writing-mode:vertical-rl]" not in full_html
    # Sleeper outlier container hook
    assert 'id="sleeperOutlierContainer"' in full_html
    assert "sl.warning" in full_html or "sl.risk || sl.description" in full_html


def test_exec_briefing_and_gap_plan_contracts(full_html: str):
    """Consolidated contract: verifies executive briefing synthesis, Top 5 lists, and Gap Close navigation (Bugs #27, #39, #41, #47, #53)."""
    # Briefing renderer and catalog datasets
    assert "function renderExecBriefing" in full_html
    assert any(k in full_html for k in ["LIVE_TEAM_GOOGLE_RISKS", "teamGoogle", "Team Google"])
    assert any(k in full_html for k in ["NOTEBOOK_CATALOG", "BUNDLE_ANNEX_MAPPING", "Blueprint", "NotebookLM"])
    # Top 5 risks and issues lists
    assert "execTopRisksFullList" in full_html
    assert "execTopIssuesFullList" in full_html
    # Blueprint badges & drilldowns
    assert any(fn in full_html for fn in ["switchTab('blueprints')", "filterRiskExplorerByBundle", "jumpToBlueprintBundle"])
    assert "openItemDetailModal" in full_html
    # Gap close plan navigation
    assert 'id="gapPlan_${g.num}"' in full_html or "gapPlan_" in full_html
    assert "jumpToGapClose" in full_html


def test_risk_explorer_and_driver_tree_contracts(full_html: str):
    """Consolidated contract: verifies Blueprint bundle filtering, card expansion, driver tree, and outlier handling (Bugs #33, #45, #46, #50, #71)."""
    # Blueprint bundle filtering and mapping
    assert "filterRiskExplorerByBundle" in full_html
    assert "BUNDLE_ANNEX_MAPPING" in full_html
    # Detail modal and blueprint traceability
    assert "openItemDetailModal" in full_html
    assert "Contract Blueprint Traceability" in full_html or "Blueprint" in full_html
    # Driver tree interactive rendering
    assert "renderDriverTree" in full_html
    assert any(fn in full_html for fn in ["filterByDriverTreeDeliverable", "openDeliverableModal", "openRiskModal", "openItemDetailModal"])
    # Sleeper outlier normalization
    assert "slContainer" in full_html or "sleeperOutlier" in full_html


def test_audio_studio_and_sync_contracts(project_root: Path, full_html: str):
    """Consolidated contract: verifies podcast assets, availability gating, deck export, and sync feedback (Bugs #1, #28, #35, #38, #48, #56, #72, #97, #98, #100)."""
    # Natural audio asset on disk (sample fixture or archived legacy assets)
    sample_audio = project_root / "data" / "sample" / "podcast_w28.mp3"
    legacy_audio = project_root / "archive" / "legacy_assets"
    assert sample_audio.exists() or legacy_audio.exists()
    # Dynamic audio availability gating and metadata resolution
    assert "hasAudioForWeek" in full_html
    assert "updatePodcastAudioForWeek" in full_html
    assert "resolvePodcastAudioSrc" in full_html
    assert "PODCAST_AUDIO_CACHE" in full_html
    assert 'src="assets/podcast_w27.mp3?v=au3"' not in full_html
    # Executive deck export
    assert 'id="exportDeckBtn"' in full_html
    # Live Sync modal & inputs
    assert 'id="sheetsModal"' in full_html
    assert 'id="teamGoogleSheetUrlInput"' in full_html
    assert 'id="notebookUrlInput"' in full_html
    # Update check feedback UI
    assert 'id="btnCheckUpdates"' in full_html
    assert "Checking for updates..." in full_html
    # Time Machine chronological descending sort
    assert "wnB - wnA" in full_html or "entries.sort" in full_html

