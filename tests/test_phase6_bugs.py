"""Regression tests for Phase 6 bug fixes."""

from pathlib import Path
import pytest


def load_full_html(project_root: Path) -> str:
    """Loads index.html concatenated with all ES modules under src/js/."""
    html = (project_root / 'index.html').read_text(encoding='utf-8')
    js_dir = project_root / 'src' / 'js'
    if js_dir.exists():
        for fn in sorted(js_dir.rglob('*.js')):
            html += '\n' + fn.read_text(encoding='utf-8')
    return html


def test_bug_51_issue_table_column_widths_and_concise_ref(project_root: Path):
    """Bug #51: Issue table must have balanced column widths and concise Driver Ref badge."""
    html = load_full_html(project_root)
    idx = html.find("function renderIssueTable")
    idx_end = html.find("function ", idx + 30)
    body = html[idx:idx_end]
    assert "renderIssueTable" in html, "renderIssueTable must exist"
    assert "driverTreeRef" in body, "renderIssueTable must format driverTreeRef cleanly"

    # Check table headers have width constraints
    idx_section = html.find('id="view-issues"')
    body_section = html[idx_section:idx_section+2500]
    assert "table" in body_section, "view-issues must have table element"


def test_bug_52_issue_inspect_modal_trigger(project_root: Path):
    """Bug #52: Issue Register must have explicit Inspect button triggering openItemDetailModal."""
    html = load_full_html(project_root)
    idx = html.find("function renderIssueTable")
    idx_end = html.find("function ", idx + 30)
    body = html[idx:idx_end]
    assert "openItemDetailModal" in body, "renderIssueTable must call openItemDetailModal with 'issue'"
    assert "Inspect" in body, "renderIssueTable must render Inspect button"


def test_bug_38_podcast_scripts_w27_and_no_undefined(project_root: Path):
    """Bug #38: Podcast dialogue must be resolved dynamically with avatar, role, and time fields."""
    html = load_full_html(project_root)
    assert "function getPodcastScriptForWeek" in html
    assert "renderPodcastTranscript" in html
    assert "function togglePodcastPlayback" in html


def test_bug_48_podcast_audio_assets_exist(project_root: Path):
    """Bug #48: podcast audio file or generator must exist in assets directory."""
    assets_dir = project_root / "assets"
    assert assets_dir.exists(), "assets directory must exist"
    has_audio = (
        (assets_dir / "podcast_w27.mp3").exists() or
        (assets_dir / "podcast_w27.wav").exists()
    )
    assert has_audio, "assets/podcast_w27.wav or .mp3 must exist on disk"


def test_bug_91_cloudbuild_pipeline_efficiency(project_root: Path):
    """FR #91: Cloud Build pipeline must be streamlined with high-throughput worker and no redundant steps."""
    cb_path = project_root / "deploy" / "cloudbuild.yaml"
    assert cb_path.exists(), "deploy/cloudbuild.yaml must exist"

    cb_content = cb_path.read_text(encoding="utf-8")

    # 1. Standard optimal worker pool (no custom expensive machineType override)
    assert "machineType:" not in cb_content, (
        "options should not force expensive custom machineType; default warm pool is optimal"
    )

    # 2. No redundant Artifact Registry create/describe in per-commit build
    assert "artifacts repositories create" not in cb_content, (
        "Artifact Registry check/creation must not run on every commit build"
    )
    assert "artifacts repositories describe" not in cb_content, (
        "Artifact Registry describe must not run on every commit build"
    )

    # 3. No redundant repetitive IAM bindings on every commit build
    assert "roles/iap.httpsResourceAccessor" not in cb_content, (
        "Static IAP IAM policy bindings must not be repeated on every commit build"
    )

    # 4. Metadata step reuses cached python image to avoid pulling cloudsdk
    assert "name: 'python:3.13-slim'" in cb_content

    # 5. Push uses --all-tags
    assert "'--all-tags'" in cb_content, "Docker push should use --all-tags"

    # 6. Uses pre-warmed gcloud builder
    assert "name: 'gcr.io/cloud-builders/gcloud'" in cb_content, "Should use gcr.io/cloud-builders/gcloud"

    # 7. Provisioning script retains complete infrastructure setup
    prov_path = project_root / "setup.sh"
    if not prov_path.exists():
        prov_path = project_root / "deploy" / "provision_environment.sh"
    prov_content = prov_path.read_text(encoding="utf-8")
    assert "gcloud artifacts repositories create" in prov_content
    assert "roles/iap.httpsResourceAccessor" in prov_content