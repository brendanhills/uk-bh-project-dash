"""
Tier 1 Prompt Integrity & Variable Coverage Tests.

Verifies:
1. Both prompt templates (exec_summary_prompt.md and podcast_prompt.md) exist on disk.
2. Prompts adhere to Google Universal Prompt Engineering Standards (RASCEF XML structure: <role>, <context>, <instructions>, <guardrails>).
3. All dynamic template variables ({{VARIABLE}}) in both templates are completely resolved
   by build_synthesis_prompt and build_podcast_prompt with 0 orphaned tokens remaining.
4. Graceful handling of missing/sparse input payloads without unhandled exceptions or leaks.
5. Runtime coupling: generate_multispeaker_podcast uses build_podcast_prompt instead of hardcoded strings.
"""

import os
import re
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.gemini_generator import (
    build_synthesis_prompt,
    build_podcast_prompt,
    generate_multispeaker_podcast,
    generate_executive_synthesis,
)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
EXEC_PROMPT_PATH = PROMPTS_DIR / "exec_summary_prompt.md"
PODCAST_PROMPT_PATH = PROMPTS_DIR / "podcast_prompt.md"

VARIABLE_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


# ==============================================================================
# 1. Template File Existence & XML Structural Validation
# ==============================================================================

def test_prompt_files_exist():
    """Verify that canonical prompt templates exist in the prompts directory."""
    assert EXEC_PROMPT_PATH.is_file(), f"Missing template: {EXEC_PROMPT_PATH}"
    assert PODCAST_PROMPT_PATH.is_file(), f"Missing template: {PODCAST_PROMPT_PATH}"


@pytest.mark.parametrize("prompt_path", [EXEC_PROMPT_PATH, PODCAST_PROMPT_PATH])
def test_prompt_rascef_xml_structure(prompt_path: Path):
    """Verify that prompt templates use Google RASCEF XML delimiters."""
    content = prompt_path.read_text(encoding="utf-8")
    for tag in ["<role>", "</role>", "<context>", "</context>", "<instructions>", "</instructions>", "<guardrails>", "</guardrails>"]:
        assert tag in content, f"Prompt {prompt_path.name} is missing mandatory XML delimiter: {tag}"


# ==============================================================================
# 2. Variable Coverage & Substitution Integrity: Executive Synthesis Prompt
# ==============================================================================

def test_exec_summary_prompt_variable_coverage():
    """Verify all template variables in exec_summary_prompt.md are substituted."""
    raw_template = EXEC_PROMPT_PATH.read_text(encoding="utf-8")
    expected_vars = set(VARIABLE_PATTERN.findall(raw_template))
    assert expected_vars, "exec_summary_prompt.md should contain template variables"

    sample_metrics = {
        "project_name": "Test Project",
        "project_title": "Governance Stream",
        "organization": "Joint Board",
        "report_week": "Week 32",
        "report_date": "11 Sep 2026",
        "baseline_week": "Week 31",
        "baseline_date": "04 Sep 2026",
        "overall_status": "GREEN (On Track)",
        "commercial_status": "ON TRACK",
        "ibr_status": "COMPLETED",
        "ato_status": "GRANTED",
        "escalations_count": "1",
        "total_risks": "42",
        "inherent_avg_score": "14.2",
        "residual_avg_score": "6.8",
        "delta_compression": "-7.4",
        "eventuated_issues_count": "0",
        "total_issues": "5"
    }
    sample_plans = [
        {"num": 1, "ref": "DEL-101", "status": "GREEN", "title": "Core Gateway", "plan": "Production rollout", "owner": "Alice", "target": "Sep 2026"}
    ]

    rendered_prompt = build_synthesis_prompt(sample_metrics, sample_plans)

    # Assert that all expected variables were replaced and 0 {{VAR}} placeholders remain
    orphaned = VARIABLE_PATTERN.findall(rendered_prompt)
    assert not orphaned, f"Orphaned variables found in rendered exec summary prompt: {orphaned}"

    for key, val in sample_metrics.items():
        assert val in rendered_prompt, f"Expected metric value '{val}' for '{key}' not found in rendered prompt"


def test_exec_summary_prompt_sparse_metrics_fallback():
    """Verify build_synthesis_prompt handles empty/sparse metrics gracefully."""
    rendered_prompt = build_synthesis_prompt({}, [])
    orphaned = VARIABLE_PATTERN.findall(rendered_prompt)
    assert not orphaned, f"Orphaned variables found with sparse input: {orphaned}"
    assert "Current Reporting Cycle" in rendered_prompt
    assert "No active plan movements reported." in rendered_prompt


# ==============================================================================
# 3. Variable Coverage & Substitution Integrity: Podcast Briefing Prompt
# ==============================================================================

def test_podcast_prompt_variable_coverage():
    """Verify all template variables in podcast_prompt.md are substituted."""
    raw_template = PODCAST_PROMPT_PATH.read_text(encoding="utf-8")
    expected_vars = set(VARIABLE_PATTERN.findall(raw_template))
    assert expected_vars, "podcast_prompt.md should contain template variables"

    sample_metrics = {
        "report_week": "Week 32",
        "report_date": "11 Sep 2026",
        "overall_status": "AMBER (Action Required)",
        "commercial_status": "ON TRACK",
        "ibr_status": "85% COMPLETE",
        "ato_status": "ASSESSORS ACTIVE",
        "inherent_avg_score": "16.0",
        "residual_avg_score": "8.5",
        "delta_compression": "-7.5"
    }
    sample_synthesis = {
        "synthesis": {
            "executive": "Executive delivery briefing on critical path."
        },
        "top3": [
            {"num": 1, "type": "decision", "tag": "🚨 Immediate Executive Action", "ref": "D-1", "title": "Firewall Approval", "action": "Board signoff", "impact": "Unblocks staging"}
        ],
        "sleeperOutlier": {
            "ref": "SO-4",
            "title": "Enclave Bandwidth",
            "warning": "Lead time compression on cross-connects"
        }
    }

    rendered_prompt = build_podcast_prompt(sample_metrics, sample_synthesis)

    orphaned = VARIABLE_PATTERN.findall(rendered_prompt)
    assert not orphaned, f"Orphaned variables found in rendered podcast prompt: {orphaned}"

    assert "Week 32" in rendered_prompt
    assert "11 Sep 2026" in rendered_prompt
    assert "Executive delivery briefing on critical path" in rendered_prompt
    assert "ON TRACK" in rendered_prompt
    assert "85% COMPLETE" in rendered_prompt
    assert "ASSESSORS ACTIVE" in rendered_prompt
    assert "Firewall Approval" in rendered_prompt
    assert "Enclave Bandwidth" in rendered_prompt


def test_podcast_prompt_sparse_metrics_fallback():
    """Verify build_podcast_prompt handles empty/sparse metrics and synthesis gracefully."""
    rendered_prompt = build_podcast_prompt({}, {})
    orphaned = VARIABLE_PATTERN.findall(rendered_prompt)
    assert not orphaned, f"Orphaned variables found with sparse input: {orphaned}"
    assert "Current Reporting Cycle" in rendered_prompt
    assert "AMBER (Stable)" in rendered_prompt
    assert "No critical priority items flagged." in rendered_prompt
    assert "No immediate sleeper outlier identified." in rendered_prompt


# ==============================================================================
# 4. Runtime Re-Coupling Verification
# ==============================================================================

def test_generate_multispeaker_podcast_uses_build_podcast_prompt():
    """Verify generate_multispeaker_podcast calls build_podcast_prompt and loads external template."""
    metrics = {"report_week": "Week 35", "report_date": "02 Oct 2026"}
    synthesis = {
        "synthesis": {"executive": "Test Exec", "technical": "Test Tech", "governance": "Test Gov"},
        "top3": [],
        "sleeperOutlier": {}
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"dialogue": [{"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Hello"}]}'
    mock_client.models.generate_content.return_value = mock_response

    with patch("scripts.gemini_generator.get_gemini_client", return_value=mock_client), \
         patch("scripts.gemini_generator.build_podcast_prompt", wraps=build_podcast_prompt) as spy_build:

        script = generate_multispeaker_podcast(metrics, synthesis)

        assert spy_build.called, "generate_multispeaker_podcast must invoke build_podcast_prompt"
        assert len(script) == 1
        assert script[0]["speaker"] == "Alex"

        # Verify the prompt passed to generate_content came from the template
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        contents_passed = call_kwargs["contents"]
        assert "<role>" in contents_passed
        assert "Alex (Lead Host / Program Delivery Analyst" in contents_passed
        assert "Week 35" in contents_passed
        assert "02 Oct 2026" in contents_passed

        # Verify thinking_config is used and temperature is omitted
        config_passed = call_kwargs["config"]
        assert hasattr(config_passed, "thinking_config")
        assert config_passed.thinking_config.thinking_level == "LOW"
        assert getattr(config_passed, "temperature", None) is None
