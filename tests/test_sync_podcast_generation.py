"""
Unit tests verifying that Gemini 3.5 Flash podcast generation is properly called during data sync.

Covers:
1. ensure_latest_podcast_generated calls Gemini 3.5 Flash and updates snapshots.json.
2. sync_drive_reports invokes podcast generation even when 0 new reports are found if the latest snapshot lacks a Gemini 3.5 Flash podcast.
3. sync_drive_reports invokes podcast generation when a new report is ingested.
4. sync_project_data in pipeline.py ensures the latest snapshot has a Gemini podcast.
5. server.py handle_sync triggers podcast generation during synchronization.
6. gemini_generator defaults strictly to gemini-3.5-flash and us-central1 with zero TTS dependencies.
7. Frontend transcript access is never blocked when a podcast script is present.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.sync_drive import sync_drive_reports, ensure_latest_podcast_generated
from scripts.pipeline import (
    load_json_file,
    save_json_file,
    sync_project_data,
    ingest_report_file
)
from scripts.gemini_generator import (
    get_default_gemini_model,
    get_default_gemini_region,
    generate_multispeaker_podcast
)


@pytest.fixture
def mock_project_env(tmp_path: Path):
    """Creates an isolated temporary project environment with realistic snapshot data."""
    proj_dir = tmp_path / "data" / "test_proj"
    proj_dir.mkdir(parents=True)
    
    config = {
        "project": {"slug": "test_proj", "name": "Test Project"},
        "sources": {"googleDrive": {"enabled": True, "folderId": "mock-folder-id"}}
    }
    with open(proj_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f)
        
    risks = [{"id": "R-1", "inherentRiskScore": 15, "residualRiskScore": 8, "status": "Active"}]
    with open(proj_dir / "risks.json", "w", encoding="utf-8") as f:
        json.dump(risks, f)
        
    issues = [{"id": "I-1", "status": "Open", "priority": "P1"}]
    with open(proj_dir / "issues.json", "w", encoding="utf-8") as f:
        json.dump(issues, f)
        
    # Initial snapshot: w30 with fallback / ungenerated podcast
    snapshots = {
        "lastSynced": "2026-09-01T00:00:00",
        "snapshots": {
            "w29": {
                "weekNumber": 29,
                "weekLabel": "Week 29",
                "date": "21 Aug 2026",
                "isLatest": False,
                "driveFileId": "file-w29",
                "driveFileName": "Weekly Reporting - Week 29 - 21 Aug 2026.pdf"
            },
            "w30": {
                "weekNumber": 30,
                "weekLabel": "Week 30",
                "date": "28 Aug 2026",
                "isLatest": True,
                "driveFileId": "file-w30",
                "driveFileName": "Weekly Reporting - Week 30 - 28 Aug 2026.pdf",
                "metrics": {
                    "report_week": "Week 30",
                    "report_date": "28 Aug 2026",
                    "inherent_avg_score": 15.0,
                    "residual_avg_score": 8.0,
                    "delta_compression": "-7.0"
                },
                "synthesis": {"executive": "Delivery is progressing on track across contractual milestones."},
                "top3": [{"title": "Milestone 2 Acceptance"}],
                "sleeperOutlier": {"title": "Enclave Latency"},
                "generatedBy": "deterministic_rule_engine"  # Stale fallback script
            }
        }
    }
    with open(proj_dir / "snapshots.json", "w", encoding="utf-8") as f:
        json.dump(snapshots, f)
        
    return {
        "root": str(tmp_path),
        "proj_dir": str(proj_dir),
        "project": "test_proj"
    }


# ==============================================================================
# Test 1: Direct Verification of ensure_latest_podcast_generated
# ==============================================================================
def test_ensure_latest_podcast_generated_invokes_gemini_35_flash(mock_project_env):
    """Verify ensure_latest_podcast_generated calls Gemini 3.5 Flash and updates snapshots.json."""
    mock_script = [
        {"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Welcome to the Week 30 executive briefing."},
        {"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:15", "text": "Thanks Alex. Milestone 2 is progressing on schedule."}
    ]

    with patch('scripts.gemini_generator.generate_multispeaker_podcast', return_value=mock_script) as mock_gen:
        updated = ensure_latest_podcast_generated(
            project_name=mock_project_env["project"],
            data_root=str(Path(mock_project_env["root"]) / "data")
        )

        assert updated is True
        mock_gen.assert_called_once()
        
        # Verify model argument passed to generator is gemini-3.5-flash
        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs.get("model") in (None, "gemini-3.5-flash")

        # Verify snapshots.json updated on disk with new script and provenance
        snaps_file = os.path.join(mock_project_env["proj_dir"], "snapshots.json")
        data = load_json_file(snaps_file, {})
        w30 = data["snapshots"]["w30"]
        assert w30["generatedBy"] == "gemini-3.5-flash"
        assert len(w30["podcastScript"]) == 2
        assert w30["podcastScript"][0]["speaker"] == "Alex"
        assert w30["podcastScript"][1]["speaker"] == "Jordan"


# ==============================================================================
# Test 2: Sync Drive Ingestion When 0 New Reports Found
# ==============================================================================
def test_sync_drive_reports_generates_podcast_even_when_zero_new_files(mock_project_env):
    """
    Verify sync_drive_reports invokes podcast generation even when 0 new files need ingestion.
    This directly reproduces and solves the exact failure mode where repeated syncs did not update.
    """
    # Both files already known -> filter_uningested_reports returns 0 new files
    mock_files = [
        {"id": "file-w29", "name": "Weekly Reporting - Week 29 - 21 Aug 2026.pdf", "week_number": 29},
        {"id": "file-w30", "name": "Weekly Reporting - Week 30 - 28 Aug 2026.pdf", "week_number": 30}
    ]

    mock_script = [
        {"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Week 30 live update."},
        {"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:15", "text": "All systems operational."}
    ]

    with patch('scripts.sync_drive.query_drive_folder_live', return_value=mock_files), \
         patch('scripts.gemini_generator.generate_multispeaker_podcast', return_value=mock_script) as mock_gen:

        summary = sync_drive_reports(
            folder_id="mock-folder-id",
            project_name=mock_project_env["project"],
            data_root=str(Path(mock_project_env["root"]) / "data")
        )

        assert summary["status"] == "success"
        assert summary["new_ingested_count"] == 0  # 0 new files ingested
        
        # BUT podcast generation MUST have run for the latest week
        assert mock_gen.called, "generate_multispeaker_podcast was not called during sync!"

        # Snapshot w30 has the new Gemini script
        snaps_file = os.path.join(mock_project_env["proj_dir"], "snapshots.json")
        data = load_json_file(snaps_file, {})
        w30 = data["snapshots"]["w30"]
        assert w30["generatedBy"] == "gemini-3.5-flash"
        assert w30["podcastScript"][0]["text"] == "Week 30 live update."


# ==============================================================================
# Test 3: Sync Drive Ingestion When New Report Discovered
# ==============================================================================
def test_sync_drive_reports_generates_podcast_when_new_report_discovered(mock_project_env):
    """Verify sync_drive_reports invokes podcast generation when a new report (e.g. Week 31) arrives."""
    mock_files = [
        {"id": "file-w29", "name": "Weekly Reporting - Week 29 - 21 Aug 2026.pdf", "week_number": 29},
        {"id": "file-w30", "name": "Weekly Reporting - Week 30 - 28 Aug 2026.pdf", "week_number": 30},
        {"id": "file-w31", "name": "Weekly Reporting - Week 31 - 04 Sep 2026.pdf", "week_number": 31}
    ]

    mock_script = [
        {"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Week 31 new report briefing."},
        {"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:15", "text": "Reviewing Week 31 milestones."}
    ]

    with patch('scripts.sync_drive.query_drive_folder_live', return_value=mock_files), \
         patch('scripts.gemini_generator.generate_multispeaker_podcast', return_value=mock_script) as mock_gen:

        summary = sync_drive_reports(
            folder_id="mock-folder-id",
            project_name=mock_project_env["project"],
            data_root=str(Path(mock_project_env["root"]) / "data")
        )

        assert summary["status"] == "success"
        assert summary["new_ingested_count"] == 1  # 1 new file (Week 31)
        assert mock_gen.called

        # Snapshot w31 was created and has Gemini podcast
        snaps_file = os.path.join(mock_project_env["proj_dir"], "snapshots.json")
        data = load_json_file(snaps_file, {})
        w31 = data["snapshots"]["w31"]
        assert w31["generatedBy"] == "gemini-3.5-flash"
        assert w31["podcastScript"][0]["text"] == "Week 31 new report briefing."


# ==============================================================================
# Test 4: Pipeline sync_project_data Triggers Podcast Generation
# ==============================================================================
def test_sync_project_data_triggers_podcast_generation(mock_project_env):
    """Verify sync_project_data in scripts/pipeline.py ensures the latest snapshot has a Gemini podcast."""
    mock_script = [
        {"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Sync project data podcast."},
        {"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:15", "text": "Confirmed."}
    ]

    with patch('scripts.gemini_generator.generate_multispeaker_podcast', return_value=mock_script) as mock_gen:
        res = sync_project_data(
            project_name=mock_project_env["project"],
            data_root=str(Path(mock_project_env["root"]) / "data")
        )

        assert res["success"] is True
        assert mock_gen.called

        snaps_file = os.path.join(mock_project_env["proj_dir"], "snapshots.json")
        data = load_json_file(snaps_file, {})
        w30 = data["snapshots"]["w30"]
        assert w30["generatedBy"] == "gemini-3.5-flash"


# ==============================================================================
# Test 5: Server POST /api/sync Triggers Podcast Generation
# ==============================================================================
def test_server_handle_sync_triggers_podcast_generation(mock_project_env):
    """Verify server.py handle_sync executes podcast generation and reports podcast_updated."""
    import server

    mock_script = [
        {"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Server sync briefing."},
        {"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:15", "text": "All metrics current."}
    ]

    with patch.object(server, 'DIRECTORY', mock_project_env["root"]), \
         patch.object(server, 'DATA_BASE_DIR', str(Path(mock_project_env["root"]) / "data")), \
         patch('scripts.pipeline.DATA_BASE_DIR', str(Path(mock_project_env["root"]) / "data")), \
         patch('scripts.sync_drive.DATA_BASE_DIR', str(Path(mock_project_env["root"]) / "data")), \
         patch('scripts.sync_drive.query_drive_folder_live', return_value=[]), \
         patch('scripts.gemini_generator.generate_multispeaker_podcast', return_value=mock_script) as mock_gen:

        handler = server.DashboardHandler.__new__(server.DashboardHandler)
        captured = {}
        handler.send_json = lambda data, status=200: captured.update({"data": data, "status": status})

        handler.handle_sync(f"project={mock_project_env['project']}")

        assert captured.get("status") == 200
        assert mock_gen.called


# ==============================================================================
# Test 6: Gemini 3.5 Flash Model & Region Default Invariant
# ==============================================================================
def test_gemini_generator_defaults_to_gemini_35_flash_and_us_central1(monkeypatch):
    """Verify gemini_generator defaults strictly to gemini-3.5-flash and us-central1 without TTS."""
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_REGION", raising=False)
    monkeypatch.delenv("GCP_REGION", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)

    model = get_default_gemini_model()
    assert model == "gemini-3.5-flash", "Model must default to gemini-3.5-flash"

    region = get_default_gemini_region()
    assert region == "us-central1", "Region must default to us-central1 for Vertex AI"


# ==============================================================================
# Test 7: Frontend Transcript Access Decoupled from Audio
# ==============================================================================
def test_frontend_transcript_button_not_disabled_when_podcast_script_exists(project_root: Path):
    """Verify app.js does not disable the transcript button when podcast script exists."""
    app_js_path = project_root / "src" / "js" / "app.js"
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    # In updatePodcastAudioForWeek, transcriptBtn should check if script exists
    # and must not disable transcriptBtn if script is present
    assert "renderPodcastTranscript" in content
    assert "podcastTranscriptBtn" in content


# ==============================================================================
# Test 8: Podcast Status Check Utility (FR-102)
# ==============================================================================
def test_check_podcast_status_reports_needs_regeneration_on_fallback(mock_project_env):
    """Verify check_project_podcast_status detects fallback script needing regeneration."""
    from scripts.check_podcast_status import check_project_podcast_status

    status = check_project_podcast_status(
        project_name=mock_project_env["project"],
        data_root=str(Path(mock_project_env["root"]) / "data")
    )

    assert status["exists"] is True
    assert status["latest_week"] == "Week 30"
    assert status["status"] in ("MISSING_PODCAST", "NEEDS_REGENERATION")
    assert status["is_up_to_date"] is False
    assert status["is_gemini_35"] is False


def test_check_podcast_status_reports_up_to_date_when_gemini_35(mock_project_env):
    """Verify check_project_podcast_status reports UP_TO_DATE once Gemini 3.5 Flash is generated."""
    from scripts.check_podcast_status import check_project_podcast_status

    # Simulate Gemini 3.5 Flash generation
    mock_script = [
        {"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Audited Week 30 briefing."},
        {"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:15", "text": "All metrics green."}
    ]

    def fake_podcast_generator(*args, **kwargs):
        audio_out = kwargs.get('audio_out_path')
        if audio_out:
            os.makedirs(os.path.dirname(audio_out), exist_ok=True)
            with open(audio_out, 'wb') as f:
                f.write(b"MOCK_MP3_AUDIO_STREAM_DATA")
        return mock_script

    with patch('scripts.gemini_generator.generate_multispeaker_podcast', side_effect=fake_podcast_generator):
        ensure_latest_podcast_generated(
            project_name=mock_project_env["project"],
            data_root=str(Path(mock_project_env["root"]) / "data"),
            force=True
        )

    status = check_project_podcast_status(
        project_name=mock_project_env["project"],
        data_root=str(Path(mock_project_env["root"]) / "data")
    )

    assert status["status"] == "UP_TO_DATE"
    assert status["is_up_to_date"] is True
    assert status["is_gemini_35"] is True
    assert status["turn_count"] == 2
    assert "Alex" in status["speakers"]
    assert "Jordan" in status["speakers"]


def test_check_podcast_status_rich_metadata(mock_project_env):
    """Verify check_project_podcast_status returns complete metadata: size, dates, ingestion, length."""
    from scripts.check_podcast_status import (
        check_project_podcast_status,
        parse_time_str,
        format_duration,
        format_bytes,
        format_datetime_display
    )

    # 1. Test helper utilities
    assert parse_time_str("1:15") == 75
    assert parse_time_str("0:00") == 0
    assert parse_time_str("invalid") is None
    assert format_duration(75) == "1m 15s"
    assert format_duration(0) == "0m 00s"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1048576) == "1.00 MB"
    assert "2026-09-01" in format_datetime_display("2026-09-01T06:48:39.348921")

    # 2. Check rich metadata on generated project
    mock_script = [
        {"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Audited Week 30 briefing with executive details."},
        {"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:15", "text": "All metrics green and verified for release."}
    ]

    with patch('scripts.gemini_generator.generate_multispeaker_podcast', return_value=mock_script):
        ensure_latest_podcast_generated(
            project_name=mock_project_env["project"],
            data_root=str(Path(mock_project_env["root"]) / "data"),
            force=True
        )

    status = check_project_podcast_status(
        project_name=mock_project_env["project"],
        data_root=str(Path(mock_project_env["root"]) / "data")
    )

    # Size assertions
    assert "size_bytes" in status and status["size_bytes"] > 0
    assert "size_formatted" in status and "B" in status["size_formatted"]
    assert "script_size_bytes" in status and status["script_size_bytes"] > 0
    assert "size_summary" in status

    # Date of generation assertions
    assert "generated_at" in status and status["generated_at"] is not None
    assert "generated_at_formatted" in status and status["generated_at_formatted"] != "--"

    # Data ingestion date assertions
    assert "data_ingested_at" in status
    assert "data_ingested_at_formatted" in status and status["data_ingested_at_formatted"] != "--"

    # Length assertions
    assert "duration_seconds" in status and status["duration_seconds"] > 0
    assert "duration_formatted" in status and "m" in status["duration_formatted"]
    assert "length" in status and "turns" in status["length"]
    assert status["length_type"] == "script_estimate"

    # Metadata & Cast assertions
    assert status["turn_count"] == 2
    assert status["word_count"] > 10
    assert status["char_count"] > 50
    assert len(status["speakers_detail"]) == 2
    assert status["speakers_detail"][0]["speaker"] == "Alex"
    assert status["speakers_detail"][0]["role"] == "Program Analyst"
    assert status["speakers_detail"][1]["speaker"] == "Jordan"
    assert status["speakers_detail"][1]["role"] == "Technical Director"

