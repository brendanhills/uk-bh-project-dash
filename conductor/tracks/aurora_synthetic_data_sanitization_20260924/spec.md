---
track_id: aurora_synthetic_data_sanitization_20260924
type: feature
focus: robustness
status: ACTIVE
bug_id: null
related_backlog_ids:
  - 16
  - 126
target_sdd_sections:
  - "Multi-Project Data Architecture & Configuration Model"
  - "Showcase Project Isolation & Public Demonstration Tier"
  - "Google Workspace & Grounded Sources Integration (Streams 1–4)"
---

# Specification: Project Aurora Synthetic Assets & Healthcare Modernization Pivot (Delta RFC)

## 1. Overview & Objectives
Establish a complete, realistic, and domain-distinct suite of synthetic external assets (Google Sheets, Google Drive weekly packs, and NotebookLM grounding sources) for **Project Aurora** (the public showcase dataset).
To guarantee zero leakage or cross-contamination with the Monaro sovereign defence project, Aurora is pivoted cleanly to a **Healthcare Digital Health & Clinical Cloud Transformation** domain (e.g. "Aurora Health Cloud Modernization").

## 2. Proposed Architectural Amendments
1. **Domain Pivot to Healthcare Cloud Modernization**:
   - Pivot Project Aurora entities, terminology, and operational risks from defence/national security to acute healthcare, electronic health record (EHR) migrations, clinical imaging PACS pipelines, FHIR APIs, and clinical staff onboarding.
   - Replace defence contract annexes with authentic **Healthcare Cloud Transformation** annexes:
     - **Annex A.1**: Integrated Clinical Rollout Schedule (ICRS) & Hospital Go-Live
     - **Annex B.1**: Clinical Data Protection & HIPAA / My Health Record Security Controls
     - **Annex C.2**: Clinical Informatics Workforce & FHIR Integration Team
     - **Annex D.1**: Healthcare Service Level Agreements (SLA) & Data Custodianship Ledger
   - Update `BUNDLE_ANNEX_MAPPING` in `src/js/state.js` and `data/sample/knowledge.json` so bundle cards, contract links, and detail modals reflect the healthcare domain.

2. **Sanitized Synthetic External Assets (Streams 1–4)**:
   - **Stream 1 (Joint Program Risk & Issue Register)**: Create a public read-only Google Sheet populated with Project Aurora's healthcare risks and issues.
   - **Stream 2 (Team Cloud Risk Register)**: Create a public read-only Google Sheet reflecting Aurora's secondary cloud risks (`AUR-TG-*`).
   - **Stream 3 (Google Drive Governance Folder)**: Create a public Google Drive folder containing realistic Weekly Status Report PDF packs (Week 27 & Week 28) aligned with healthcare clinical milestones.
   - **Stream 4 (NotebookLM Grounding Sources)**: Link a clean NotebookLM notebook containing Aurora's synthetic healthcare contract annexes and architecture documents.

3. **LLM-as-a-Judge Realism & Anti-Leakage Gate**:
   - Introduce an automated test harness (`tests/eval/eval_aurora_realism.py`) evaluated with Gemini 3.5 Flash grading:
     - *In-flight realism*: Does it realistically depict a high-stakes hospital clinical transformation with authentic blockers and mitigations?
     - *Zero leakage*: Strictly 100% score on absence of Monaro/defence terms.

4. **Configuration Grounding (`data/sample/config.json`)**:
   - Update `data/sample/config.json` with the real, accessible synthetic URLs for `primaryRegisterSheet`, `teamGoogleSheet`, `driveFolder`, and `notebookLm`.
   - Update `sources.googleSheets` and `sources.googleDrive` to reflect enabled state with verified synthetic folder/sheet IDs.

## 3. Data Contracts & Interface Changes
- **`data/sample/config.json`**:
  ```json
  {
    "project": {
      "slug": "sample",
      "name": "Project Aurora",
      "title": "Clinical Cloud Modernization & Healthcare Intelligence",
      "organization": "Aurora Health Transformation Board",
      "logoIcon": "🌌",
      "heroTag": "Clinical Informatics • FHIR Data Platform Modernization",
      "primaryRegisterName": "Joint Clinical Governance Register",
      "secondaryRegisterName": "Team Cloud Register",
      "links": {
        "primaryRegisterSheet": "https://docs.google.com/spreadsheets/d/<AURORA_SHEET_ID>/edit?usp=sharing",
        "teamGoogleSheet": "https://docs.google.com/spreadsheets/d/<AURORA_TG_SHEET_ID>/edit?usp=sharing",
        "driveFolder": "https://drive.google.com/drive/folders/<AURORA_DRIVE_FOLDER_ID>",
        "notebookLm": "https://notebooklm.google.com/notebook/<AURORA_NOTEBOOK_ID>"
      }
    }
  }
  ```

## 4. Acceptance Criteria & Invariants
- [ ] **Zero Confidentiality Leakage**: Automated test asserting zero occurrences of "Monaro", departmental customer names, or real team email addresses across all Aurora datasets.
- [ ] **Healthcare Domain Integrity**: Blueprint bundles, contract annexes, risks, and weekly status packs consistently reflect the healthcare transformation domain.
- [ ] **Working Links**: Clicking "Open Sheet ▾", "Joint Clinical Governance Register", "Team Cloud Register", "Weekly Pack", or "Open in NotebookLM" on Project Aurora navigates to valid, accessible synthetic documents.
- [ ] **LLM Evaluation Score**: Realism and in-flight quality judged >= 90% and zero-leakage 100% via Gemini 3.5 Flash evaluation.
- [ ] **100% Test Pass Rate**: Vitest and Pytest test suites pass without regression.

## 5. Out of Scope (Deferred to Future Tracks)
- **Live Ingestion Automation for Aurora**: Scheduled polling of the Aurora synthetic Drive folder is deferred to future ingestion tracks; Aurora remains read-only mock presentation.
- **Two-Way NotebookLM Syncing**: Live bidirectional document synchronization via private NotebookLM APIs is out of scope.
- **Selective Git Remote Filtering**: The git push isolation mechanism between `cloud-gtm` and `depot` is tracked in Feature Request #126.
