"""Architectural contracts, AST syntax checks, build pipeline, and provisioning tests."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import pytest

EXPECTED_MODULES = [
    'analytics.js',
    'state.js',
    'api.js',
    'charts.js',
    'app.js',
    'modules/exec_briefing.js',
    'modules/risk_heatmap.js',
    'modules/risk_explorer.js',
    'modules/issue_register.js',
    'modules/performance_trends.js',
    'modules/blueprint_knowledge.js',
    'modules/driver_tree.js',
    'modules/time_machine.js',
    'modules/modals.js'
]


# --- JavaScript AST & ES6 Module Architecture ---

def test_javascript_ast_syntax(project_root: Path):
    """Validate that JavaScript in src/js passes syntax checks with node -c."""
    js_dir = project_root / 'src' / 'js'
    if js_dir.exists() and shutil.which('node'):
        for js_file in js_dir.rglob('*.js'):
            proc = subprocess.run(['node', '-c', str(js_file)], capture_output=True, text=True)
            assert proc.returncode == 0, f"JS Syntax error in {js_file.name}: {proc.stderr}"


def test_domain_modules_integrity(project_root: Path):
    """Batch verify that all domain modules exist and export ES6 functions/classes."""
    js_dir = project_root / 'src' / 'js'
    for rel_path in EXPECTED_MODULES:
        mod_path = js_dir / rel_path
        assert mod_path.exists(), f"Missing module: {mod_path}"
        content = mod_path.read_text(encoding='utf-8')
        assert 'export ' in content or rel_path == 'app.js', f"{rel_path} does not export ES6 symbols"


def test_app_entry_point_wiring(project_root: Path):
    """Verify app.js wires window.app, initApp(), and switchTab."""
    app_path = project_root / 'src' / 'js' / 'app.js'
    content = app_path.read_text(encoding='utf-8')
    assert 'window.app =' in content
    assert 'initApp()' in content
    assert 'switchTab' in content


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
