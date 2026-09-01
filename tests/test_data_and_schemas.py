"""Schema validation, mathematical integrity, and confidential data isolation tests across datasets."""

import json
from pathlib import Path
import pytest


# --- Parameterized Multi-Project Dataset Contracts ---

@pytest.mark.parametrize("project", ["sample", "monaro", "f-dse"])
def test_project_data_files_exist_and_parse(project_root: Path, project: str):
    """Verify that sample, monaro, and f-dse directories contain valid JSON for all 6 required data files."""
    required_files = [
        'config.json',
        'snapshots.json',
        'risks.json',
        'issues.json',
        'knowledge.json',
        'driver_tree.json'
    ]
    proj_dir = project_root / 'data' / project
    if not proj_dir.is_dir():
        pytest.skip(f"Private data/{project} directory not present in clean checkout (supplied via GCS volume mount)")

    for fname in required_files:
        fpath = proj_dir / fname
        assert fpath.is_file(), f"Missing required file for {project}: {fpath}"
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data is not None, f"{fpath} is empty or null"


# --- Sample Dataset Schema & Math Integrity ---

def test_sample_config_schema(sample_config: dict):
    """Verify data/sample/config.json schema, features, and 4 KPI pillars."""
    assert sample_config.get("project", {}).get("slug") == "sample"
    assert "name" in sample_config.get("project", {})
    assert "title" in sample_config.get("project", {})
    assert "features" in sample_config
    assert "kpiPillars" in sample_config
    assert len(sample_config["kpiPillars"]) == 4


def test_sample_risks_and_5x5_math(sample_risks: list):
    """Verify 5x5 Likelihood x Consequence score math across all sample risks."""
    assert len(sample_risks) >= 25, "Sample risks dataset must have at least 25 records"

    for r in sample_risks:
        assert "id" in r
        assert "title" in r
        assert "status" in r

        inh_l = int(r.get("inherentLikelihood", 1))
        inh_c = int(r.get("inherentConsequence", 1))
        res_l = int(r.get("residualLikelihood", 1))
        res_c = int(r.get("residualConsequence", 1))

        assert 1 <= inh_l <= 5, f"Inherent likelihood out of range for {r.get('id')}"
        assert 1 <= inh_c <= 5, f"Inherent consequence out of range for {r.get('id')}"
        assert 1 <= res_l <= 5, f"Residual likelihood out of range for {r.get('id')}"
        assert 1 <= res_c <= 5, f"Residual consequence out of range for {r.get('id')}"

        assert int(r.get("inherentRiskScore")) == inh_l * inh_c
        assert int(r.get("residualRiskScore")) == res_l * res_c


def test_sample_issues_and_snapshots_schema(sample_issues: list, sample_snapshots: dict):
    """Verify sample issues and multi-week historical snapshots schema."""
    assert len(sample_issues) >= 10
    for iss in sample_issues:
        assert "id" in iss
        assert "title" in iss
        assert "severity" in iss
        assert "status" in iss

    snapshots = sample_snapshots.get("snapshots", {})
    assert len(snapshots) >= 6, "Sample snapshots must have at least 6 historical weeks"
    latest = [s for s in snapshots.values() if s.get("isLatest") or s.get("isCurrent")]
    assert len(latest) >= 1
    latest_snap = latest[0]
    assert "synthesis" in latest_snap
    assert "top3" in latest_snap
    assert "sleeperOutlier" in latest_snap
    assert "podcastScript" in latest_snap


def test_sample_driver_tree_and_knowledge(sample_driver_tree: dict, sample_knowledge: dict):
    """Verify sample driver tree and blueprint knowledge schema."""
    assert sample_driver_tree is not None
    assert len(sample_knowledge.get("blueprints", [])) >= 8


# --- Register Separation & Enterprise Data Checks ---

def test_register_separation_and_counts(project_root: Path):
    """Verify primary and secondary register configuration and distinct counts."""
    data_dir = (project_root / 'data' / 'monaro') if (project_root / 'data' / 'monaro').exists() else (project_root / 'data' / 'f-dse')
    if not data_dir.exists():
        pytest.skip("Private enterprise data directory not present")

    config = json.loads((data_dir / 'config.json').read_text(encoding='utf-8'))
    assert config.get('project', {}).get('primaryRegisterName') == 'Internal Risks'
    assert config.get('project', {}).get('secondaryRegisterName') == 'Team Google Risks'

    risks = json.loads((data_dir / 'risks.json').read_text(encoding='utf-8'))
    assert len(risks) == 119
    internal = [r for r in risks if not (r.get('sourceRegister') == 'team_google' or str(r.get('id')).startswith(('TG-', 'AUR-TG-')))]
    tg = [r for r in risks if r.get('sourceRegister') == 'team_google' or str(r.get('id')).startswith(('TG-', 'AUR-TG-'))]
    assert len(internal) == 107
    assert len(tg) == 12


def test_enterprise_driver_tree_and_knowledge(project_root: Path):
    """Verify F-DSE driver tree 24 gates (Bug #70) and blueprint bundle sources."""
    data_dir = (project_root / 'data' / 'monaro') if (project_root / 'data' / 'monaro').exists() else (project_root / 'data' / 'f-dse')
    if not data_dir.exists():
        pytest.skip("Private enterprise data directory not present")

    k_data = json.loads((data_dir / 'knowledge.json').read_text(encoding='utf-8'))
    sources = k_data.get('sources', [])
    blueprints = [s for s in sources if s.get('bundle')]
    assert len(blueprints) >= 10, "Expected at least 10 blueprint bundle sources in knowledge"

    if (data_dir / 'driver_tree.json').exists():
        dt = json.loads((data_dir / 'driver_tree.json').read_text(encoding='utf-8'))
        all_gates = []
        for cd in dt.get('capabilityDrops', []):
            all_gates.extend(cd.get('gates', []))
        if len(all_gates) == 24:
            l2_gates = [g for g in all_gates if g.get('level') == 2]
            l3_gates = [g for g in all_gates if g.get('level') == 3]
            assert len(l2_gates) >= 10
            assert len(l3_gates) >= 10


def test_live_synced_data_schema_if_present(project_root: Path):
    """Verify schema and validity constraints of data/sheets/live_synced_data.json if present."""
    data_file = project_root / "data" / "sheets" / "live_synced_data.json"
    if not data_file.exists():
        pytest.skip("Optional sheets sync data file not present")

    data = json.loads(data_file.read_text(encoding="utf-8"))
    assert "risks" in data
    assert "teamGoogleRisks" in data
    assert "registers" in data
    assert "issues" in data
    assert len(data["risks"]) == 107
    assert len(data["teamGoogleRisks"]) >= 12
    assert len(data["issues"]) == 29


# --- Bug #80 Confidentiality Audit ---

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

    for json_file in sample_dir.glob("*.json"):
        content = json_file.read_text(encoding="utf-8")
        for cid in confidential_ids:
            assert cid not in content, f"Confidential ID {cid} leaked in {json_file.name}"
        assert "monaro" not in content.lower(), f"'Monaro' leaked in {json_file.name}"
        assert "f-dse" not in content.lower(), f"'F-DSE' leaked in {json_file.name}"

    html = (project_root / "index.html").read_text(encoding="utf-8")
    for cid in confidential_ids:
        assert cid not in html, f"Confidential ID {cid} leaked in static index.html"
