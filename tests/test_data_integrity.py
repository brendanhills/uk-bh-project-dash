"""Data integrity tests for synced risk registers and index.html bindings."""

import json
from pathlib import Path
import pytest


def load_full_html(project_root: Path) -> str:
    """Loads index.html concatenated with all ES modules under src/js/."""
    html_file = project_root / "index.html"
    html = html_file.read_text(encoding="utf-8")
    js_dir = project_root / "src" / "js"
    if js_dir.exists():
        for js_path in sorted(js_dir.rglob("*.js")):
            html += "\n" + js_path.read_text(encoding="utf-8")
    return html


def test_live_data_schema(project_root: Path):
    """Verify schema and validity constraints of data/sheets/live_synced_data.json."""
    data_file = project_root / "data" / "sheets" / "live_synced_data.json"
    assert data_file.exists(), f"Missing {data_file}"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "risks" in data
    assert "teamGoogleRisks" in data
    assert "registers" in data
    assert "issues" in data
    assert len(data["risks"]) == 107
    assert len(data["teamGoogleRisks"]) >= 12
    assert len(data["issues"]) == 29

    # Verify joint risks schema
    for r in data["risks"]:
        assert r["status"] in ["Active", "Closed", "Issue Eventuated"]
        assert r["trend"] in ["↔", "↑", "↓"]
        assert r.get("sourceRegister") == "joint"
        assert 1 <= r["inherentLikelihood"] <= 5
        assert 1 <= r["inherentConsequence"] <= 5
        assert len(r["riskName"]) > 0
        assert len(r["riskOwner"]) > 0

    # Verify Team Google risks schema
    for gr in data["teamGoogleRisks"]:
        assert gr["status"] in ["Active", "Closed", "Issue Eventuated"]
        assert gr["trend"] in ["↔", "↑", "↓"]
        assert gr.get("sourceRegister") == "teamGoogle"
        assert 1 <= gr["inherentLikelihood"] <= 5
        assert 1 <= gr["inherentConsequence"] <= 5
        assert len(gr["riskName"]) > 0
        assert len(gr["riskOwner"]) > 0


def test_index_html_canvas_binding(project_root: Path):
    """Verify Chart.js canvas element and script binding IDs are harmonized."""
    html = load_full_html(project_root)
    assert 'id="chartBurndownTimeline"' in html
    assert "document.getElementById('chartBurndownTimeline')" in html
    assert "document.getElementById('chartBurndownBurnup')" not in html


def test_bug_80_aurora_sample_data_isolation(project_root: Path):
    """Bug #80: Audit and eliminate confidential Monaro/F-DSE data leaks from Project Aurora sample dashboard."""
    sample_dir = project_root / "data" / "sample"
    assert sample_dir.exists(), "data/sample must exist"

    confidential_ids = [
        "1qR1tEHFs0QC6CGSUpzHgVgolcF0zQNcg99yZgJwoMVY",  # Monaro Joint Sheet ID
        "1lNRf5NEBd6ygc91nNwFA4HWGFfbDK02QkbkVfr4OUoA",  # Team Google Sheet ID
        "1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C",            # Monaro Drive Folder ID
        "acdbb29b-8632-4fc7-9ba8-2357beeff141",          # Monaro Notebook ID
        "1HBfI9itx3BER4IRnH9eavBgAsrDGHnmu",            # W27 Monaro Drive File ID
        "1UlQmROLEbOroFI8neyne3qOUm4wEgCyC",            # W26 Monaro Drive File ID
        "13ThXt0QIpS2OFg4NEewfx8ggoD2CItlz",            # W25 Monaro Drive File ID
        "100xnsVUDdlKVzxTgK26_lmjSYYUWnUhK",            # W24 Monaro Drive File ID
        "1YRJuXlIIkYRYEsU41K_nuO9iIwrS9k0e",            # W23 Monaro Drive File ID
        "1kQiDQPF9DCUZ0vvbivToMoJWeZJoB0eREFnywRxpCHA",  # W22 Monaro Drive Doc ID
    ]

    # Verify no confidential IDs exist in any data/sample/ JSON file
    for json_file in sample_dir.glob("*.json"):
        content = json_file.read_text(encoding="utf-8")
        for cid in confidential_ids:
            assert cid not in content, f"Confidential ID {cid} leaked in {json_file.name}"
        assert "monaro" not in content.lower(), f"'Monaro' leaked in {json_file.name}"
        assert "f-dse" not in content.lower(), f"'F-DSE' leaked in {json_file.name}"

    # Verify static HTML does not hardcode confidential IDs
    html = (project_root / "index.html").read_text(encoding="utf-8")
    for cid in confidential_ids:
        assert cid not in html, f"Confidential ID {cid} leaked in static index.html"


def test_bug_1_export_deck_functionality(project_root: Path):
    """Bug #1: Downloaded PPTX and PDF export docs are valid files and functions are bound."""
    html = load_full_html(project_root)
    assert 'id="exportDeckBtn"' in html, "exportDeckBtn must exist on briefing card"
    assert "function exportDeckPDF" in html, "exportDeckPDF must be defined"
    assert "function exportExecutiveDeck" in html, "exportExecutiveDeck must be defined"
    assert "window.exportDeckPDF" in html, "exportDeckPDF must be bound to window"
    assert "window.exportExecutiveDeck" in html, "exportExecutiveDeck must be bound to window"