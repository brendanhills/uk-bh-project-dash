#!/usr/bin/env python3
"""LLM-as-a-Judge Realism and Anti-Leakage Evaluation Harness for Project Aurora.

Evaluates generated synthetic assets against rubric criteria using Gemini 3.5 Flash:
  1. In-flight Realism (0-100%, threshold >= 85%):
     - Does the dataset authentically paint the picture of a real in-flight clinical cloud
       modernization program (EHR cutovers, PACS medical imaging, FHIR APIs, hospital nursing
       and clinical informatics staff)?
     - Are risks and escalations authentic with plausible mitigations and clinical treatment owners?
  2. Contextual Consistency (0-100%, threshold >= 85%):
     - Do the weekly status reports, driver tree gates, and contract blueprint annexes tell a
       consistent, cohesive narrative?
  3. Zero Confidentiality Leakage (0-100%, threshold = 100%):
     - Strictly 0 occurrences of Monaro entities, defence agencies, defence contract acronyms
       (AGSVA, ISM, NV2/PV, CDS, ATO-C, IRAP), or defence operational contexts.
"""

import json
import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.gemini_generator import get_gemini_client, get_default_gemini_model
from google.genai import types


class RealismEvalScores(BaseModel):
    inflight_realism_score: int = Field(
        description="Score from 0 to 100 on how realistically this dataset depicts an active, in-flight healthcare digital health transformation program."
    )
    contextual_consistency_score: int = Field(
        description="Score from 0 to 100 on narrative alignment and cross-artifact consistency between registers, weekly reports, and contract annexes."
    )
    zero_leakage_score: int = Field(
        description="Score from 0 to 100 on total absence of defence, military, intelligence, or confidential Monaro project keywords (100 = completely clean healthcare domain, 0 = defence terms present)."
    )
    reasoning: str = Field(
        description="Detailed multi-sentence evaluation critique explaining the assigned scores across realism, consistency, and anti-leakage."
    )
    leaked_terms_found: list[str] = Field(
        default_factory=list,
        description="List of any defence or confidential terms detected in the evaluated samples (must be empty for pass)."
    )


def build_evaluation_prompt(sample_data_summary: dict) -> str:
    return f"""<role>
You are an expert Principal Systems Architect and Generative AI Judge evaluating synthetic datasets created for an executive risk and program dashboard.
</role>

<context>
The project being evaluated is "Project Aurora" (Clinical Cloud Modernization & Healthcare Intelligence).
Project Aurora is designed as a public demonstration dataset.
CRITICAL MANDATE:
Project Aurora MUST portray an authentic, in-flight acute Healthcare Cloud Transformation (EHR migration, FHIR APIs, PACS diagnostic imaging pipelines, hospital clinical go-lives).
It MUST have ZERO leakage or contamination with sovereign defence or military projects (e.g. Project Monaro, AGSVA, NV2/PV clearances, ISM, IRAP, Cross-Domain Diode CDS, ATO-C).
</context>

<instructions>
Evaluate the provided synthetic dataset excerpts against three core dimensions:
1. In-flight Realism (0-100):
   - Does this paint an authentic, credible picture of a major hospital and healthcare cloud migration in progress?
   - Are the risks (e.g. FHIR API throughput, DICOM image cache sizing, HL7 translation, clinical informatics staffing) realistic and high-fidelity?
2. Contextual Consistency (0-100):
   - Are the KPIs, weekly status reports, deliverable gates, and contract annexes coherent with each other?
3. Zero Confidentiality Leakage (0-100):
   - Are there ANY defence, military, intelligence, or sovereign defence terms present?
   - If ANY defence terms appear, score 0 for zero_leakage_score and list the terms in leaked_terms_found.
   - If the dataset is purely healthcare and clinical, score 100.
</instructions>

<input_dataset_excerpts>
{json.dumps(sample_data_summary, indent=2)}
</input_dataset_excerpts>

Return your structured judgment adhering strictly to the response schema.
"""


def evaluate_aurora_realism() -> RealismEvalScores:
    data_sample_dir = PROJECT_ROOT / "data" / "sample"
    grounding_dir = PROJECT_ROOT / "assets" / "synthetic" / "grounding_docs"

    risks = json.loads((data_sample_dir / "risks.json").read_text(encoding="utf-8"))[:6]
    issues = json.loads((data_sample_dir / "issues.json").read_text(encoding="utf-8"))[:5]
    knowledge = json.loads((data_sample_dir / "knowledge.json").read_text(encoding="utf-8"))
    config = json.loads((data_sample_dir / "config.json").read_text(encoding="utf-8"))
    
    annex_sample = ""
    if (grounding_dir / "Annex_A1_Integrated_Clinical_Rollout_Schedule.md").exists():
        annex_sample = (grounding_dir / "Annex_A1_Integrated_Clinical_Rollout_Schedule.md").read_text(encoding="utf-8")[:500]

    sample_summary = {
        "project_config": config.get("project", {}),
        "blueprint_annexes": knowledge.get("blueprints", [])[:4],
        "sample_risks": [
            {
                "id": r.get("id"),
                "name": r.get("riskName"),
                "desc": r.get("riskDescription"),
                "bundle": r.get("bundle"),
                "treatment": r.get("treatmentPlan")
            } for r in risks
        ],
        "sample_issues": [
            {
                "id": i.get("id"),
                "name": i.get("issueName"),
                "desc": i.get("issueDescription"),
                "action": i.get("actionPlan")
            } for i in issues
        ],
        "annex_excerpt": annex_sample
    }

    client = get_gemini_client()
    if not client:
        raise RuntimeError("Gemini client could not be initialized for LLM-as-a-judge evaluation.")

    model_name = get_default_gemini_model()
    prompt = build_evaluation_prompt(sample_summary)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RealismEvalScores,
            thinking_config=types.ThinkingConfig(thinking_budget=1024)
        )
    )

    result_json = json.loads(response.text)
    return RealismEvalScores.model_validate(result_json)


def main():
    print("=" * 70)
    print("⚖️ Running LLM-as-a-Judge Realism & Anti-Leakage Evaluation...")
    print("=" * 70)
    
    try:
        eval_result = evaluate_aurora_realism()
    except Exception as e:
        print(f"❌ Evaluation error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"📊 In-Flight Realism Score:       {eval_result.inflight_realism_score}/100")
    print(f"📊 Contextual Consistency Score:   {eval_result.contextual_consistency_score}/100")
    print(f"🛡️ Zero Confidentiality Leakage:   {eval_result.zero_leakage_score}/100")
    print("\n📝 Judge Critique:")
    print(eval_result.reasoning)

    if eval_result.leaked_terms_found:
        print(f"\n🚨 Leaked Terms Detected: {eval_result.leaked_terms_found}")

    passed = (
        eval_result.inflight_realism_score >= 85 and
        eval_result.contextual_consistency_score >= 85 and
        eval_result.zero_leakage_score == 100 and
        len(eval_result.leaked_terms_found) == 0
    )

    print("=" * 70)
    if passed:
        print("✅ VERDICT: PASSED (Project Aurora achieves authentic clinical realism with 100% zero-leakage)")
        sys.exit(0)
    else:
        print("❌ VERDICT: FAILED (Thresholds not met: realism>=85, consistency>=85, leakage=100)")
        sys.exit(1)


if __name__ == "__main__":
    main()
