# 📊 Project Dash — Project Manager & Governance User Guide

This guide explains how to navigate, interpret, and run weekly governance cycles using the **Project Monaro Risk & Delivery Dashboard** (`?project=monaro`) and the public showcase dataset (`?project=sample`).

---

## 1. Top Navigation Header & Quick Actions

The sticky top header bar provides global context and 1-click access to authoritative source documents across every tab:

| Control | Location | What It Does |
| :--- | :--- | :--- |
| **Project Title & Logo (`🛡️`)** | Top Left | Displays the active portfolio name and governance board. Clicking the logo or title returns immediately to **Tab 1 (`Executive Summary v2`)**. |
| **`Live (<Week>)` & `🔒 Google Need to Know (NTK)`** | Top Left Badges | Indicates the active reporting cycle loaded in the dashboard and the confidentiality classification of the register. |
| **`⏱️ Time Machine`** | Top Right | Opens the **Program Governance Time Machine** modal, allowing you to rewind the entire dashboard (KPIs, synthesis, gap close plans, and podcasts) to any historical reporting snapshot in `snapshots.json`. When rewound, a pulsing amber banner appears at the top of the screen with a **`⚡ Return to Present`** button. |
| **`Open Sheet ▾`** | Top Right | Dropdown menu with direct 1-click links to the live Google Sheets:<br>• **`📊 Joint Program Register`** (Stream 1 — Internal/Joint Risks & Issues)<br>• **`🛡️ Team Google Register`** (Stream 2 — Google Engineering & Delivery Tasks) |
| **`<Week> Pack ↗`** | Top Right | Opens the raw Weekly Status Report PDF for the active reporting week directly in Google Drive. |
| **`Data`** | Top Right | Opens the **Data Provenance Hub** (`Google Workspace & Pipeline Sources`), displaying verified connection status for all 4 data streams and the **`↻ Check for Updates`** button. |

---

## 2. Tab-by-Tab Dashboard Tour (Tabs 1–8)

### Tab 1: `Executive Summary v2` (Default Landing Cockpit)
Designed to synthesize weekly program posture into a 2-minute executive readout:
1. **Executive Cockpit & 4 KPI Pillars Strip**:
   - Displays the **Overall Program Posture** badge (`🟢 ON TRACK`, `🟡 AMBER`, or `🔴 RED`) alongside the 4 core governance pillars: **`Commercial`**, **`Milestone 2 (IBR)`**, **`ATO-C Gate`**, and **`Escalations`**.
2. **✨ Gemini Briefing (`Executive Decision Briefing & Critical Exceptions`)**:
   - **AI Narrative Paragraph**: Exception-first executive summary synthesized from active risks, issues, and contractual gates.
   - **🚨 Top 3 Critical Executive Attention Items**: Cards formatted as **Ask / Impact / Outcome** with target dates and 1-click deep-link chips (**`Ref 1.xx ↗`** jumps directly to the contractual gate in Tab 7; **`Gap #N ↗`** scrolls to the remediation plan below; **`Report Pack ↗`** opens the source PDF).
   - **🔍 Early Warning Sleeper Outlier**: Highlights emerging cross-bundle risks or schedule compression traps before they breach red thresholds.
   - **Action Buttons**:
     - **`📋 Copy Synthesis & Top 3`**: Copies the formatted executive summary and Top 3 items to your clipboard for pasting into weekly status emails or slides.
     - **`📊 Export Deck (PDF)`**: Opens the formatted print/PDF deck view for offline executive distribution.
3. **🎙️ NotebookLM Podcast Banner (`en-AU` Chirp 3 HD Audio Briefing)**:
   - Dual-host ~90-second dialogue (**Alex**, Program Delivery Analyst & **Jordan**, Technical Director) summarizing the week's critical movements.
   - Includes playback speed controls (**`1.0x`**, **`1.25x`**, **`1.5x`**), **`📜 Transcript`** (full interactive script modal with **`📋 Copy Script`**), and **`Download Audio`** (`.mp3`).
4. **Active Issue/Risk or Escalation Being Tracked with Gap Close Plan**:
   - Tracks formal remediation plans with owners, target dates, and status badges (`✅ Delivered This Cycle` vs. active escalations).
   - **`Show changes since:` Baseline Diff Selector**: Use the dropdown on the right (`Last Week`, `2 Weeks Ago`, `N Weeks Ago`) to dynamically highlight schedule shifts (`⚡ Shift`), newly added plans (`🆕`), and delivered items (`🚀 Delivered`) between the active cycle and any prior baseline week.
5. **🔴 Top 5 Critical Risks & ⚠️ Top 5 Escalated Issues**:
   - Side-by-side ranked lists of the highest-exposure open risks and issues. Clicking any item opens the full **Item Detail Modal**.
6. **📅 Coming Up: Near-Term Deliverables & Schedule Squeeze Warnings (`Zero Float Alerts`)**:
   - Highlights upcoming contractual gates where upstream slippage has compressed downstream buffer (negative or tight float) against fixed milestone dates.

---

### Tab 2: `Internal Risks` (5×5 Heatmap & Live Risk Explorer)
The primary workspace for triaging the Joint Program / Internal Risk Register:
1. **5×5 Risk Heatmap Matrix**:
   - **Status Filter Toggle**: Filter matrix counts by **`Open`** (Active + Eventuated), **`Active`**, **`Eventuated`**, **`Closed`**, or **`All`**.
   - **Rating Mode Toggle**: Switch between **`Inherent`** (pre-control gross risk) and **`Residual`** (post-control net exposure) to visualize mitigation efficacy.
   - **3 Clickable KPI Filter Boxes**: Click **`🔴 CRITICAL EXPOSURE RISKS`** (Score 18–25), **`⚠️ EVENTUATED ISSUES`**, or **`🟡 UNACTIONED RISKS`** (missing treatment plans) to filter the explorer below.
   - **Cell Focus Filtering**: Click any cell in the 5×5 grid (e.g. `Likelihood 4 × Consequence 5 = Score 20`) to lock a focus ring and filter the Risk Explorer strictly to items in that cell. Click **`✕ Clear Matrix Filter`** to reset.
2. **🔎 Live Risk Explorer & Triage**:
   - **View Mode Toggle**: Switch between **`📇 Cards View`** (detailed 2-column triage cards) and **`📑 Compact Table`** (dense tabular layout).
   - **Search Bar**: Real-time search across Risk ID, statement, owner, root cause, treatment plan, and Driver Tree Ref (`1.10b`, `1.14`, etc.).
   - **Quick Preset Chips**: 1-click filters for `📋 All Risks`, `🔴 Score ≥ 18`, `📈 Trending Worse`, `⚠️ Eventuated Issues`, and `🏛️ Joint Exec Escalations`—plus **`↺ Reset All Filters`**.
   - **4 Faceted Dropdowns**: Filter simultaneously by **`Bundle / Workstream`** (`Bundle G`, `Bundle A.AO`, `Bundle F`, `Bundle I`, `Bundle L`, `Bundle A.PI`), **`Cause Category`**, **`Governance Level`** (`Internal Google`, `Team Google`, `PSG`, `IPF`), and **`Status`**.

---

### Tab 3: `⚠️ Issue Register`
- Dedicated full-viewport register of eventuated risks and operational blockers.
- Use the top search bar to filter by Issue ID, owner, driver ref, or description, and click any row to inspect its **Governance Action Plan** in the Item Detail Modal.

---

### Tab 4: `🛡️ Team Google Risks`
- Isolates internal Google engineering, platform, and supply-chain delivery tasks (`TG-*`) from the Joint Program Register so technical workstream tracking does not pollute client-facing joint numbers.
- Includes its own dedicated **5×5 Heatmap Matrix** (`Inherent (Gross)` vs. `Residual (Net)`), 3 summary KPI cards (`Critical Google Exposure`, `Active Delivery Tasks`, `Resolved / Closed`), **`Open Google Sheet ↗`** shortcut, and searchable explorer.

---

### Tab 5: `📈 Performance Trends`
- **Granularity Switcher**: Toggle longitudinal charts across **`Monthly`**, **`Bi-Weekly`**, and **`Weekly`** horizons.
- **4 Analytical Panels**:
  1. **Risk Volume & Intake vs. Closures (Backlog)**: Tracks active backlog against newly opened (`+`) and closed tickets per period. Clicking any data point opens the **Week Performance Drill-Down Modal** (with a 1-click **`⏱️ Travel to Week`** button).
  2. **Risk Mitigation Score Performance (Burndown)**: Compares average Inherent Score vs. Residual Score over time to prove control effectiveness.
  3. **Risk Cause Category Concentration**: Horizontal breakdown of risk volume by root cause (`Schedule`, `Governance Assurance`, `Cost`, `Scope`, etc.). Clicking a bar filters the Risk Explorer to that category.
  4. **Risk Severity Profile (`5x5 Score Bands`)**: Interactive distribution across `Very High (23–25)`, `High (18–22)`, `Medium (13–17)`, `Low (7–12)`, and `Very Low (1–6)`. Clicking any band drills directly into those items in Tab 2.

---

### Tab 6: `📚 Blueprint Knowledge` (NotebookLM Grounded)
- Provides bidirectional traceability between contractual solution blueprints (**Bundles A through L**) and active governance risks/issues.
- **Notebook Selector Dropdown**: Switch between registered Gemini / NotebookLM notebooks, click **`Open in NotebookLM ↗`** to query original contract annexes, or click any Bundle card to filter Tab 2 (`Internal Risks`) to risks impacting that contract bundle.

---

### Tab 7: `🌳 CD1 Driver Tree`
- Maps **Tier 0 Strategic Objectives** and **Tier 1 Capability Drops (`CD1` & `CD1.5`)** down to individual contractual deliverables and review gates.
- **Level Filter Toggle**: Switch between **`All Items`**, **`Level 2 (Primary Gates)`**, and **`Level 3 (Work Packages)`**.
- Each deliverable card displays RAG status, completion progress bar, owner, schedule shift badges, linked Gap Close Plan chip, and 1-click counters to filter associated **Risks** or **Issues**.

---

### Tab 8: `📋 Whole Register Ledger` & CSV Export (PM Power View)
To keep the executive interface clean, **Tab 8 is hidden by default** and unlocked via URL parameter for Project Managers and Governance Officers:
- **How to Unlock**: Append **`?view=pm`** or **`&ledger=true`** to the dashboard URL:
  - Example: `https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=monaro&view=pm`
- **Capabilities**:
  - Displays the combined **Whole Register Ledger** (all Internal Risks + Team Google Risks in a single unified table).
  - **`📥 Export CSV`**: Downloads the complete register cut as a `.csv` file for spreadsheet analysis or formal Commonwealth reporting packs.
  - **`📄 Export Deck (PDF)`**: Generates a printable governance deck.

---

## 3. How the Weekly Reporting & Data Sync Cycle Works

The dashboard separates **authoritative data editing** (in Google Sheets and Google Drive) from **web viewing** (in the browser):

1. **Updating Risks & Issues (Daily / Continuous)**:
   - Click **`Open Sheet ▾`** in the top header to edit the **Joint Program Register** or **Team Google Register** directly in Google Sheets.
2. **Publishing a New Weekly Status Report PDF (Weekly)**:
   - Upload the weekly PDF pack (e.g. `Weekly Reporting - Week XX - DD MMM YYYY.pdf`) into the shared **Weekly Status Reports Archive** Google Drive folder (accessible via **`Data` $\rightarrow$ `Open Folder ↗`**).
3. **When Does the Dashboard Ingest New Data?**:
   - **Scheduled Automatic Sync**: Every **Friday at 5:00 PM Sydney time (AEST/AEDT)**, Google Cloud Scheduler triggers the background ingestion job (`monaro-risk-sync-job`). The job scans the Google Sheets and Drive folder, uses **Gemini 3.5 Flash** to synthesize the new Executive Summary and Top 3 cards, generates the **Chirp 3 HD** audio podcast, and publishes the updated `snapshots.json` to Cloud Storage.
   - **Out-of-Cycle / Mid-Week Updates**: Because the web application mounts Cloud Storage as read-only for security, uploading a PDF to Drive mid-week does not immediately trigger ingestion on its own. To publish an update before Friday 5:00 PM, ask an Administrator to run the 1-click **`monaro-risk-sync-job`** in Cloud Run Jobs (see [`docs/ADMIN_DEV_GUIDE.md`](./ADMIN_DEV_GUIDE.md)).
4. **Refreshing Your Browser Session (`Data` $\rightarrow$ `↻ Check for Updates`)**:
   - Once the background sync job finishes, click **`Data`** in the top-right header and click **`↻ Check for Updates`**. The browser fetches the latest `snapshots.json` without caching and refreshes all charts, matrices, and briefings in place.

---

## 4. Executive RAG & ISO 31000 5×5 Scoring Reference

### 1. 5×5 Risk Score Math
Every risk is scored across **Likelihood ($1\text{ to }5$)** and **Consequence ($1\text{ to }5$)** for both Inherent (pre-control) and Residual (post-control) ratings:
$$\text{Risk Score} = \text{Likelihood} \times \text{Consequence} \in [1, 25]$$

| Band | Score Range | Operational Meaning & Governance Action |
| :--- | :---: | :--- |
| **Low** | **1 – 4** | Routine workstream management and standard operational controls. |
| **Medium** | **5 – 9** | Tracked in workstream syncs with assigned owner and target date. |
| **High** | **10 – 14** | Active treatment plan required; reviewed by Delivery Leads. |
| **Extreme / Critical** | **15 – 25** | Scores $\ge 15$ trigger **🟡 AMBER** executive visibility; scores $\ge 18$ (or $\ge 20$ on Commercial/Security pillars) trigger **🔴 RED** Steering Committee escalation and Gap Close Plans. |

### 2. Overall Program Posture & 4 KPI Pillar Rules
Default thresholds follow the Commonwealth Defence / ISO 31000 standard (customizable per project in `config.json` under `governance.ragThresholds`):

| Pillar / Badge | 🟢 GREEN | 🟡 AMBER | 🔴 RED |
| :--- | :--- | :--- | :--- |
| **Overall Program (`#execOverallBadge`)** | $0$ eventuated issues, all gates baselined, and portfolio residual avg $< 12.0$. | $1\text{–}2$ eventuated issues under containment, gate review in progress, or residual avg $12.0\text{–}17.9$. | $\ge 3$ eventuated issues, critical-path milestone blocked, residual avg $\ge 18.0$, or any KPI pillar is 🔴 RED. |
| **1. Commercial (`#kpiCommercial`)** | Fixed-price deliverables & payments aligned to baseline (`ON TRACK`). | Active commercial variance or mitigation plan ($\text{residual score} \ge 15$). | Unresolved commercial dispute, payment stopped, or claim ($\text{residual score} \ge 20$). |
| **2. Milestone 2 / IBR (`#kpiIbr`)** | Review gate accepted and baselined (`BASELINED 100%`). | Gate review in progress with active gap close plans (`IN PROGRESS / DUE <DATE>`). | Critical path slipped past contractual gate date; sign-off blocked. |
| **3. ATO-C Gate (`#kpiAto`)** | Enclaves accredited and assessors validated (`GREEN / ACCREDITED`). | Security assessment or POAM remediation active ($\text{residual score} \ge 15$). | Accreditation blocked or critical enclave vulnerability ($\text{residual score} \ge 20$). |
| **4. Escalations (`#kpiEscalations`)** | `0 ITEMS` eventuated. | `1–2 ITEMS` active under treatment. | `≥ 3 ITEMS` eventuated or P0 blocker requiring board intervention. |
