"""Unit tests for pipeline engine, Gemini multimodal AI generator, and Drive sync."""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from scripts.gemini_generator import (
    get_gemini_client,
    generate_executive_synthesis,
    generate_multispeaker_podcast,
    build_synthesis_prompt,
    inspect_report_with_gemini,
    get_default_gemini_region,
)
from scripts.pipeline import (
    parse_report_metadata,
    compute_risk_metrics,
    generate_fallback_synthesis,
    generate_fallback_podcast,
    sync_project_data,
    ingest_report_file,
    resolve_target_projects,
    load_project_config,
    ingest_single_project,
    get_project_dir as get_pipeline_project_dir,
)
from scripts.sync_drive import (
    query_drive_folder_live,
    sync_drive_reports,
    filter_uningested_reports,
    run_preflight_diagnostics,
)


# --- Gemini Generator & Client Configuration ---

def test_client_init_adc_priority(monkeypatch: pytest.MonkeyPatch):
    """Verify Gemini client prioritizes Vertex AI ADC configuration when project and region are set."""
    monkeypatch.setenv('GCP_PROJECT_ID', 'test-project')
    monkeypatch.setenv('GCP_REGION', 'us-central1')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')

    with patch('google.genai.Client') as mock_client:
        get_gemini_client()
        mock_client.assert_called_with(vertexai=True, project='test-project', location='us-central1')


def test_client_init_api_key_fallback(monkeypatch: pytest.MonkeyPatch):
    """Verify Gemini client falls back to API key when Vertex AI environment variables are absent."""
    monkeypatch.delenv('GCP_PROJECT_ID', raising=False)
    monkeypatch.setenv('GEMINI_API_KEY', 'valid-api-key')

    with patch('google.genai.Client') as mock_client:
        get_gemini_client()
        mock_client.assert_called_with(api_key='valid-api-key')


def test_gemini_model_environment_and_explicit_override(monkeypatch):
    """Verify GEMINI_MODEL environment variable and explicit argument precedence."""
    monkeypatch.setenv("GEMINI_MODEL", "gemini-custom-enterprise-model")

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = json.dumps({
        'synthesis': {'executive': 'Exec.', 'technical': 'Tech.', 'governance': 'Gov.'},
        'top3': [],
        'sleeperOutlier': {'ref': '1.1', 'title': 'S', 'warning': 'W'}
    })

    with patch('scripts.gemini_generator.get_gemini_client', return_value=mock_client):
        # 1. Environment variable
        res_env = generate_executive_synthesis({}, [])
        assert res_env['generatedBy'] == "gemini-custom-enterprise-model"

        # 2. Explicit override
        res_exp = generate_executive_synthesis({}, [], model="gemini-explicit-override")
        assert res_exp['generatedBy'] == "gemini-explicit-override"


def test_gemini_region_and_multi_region_rep_endpoint(monkeypatch):
    """Verify get_default_gemini_region and multi-region .rep. base URL configuration."""
    monkeypatch.delenv("GEMINI_REGION", raising=False)
    monkeypatch.delenv("GCP_REGION", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    assert get_default_gemini_region() == "us"
    assert get_default_gemini_region("australia-southeast1") == "australia-southeast1"

    monkeypatch.setenv("GCP_PROJECT_ID", "monaro-risk-dev")
    monkeypatch.setenv("GEMINI_REGION", "us")

    with patch('scripts.gemini_generator.genai.Client') as mock_genai_client:
        get_gemini_client()
        mock_genai_client.assert_called_once()
        kwargs = mock_genai_client.call_args.kwargs
        assert kwargs['vertexai'] is True
        assert kwargs['location'] == 'us'
        assert kwargs['http_options'].base_url == "https://aiplatform.us.rep.googleapis.com"


def test_build_synthesis_prompt_and_parsing():
    """Verify prompt formatting and structured response parsing of synthesis, top 3, and sleeper outlier."""
    metrics = {
        'report_week': 'Week 28',
        'report_date': '14 Aug 2026',
        'inherent_avg_score': 15.4,
    }
    plans = [{'num': 1, 'ref': '1.2b', 'title': 'Milestone 1 Acceptance', 'plan': 'Plan details', 'owner': 'Adam', 'target': 'Aug 2026'}]
    prompt = build_synthesis_prompt(metrics, plans)
    assert 'Week 28' in prompt
    assert '14 Aug 2026' in prompt
    assert 'Milestone 1 Acceptance' in prompt

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        'synthesis': {'executive': 'Exec text', 'technical': 'Tech text', 'governance': 'Gov text'},
        'top3': [{'num': 1, 'type': 'decision', 'tag': '🚨 Action', 'ref': '1.2b', 'title': 'Signoff', 'action': 'Do it'}],
        'sleeperOutlier': {'ref': '1.15', 'title': 'Schedule', 'warning': 'Warning text'}
    })

    with patch('scripts.gemini_generator.get_gemini_client') as mock_get_client:
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client_instance

        result = generate_executive_synthesis({}, [])
        assert result['synthesis']['executive'] == 'Exec text'
        assert len(result['top3']) == 1
        assert result['sleeperOutlier']['ref'] == '1.15'


# --- Pipeline Metadata, Metrics & Fallbacks ---

@pytest.mark.parametrize("filename, fallback_week, expected_week, expected_label, expected_date_substr", [
    ("Weekly Reporting - Week 28 - 14 Aug 2026.pdf", None, 28, "Week 28", "14 Aug 2026"),
    ("W29_Executive_Summary_21Aug2026.pdf", None, 29, None, "Aug"),
    ("Status_Report_Final.pdf", 30, 30, "Week 30", None),
])
def test_parse_report_metadata_various_formats(
    filename: str, fallback_week: int | None, expected_week: int, expected_label: str | None, expected_date_substr: str | None
):
    """Verify filename regex parsing across standard, abbreviated, and fallback naming patterns."""
    kwargs = {"use_gemini": False}
    if fallback_week is not None:
        kwargs["fallback_week"] = fallback_week

    meta = parse_report_metadata(filename, **kwargs)
    assert meta["week_number"] == expected_week
    if expected_label:
        assert meta["week_label"] == expected_label
    if expected_date_substr:
        assert expected_date_substr in meta["report_date"]


@patch('scripts.gemini_generator.inspect_report_with_gemini')
def test_parse_report_metadata_gemini_multimodal_and_fallback(mock_inspect: MagicMock, tmp_path: Path):
    """Verify Gemini multimodal inspection of PDFs with automatic fallback to heuristics on error."""
    mock_inspect.return_value = {
        'week_number': 31,
        'week_label': 'Week 31',
        'report_date': '28 Aug 2026',
        'title': 'Monaro Executive Risk Review',
        'inspectedBy': 'gemini-3.7-flash'
    }

    dummy_pdf = tmp_path / "test_report.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 dummy content")

    # 1. Success case
    meta = parse_report_metadata(str(dummy_pdf), use_gemini=True)
    assert meta['week_number'] == 31
    assert meta['inspectedBy'] == 'gemini-3.7-flash'

    # 2. Error fallback case
    mock_inspect.side_effect = RuntimeError("API quota exceeded")
    meta_fallback = parse_report_metadata("Weekly Reporting - Week 28 - 14 Aug 2026.pdf", use_gemini=True)
    assert meta_fallback['week_number'] == 28
    assert meta_fallback['inspectedBy'] == 'regex_heuristic'


def test_compute_risk_metrics_and_fallbacks():
    """Verify calculation of risk compression, counts, averages, and deterministic fallbacks."""
    risks = [
        {"inherentRiskScore": 20, "residualRiskScore": 6, "status": "Active"},
        {"inherentRiskScore": 15, "residualRiskScore": 9, "status": "Eventuated"},
        {"inherentRiskScore": 10, "residualRiskScore": 4, "status": "Active"}
    ]
    issues = [{"id": "ISS-01"}, {"id": "ISS-02"}]
    metrics = compute_risk_metrics(risks, issues)

    assert metrics['total_risks'] == 3
    assert metrics['total_issues'] == 2
    assert metrics['eventuated_issues_count'] == 1
    assert metrics['inherent_avg_score'] == 15.0
    assert metrics['residual_avg_score'] == 6.3
    assert metrics['delta_compression'] == "-8.7"

    # Deterministic fallback synthesis & podcast
    synthesis = generate_fallback_synthesis(metrics)
    assert 'synthesis' in synthesis
    assert len(synthesis['top3']) == 3
    assert synthesis['generatedBy'] == 'deterministic_rule_engine'

    podcast = generate_fallback_podcast(metrics, synthesis)
    assert isinstance(podcast, list)
    assert len(podcast) >= 4
    assert podcast[0]['speaker'] == 'Alex'
    assert podcast[1]['speaker'] == 'Jordan'


# --- Project Resolution & Orchestration ---

def test_resolve_target_projects_and_pipeline_defaults(monkeypatch):
    """Verify target project resolution across CLI args, DEFAULT_PROJECTS env var, and defaults."""
    assert resolve_target_projects(cli_arg='monaro') == ['monaro']

    monkeypatch.setenv('DEFAULT_PROJECTS', 'monaro, sample, custom-app')
    assert resolve_target_projects(cli_arg=None) == ['monaro', 'sample', 'custom-app']

    monkeypatch.delenv('DEFAULT_PROJECTS', raising=False)
    assert resolve_target_projects(cli_arg=None) == ['sample']

    # Bug #94: get_pipeline_project_dir defaults to monaro if present
    default_dir = get_pipeline_project_dir()
    assert Path(default_dir).exists()


def test_ingest_report_file_and_single_project(tmp_path: Path):
    """Verify report ingestion updates snapshots.json in an isolated directory."""
    proj_dir = tmp_path / 'data' / 'sample'
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / 'config.json').write_text(json.dumps({'project': {'name': 'Project Aurora'}}), encoding='utf-8')
    (proj_dir / 'risks.json').write_text(json.dumps([{"inherentRiskScore": 16, "residualRiskScore": 8, "status": "Active"}]), encoding='utf-8')
    (proj_dir / 'issues.json').write_text(json.dumps([]), encoding='utf-8')
    (proj_dir / 'snapshots.json').write_text(json.dumps({'snapshots': {}}), encoding='utf-8')

    with patch('scripts.pipeline.DATA_BASE_DIR', str(tmp_path / 'data')):
        config = load_project_config('sample')
        assert config['project']['name'] == 'Project Aurora'

        result = ingest_single_project('sample', generate_ai=False)
        assert result['success'] is True
        assert result['totalRisks'] == 1

        ingest_res = ingest_report_file(
            file_name="Weekly Reporting - Week 29 - 21 Aug 2026.pdf",
            project_name="sample",
            data_root=str(tmp_path / 'data'),
            force_fallback=True
        )
        assert ingest_res['success'] is True
        assert ingest_res['week'] == 29


# --- Drive Sync Client & Preflight Diagnostics ---

def test_drive_folder_live_querying_and_error_handling():
    """Verify Drive live querying returns formatted reports and raises on auth error."""
    mock_service = MagicMock()
    mock_files = [{
        'id': 'file-w29',
        'name': 'Monaro Weekly Pack Week 29 - 21 Aug 2026.pdf',
        'webViewLink': 'https://drive.google.com/file/d/file-w29/view'
    }]
    mock_service.files().get().execute.return_value = {'id': '1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C', 'name': 'Monaro Packs', 'driveId': None}
    mock_service.files().list().execute.return_value = {'files': mock_files}

    with patch('scripts.sync_drive.get_drive_service', return_value=mock_service):
        reports = query_drive_folder_live('1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C')
        assert len(reports) == 1
        assert reports[0]['id'] == 'file-w29'

    mock_service.files().get().execute.side_effect = RuntimeError("Drive API 403 Forbidden")
    with patch('scripts.sync_drive.get_drive_service', return_value=mock_service):
        with pytest.raises(RuntimeError, match="Drive API 403 Forbidden"):
            query_drive_folder_live('invalid-folder-id')


def test_filter_uningested_reports_and_incremental_sync(tmp_path: Path):
    """Verify uningested report filtering, file ID deduplication, and max latest_week sync workflow."""
    existing_snapshots = {
        "snapshots": {
            "w28": {"weekNumber": 28, "driveFileId": "f28", "driveFileName": "W28.pdf"},
            "w10": {"weekNumber": 10, "driveFileId": "f-enabling-10", "driveFileName": "FDSE Enabling Services.pdf"}
        }
    }
    drive_files = [
        {'id': 'f28', 'name': 'W28.pdf', 'week_number': 28},
        {'id': 'f29', 'name': 'W29.pdf', 'week_number': 29},
        # File with None week_number but matching driveFileId should be skipped
        {'id': 'f-enabling-10', 'name': 'FDSE Enabling Services.pdf', 'week_number': None},
        # File with None week_number but new ID should be included
        {'id': 'f-new-report', 'name': 'FDSE New Report.pdf', 'week_number': None},
    ]
    new_reps = filter_uningested_reports(drive_files, existing_snapshots)
    assert len(new_reps) == 2
    assert {r['id'] for r in new_reps} == {'f29', 'f-new-report'}

    proj_dir = tmp_path / "monaro"
    proj_dir.mkdir(parents=True)
    # Existing snapshot database has Week 30
    (proj_dir / "snapshots.json").write_text(json.dumps({
        "snapshots": {
            "w30": {"weekNumber": 30, "weekLabel": "Week 30"}
        }
    }), encoding="utf-8")

    # Ingest an out-of-order backfill report (Week 10)
    with patch('scripts.sync_drive.query_drive_folder_live', return_value=[{'id': 'f10', 'name': 'Backfill_W10.pdf', 'week_number': 10}]):
        with patch('scripts.sync_drive.ingest_report_file') as mock_ingest:
            mock_ingest.return_value = {'week': 10, 'status': 'success'}
            summary = sync_drive_reports(
                folder_id='test-folder',
                project_name='monaro',
                data_root=str(tmp_path),
                model='gemini-3.5-flash',
                location='us'
            )
            assert summary['status'] == 'success'
            mock_ingest.assert_called_once()
            assert mock_ingest.call_args.kwargs['location'] == 'us'
            # latest_week must reflect the true max week (Week 30), NOT the backfill loop item (10)
            assert summary['latest_week'] == 'Week 30'


def test_run_preflight_diagnostics_success_and_failure(tmp_path: Path):
    """Verify run_preflight_diagnostics executes 4 checks and catches component failures."""
    proj_dir = tmp_path / "monaro"
    proj_dir.mkdir(parents=True)
    (proj_dir / "snapshots.json").write_text(json.dumps({"snapshots": {}}), encoding="utf-8")

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
            assert results['storage']['status'] == 'OK'
            assert results['schema']['status'] == 'OK'

    # Failure case
    mock_drive.files().get().execute.side_effect = RuntimeError("Drive Access Revoked 403")
    with patch('scripts.sync_drive.get_drive_service', return_value=mock_drive):
        with patch('scripts.gemini_generator.get_gemini_client'):
            with pytest.raises(RuntimeError, match="Pre-flight diagnostics failed on"):
                run_preflight_diagnostics(folder_id='folder-123', project_name='monaro', data_root=str(tmp_path))


# --- Additional Coverage Enhancements ---

def test_generate_multispeaker_podcast_success(tmp_path: Path):
    """Verify generate_multispeaker_podcast dialogue parsing and audio export."""
    mock_podcast_response = MagicMock()
    mock_podcast_response.text = json.dumps([
        {"speaker": "Alex", "role": "Host", "text": "Welcome to the executive briefing.", "time": "0:00"},
        {"speaker": "Jordan", "role": "Technical Director", "text": "Let's review the critical path.", "time": "0:15"}
    ])

    with patch('scripts.gemini_generator.get_gemini_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_podcast_response
        mock_get_client.return_value = mock_client

        audio_file = str(tmp_path / "test_podcast.mp3")
        dialogue = generate_multispeaker_podcast(
            metrics={'report_week': 'Week 28', 'report_date': '14 Aug 2026'},
            synthesis_result={'synthesis': {'executive': 'Summary'}},
            audio_out_path=audio_file
        )
        assert len(dialogue) == 2
        assert dialogue[0]['speaker'] == 'Alex'
        assert dialogue[1]['speaker'] == 'Jordan'


def test_generate_multispeaker_podcast_error_handling():
    """Verify generate_multispeaker_podcast error handling on uninitialized client or invalid JSON."""
    with patch('scripts.gemini_generator.get_gemini_client', return_value=None):
        with pytest.raises(RuntimeError, match="Gemini Client could not be initialized"):
            generate_multispeaker_podcast({}, {})

    mock_corrupt_response = MagicMock()
    mock_corrupt_response.text = "NOT_JSON_RESPONSE"
    with patch('scripts.gemini_generator.get_gemini_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_corrupt_response
        mock_get_client.return_value = mock_client
        with pytest.raises(ValueError, match="Invalid podcast script JSON"):
            generate_multispeaker_podcast({}, {})


def test_generate_executive_synthesis_404_region_retry_and_invalid_json():
    """Verify regional 404 retry logic falling back to multi-region 'us' endpoint and JSON error handling."""
    mock_synthesis_response = MagicMock()
    mock_synthesis_response.text = json.dumps({
        'synthesis': {'executive': 'Exec.', 'technical': 'Tech.', 'governance': 'Gov.'},
        'top3': [],
        'sleeperOutlier': {'ref': '1.1', 'title': 'S', 'warning': 'W'}
    })

    # 1. 404 Regional retry test
    mock_regional_client = MagicMock()
    mock_regional_client.models.generate_content.side_effect = RuntimeError("404 NotFound: Model not found in australia-southeast1")

    mock_us_client = MagicMock()
    mock_us_client.models.generate_content.return_value = mock_synthesis_response

    def client_side_effect(location=None):
        if location in ('us', 'us-central1'):
            return mock_us_client
        return mock_regional_client

    with patch('scripts.gemini_generator.get_gemini_client', side_effect=client_side_effect):
        res = generate_executive_synthesis({}, [], location='australia-southeast1')
        assert res['synthesis']['executive'] == 'Exec.'
        mock_us_client.models.generate_content.assert_called_once()

    # 2. Corrupt JSON test
    mock_corrupt = MagicMock()
    mock_corrupt.text = "CORRUPT_JSON"
    with patch('scripts.gemini_generator.get_gemini_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_corrupt
        mock_get_client.return_value = mock_client
        with pytest.raises(ValueError, match="Invalid JSON output"):
            generate_executive_synthesis({}, [])


def test_sync_project_data_full_orchestration(tmp_path: Path):
    """Verify sync_project_data orchestrates multi-source sync across Sheets, Drive, and Notebooks."""
    proj_dir = tmp_path / "sample"
    proj_dir.mkdir(parents=True)
    config = {
        'project': {'slug': 'sample', 'name': 'Project Aurora'},
        'sources': {
            'googleSheets': {'enabled': True, 'sheetUrl': 'mock-url'},
            'googleDrive': {'enabled': True, 'folderId': 'mock-folder'},
            'geminiNotebooks': {'enabled': True, 'notebookIds': ['mock-nb']}
        }
    }
    (proj_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (proj_dir / "risks.json").write_text(json.dumps([]), encoding="utf-8")
    (proj_dir / "issues.json").write_text(json.dumps([]), encoding="utf-8")
    (proj_dir / "snapshots.json").write_text(json.dumps({"snapshots": {}}), encoding="utf-8")
    (proj_dir / "knowledge.json").write_text(json.dumps({"blueprints": []}), encoding="utf-8")

    result = sync_project_data('sample', data_root=str(tmp_path))
    assert result['success'] is True
    assert result['project'] == 'sample'
    assert 'total_snapshots' in result


def test_get_drive_service_credentials_resolution(monkeypatch):
    """Verify get_drive_service credential resolution order (service account file vs ADC vs failure)."""
    from scripts.sync_drive import get_drive_service

    # 1. Non-existent explicit SA file raises
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/non_existent_key_xyz.json")
    with pytest.raises(Exception):
        get_drive_service()

    # 2. Mock ADC success
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with patch('google.auth.default', return_value=(MagicMock(), 'test-project')):
        with patch('googleapiclient.discovery.build') as mock_build:
            get_drive_service()
            mock_build.assert_called_once()


def test_sync_drive_reports_dry_run_and_download_resilience(tmp_path: Path):
    """Verify sync_drive_reports dry_run mode and exception propagation."""
    proj_dir = tmp_path / "monaro"
    proj_dir.mkdir(parents=True)
    (proj_dir / "snapshots.json").write_text(json.dumps({"snapshots": {}}), encoding="utf-8")

    discovered = [
        {'id': 'f1', 'name': 'W30.pdf', 'week_number': 30},
        {'id': 'f2', 'name': 'W31.pdf', 'week_number': 31}
    ]

    # 1. Dry-run mode
    with patch('scripts.sync_drive.query_drive_folder_live', return_value=discovered):
        summary_dry = sync_drive_reports(
            folder_id='test-folder',
            project_name='monaro',
            data_root=str(tmp_path),
            dry_run=True
        )
        assert summary_dry['status'] == 'success'
        assert summary_dry['dry_run'] is True
        assert summary_dry['new_ingested_count'] == 0

    # 2. Ingestion exception propagation
    with patch('scripts.sync_drive.query_drive_folder_live', return_value=discovered):
        with patch('scripts.sync_drive.ingest_report_file', side_effect=RuntimeError("Corrupt PDF bytes")):
            with pytest.raises(RuntimeError, match="Corrupt PDF bytes"):
                sync_drive_reports(
                    folder_id='test-folder',
                    project_name='monaro',
                    data_root=str(tmp_path),
                    dry_run=False
                )


def test_sync_drive_cli_arguments_parser(project_root: Path):
    """Verify sync_drive.py CLI execution with --help."""
    import sys
    import subprocess
    script_path = project_root / "scripts" / "sync_drive.py"
    proc = subprocess.run([sys.executable, str(script_path), "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--folder-id" in proc.stdout
    assert "--dry-run" in proc.stdout
    assert "--project" in proc.stdout



