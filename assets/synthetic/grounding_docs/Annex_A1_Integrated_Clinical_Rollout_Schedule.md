# Annex A.1: Integrated Clinical Rollout Schedule (ICRS) & Hospital Go-Live Matrix

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
