#!/usr/bin/env python3
"""Export synthetic external assets for Project Aurora (Streams 1–4).

Generates:
  Stream 1: assets/synthetic/aurora_joint_clinical_register.csv
  Stream 2: assets/synthetic/aurora_team_cloud_register.csv
  Stream 3: assets/synthetic/weekly_reports/Weekly_Reporting_Week_27_07_Aug_2026.pdf
            assets/synthetic/weekly_reports/Weekly_Reporting_Week_28_14_Aug_2026.pdf
  Stream 4: assets/synthetic/grounding_docs/Annex_A1_Integrated_Clinical_Rollout_Schedule.md
            assets/synthetic/grounding_docs/Annex_B1_Clinical_Data_Protection_and_HIPAA.md
            assets/synthetic/grounding_docs/Annex_C2_Clinical_Informatics_Workforce.md
            assets/synthetic/grounding_docs/Annex_D1_Healthcare_SLAs_and_Custodianship.md

All assets are strictly grounded in the Healthcare Digital Health transformation domain
(EHR migrations, FHIR APIs, PACS imaging pipelines, acute clinical go-lives).
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "synthetic"
REPORTS_DIR = OUTPUT_DIR / "weekly_reports"
GROUNDING_DIR = OUTPUT_DIR / "grounding_docs"


def ensure_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    GROUNDING_DIR.mkdir(parents=True, exist_ok=True)


def export_stream_1_joint_register():
    """Export Stream 1: Joint Clinical Governance Register CSV."""
    risks_file = DATA_SAMPLE_DIR / "risks.json"
    issues_file = DATA_SAMPLE_DIR / "issues.json"

    risks = json.loads(risks_file.read_text(encoding="utf-8")) if risks_file.exists() else []
    issues = json.loads(issues_file.read_text(encoding="utf-8")) if issues_file.exists() else []

    joint_risks = [r for r in risks if r.get("sourceRegister") != "team_google" and not str(r.get("id")).startswith("AUR-TG-")]

    csv_path = OUTPUT_DIR / "aurora_joint_clinical_register.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Item Type", "ID", "Display ID", "Status", "Clinical Lead / Owner",
            "Blueprint Bundle", "Ref", "Title / Summary", "Description",
            "Category", "Likelihood (1-5)", "Consequence (1-5)", "Risk Score",
            "Treatment / Action Plan", "Target Date", "Date Raised", "Last Updated"
        ])
        for r in joint_risks:
            writer.writerow([
                "Risk",
                r.get("id", ""),
                r.get("displayId", ""),
                r.get("status", ""),
                r.get("riskOwner", ""),
                r.get("bundle", ""),
                r.get("driverTreeRef", ""),
                r.get("riskName", ""),
                r.get("riskDescription", ""),
                r.get("causeCategory", ""),
                r.get("residualLikelihood", r.get("inherentLikelihood", "")),
                r.get("residualConsequence", r.get("inherentConsequence", "")),
                r.get("residualRiskScore", r.get("inherentRiskScore", "")),
                r.get("treatmentPlan", ""),
                r.get("targetDate", ""),
                r.get("dateRaised", ""),
                r.get("riskLastUpdated", "")
            ])
        for i in issues:
            writer.writerow([
                "Issue / Escalation",
                i.get("id", ""),
                i.get("displayId", ""),
                i.get("status", ""),
                i.get("issueOwner", ""),
                i.get("bundle", ""),
                i.get("driverTreeRef", ""),
                i.get("issueName", ""),
                i.get("issueDescription", ""),
                i.get("impactCategory", "Clinical Schedule"),
                "-", "-", i.get("severity", "High"),
                i.get("actionPlan", ""),
                "-",
                i.get("dateRaised", ""),
                i.get("lastUpdated", "")
            ])
    print(f"Exported Stream 1 CSV: {csv_path} ({len(joint_risks)} risks, {len(issues)} issues)")
    return csv_path


def export_stream_2_team_cloud_register():
    """Export Stream 2: Team Cloud Register CSV."""
    risks_file = DATA_SAMPLE_DIR / "risks.json"
    risks = json.loads(risks_file.read_text(encoding="utf-8")) if risks_file.exists() else []

    tg_risks = [r for r in risks if r.get("sourceRegister") == "team_google" or str(r.get("id")).startswith("AUR-TG-")]

    csv_path = OUTPUT_DIR / "aurora_team_cloud_register.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Display ID", "Status", "Cloud Technical Lead",
            "Bundle", "Ref", "Risk Title", "Description",
            "Category", "Likelihood (1-5)", "Consequence (1-5)", "Residual Score",
            "Mitigation Strategy", "Target Date", "Last Updated"
        ])
        for r in tg_risks:
            writer.writerow([
                r.get("id", ""),
                r.get("displayId", ""),
                r.get("status", ""),
                r.get("riskOwner", ""),
                r.get("bundle", ""),
                r.get("driverTreeRef", ""),
                r.get("riskName", ""),
                r.get("riskDescription", ""),
                r.get("causeCategory", ""),
                r.get("residualLikelihood", ""),
                r.get("residualConsequence", ""),
                r.get("residualRiskScore", ""),
                r.get("treatmentPlan", ""),
                r.get("targetDate", ""),
                r.get("riskLastUpdated", "")
            ])
    print(f"Exported Stream 2 CSV: {csv_path} ({len(tg_risks)} cloud risks)")
    return csv_path


def html_to_pdf_chrome(html_content: str, output_pdf_path: Path):
    """Compiles an HTML string into a PDF via Headless Chrome."""
    temp_html = output_pdf_path.with_suffix(".temp.html")
    temp_html.write_text(html_content, encoding="utf-8")
    try:
        cmd = [
            "google-chrome",
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={output_pdf_path}",
            str(temp_html)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Rendered PDF via Chrome: {output_pdf_path}")
    finally:
        if temp_html.exists():
            temp_html.unlink()


def generate_stream_3_weekly_reports():
    """Generate Stream 3: Weekly Status Report PDF packs (Week 27 & Week 28)."""
    snaps_file = DATA_SAMPLE_DIR / "snapshots.json"
    snaps_data = json.loads(snaps_file.read_text(encoding="utf-8")) if snaps_file.exists() else {}
    snapshots = snaps_data.get("snapshots", {})

    reports_generated = []

    # Generate reports for all weeks in snapshots (e.g. W21 through W28)
    week_keys = sorted(snapshots.keys(), key=lambda k: int("".join(c for c in k if c.isdigit()) or "0"))
    for week_key in week_keys:
        snap = snapshots.get(week_key, {})
        week_num = snap.get("weekNumber", 28)
        week_label = snap.get("weekLabel", f"Week {week_num}")
        report_date = snap.get("date", "14 Aug 2026")
        status = snap.get("overallStatus", "ON TRACK")
        syn = snap.get("synthesis", {})
        top3 = snap.get("top3", [])
        sleeper = snap.get("sleeperOutlier", {})
        plans = snap.get("plans", [])

        top3_html = "".join([
            f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #6366f1; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="font-size: 11px; font-weight: 700; color: #4338ca; text-transform: uppercase;">{item.get('tag', 'Attention Item')} &bull; Ref {item.get('ref', '')}</div>
                <div style="font-size: 13px; font-weight: 800; color: #0f172a; margin: 4px 0;">{item.get('title', '')}</div>
                <div style="font-size: 12px; color: #334155; line-height: 1.5;">{item.get('action', item.get('impact', ''))}</div>
            </div>
            """ for item in top3
        ])

        plans_html = "".join([
            f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-size: 11px;">{p.get('ref', '')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-weight: 600; font-size: 12px;">{p.get('title', '')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-size: 11px; color: #475569;">{p.get('owner', '')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-size: 11px; font-weight: 700;">{p.get('status', 'AMBER')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; font-size: 11px;">{p.get('target', 'TBD')}</td>
            </tr>
            """ for p in plans
        ])

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Project Aurora - {week_label} Status Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            margin: 0;
            padding: 32px 40px;
            background: #ffffff;
            line-height: 1.5;
        }}
        .header {{
            border-bottom: 2px solid #0284c7;
            padding-bottom: 16px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 900;
            color: #0369a1;
            letter-spacing: -0.5px;
        }}
        .sub {{
            font-size: 13px;
            color: #64748b;
            margin-top: 2px;
        }}
        .badge {{
            display: inline-block;
            background: #0284c7;
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 9999px;
            text-transform: uppercase;
        }}
        h2 {{
            font-size: 14px;
            font-weight: 800;
            color: #0f172a;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 6px;
            margin-top: 24px;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .summary-box {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 14px 16px;
            font-size: 12.5px;
            color: #166534;
            line-height: 1.6;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
        }}
        th {{
            background: #f1f5f9;
            text-align: left;
            padding: 8px;
            font-size: 11px;
            font-weight: 800;
            color: #475569;
            text-transform: uppercase;
            border-bottom: 2px solid #cbd5e1;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 12px;
            border-top: 1px solid #e2e8f0;
            font-size: 11px;
            color: #94a3b8;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="logo">🌌 PROJECT AURORA &bull; HEALTHCARE CLOUD TRANSFORMATION</div>
            <div class="sub">Joint Clinical Governance Board &bull; Hospital Modernization Program</div>
        </div>
        <div style="text-align: right;">
            <div class="badge">{status}</div>
            <div style="font-size: 12px; font-weight: 700; margin-top: 6px; color: #334155;">{week_label} &bull; {report_date}</div>
        </div>
    </div>

    <h2>1. Executive Clinical Synthesis</h2>
    <div class="summary-box">
        {syn.get('executive', 'Delivery velocity remains active. Critical path clinical go-live milestones are advancing on schedule.')}
    </div>

    <h2>2. Top Executive Attention Items</h2>
    {top3_html}

    <h2>3. Critical Milestone & Gap Close Status</h2>
    <table>
        <thead>
            <tr>
                <th>Gate Ref</th>
                <th>Deliverable / Action Plan</th>
                <th>Clinical Owner</th>
                <th>Status</th>
                <th>Target Date</th>
            </tr>
        </thead>
        <tbody>
            {plans_html if plans else '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #64748b;">All clinical rollout gap close plans on track.</td></tr>'}
        </tbody>
    </table>

    <h2>4. Sleeper Outlier & Proactive Advisory</h2>
    <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px 16px; font-size: 12px; color: #92400e;">
        <strong>Ref {sleeper.get('ref', '1.14')} &mdash; {sleeper.get('title', 'Clinical Interoperability Review Window')}:</strong>
        <p style="margin: 4px 0 0 0;">{sleeper.get('warning', 'Inter-departmental clinical validation handoffs may compress go-live window if pre-requisite PACS interfaces are delayed.')}</p>
    </div>

    <div class="footer">
        Project Aurora Healthcare Modernization &bull; Certified Confidential Synthetic Asset &bull; Generated for Project Dash
    </div>
</body>
</html>"""

        filename = f"Weekly_Reporting_{week_label.replace(' ', '_')}_{report_date.replace(' ', '_')}.pdf"
        out_pdf = REPORTS_DIR / filename
        html_to_pdf_chrome(html_content, out_pdf)
        reports_generated.append(out_pdf)

    return reports_generated


def generate_stream_4_grounding_docs():
    """Generate Stream 4: Authentic Healthcare Contract Annexes as Markdown documents."""
    annexes = [
        (
            "Annex_A1_Integrated_Clinical_Rollout_Schedule.md",
            "Annex A.1 — Integrated Clinical Rollout Schedule (ICRS) & Hospital Go-Live",
            """# Annex A.1: Integrated Clinical Rollout Schedule (ICRS) & Hospital Go-Live Matrix

## 1. Scope & Objective
This schedule governs the multi-phase deployment, clinical departmental cutover, and verification gates for the Project Aurora Healthcare Cloud Platform across regional and metropolitan hospitals.

## 2. Capability Drop & Cutover Milestones
- **Gate 1.2b — Architecture & V&V Acceptance**: Formal clinical sponsor sign-off on FHIR R4 schema bindings, electronic health record (EHR) gateway latencies (<150ms P99), and end-to-end clinical workflow test cases.
- **Gate 1.6 — Hospital LAN & High-Assurance Clinical Optical Connectivity**: Verification of redundant low-latency fiber links between central healthcare cloud clusters and acute intensive care units (ICU).
- **Gate 1.10b — Hospital Private Cloud Infrastructure & PACS Storage Fabric**: Commissioning of on-site high-throughput DICOM imaging cache clusters and Tier-1 clinical database nodes.
- **Gate 1.14 — Systems Requirements Review (SRR) Hospital Baseline**: Clinical review of multi-site disaster recovery and emergency offline clinical chart caching.

## 3. Go-Live Verification Criteria
Each hospital hospital facility must achieve 100% completion on:
1. Medical device VLAN microsegmentation and bedside telemetry validation.
2. Clinician single sign-on (SSO) biometric badge pairing via SMART-on-FHIR.
3. 24/7 dry-run emergency simulation with zero patient data dropped.
"""
        ),
        (
            "Annex_B1_Clinical_Data_Protection_and_HIPAA.md",
            "Annex B.1 — Clinical Data Protection, HIPAA & Health Record Security Controls",
            """# Annex B.1: Clinical Data Protection, HIPAA & Health Record Security Controls

## 1. Compliance Baseline
All services and storage buckets deployed under Project Aurora must comply with:
- **HIPAA Security & Privacy Rules** (45 CFR Part 160 and Part 164)
- **Australian My Health Record Privacy Framework & Privacy Act 1988**
- **ISO 27799:2016** (Health informatics & information security management in health)

## 2. Cryptographic Controls & Key Management
- **At-Rest Protection**: All patient health identifiers (PHI) and clinical records stored within database columns or cloud storage objects must utilize AES-256 GCM authenticated encryption with Customer-Managed Encryption Keys (CMEK) held in regional dedicated Cloud HSM partitions.
- **In-Transit Protection**: Clinical REST endpoints enforce TLS 1.3 with mutual authentication (mTLS) for all backend service-to-service calls.
- **Automated Evidence Collection**: Continuous compliance probers verify zero unencrypted data stores daily, automatically streaming audit logs to immutable cold storage.
"""
        ),
        (
            "Annex_C2_Clinical_Informatics_Workforce.md",
            "Annex C.2 — Clinical Informatics Workforce & FHIR Integration Team Staffing",
            """# Annex C.2: Clinical Informatics Workforce & FHIR Integration Team

## 1. Operational Headcount Allocation
The delivery organization maintains dedicated clinical liaison teams to oversee hospital workflow translation:
- **Chief Medical Informatics Officer (CMIO) Liaison**: 2 FTE
- **Lead Clinical Nurse Informaticists**: 6 FTE assigned across acute care wards
- **FHIR R4 / HL7 v2 Interface Engineers**: 8 FTE
- **DICOM / PACS Imaging Pipeline Specialists**: 4 FTE

## 2. Onboarding & Certification Protocol
All technical and clinical engineering personnel must complete:
1. Certified Health Data Privacy and Information Handling credentialing.
2. Clinical Workflow Observation Rotation (minimum 40 hours in acute clinical setting).
3. Zero-Trust Access Authorization with periodic role-based review.
"""
        ),
        (
            "Annex_D1_Healthcare_SLAs_and_Custodianship.md",
            "Annex D.1 — Healthcare Service Level Agreements (SLA) & Data Custodianship Ledger",
            """# Annex D.1: Healthcare Service Level Agreements (SLA) & Data Custodianship Ledger

## 1. Service Level Guarantees (SLA)
- **Emergency Department EHR Ingestion**: 99.999% monthly availability (< 26 seconds allowable downtime/month).
- **Clinical PACS Diagnostic Imaging Retrieval**: Median latency < 450ms for urgent radiological CT/MRI scans.
- **Outpatient FHIR API Availability**: 99.95% monthly uptime.

## 2. Financial Penalty & Service Credit Matrix
Breaches of core clinical availability trigger progressive service credits:
- Monthly availability < 99.99%: 10% monthly service fee rebate.
- Monthly availability < 99.90%: 25% monthly service fee rebate and immediate root-cause presentation to the Joint Clinical Steering Committee.

## 3. Data Custodianship & Sovereignty
The customer retains sole legal and beneficial ownership of all patient clinical records, diagnostic images, and telemetry data. Vendor access is strictly mediated by ephemeral, audited access tokens granted by the Hospital Data Custodian.
"""
        )
    ]

    docs_generated = []
    for filename, title, markdown in annexes:
        doc_path = GROUNDING_DIR / filename
        doc_path.write_text(markdown, encoding="utf-8")
        print(f"Generated Grounding Doc: {doc_path}")
        docs_generated.append(doc_path)
    return docs_generated


def main():
    print("=" * 70)
    print("🏥 Generating Project Aurora Synthetic External Assets (Streams 1–4)...")
    print("=" * 70)
    ensure_directories()
    s1 = export_stream_1_joint_register()
    s2 = export_stream_2_team_cloud_register()
    s3 = generate_stream_3_weekly_reports()
    s4 = generate_stream_4_grounding_docs()
    print("=" * 70)
    print("✅ All synthetic assets successfully generated:")
    print(f"  Stream 1: {s1}")
    print(f"  Stream 2: {s2}")
    print(f"  Stream 3: {len(s3)} PDF report packs in {REPORTS_DIR}")
    print(f"  Stream 4: {len(s4)} Markdown annexes in {GROUNDING_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
