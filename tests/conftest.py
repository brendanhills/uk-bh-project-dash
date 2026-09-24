"""Shared pytest fixtures for Project Dash test suites.

Provides standardized fixtures for sample datasets, project configurations,
temporary isolated workspaces, and pipeline mocking.
"""

import json
import os
import shutil
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def full_html(project_root: Path) -> str:
    """Loads index.html concatenated with all ES modules under src/js/ once per test session."""
    html_file = project_root / "index.html"
    html = html_file.read_text(encoding="utf-8")
    js_dir = project_root / "src" / "js"
    if js_dir.exists():
        for js_path in sorted(js_dir.rglob("*.js")):
            html += "\n" + js_path.read_text(encoding="utf-8")
    return html


@pytest.fixture(scope="session")
def sample_project_dir(project_root: Path) -> Path:
    """Returns the Path to data/sample/ directory."""
    return project_root / "data" / "sample"


@pytest.fixture(scope="session")
def sample_dir(sample_project_dir: Path) -> Path:
    """Alias for sample_project_dir."""
    return sample_project_dir


@pytest.fixture(scope="session")
def sample_config(sample_project_dir: Path) -> dict:
    """Loads and returns data/sample/config.json."""
    config_path = sample_project_dir / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def sample_risks(sample_project_dir: Path) -> list:
    """Loads and returns data/sample/risks.json."""
    risks_path = sample_project_dir / "risks.json"
    with open(risks_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("risks", data) if isinstance(data, dict) else data


@pytest.fixture(scope="session")
def sample_issues(sample_project_dir: Path) -> list:
    """Loads and returns data/sample/issues.json."""
    issues_path = sample_project_dir / "issues.json"
    with open(issues_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("issues", data) if isinstance(data, dict) else data


@pytest.fixture(scope="session")
def sample_snapshots(sample_project_dir: Path) -> dict:
    """Loads and returns data/sample/snapshots.json."""
    snapshots_path = sample_project_dir / "snapshots.json"
    with open(snapshots_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def sample_driver_tree(sample_project_dir: Path) -> dict:
    """Loads and returns data/sample/driver_tree.json."""
    driver_tree_path = sample_project_dir / "driver_tree.json"
    with open(driver_tree_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def sample_knowledge(sample_project_dir: Path) -> dict:
    """Loads and returns data/sample/knowledge.json."""
    knowledge_path = sample_project_dir / "knowledge.json"
    with open(knowledge_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def tmp_project_workspace(tmp_path: Path, sample_project_dir: Path) -> Path:
    """Creates a temporary, isolated workspace directory pre-populated with sample project data.
    
    Returns the root path containing a sample/ subdirectory.
    """
    workspace = tmp_path / "data"
    workspace.mkdir(parents=True, exist_ok=True)
    target_sample = workspace / "sample"
    shutil.copytree(sample_project_dir, target_sample)
    return workspace


@pytest.fixture
def mock_pipeline_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Sets up an isolated pipeline environment with mock environment variables and data dir."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("DEFAULT_PROJECT", "sample")
    monkeypatch.setenv("ENABLE_DRIVE_SCAN", "false")
    return data_dir


class DummyHandler:
    """Mock DashboardHandler for testing API endpoints."""

    def __init__(self):
        self.sent_data = None
        self.sent_code = None
        self.headers = {}

    def send_json(self, data, status_code=200):
        self.sent_data = data
        self.sent_code = status_code

    def send_response(self, code, message=None):
        self.sent_code = code

    def send_header(self, keyword, value):
        pass

    def end_headers(self):
        pass

    def _reject_if_read_only(self):
        import server
        if getattr(server, 'STRICT_READ_ONLY', False):
            self.send_json({
                'error': 'Mutation endpoints are disabled on the web presentation tier.',
                'status': 'forbidden'
            }, status_code=403)
            return True
        return False



@pytest.fixture
def dummy_handler() -> DummyHandler:
    """Returns a fresh DummyHandler instance for testing DashboardHandler methods."""
    return DummyHandler()


@pytest.fixture(autouse=True)
def prevent_live_cloud_mutations(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """Prevents unit tests (without @pytest.mark.live) from making accidental live calls to GCS or Cloud TTS."""
    if request.node.get_closest_marker("live"):
        return

    import scripts.gemini_generator as gg

    monkeypatch.setattr(gg, "upload_bytes_to_gcs", lambda *a, **kw: True)
    monkeypatch.setattr(gg, "check_gcs_blob_metadata", lambda *a, **kw: (False, None))

    def _fast_mock_synthesize_audio(podcast_script, output_audio_path=None, language_code="en-AU", gcs_bucket=None, gcs_blob_name=None):
        mock_mp3 = b"ID3_MOCK_FAST_UNIT_TEST_MP3_BYTES"
        if output_audio_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(mock_mp3)
        return podcast_script, mock_mp3, 45.0

    monkeypatch.setattr(gg, "synthesize_podcast_audio", _fast_mock_synthesize_audio)


