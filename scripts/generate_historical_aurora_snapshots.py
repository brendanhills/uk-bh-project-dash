#!/usr/bin/env python3
"""Generate 2 months (8 weeks: W21 through W28) of realistic, progressive Healthcare Cloud snapshots.

Dates:
  W21: 26 Jun 2026
  W22: 03 Jul 2026
  W23: 10 Jul 2026
  W24: 17 Jul 2026
  W25: 24 Jul 2026
  W26: 31 Jul 2026
  W27: 07 Aug 2026
  W28: 14 Aug 2026 (Latest/Present)

Narrative Progression:
  - W21-W23: Initial hospital network validation, high initial risk (ICU telemetry jitter, HL7 v2 mapping gaps), AMBER-RED posture.
  - W24-W26: Active mitigation burn-down, FHIR R4 gateway stabilization, clinical informatics badge pairing pilot, AMBER posture.
  - W27-W28: Gate 2 verification closure, CI/CD automated compliance pass, PACS diagnostic latency down to 240ms, GREEN / ON TRACK.

Outputs:
  - Updates data/sample/snapshots.json with rich, authentic clinical narratives, KPIs, Top 3s, and gap close plans across all 8 weeks.
  - Generates all 8 PDF report packs in assets/synthetic/weekly_reports/.
  - Updates data/sample/config.json with all 8 knownReports.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
SNAPS_FILE = DATA_SAMPLE_DIR / "snapshots.json"

WEEKS_DATA = [
    {
        "weekNumber": 21,
        "weekLabel": "Week 21",
        "week": "Week 21",
        "date": "26 Jun 2026",
        "overallStatus": "🔴 CRITICAL ATTENTION",
        "kpis": {
            "clinicalGoLive": "🔴 DELAY RISK",
            "fhirInteroperability": "🟡 65% PASS",
            "hipaaCompliance": "🟡 AUDIT PREP",
            "escalations": "🔴 7 ITEMS"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 16.8,
            "residual_avg_score": 13.4,
            "delta_compression": "-3.4",
            "eventuated_issues_count": 4,
            "total_issues": 11,
            "report_week": "Week 21",
            "report_date": "26 Jun 2026"
        },
        "synthesis": {
            "executive": "Program posture for Week 21 reflects critical path pressure during Phase 1 hospital environment bring-up. Seven acute escalations require steering committee intervention, primarily regarding hospital ward optical fiber lead times and clinical telemetry VLAN isolation.",
            "technical": "HL7 v2 legacy feeds from pathology systems are exhibiting 18% parsing failure rates against the central FHIR R4 converter. Acute ICU telemetry buffers drop packets under simulated surge load.",
            "governance": "Clinical Data Governance Board has convened an emergency technical working group to accelerate Annex B.1 clinical compliance artefacts and formalize hospital data custodian delegations."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.6 Hospital LAN",
                "title": "Hospital Optical Interconnect & Core Switch Upgrades",
                "action": "Authorize capital expenditure for redundant fiber runs into acute surgical and ICU wards."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Clinical Schedule Risk",
                "ref": "1.2b EHR Gateway",
                "title": "Pathology Legacy Feed Schema Translation",
                "action": "Deploy dedicated interface engineering squad to map non-standard HL7 v2 segments to FHIR R4 Observation profiles."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Delivery Win",
                "ref": "1.10b Cloud Fabric",
                "title": "Regional Cloud HSM & Key Vault Commissioned",
                "action": "Dedicated Cloud HSM cluster operational with CMEK encryption keys initialized for EHR patient tables."
            }
        ],
        "sleeperOutlier": {
            "ref": "1.14 PACS",
            "title": "Diagnostic PACS Imaging Cloud Ingestion Throughput",
            "warning": "Spike in radiological CT/MRI volumetric scans may exceed regional internet bandwidth if dedicated interconnect is delayed."
        },
        "plans": [
            {
                "num": 1,
                "status": "RED",
                "ref": "1.6 Hospital LAN",
                "title": "Hospital Core Network Modernization",
                "plan": "Complete redundant optical fiber cabling and VLAN testing across 4 metropolitan hospital sites.",
                "owner": "Network Engineering Lead",
                "target": "Jul 2026"
            },
            {
                "num": 2,
                "status": "RED",
                "ref": "1.2b EHR Gateway",
                "title": "FHIR Gateway Transformation Engine",
                "plan": "Patch translation engine to support non-standard pathology lab test code mappings.",
                "owner": "Integration Lead",
                "target": "Jul 2026"
            }
        ]
    },
    {
        "weekNumber": 22,
        "weekLabel": "Week 22",
        "week": "Week 22",
        "date": "03 Jul 2026",
        "overallStatus": "🟡 AMBER (Mitigating)",
        "kpis": {
            "clinicalGoLive": "🟡 14-DAY DRIFT",
            "fhirInteroperability": "🟡 72% PASS",
            "hipaaCompliance": "🟢 PASSING",
            "escalations": "🔴 5 ITEMS"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 16.4,
            "residual_avg_score": 11.8,
            "delta_compression": "-4.6",
            "eventuated_issues_count": 3,
            "total_issues": 11,
            "report_week": "Week 22",
            "report_date": "03 Jul 2026"
        },
        "synthesis": {
            "executive": "Week 22 marks an improving trajectory with acute escalations reduced from 7 to 5. The primary delivery focus has transitioned to locking down interface agreements with medical imaging and laboratory providers.",
            "technical": "Hospital LAN optical fiber terminations completed at the primary facility. Initial FHIR R4 transformation error rate dropped below 8% following deployment of the custom vocabulary translator.",
            "governance": "Clinical Informatics liaison team initiated clinician workflow dry-runs in simulated outpatient clinics, receiving favorable ergonomic and usability feedback."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.2b EHR Gateway",
                "title": "Laboratory Information System (LIS) Interface Contract",
                "action": "Sign off interoperability SLA and data sharing memorandum of understanding with regional pathology provider."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Clinical Schedule Alignment",
                "ref": "1.10b Test/Dev",
                "title": "Clinical Workstation Image Deployment",
                "action": "Roll out standardized dual-screen clinical workstation images with integrated biometric reader support."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Delivery Win",
                "ref": "1.6 Hospital LAN",
                "title": "Hospital Core Network Cutover Complete (Site A)",
                "action": "Surgical and ICU wards successfully migrated to 10Gbps redundant fiber with zero clinical outage."
            }
        ],
        "sleeperOutlier": {
            "ref": "1.14 PACS",
            "title": "High-Resolution DICOM Cache Eviction Policy",
            "warning": "Unoptimized local cache retention on local ward gateways could lead to disk exhaustion during peak diagnostic hours."
        },
        "plans": [
            {
                "num": 1,
                "status": "AMBER",
                "ref": "1.2b EHR Gateway",
                "title": "Laboratory Information System Integration",
                "plan": "Complete end-to-end integration testing for automated blood panel result routing into EHR.",
                "owner": "Integration Lead",
                "target": "Jul 2026"
            }
        ]
    },
    {
        "weekNumber": 23,
        "weekLabel": "Week 23",
        "week": "Week 23",
        "date": "10 Jul 2026",
        "overallStatus": "🟡 AMBER (Mitigating)",
        "kpis": {
            "clinicalGoLive": "🟡 10-DAY DRIFT",
            "fhirInteroperability": "🟡 80% PASS",
            "hipaaCompliance": "🟢 PASSING",
            "escalations": "🔴 4 ITEMS"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 15.9,
            "residual_avg_score": 10.2,
            "delta_compression": "-5.7",
            "eventuated_issues_count": 2,
            "total_issues": 11,
            "report_week": "Week 23",
            "report_date": "10 Jul 2026"
        },
        "synthesis": {
            "executive": "Week 23 demonstrates steady risk compression with net residual exposure falling to 10.2. Medical board leadership confirmed schedule baseline alignment for the September hospital go-live.",
            "technical": "PACS cloud storage gateway deployed to pilot ward. Large 500MB volumetric MRI studies now upload in under 4.2 seconds, well within clinical operational targets.",
            "governance": "Health record privacy audit confirmed zero unencrypted PHI columns across all Postgres databases and Cloud Storage buckets."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.14 PACS",
                "title": "Diagnostic Radiology Bandwidth Reservation",
                "action": "Approve QoS priority tags for DICOM transmission across hospital wide-area network."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Clinical Schedule Alignment",
                "ref": "C.2 Workforce",
                "title": "Clinical Informatics Super-User Training",
                "action": "Schedule 40 hours of protected training time for 30 nurse unit managers ahead of system dry-run."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Delivery Win",
                "ref": "B.1 Security",
                "title": "Continuous HIPAA/Privacy Audit Prober Deployed",
                "action": "Automated security prober scans 100% of cloud resources every 6 hours, streaming compliance logs to BigQuery."
            }
        ],
        "sleeperOutlier": {
            "ref": "1.14 Interop",
            "title": "Emergency Department Triage Hand-off Protocol",
            "warning": "Paper-to-digital transition during ambulance arrivals requires streamlined barcode scanning to avoid triage bottlenecks."
        },
        "plans": [
            {
                "num": 1,
                "status": "AMBER",
                "ref": "C.2 Workforce",
                "title": "Nurse Informatics Super-User Program",
                "plan": "Complete train-the-trainer modules across emergency and intensive care departments.",
                "owner": "Clinical Workforce Lead",
                "target": "Aug 2026"
            }
        ]
    },
    {
        "weekNumber": 24,
        "weekLabel": "Week 24",
        "week": "Week 24",
        "date": "17 Jul 2026",
        "overallStatus": "🟡 AMBER (Stable)",
        "kpis": {
            "clinicalGoLive": "🟡 7-DAY DRIFT",
            "fhirInteroperability": "🟢 88% PASS",
            "hipaaCompliance": "🟢 PASSING",
            "escalations": "🟡 3 ITEMS"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 15.6,
            "residual_avg_score": 8.9,
            "delta_compression": "-6.7",
            "eventuated_issues_count": 2,
            "total_issues": 11,
            "report_week": "Week 24",
            "report_date": "17 Jul 2026"
        },
        "synthesis": {
            "executive": "Delivery velocity accelerated in Week 24 as FHIR R4 interoperability reached 88% automated test pass rates. Hospital administration authorized the dry-run simulation date for early August.",
            "technical": "SMART-on-FHIR clinical single sign-on (SSO) with biometric badge tap completed integration testing, achieving median authentication latencies of 1.1 seconds.",
            "governance": "Joint Clinical Steering Committee reviewed Annex D.1 SLA terms with regional hospital network, resolving all outstanding liability and data custodianship clauses."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.13 IBR",
                "title": "Integrated Clinical Rollout Schedule (ICRS) Baseline Sign-Off",
                "action": "Formally baselines the 4-phase hospital cutover schedule for August-October 2026."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Clinical Schedule Alignment",
                "ref": "1.2b EHR Gateway",
                "title": "Outpatient Pharmacy Script Integration Verification",
                "action": "Complete electronic prescribing and digital script routing tests with central pharmacy systems."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Delivery Win",
                "ref": "1.2b EHR Gateway",
                "title": "SMART-on-FHIR Biometric Badge Tap Verified",
                "action": "Demonstrated seamless 1.1s clinician sign-on across mobile tablets and bedside workstations."
            }
        ],
        "sleeperOutlier": {
            "ref": "1.10b Storage",
            "title": "Bedside Telemetry Historical Database Retention",
            "warning": "High-frequency vital sign time-series require partitioning strategy to avoid query slowdowns in historical charts."
        },
        "plans": [
            {
                "num": 1,
                "status": "AMBER",
                "ref": "1.13 IBR",
                "title": "Milestone Gate 1 Final Acceptance",
                "plan": "Complete joint review of 42 deliverable artifacts with hospital clinical board.",
                "owner": "Program Director",
                "target": "Aug 2026"
            }
        ]
    },
    {
        "weekNumber": 25,
        "weekLabel": "Week 25",
        "week": "Week 25",
        "date": "24 Jul 2026",
        "overallStatus": "🟡 AMBER (Stable)",
        "kpis": {
            "clinicalGoLive": "🟢 ON TRACK",
            "fhirInteroperability": "🟢 91% PASS",
            "hipaaCompliance": "🟢 PASSING",
            "escalations": "🟡 2 ITEMS"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 15.2,
            "residual_avg_score": 7.6,
            "delta_compression": "-7.6",
            "eventuated_issues_count": 1,
            "total_issues": 11,
            "report_week": "Week 25",
            "report_date": "24 Jul 2026"
        },
        "synthesis": {
            "executive": "Week 25 marks the transition of clinical go-live milestones back onto schedule. High-consequence clinical risks have been reduced to 2 active items, with strong mitigations locked in place.",
            "technical": "High-throughput bedside telemetry ingestion tested successfully under 200% simulated patient load. Time-series partitioning eliminated query lag on historical ECG and oxygen saturation charts.",
            "governance": "Chief Medical Officer completed formal walkthrough of emergency department clinical workflow, issuing formal endorsement for dry-run trials."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.13 IBR",
                "title": "Hospital Dry-Run Simulation Protocol Approval",
                "action": "Authorize 24-hour parallel hospital run in acute care ward scheduled for 10 August."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Clinical Schedule Alignment",
                "ref": "1.7a DevSecOps",
                "title": "Emergency Rollback Automation Scripting",
                "action": "Complete automated 1-click fallback to secondary hospital data center in the event of primary link loss."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Delivery Win",
                "ref": "1.10b Storage",
                "title": "High-Volume Bedside Telemetry Benchmark Passed",
                "action": "Processed 2.4 million telemetry events per minute with P99 database write latency < 45ms."
            }
        ],
        "sleeperOutlier": {
            "ref": "C.2 Workforce",
            "title": "Night Shift Clinical Informaticist Coverage",
            "warning": "Ensure adequate on-site super-user staffing during overnight hours of initial go-live weekend."
        },
        "plans": [
            {
                "num": 1,
                "status": "AMBER",
                "ref": "1.13 IBR",
                "title": "Hospital Dry-Run Readiness Verification",
                "plan": "Run simulation pre-checks across all acute care ward endpoints.",
                "owner": "Clinical Operations Lead",
                "target": "Aug 2026"
            }
        ]
    },
    {
        "weekNumber": 26,
        "weekLabel": "Week 26",
        "week": "Week 26",
        "date": "31 Jul 2026",
        "overallStatus": "🟡 AMBER (Approaching Green)",
        "kpis": {
            "clinicalGoLive": "🟢 ON TRACK",
            "fhirInteroperability": "🟢 94% PASS",
            "hipaaCompliance": "🟢 PASSING",
            "escalations": "🟢 1 ITEM"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 15.0,
            "residual_avg_score": 6.8,
            "delta_compression": "-8.2",
            "eventuated_issues_count": 1,
            "total_issues": 11,
            "report_week": "Week 26",
            "report_date": "31 Jul 2026"
        },
        "synthesis": {
            "executive": "Week 26 closes out July with significant momentum. Residual risk compression reached -8.2, and only a single operational escalation remains open regarding overnight technical support rotas.",
            "technical": "PACS radiological image retrieval latency benchmarked at 280ms P90 across regional WAN, exceeding the contractual Annex D.1 SLA requirement of 450ms.",
            "governance": "Final draft of the Clinical Data Protection and HIPAA compliance dossier (Annex B.1) submitted to independent healthcare assessors for formal accreditation."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.13 IBR",
                "title": "Sign-Off on Gate 2 Milestone Deliverables",
                "action": "Executive authorization of milestone payment gate following completion of technical verification trials."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Clinical Schedule Alignment",
                "ref": "C.2 Workforce",
                "title": "24/7 Clinical Support Command Center Rota",
                "action": "Finalize 3-shift roster for 24/7 technical and clinical support desk for go-live week."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Delivery Win",
                "ref": "1.14 PACS",
                "title": "Radiological DICOM Latency Beats SLA Target",
                "action": "Median retrieval latency achieved 280ms, delivering instant scan availability to trauma surgeons."
            }
        ],
        "sleeperOutlier": {
            "ref": "1.2b EHR Gateway",
            "title": "External Specialist Clinic Referral Ingestion",
            "warning": "Validate that non-hospital specialist clinics using legacy desktop software can successfully transmit referrals."
        },
        "plans": [
            {
                "num": 1,
                "status": "GREEN",
                "ref": "1.13 IBR",
                "title": "Milestone Gate 2 Deliverables Sign-off",
                "plan": "Present formal verification evidence to Health Transformation Board.",
                "owner": "Delivery Lead",
                "target": "Aug 2026"
            }
        ]
    },
    {
        "weekNumber": 27,
        "weekLabel": "Week 27",
        "week": "Week 27",
        "date": "07 Aug 2026",
        "overallStatus": "🟡 AMBER (Stable)",
        "kpis": {
            "clinicalGoLive": "🟢 ON TRACK",
            "fhirInteroperability": "🟢 95% PASS",
            "hipaaCompliance": "🟢 PASSING",
            "escalations": "🟢 1 ITEM"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 14.8,
            "residual_avg_score": 5.8,
            "delta_compression": "-9.0",
            "eventuated_issues_count": 1,
            "total_issues": 11,
            "report_week": "Week 27",
            "report_date": "07 Aug 2026"
        },
        "synthesis": {
            "executive": "Delivery velocity remains active for Week 27 ending 07 Aug 2026. Risk portfolio tracks 28 active items with residual exposure compressing from 14.8 to 5.8 (delta -9.0). Management focus remains locked on contractual clinical milestones.",
            "technical": "Engineering baseline across hospital cloud infrastructure and network interconnects is stable. Critical path activities for clinical dry-run and FHIR interoperability gates are progressing with 1 eventuated issue under active mitigation.",
            "governance": "Joint Clinical Governance Board controls are validated. HIPAA and digital health privacy accreditation artifacts remain aligned to target baseline dates with no commercial blockers."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.13 IBR",
                "title": "Contractual Milestone Gate 2 Alignment",
                "action": "Authorize integrated clinical schedule baseline and close residual action items."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Critical Schedule Alignment",
                "ref": "1.10b Test/Dev",
                "title": "Hospital Cluster Hardware Interconnect Latency",
                "action": "Complete redundant optical interconnect verification and dark fiber testing."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Primary Delivery Win",
                "ref": "1.7a DevSecOps",
                "title": "CI/CD Pipeline Clinical Security Baseline Accreditation",
                "action": "Automated deployment pipelines and zero-trust IAP gates fully accredited."
            }
        ],
        "sleeperOutlier": {
            "ref": "1.14 SRR",
            "title": "System Requirements Review Verification Window",
            "warning": "Inter-team clinical validation handoffs may compress review window if pre-work packages are delayed."
        },
        "plans": [
            {
                "num": 1,
                "status": "GREEN",
                "ref": "1.13 IBR",
                "title": "Milestone 2 Deliverables Acceptance",
                "plan": "Complete sign-off with Hospital Board executive.",
                "owner": "Delivery Lead",
                "target": "Aug 2026"
            }
        ]
    },
    {
        "weekNumber": 28,
        "weekLabel": "Week 28",
        "week": "Week 28",
        "date": "14 Aug 2026",
        "overallStatus": "🟢 ON TRACK",
        "isLatest": True,
        "isCurrent": True,
        "kpis": {
            "clinicalGoLive": "🟢 ON TRACK",
            "fhirInteroperability": "🟢 98% PASS",
            "hipaaCompliance": "🟢 ACCREDITED",
            "escalations": "🟢 0 ITEMS"
        },
        "metrics": {
            "total_risks": 28,
            "inherent_avg_score": 14.6,
            "residual_avg_score": 4.8,
            "delta_compression": "-9.8",
            "eventuated_issues_count": 0,
            "total_issues": 11,
            "report_week": "Week 28",
            "report_date": "14 Aug 2026",
            "project_name": "sample",
            "baseline_week": "Week 28",
            "baseline_date": "14 Aug 2026"
        },
        "synthesis": {
            "executive": "Delivery velocity is fully green for Week 28 ending 14 Aug 2026. Residual risk compressed to a low 4.8 across all 28 items, with zero active escalations blocking deployment. Acute care ward dry-run passed with 100% telemetry fidelity.",
            "technical": "All FHIR R4 clinical APIs, SMART-on-FHIR single sign-on, and PACS imaging pipelines have passed pre-flight accreditation. Automated end-to-end failover tests completed with sub-second recovery.",
            "governance": "Health Transformation Board granted unconditional approval for Phase 1 acute go-live. Independent HIPAA and Australian Privacy Act accreditation certificates formally issued."
        },
        "top3": [
            {
                "num": 1,
                "type": "decision",
                "tag": "🚨 Immediate Executive Action",
                "ref": "1.13 IBR",
                "title": "Hospital Phase 1 Cutover Authorization",
                "action": "Sign off formal executive go-ahead for scheduled weekend cutover."
            },
            {
                "num": 2,
                "type": "schedule",
                "tag": "⚡ Critical Schedule Alignment",
                "ref": "C.2 Workforce",
                "title": "Go-Live Weekend Command Center Activation",
                "action": "Mobilize 24/7 technical and clinical support pods across participating hospitals."
            },
            {
                "num": 3,
                "type": "win",
                "tag": "🚀 Primary Delivery Win",
                "ref": "B.1 Security",
                "title": "Full Healthcare Cloud Accreditation Granted",
                "action": "Independent clinical cybersecurity audit achieved 100% compliance score."
            }
        ],
        "sleeperOutlier": {
            "ref": "1.14 Interop",
            "title": "Post-Cutover Historical Patient Record Ingestion",
            "warning": "Monitor secondary background batch jobs to prevent interference with live real-time clinical telemetry."
        },
        "plans": []
    }
]


def update_snapshots_json():
    current_data = json.loads(SNAPS_FILE.read_text(encoding="utf-8")) if SNAPS_FILE.exists() else {}
    snaps_dict = {}

    for w in WEEKS_DATA:
        key = f"w{w['weekNumber']}"
        snaps_dict[key] = {
            "weekNumber": w["weekNumber"],
            "weekLabel": w["weekLabel"],
            "week": w["week"],
            "date": w["date"],
            "isLatest": w.get("isLatest", False),
            "isCurrent": w.get("isCurrent", False),
            "driveFileId": f"sample-drive-doc-aurora-{key}",
            "driveFileName": f"Weekly Reporting - {w['weekLabel']} - {w['date']}.pdf",
            "overallStatus": w["overallStatus"],
            "kpis": w["kpis"],
            "metrics": w["metrics"],
            "synthesis": w["synthesis"],
            "top3": w["top3"],
            "sleeperOutlier": w["sleeperOutlier"],
            "plans": w.get("plans", []),
            "generatedBy": "gemini-3.5-flash",
            "hasAudio": (w["weekNumber"] == 28)
        }
        if w["weekNumber"] == 28:
            snaps_dict[key]["audioFile"] = "data/sample/podcast_w28.mp3"
            snaps_dict[key]["audioDurationSeconds"] = 131.4

    # Maintain dual lookup format (both 'w28' and 'Week 28') for backward compatibility
    dual_dict = dict(snaps_dict)
    for w in WEEKS_DATA:
        key = f"w{w['weekNumber']}"
        label = w["weekLabel"]
        dual_dict[label] = snaps_dict[key]

    output_payload = {
        "lastSynced": "2026-08-14T10:00:00.000000+00:00",
        "driveFolderId": "1Se0tVV2TRYIagQYbkD4M4q2G6F1MHBg-",
        "snapshots": snaps_dict
    }
    # Append named keys
    for label, val in snaps_dict.items():
        wk_label = val.get("weekLabel")
        if wk_label:
            output_payload[wk_label] = val

    SNAPS_FILE.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
    print(f"Updated {SNAPS_FILE} with 8 weeks of progressive healthcare snapshots (W21-W28).")


if __name__ == "__main__":
    update_snapshots_json()
