# Implementation Plan: Project Aurora Synthetic Assets & Healthcare Modernization Pivot

## Overview
Establish a complete, realistic, and domain-distinct suite of synthetic external assets (Google Sheets, Google Drive weekly packs, and NotebookLM grounding sources) for **Project Aurora**. 
To ensure zero leakage or cross-contamination with the Monaro sovereign defence project, Aurora is pivoted to a **Healthcare Digital Health & Clinical Cloud Transformation** domain (e.g., "Aurora Health Cloud Modernization").

---

## Phase 1: Backlog Consolidation & Confidentiality Guardrail Audit
- [x] **Task 1.1: Backlog Reconciliation & Consolidation**
  - [x] Inspect existing related backlog items (#16 Interactive Google Sheet & Drive Folder switcher, #80 Confidentiality Isolation) and reconcile scope.
  - [x] Update backlog item metadata to link to this track.
- [x] **Task 1.2: Audit and expand existing anti-leakage test** (`tests/test_data_and_schemas.py`)
  - [x] Add explicit checks verifying that all sample links in `data/sample/config.json` use isolated synthetic URLs rather than Monaro sheet/folder IDs.
  - [x] Verify zero occurrences of Monaro entities, defence agencies, defence annexes (AGSVA, ISM, NV2/PV, CDS), or real personnel names across any sample files.
  - [x] Execute `uv run pytest tests/test_data_and_schemas.py -k test_sample_data_confidentiality_isolation` to confirm 100% pass on security baseline.
- [x] **Task 1.3: Phase 1 Verification & Checkpoint**

---

## Phase 2: Domain Pivot & Synthetic Blueprint Annex Definitions
- [x] **Task 2.1: Redefine Healthcare Modernization Blueprint Bundles & Annexes**
  - [x] Replace defence contract annexes with authentic **Healthcare Cloud Transformation** annexes:
    - *Annex A.1*: Integrated Clinical Rollout Schedule (ICRS) & Hospital Go-Live
    - *Annex B.1*: Clinical Data Protection, HIPAA / My Health Record Security Controls
    - *Annex C.2*: Clinical Informatics Workforce & FHIR Integration Team
    - *Annex D.1*: Healthcare Service Level Agreements (SLA) & Data Custodianship Ledger
  - [x] Update `BUNDLE_ANNEX_MAPPING` in `src/js/state.js` and `data/sample/knowledge.json` so bundle cards and detail modals reflect the healthcare domain.
- [x] **Task 2.2: Phase 2 Verification & Checkpoint**

---

## Phase 3: Synthetic Data Generation & LLM-as-Judge Realism Evaluation (Streams 1–4)
- [ ] **Task 3.1: Develop export & generation utility** (`scripts/export_synthetic_assets.py`)
  - [ ] **Stream 1 (Joint Program Register)**: Export CSV/TSV from `data/sample/risks.json` and `data/sample/issues.json` aligned to the healthcare domain (EHR migration, medical imaging PACS pipelines, FHIR APIs).
  - [ ] **Stream 2 (Team Cloud Register)**: Export CSV/TSV containing secondary cloud risks (`AUR-TG-*`).
  - [ ] **Stream 3 (Drive Governance Status Packs)**: Generate synthetic Weekly Status Report PDF packs (Week 27 & Week 28) aligned with healthcare clinical milestones.
  - [ ] **Stream 4 (NotebookLM Grounding Documents)**: Generate clean Markdown/PDF synthetic contract annexes for the Healthcare domain.
- [ ] **Task 3.2: LLM-as-Judge Realism Evaluation Harness**
  - [ ] Implement an evaluation script (`tests/eval/eval_aurora_realism.py`) using Gemini 3.5 Flash as an objective judge.
  - [ ] Evaluate generated synthetic datasets against rubric criteria:
    1. *In-flight realism*: Does it realistically depict a high-stakes clinical cloud transformation with authentic blockers and mitigations?
    2. *Contextual consistency*: Do the KPIs, synthesis, driver tree, and weekly status reports align coherently?
    3. *Zero leakage*: Strictly 100% score on absence of Monaro/defence terms.
- [ ] **Task 3.3: Phase 3 Verification & Checkpoint**

---

## Phase 4: External Provisioning / Link Insertion & Config Binding
- [ ] **Task 4.1: Create or link public-accessible synthetic Google Workspace assets**
  - [ ] Import Stream 1 & Stream 2 CSVs into clean Google Sheets (read-only shareable links).
  - [ ] Upload generated PDF packs into a public-accessible Google Drive demo folder.
  - [ ] Create/link a public NotebookLM notebook with the healthcare annexes.
- [ ] **Task 4.2: Update project configuration** (`data/sample/config.json`)
  - [ ] Set `project.links.primaryRegisterSheet` and `sources.googleSheets.sheetUrl`.
  - [ ] Set `project.links.teamGoogleSheet`.
  - [ ] Set `project.links.driveFolder` and `sources.googleDrive.folderId`.
  - [ ] Set `project.links.notebookLm`.
- [ ] **Task 4.3: Phase 4 Verification & Checkpoint**

---

## Phase 5: Frontend UX Verification & End-to-End Validation
- [ ] **Task 5.1: Verify header dropdown and navigation**
  - [ ] Verify `#headerJointSheetLink`, `#headerTeamGoogleSheetLink`, and `#driveReportLink` open Aurora healthcare assets.
  - [ ] Verify Data Modal (`#sheetsModal`) and Blueprint Grounding cards open synthetic links without broken redirects.
- [ ] **Task 5.2: Full regression test run**
  - [ ] Run `npm test` (all 21 Vitest tests pass).
  - [ ] Run `uv run pytest` (all 116+ tests pass).
- [ ] **Task 5.3: Headless browser verification**
  - [ ] Run `gbrowser eval` on `http://localhost:9000/?project=aurora` to confirm live links and healthcare branding (`🌌`, `PROJECT AURORA`).
- [ ] **Task 5.4: Phase 5 Verification & Checkpoint**
