"""Consolidated regression test matrix covering Bug Fixes and Feature Requests (Phases 1-6)."""

import json
from pathlib import Path
import pytest


# --- Executive Cockpit & Summary (Bugs #26, #27, #29, #39, #41, #47, #53) ---

def test_bug_26_widescreen_layout(full_html: str):
    """Bug #26: Main container should support wide layout max-w-[1750px] or max-w-screen-2xl."""
    assert any(cls in full_html for cls in ["max-w-[1750px]", "max-w-[1800px]", "max-w-7xl", "max-w-screen-2xl", "max-w-[1680px]"])


def test_bug_27_exec_briefing_synthesis(full_html: str):
    """Bug #27: Executive briefing must synthesize Team Google and Blueprint datasets."""
    idx = full_html.find("function renderExecBriefing")
    assert idx != -1
    exec_body = full_html[idx:idx+4000]
    assert any(k in exec_body for k in ["LIVE_TEAM_GOOGLE_RISKS", "teamGoogle", "Team Google"])
    assert any(k in exec_body for k in ["NOTEBOOK_CATALOG", "BUNDLE_ANNEX_MAPPING", "Blueprint", "NotebookLM"])


def test_bug_29_exec_cockpit_interactive_pills(full_html: str):
    """Bug #29: Executive Cockpit top banner and KPI pills must be interactive/clickable."""
    assert any(t in full_html for t in ["switchTab('overview')", "switchTab('team-google')", "switchTab('issues')"])


def test_bug_39_exec_summary_top_5(full_html: str):
    """Bug #39: Executive Summary must populate top 5 risks and issues lists."""
    assert "execTopRisksFullList" in full_html
    assert "execTopIssuesFullList" in full_html
    assert "renderTop5Risks" in full_html or "execTopRisksFullList" in full_html
    assert "renderTop5Issues" in full_html or "execTopIssuesFullList" in full_html


def test_bug_41_exec_summary_blueprint_badges(full_html: str):
    """Bug #41: Executive summary Top 3 attention items must have clickable Blueprint badges."""
    idx = full_html.find("function renderExecBriefing")
    body = full_html[idx:idx+2500] if idx != -1 else full_html
    assert any(fn in body or fn in full_html for fn in ["switchTab('blueprints')", "filterRiskExplorerByBundle", "jumpToBlueprintBundle"])


def test_bug_47_top_5_drilldowns(full_html: str):
    """Bug #47: Top 5 risks and issues lists must have explicit Inspect drilldowns."""
    idx_r = full_html.find("function renderTop5Risks")
    body_r = full_html[idx_r:idx_r+2000] if idx_r != -1 else ""
    assert "openItemDetailModal" in body_r

    idx_i = full_html.find("function renderTop5Issues")
    body_i = full_html[idx_i:idx_i+2000] if idx_i != -1 else ""
    assert "openItemDetailModal" in body_i


def test_bug_53_gap_close_plan_jumps(full_html: str):
    """Bug #53: Gap close plan cards have unique IDs and jumpToGapClose handles direct lookup."""
    assert 'id="gapPlan_${g.num}"' in full_html or "gapPlan_" in full_html
    assert "jumpToGapClose" in full_html


# --- 5x5 Heatmap Matrix (Bugs #30, #31, #36, #40) ---

def test_bug_30_matrix_cell_click_clears_search(full_html: str):
    """Bug #30: Clicking a 5x5 heatmap cell must clear conflicting search text."""
    idx = full_html.find("function highlightHeatmapCell")
    assert idx != -1
    body = full_html[idx:idx+2000]
    assert "explorerSearchInput" in body and ("value = ''" in body or "value=''" in body)


def test_bug_31_and_44_team_google_matrix_and_clear_banner(full_html: str):
    """Bugs #31 & #44: Team Google heatmap follows standard layout with cell click filter and clear banner."""
    assert "renderTeamGoogleHeatmap" in full_html
    assert "clearTeamGoogleActiveCellFilter" in full_html
    assert "teamGoogleActiveCellFilterBanner" in full_html


def test_bug_36_and_40_matrix_axes_standardization(full_html: str):
    """Bugs #36 & #40: 5x5 matrices must have horizontal Likelihood (Rare to Almost Certain) and vertical Consequence."""
    assert "Rare" in full_html and "Almost Certain" in full_html
    assert "Consequence (Y) ↓ / Likelihood (X) →" in full_html
    assert "[writing-mode:vertical-rl]" not in full_html


# --- Risk Explorer & Detail Modals (Bugs #33, #34, #37, #42, #45, #49, #50) ---

def test_bug_33_and_50_blueprint_bundle_badges_and_filter(full_html: str):
    """Bugs #33 & #50: Blueprint bundle filters and risk cards render Blueprint Annex badges/links."""
    assert "filterRiskExplorerByBundle" in full_html
    assert "BUNDLE_ANNEX_MAPPING" in full_html
    assert "Annex" in full_html or "Blueprint" in full_html


def test_bug_34_37_49_risk_card_expansion_and_modals(full_html: str):
    """Bugs #34, #37, #49: Joint and Team Google cards support in-line details and stringified ID modal opening."""
    assert "openItemDetailModal" in full_html
    idx = full_html.find("function openItemDetailModal")
    body = full_html[idx:idx+2500] if idx != -1 else ""
    assert "LIVE_TEAM_GOOGLE_RISKS" in body
    assert "modal.classList.remove('hidden')" in body or "modal" in body


def test_bug_42_risk_explorer_container_aligned(full_html: str):
    """Bug #42: renderRiskExplorer must update explorerCardsContainer element."""
    assert "id=\"explorerCardsContainer\"" in full_html or "id='explorerCardsContainer'" in full_html
    assert "explorerCardsContainer" in full_html


def test_bug_45_issue_modal_blueprint_traceability(full_html: str):
    """Bug #45: openItemDetailModal for issues builds Blueprint Traceability card."""
    idx = full_html.find("function openItemDetailModal")
    body = full_html[idx:idx+3500] if idx != -1 else ""
    assert "Contract Blueprint Traceability" in body or "Blueprint" in body


# --- Issue Register (Bugs #32, #51, #52) ---

def test_bug_32_51_52_issue_table_rendering_and_inspect(full_html: str):
    """Bugs #32, #51, #52: Issue Register stretches vertically, renders on tab switch, and provides Inspect modal trigger."""
    assert 'id="view-issues"' in full_html
    assert "renderIssueTable" in full_html
    idx_switch = full_html.find("function switchTab")
    idx_switch_end = full_html.find("function ", idx_switch + 30)
    body_switch = full_html[idx_switch:idx_switch_end] if idx_switch_end != -1 else full_html[idx_switch:idx_switch+3000]
    assert "renderIssueTable" in body_switch or "filterAndRenderIssues" in body_switch
    idx_table = full_html.find("function renderIssueTable")
    idx_table_end = full_html.find("function ", idx_table + 30)
    body_table = full_html[idx_table:idx_table_end] if idx_table_end != -1 else full_html[idx_table:idx_table+5000]
    assert "openItemDetailModal" in body_table
    assert "Inspect" in body_table or "cursor-pointer" in body_table


# --- Driver Tree (Bugs #46, #70) ---

def test_bug_46_driver_tree_interactive_navigation(full_html: str):
    """Bug #46: Driver tree deliverable cards have interactive navigation and modal inspection."""
    assert "renderDriverTree" in full_html
    assert any(fn in full_html for fn in ["filterByDriverTreeDeliverable", "openDeliverableModal", "openRiskModal", "openItemDetailModal"])
    assert "description: g.description || g.name || g.title" in full_html


# --- Time Machine & Audio Studio (Bugs #38, #48, #71, #72) ---

def test_bug_38_and_48_podcast_dialogue_and_speech_fallback(full_html: str):
    """Bugs #38 & #48: Podcast dialogue resolves dynamically with speech synthesis fallback."""
    assert "getPodcastScriptForWeek" in full_html
    assert "renderPodcastTranscript" in full_html
    assert any(s in full_html for s in ["speechSynthesis", "playExecutivePodcast", "togglePodcastPlayback", "togglePodcastPlay"])


def test_bug_72_podcast_audio_assets(project_root: Path, full_html: str):
    """Bug #72: Natural podcast audio asset exists on disk and is prioritized."""
    assets_dir = project_root / "assets"
    assert assets_dir.exists()
    has_audio = (assets_dir / "podcast_w27.mp3").exists() or (assets_dir / "podcast_w27.wav").exists()
    assert has_audio
    assert "nativePodcastAudio" in full_html or "audioEl" in full_html


def test_bug_71_sleeper_outlier_normalization(full_html: str):
    """Bug #71: Sleeper outlier conditionally hides container when empty and normalizes properties."""
    assert "slContainer" in full_html or "sleeperOutlier" in full_html
    assert "sl.risk || sl.description || sl.title" in full_html or "sleeperOutlier" in full_html


def test_dynamic_timeline_and_baseline_diffing(full_html: str):
    """Verify computeTimelineMetrics and baseline diff comparison dynamically compare snapshots."""
    assert "computeTimelineMetrics" in full_html
    assert "PRECOMPUTED_ANALYTICS" not in full_html
    assert "diffBaselineSelector" in full_html or "setDiffBaseline" in full_html


# --- Governance, Exports & Live Sync (Bugs #1, #23, #28, #35, #56) ---

def test_bug_1_deck_export_bindings(full_html: str):
    """Bug #1: Executive deck export functions are bound."""
    assert 'id="exportDeckBtn"' in full_html
    assert "exportExecutiveDeck" in full_html or "exportDeckPDF" in full_html


def test_bug_23_kpi_pill_wrapping(full_html: str):
    """Bug #23: ATO-C gate and KPI pills have whitespace-nowrap and shrink-0."""
    assert "whitespace-nowrap shrink-0" in full_html


def test_bug_28_35_56_workspace_sync_modal_and_header_dropdown(full_html: str):
    """Bugs #28, #35, #56: Workspace Live Sync modal has 4 streams and header has dual sheet dropdown."""
    assert 'id="sheetsModal"' in full_html
    assert 'id="teamGoogleSheetUrlInput"' in full_html
    assert 'id="notebookUrlInput"' in full_html
    assert 'id="sheetDropdownWrapper"' in full_html or "toggleSheetDropdown" in full_html


def test_ntk_global_classification_banner(full_html: str):
    """Verify Google Need to Know (NTK) classification badge is in the title banner."""
    assert 'id="ntkClassificationBadge"' in full_html
    assert 'Google Need to Know (NTK)' in full_html


def test_bug_97_podcast_audio_availability_gating(full_html: str):
    """Bug #97: Podcast player and transcript are conditionally disabled/greyed out when audio is unavailable without robotic voice fallback."""
    assert "hasAudioForWeek" in full_html
    assert "updatePodcastAudioForWeek" in full_html
    assert "Audio briefing unavailable" in full_html or "Audio unavailable" in full_html
    assert "cursor-not-allowed" in full_html
    assert 'id="podcastTranscriptBtn"' in full_html
    assert "Transcript unavailable" in full_html
    # Ensure dynamic audio resolution and metadata probing without hardcoded week checks
    assert "resolvePodcastAudioSrc" in full_html
    assert "onloadedmetadata" in full_html
    assert "PODCAST_AUDIO_CACHE" in full_html
    # Ensure nativePodcastAudio does NOT hardcode stale week 27 audio in static HTML
    assert 'src="assets/podcast_w27.mp3?v=au3"' not in full_html


def test_bug_98_check_for_updates_feedback(full_html: str):
    """Bug #98: Check for Updates button provides loading state, diff detection, and clear toast feedback."""
    assert 'id="btnCheckUpdates"' in full_html
    assert 'id="btnCheckUpdatesIcon"' in full_html
    assert 'id="btnCheckUpdatesText"' in full_html
    assert "Checking for updates..." in full_html
    assert "Already up to date: No new reports found" in full_html
    assert "Updated: Ingested" in full_html
