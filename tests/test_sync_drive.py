"""Unit tests for standalone Google Drive and Scheduled Ingestion sync script (scripts/sync_drive.py)."""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from scripts.sync_drive import (
    query_drive_folder_live,
    sync_drive_reports,
    filter_uningested_reports
)


def test_query_drive_folder_live_success():
    """Verify live Drive querying returns formatted list of files without mock fallback."""
    mock_service = MagicMock()
    mock_files = [
        {
            'id': 'file-w29',
            'name': 'Monaro Weekly Pack Week 29 - 21 Aug 2026.pdf',
            'createdTime': '2026-08-21T10:00:00Z',
            'webViewLink': 'https://drive.google.com/file/d/file-w29/view',
            'webContentLink': 'https://drive.google.com/uc?id=file-w29&export=download'
        },
        {
            'id': 'file-w30',
            'name': 'Monaro Weekly Pack Week 30 - 28 Aug 2026.pdf',
            'createdTime': '2026-08-28T10:00:00Z',
            'webViewLink': 'https://drive.google.com/file/d/file-w30/view',
            'webContentLink': 'https://drive.google.com/uc?id=file-w30&export=download'
        }
    ]
    mock_service.files().get().execute.return_value = {'id': '1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C', 'name': 'Monaro Weekly Packs', 'driveId': None}
    mock_service.files().list().execute.return_value = {'files': mock_files}

    with patch('scripts.sync_drive.get_drive_service', return_value=mock_service):
        reports = query_drive_folder_live('1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C')
        assert len(reports) == 2
        assert reports[0]['id'] == 'file-w29'
        assert reports[1]['id'] == 'file-w30'
        assert reports[1]['name'] == 'Monaro Weekly Pack Week 30 - 28 Aug 2026.pdf'


def test_query_drive_folder_live_error_raises():
    """Verify drive querying raises an exception on authentication or network error instead of silent swallowing."""
    mock_service = MagicMock()
    mock_service.files().get().execute.side_effect = RuntimeError("Drive API 403 Forbidden")

    with patch('scripts.sync_drive.get_drive_service', return_value=mock_service):
        with pytest.raises(RuntimeError, match="Drive API 403 Forbidden"):
            query_drive_folder_live('invalid-folder-id')


def test_filter_uningested_reports():
    """Verify that only files not present in snapshots.json or existing reports are flagged for ingestion."""
    existing_snapshots = {
        "snapshots": {
            "w28": {"weekNumber": 28, "weekLabel": "Week 28"},
            "w29": {"weekNumber": 29, "weekLabel": "Week 29"}
        }
    }
    drive_files = [
        {'id': 'file-w28', 'name': 'Monaro Week 28.pdf', 'week_number': 28},
        {'id': 'file-w29', 'name': 'Monaro Week 29.pdf', 'week_number': 29},
        {'id': 'file-w30', 'name': 'Monaro Week 30.pdf', 'week_number': 30},
        {'id': 'file-w31', 'name': 'Monaro Week 31.pdf', 'week_number': 31}
    ]

    new_reports = filter_uningested_reports(drive_files, existing_snapshots)
    assert len(new_reports) == 2
    assert new_reports[0]['week_number'] == 30
    assert new_reports[1]['week_number'] == 31


def test_sync_drive_reports_incremental(tmp_path: Path):
    """Verify end-to-end sync ingests newly discovered reports into snapshots.json."""
    proj_dir = tmp_path / "monaro"
    proj_dir.mkdir(parents=True)
    snapshots_file = proj_dir / "snapshots.json"
    snapshots_file.write_text(json.dumps({
        "current_week": "Week 29",
        "snapshots": {
            "w29": {"weekNumber": 29, "week": "Week 29", "date": "21 Aug 2026"}
        }
    }), encoding="utf-8")

    discovered_files = [
        {
            'id': 'file-w29',
            'name': 'Monaro_Week_29.pdf',
            'week_number': 29,
            'webViewLink': 'https://drive.google.com/file/d/file-w29/view'
        },
        {
            'id': 'file-w30',
            'name': 'Monaro_Week_30.pdf',
            'week_number': 30,
            'webViewLink': 'https://drive.google.com/file/d/file-w30/view'
        }
    ]

    with patch('scripts.sync_drive.query_drive_folder_live', return_value=discovered_files):
        with patch('scripts.sync_drive.ingest_report_file') as mock_ingest:
            mock_ingest.return_value = {
                'week': 'Week 30',
                'weekNumber': 30,
                'date': '28 Aug 2026',
                'status': 'success'
            }

            summary = sync_drive_reports(
                folder_id='test-folder-id',
                project_name='monaro',
                data_root=str(tmp_path),
                dry_run=False
            )

            assert summary['status'] == 'success'
            assert summary['discovered_count'] == 2
            assert summary['new_ingested_count'] == 1
            assert summary['latest_week'] == 'Week 30'
            mock_ingest.assert_called_once()


def test_run_preflight_diagnostics_success(tmp_path: Path):
    """Verify run_preflight_diagnostics executes all 4 checks and succeeds when components are healthy."""
    from scripts.sync_drive import run_preflight_diagnostics
    proj_dir = tmp_path / "monaro"
    proj_dir.mkdir(parents=True)
    snapshots_file = proj_dir / "snapshots.json"
    snapshots_file.write_text(json.dumps({"current_week": "Week 27", "snapshots": {"w27": {}}}), encoding="utf-8")

    mock_drive = MagicMock()
    mock_drive.files().get().execute.return_value = {'id': 'folder-123', 'name': 'Reports', 'driveId': None}

    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value.text = "pong"

    with patch('scripts.sync_drive.get_drive_service', return_value=mock_drive):
        with patch('scripts.gemini_generator.get_gemini_client', return_value=mock_genai_client):
            results = run_preflight_diagnostics(
                folder_id='folder-123',
                project_name='monaro',
                data_root=str(tmp_path),
                location='us'
            )
            assert results['drive']['status'] == 'OK'
            assert results['vertex_ai']['status'] == 'OK'
            assert results['vertex_ai']['region'] == 'us'
            assert results['vertex_ai']['model'] == 'gemini-3.5-flash'
            assert results['storage']['status'] == 'OK'
            assert results['schema']['status'] == 'OK'


def test_sync_drive_reports_forwards_gemini_region(tmp_path: Path):
    """Verify sync_drive_reports forwards gemini region parameter to ingest_report_file."""
    proj_dir = tmp_path / "monaro"
    proj_dir.mkdir(parents=True)
    snapshots_file = proj_dir / "snapshots.json"
    snapshots_file.write_text(json.dumps({"snapshots": {}}), encoding="utf-8")

    discovered_files = [{
        'id': 'file-w30',
        'name': 'Monaro_Week_30.pdf',
        'week_number': 30,
        'webViewLink': 'https://drive.google.com/file/d/file-w30/view'
    }]

    with patch('scripts.sync_drive.query_drive_folder_live', return_value=discovered_files):
        with patch('scripts.sync_drive.ingest_report_file') as mock_ingest:
            mock_ingest.return_value = {'week': 'Week 30', 'status': 'success'}
            summary = sync_drive_reports(
                folder_id='test-folder-id',
                project_name='monaro',
                data_root=str(tmp_path),
                model='gemini-3.5-flash',
                location='us'
            )
            assert summary['status'] == 'success'
            mock_ingest.assert_called_once()
            call_kwargs = mock_ingest.call_args.kwargs
            assert call_kwargs['model'] == 'gemini-3.5-flash'
            assert call_kwargs['location'] == 'us'


def test_run_preflight_diagnostics_drive_failure(tmp_path: Path):
    """Verify run_preflight_diagnostics raises an exception with diagnostic detail when a check fails."""
    from scripts.sync_drive import run_preflight_diagnostics
    proj_dir = tmp_path / "monaro"
    proj_dir.mkdir(parents=True)
    snapshots_file = proj_dir / "snapshots.json"
    snapshots_file.write_text(json.dumps({"snapshots": {}}), encoding="utf-8")

    mock_drive = MagicMock()
    mock_drive.files().get().execute.side_effect = RuntimeError("Drive Access Revoked 403")

    with patch('scripts.sync_drive.get_drive_service', return_value=mock_drive):
        with patch('scripts.gemini_generator.get_gemini_client'):
            with pytest.raises(RuntimeError, match="Pre-flight diagnostics failed on"):
                run_preflight_diagnostics(
                    folder_id='revoked-folder-id',
                    project_name='monaro',
                    data_root=str(tmp_path)
                )

