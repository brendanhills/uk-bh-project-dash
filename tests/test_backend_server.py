"""Unit and integration tests for server.py HTTP API, routing, startup, and sync handlers."""

import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import server
from tests.conftest import DummyHandler


# --- Server Startup & CLI Helpers ---

def test_get_startup_urls():
    """Verify server provides clickable URLs on startup."""
    assert hasattr(server, 'get_startup_urls'), "server.py should have get_startup_urls function"
    urls = server.get_startup_urls(9000)
    assert "http://localhost:9000" in urls
    assert "http://127.0.0.1:9000" in urls


def test_startup_banner_output():
    """Verify startup banner contains clickable URL and project parameter."""
    assert hasattr(server, 'get_startup_banner'), "server.py should have get_startup_banner function"
    banner = server.get_startup_banner(9000)
    assert "http://localhost:9000" in banner
    assert "http://127.0.0.1:9000" in banner
    assert "?project=monaro" in banner


def test_get_project_dir_helper():
    """Verify get_project_dir correctly resolves project folders with fallback."""
    sample_dir = server.get_project_dir("sample")
    assert Path(sample_dir).exists()
    assert sample_dir.endswith(str(Path("data") / "sample"))

    monaro_dir = server.get_project_dir("monaro")
    assert Path(monaro_dir).exists()
    assert monaro_dir.endswith(str(Path("data") / "monaro")) or monaro_dir.endswith(str(Path("data") / "f-dse"))

    fdse_dir = server.get_project_dir("f-dse")
    assert Path(fdse_dir).exists()
    assert fdse_dir.endswith(str(Path("data") / "monaro")) or fdse_dir.endswith(str(Path("data") / "f-dse"))

    # Default fallback
    default_dir = server.get_project_dir("")
    assert Path(default_dir).exists()
    assert default_dir.endswith(str(Path("data") / "monaro")) or default_dir.endswith(str(Path("data") / "f-dse"))


def test_bug_94_default_project_resolution(monkeypatch):
    """Verify Bug #94: server.get_default_project defaults to 'monaro' when data/monaro exists."""
    monkeypatch.delenv("DEFAULT_PROJECT", raising=False)
    monkeypatch.delenv("DEFAULT_PROJECTS", raising=False)
    default_proj = server.get_default_project()
    if os.path.exists(os.path.join(server.DIRECTORY, 'data', 'monaro')) or os.path.exists(os.path.join(server.DIRECTORY, 'data', 'f-dse')):
        assert default_proj == "monaro"
    else:
        assert default_proj == "sample"

    # Verify fallback to sample if monaro does not exist
    with patch("os.path.exists") as mock_exists:
        def side_effect(path):
            if "monaro" in str(path) or "f-dse" in str(path) or str(path).endswith(".env"):
                return False
            return True
        mock_exists.side_effect = side_effect
        assert server.get_default_project() == "sample"


# --- RESTful API Endpoints ---

def test_status_endpoint(dummy_handler: DummyHandler):
    """Verify GET /api/status returns unified health and snapshot state."""
    server.DashboardHandler.handle_status(dummy_handler, "project=sample")
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data is not None
    assert dummy_handler.sent_data.get('project') == 'sample'
    assert 'total_snapshots' in dummy_handler.sent_data
    assert 'total_risks' in dummy_handler.sent_data


def test_sync_endpoint(dummy_handler: DummyHandler):
    """Verify POST /api/sync executes unified synchronization."""
    server.DashboardHandler.handle_sync(dummy_handler, {'project': 'sample'})
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data is not None
    assert dummy_handler.sent_data.get('status') == 'ok'
    assert dummy_handler.sent_data.get('project') == 'sample'


def test_ingest_endpoint(dummy_handler: DummyHandler):
    """Verify POST /api/ingest parses report and persists snapshot."""
    params = {
        'project': 'sample',
        'fileName': 'Weekly Reporting - Week 28 - 14 Aug 2026.pdf',
        'fileId': 'mock-w28-id',
        'fallback': True
    }
    with patch('server.ingest_report_file', return_value={'week_label': 'Week 28', 'week_number': 28, 'status': 'success'}):
        server.DashboardHandler.handle_ingest(dummy_handler, params)
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data is not None
    assert dummy_handler.sent_data.get('status') == 'ok'
    assert 'Week 28' in dummy_handler.sent_data.get('message', '')


def test_briefing_generate_endpoint(dummy_handler: DummyHandler):
    """Verify POST /api/briefing/generate regenerates synthesis and podcast."""
    params = {
        'project': 'sample',
        'week': 'Week 28',
        'fallback': True
    }
    with patch('server.save_json_file') as mock_save:
        server.DashboardHandler.handle_briefing(dummy_handler, params)
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data is not None
    assert dummy_handler.sent_data.get('status') == 'ok'
    assert 'synthesis' in dummy_handler.sent_data
    mock_save.assert_called_once()


# --- Legacy Routing Aliases & Backward Compatibility ---

@pytest.mark.parametrize("project_query, min_risks", [
    ("project=sample", 20),
    ("project=monaro", 100),
    ("project=f-dse", 100),
])
def test_sync_sheet_parameterized(dummy_handler: DummyHandler, project_query: str, min_risks: int):
    """Verify handle_sync_sheet returns correct risks, secondary registers, and snapshots across projects."""
    server.DashboardHandler.handle_sync_sheet(dummy_handler, query_str=project_query)
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data is not None
    assert "risks" in dummy_handler.sent_data
    assert "issues" in dummy_handler.sent_data
    assert "snapshots" in dummy_handler.sent_data
    assert "teamGoogleRisks" in dummy_handler.sent_data
    assert "registers" in dummy_handler.sent_data
    assert len(dummy_handler.sent_data["risks"]) >= min_risks


def test_handle_sync_all_endpoint(dummy_handler: DummyHandler):
    """Verify /api/sync-all runs full multi-source sync and returns summary counts."""
    server.DashboardHandler.handle_sync_all(dummy_handler, query_or_params={"project": "sample"})
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data.get("status") == "ok"
    assert dummy_handler.sent_data.get("project") == "sample"
    assert "summary" in dummy_handler.sent_data
    assert "snapshots" in dummy_handler.sent_data["summary"]


def test_handle_ingest_data_endpoint(dummy_handler: DummyHandler):
    """Verify POST /api/ingest-data triggers ingestion orchestrator."""
    with patch('server.ingest_report_file', return_value={'week_label': 'Week 28', 'status': 'success'}):
        server.DashboardHandler.handle_ingest_data(dummy_handler, params={"project": "sample"})
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data.get("status") == "ok"
    assert dummy_handler.sent_data.get("project") == "sample"
    assert "message" in dummy_handler.sent_data


def test_handle_regenerate_briefing_endpoint(dummy_handler: DummyHandler):
    """Verify POST /api/regenerate-briefing regenerates briefing synthesis."""
    with patch('server.save_json_file') as mock_save:
        server.DashboardHandler.handle_regenerate_briefing(dummy_handler, params={"project": "sample", "week": "Week 27", "fallback": True})
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data.get("status") == "ok"
    mock_save.assert_called_once()


def test_notebook_sync_and_catalog_endpoints():
    """Verify DashboardHandler handle_check_notebook_sync, handle_sync_notebook, and handle_list_notebooks."""
    dummy1 = DummyHandler()
    server.DashboardHandler.handle_check_notebook_sync(dummy1)
    assert dummy1.sent_code == 200
    assert 'sources' in dummy1.sent_data
    assert dummy1.sent_data['totalSources'] > 0
    assert 'bundleMapping' in dummy1.sent_data

    dummy2 = DummyHandler()
    server.DashboardHandler.handle_sync_notebook(dummy2)
    assert dummy2.sent_code == 200
    assert dummy2.sent_data['status'] == 'ok'

    dummy3 = DummyHandler()
    server.DashboardHandler.handle_list_notebooks(dummy3)
    assert dummy3.sent_code == 200
    assert 'notebooks' in dummy3.sent_data
    assert len(dummy3.sent_data['notebooks']) >= 1


# --- Drive Sync Handlers & Reconciliation ---

def test_known_drive_reports_week27():
    """Verify Week 27 pack is present in KNOWN_DRIVE_REPORTS."""
    assert hasattr(server, 'KNOWN_DRIVE_REPORTS')
    week27_reports = [r for r in server.KNOWN_DRIVE_REPORTS if r.get('week') == 'Week 27' or 'Week 27' in r.get('name', '')]
    assert len(week27_reports) >= 1, "Week 27 must be present in KNOWN_DRIVE_REPORTS"
    assert week27_reports[0]['id'] == "1HBfI9itx3BER4IRnH9eavBgAsrDGHnmu"


def test_check_drive_sync_handler(dummy_handler: DummyHandler):
    """Verify DashboardHandler handle_check_drive_sync recognizes snapshots across projects."""
    with patch("server.query_live_drive_folder", return_value=[]):
        server.DashboardHandler.handle_check_drive_sync(dummy_handler, query_str="project=sample")
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data is not None
    assert "snapshots" in dummy_handler.sent_data
    assert "w27" in dummy_handler.sent_data["snapshots"]


def test_check_drive_sync_reconciles_nested_drive_file_and_week_labels(dummy_handler: DummyHandler):
    """Verify Bug #83: handle_check_drive_sync recognizes snapshots with nested driveFile dicts and week labels."""
    mock_snapshots = {
        "snapshots": {
            "w27": {
                "weekNumber": 27,
                "weekLabel": "Week 27",
                "date": "07 Aug 2026",
                "driveFileId": "1HBfI9itx3BER4IRnH9eavBgAsrDGHnmu",
                "driveFileName": "Weekly Reporting - Week 27 - 07 Aug 2026.pdf"
            },
            "Week 28": {
                "week": "Week 28",
                "date": "14 Aug 2026",
                "driveFile": {
                    "name": "Weekly Reporting - Week 28 - 14 Aug 2026.pdf",
                    "id": "mock-drive-id-28"
                }
            }
        }
    }

    with patch("server.load_json_file") as mock_load:
        def side_effect(path, default=None):
            if "snapshots.json" in path:
                return mock_snapshots
            if "config.json" in path:
                return {
                    "sources": {
                        "googleDrive": {
                            "knownReports": [
                                {"id": "1HBfI9itx3BER4IRnH9eavBgAsrDGHnmu", "week": "Week 27", "name": "Weekly Reporting - Week 27 - 07 Aug 2026.pdf", "url": "https://drive.google.com/file/d/1HBfI9itx3BER4IRnH9eavBgAsrDGHnmu/view"},
                                {"id": "1_monaro_drive_w28", "week": "Week 28", "name": "Weekly Reporting - Week 28 - 14 Aug 2026.pdf", "url": "https://drive.google.com/file/d/1_monaro_drive_w28/view"}
                            ]
                        }
                    }
                }
            return default or {}
        mock_load.side_effect = side_effect

        server.DashboardHandler.handle_check_drive_sync(dummy_handler, query_str="project=monaro")
        assert dummy_handler.sent_code == 200
        assert dummy_handler.sent_data.get("uningestedCount") == 0
        assert len(dummy_handler.sent_data.get("uningestedReports")) == 0
        w28_rep = next((r for r in dummy_handler.sent_data.get("allReports", []) if r.get("week") == "Week 28"), None)
        assert w28_rep is not None
        assert w28_rep["isIngested"] is True


def test_check_drive_sync_queries_live_folder_on_demand_and_merges_real_urls(dummy_handler: DummyHandler):
    """Verify Bug #84 & #85: handle_check_drive_sync queries live Drive folder on demand and uses real Drive URLs."""
    mock_live_reports = [
        {
            "id": "real_gdrive_w29_id_xyz",
            "name": "Weekly Reporting - Week 29 - 21 Aug 2026.pdf",
            "week": "Week 29",
            "date": "21 Aug 2026",
            "url": "https://drive.google.com/file/d/real_gdrive_w29_id_xyz/view"
        },
        {
            "id": "real_gdrive_w28_id_abc",
            "name": "Weekly Reporting - Week 28 - 14 Aug 2026.pdf",
            "week": "Week 28",
            "date": "14 Aug 2026",
            "url": "https://drive.google.com/file/d/real_gdrive_w28_id_abc/view"
        }
    ]

    with patch("server.query_live_drive_folder") as mock_live_query:
        mock_live_query.return_value = mock_live_reports

        server.DashboardHandler.handle_check_drive_sync(dummy_handler, query_str="project=monaro")
        assert dummy_handler.sent_code == 200
        mock_live_query.assert_called_once_with("1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C")

        all_reps = dummy_handler.sent_data.get("allReports", [])
        w29_rep = next((r for r in all_reps if r.get("week") == "Week 29"), None)
        assert w29_rep is not None
        assert w29_rep["id"] == "real_gdrive_w29_id_xyz"
        assert w29_rep["url"] == "https://drive.google.com/file/d/real_gdrive_w29_id_xyz/view"
        uningested = dummy_handler.sent_data.get("uningestedReports", [])
        assert any(r.get("week") == "Week 29" for r in uningested)


# --- HTTP Dispatcher & Handler Request Tests ---

def test_dashboard_handler_do_options():
    """Verify DashboardHandler.do_OPTIONS sets CORS headers and 204 status."""
    handler = server.DashboardHandler.__new__(server.DashboardHandler)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler.do_OPTIONS()
    handler.send_response.assert_called_once_with(204)
    handler.send_header.assert_any_call('Access-Control-Allow-Origin', '*')


def test_dashboard_handler_do_get_routing():
    """Verify DashboardHandler.do_GET routes API endpoints and handles favicon."""
    handler = server.DashboardHandler.__new__(server.DashboardHandler)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.handle_status = MagicMock()
    handler.handle_sync = MagicMock()
    handler.handle_sync_sheet = MagicMock()
    handler.handle_check_drive_sync = MagicMock()
    handler.handle_list_notebooks = MagicMock()
    handler.handle_check_notebook_sync = MagicMock()
    handler.handle_sync_notebook = MagicMock()
    handler.handle_ingest_report = MagicMock()

    # Favicon
    handler.path = "/favicon.ico"
    handler.do_GET()
    handler.send_response.assert_called_with(204)

    # API Routes
    routes = [
        ("/api/status?project=sample", handler.handle_status),
        ("/api/sync?project=sample", handler.handle_sync),
        ("/api/sync-sheet?project=sample", handler.handle_sync_sheet),
        ("/api/check-drive-sync?project=sample", handler.handle_check_drive_sync),
        ("/api/notebooks", handler.handle_list_notebooks),
        ("/api/check-notebook-sync", handler.handle_check_notebook_sync),
        ("/api/sync-notebook", handler.handle_sync_notebook),
        ("/api/ingest-report?week=28", handler.handle_ingest_report),
    ]
    for path, target_mock in routes:
        handler.path = path
        handler.do_GET()
        target_mock.assert_called()


def test_dashboard_handler_do_post_routing():
    """Verify DashboardHandler.do_POST parses JSON body and routes to handlers."""
    handler = server.DashboardHandler.__new__(server.DashboardHandler)
    handler.handle_sync = MagicMock()
    handler.handle_ingest = MagicMock()
    handler.handle_briefing = MagicMock()
    handler.handle_ingest_data = MagicMock()
    handler.handle_sync_notebook = MagicMock()

    body_bytes = json.dumps({"project": "sample", "week": "Week 28"}).encode('utf-8')
    handler.headers = {'Content-Length': str(len(body_bytes))}
    handler.rfile = MagicMock()
    handler.rfile.read.return_value = body_bytes

    post_routes = [
        ("/api/sync", handler.handle_sync),
        ("/api/ingest", handler.handle_ingest),
        ("/api/briefing/generate", handler.handle_briefing),
        ("/api/ingest-data", handler.handle_ingest_data),
        ("/api/sync-notebook", handler.handle_sync_notebook),
    ]
    for path, target_mock in post_routes:
        handler.path = path
        handler.rfile.read.return_value = body_bytes
        handler.do_POST()
        target_mock.assert_called()


def test_query_live_drive_folder_fallback():
    """Verify query_live_drive_folder returns empty list for sample folder IDs or on exception."""
    assert server.query_live_drive_folder("sample-folder-id") == []
    assert server.query_live_drive_folder("") == []

    with patch("server.query_drive_folder_live", side_effect=Exception("API Error")):
        assert server.query_live_drive_folder("real-folder-id-error") == []


def test_server_send_json_helper():
    """Verify DashboardHandler.send_json formats response and headers properly."""
    handler = server.DashboardHandler.__new__(server.DashboardHandler)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = MagicMock()

    server.DashboardHandler.send_json(handler, {"status": "ok"}, status_code=200)
    handler.send_response.assert_called_once_with(200)
    handler.send_header.assert_any_call('Content-type', 'application/json')
    handler.wfile.write.assert_called_once()


def test_bug_98_sync_endpoint_returns_updated_flag_and_lock(dummy_handler: DummyHandler):
    """Bug #98: /api/sync returns explicit updated boolean and enforces non-blocking mutex lock."""
    # Test 1: Standard sync returns updated: False when no new files ingested
    server.DashboardHandler.handle_sync(dummy_handler, {'project': 'sample'})
    assert dummy_handler.sent_code == 200
    assert dummy_handler.sent_data is not None
    assert dummy_handler.sent_data.get('status') == 'ok'
    assert 'updated' in dummy_handler.sent_data
    assert dummy_handler.sent_data.get('updated') is False
    assert dummy_handler.sent_data.get('new_ingested_count') == 0

    # Test 2: When lock is acquired by another process/thread, second sync returns in_progress
    assert server._sync_lock.acquire(blocking=False)
    try:
        dummy_handler_2 = DummyHandler()
        server.DashboardHandler.handle_sync(dummy_handler_2, {'project': 'sample'})
        assert dummy_handler_2.sent_code == 200
        assert dummy_handler_2.sent_data.get('status') == 'in_progress'
        assert dummy_handler_2.sent_data.get('updated') is False
        assert 'already running' in dummy_handler_2.sent_data.get('message', '')
    finally:
        server._sync_lock.release()

