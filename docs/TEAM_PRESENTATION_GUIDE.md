# 🎤 Team Presentation & Demo Guide (5-Minute Walkthrough)

Use this script to showcase the **Project Monaro Risk & Delivery Dashboard** during steering committees, stakeholder reviews, or team onboarding. Every step matches the live controls in `index.html`.

---

## ⏱️ Pre-Flight Checklist (Before Sharing Screen)

1. Open the Production dashboard in Chrome (`https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=monaro`).
   * *Tip*: Append **`&view=pm`** to the URL if you plan to demonstrate **Tab 8 (`📋 Whole Register Ledger`)** and **`📥 Export CSV`** at the end of the call.
2. Click **`Data`** in the top-right header to open the **Data Provenance Hub** and verify the connection status for all 4 Google Workspace sources.
3. Ensure browser tab audio sharing is enabled if playing the **NotebookLM Podcast Banner**.

---

## 🎬 Act 1: Executive Cockpit, Gemini Briefing & Audio Podcast (90 Seconds)
**Location**: **Tab 1 — `Executive Summary v2`** (Default Landing Cockpit)

1. **The 10-Second Programme Pulse**:
   * Point to the **Overall Program Posture** badge (`🟢 ON TRACK` / `🟡 AMBER` / `🔴 RED`) and the **4 KPI Pillars Strip** (`Commercial`, `Milestone 2 (IBR)`, `ATO-C Gate`, `Escalations`).
   * *Talking Point*: *"Instead of paging through a 40-row spreadsheet or static slide deck, leadership gets an immediate, exception-first readout across our four core contractual gates."*
2. **✨ Gemini Briefing & Top 3 Executive Attention Items**:
   * Point to the **AI Narrative Paragraph**, the **🚨 Top 3 Critical Executive Attention Items** (`Ask / Impact / Outcome`), and the **🔍 Early Warning Sleeper Outlier**.
   * Click a **`Ref 1.xx ↗`** chip on one of the cards to show how it deep-links directly to the contractual deliverable gate, or click **`📋 Copy Synthesis & Top 3`**.
3. **🎙️ NotebookLM Podcast Banner (`en-AU` Chirp 3 HD Audio Briefing)**:
   * Click Play on the **NotebookLM Podcast Banner** to play 10–15 seconds of the dual-host dialogue (**Alex** & **Jordan**, synthesized via `Gemini 3.5 Flash` + `Chirp 3 HD`), then click **`📜 Transcript`**.
4. **Dynamic Period-over-Period Diffing (`Show changes since:`)**:
   * Scroll to **Active Issue/Risk or Escalation Being Tracked with Gap Close Plan** and change the **`Show changes since:`** dropdown (`Last Week`, `2 Weeks Ago`, `N Weeks Ago`).
   * Point out the **`⚡ Shift`**, **`🆕`**, and **`🚀 Delivered`** delta badges that dynamically highlight schedule movements against the chosen baseline week.

---

## 🎬 Act 2: Interactive ISO 31000 Governance & Cross-Filtering (90 Seconds)
**Locations**: **Tab 2 (`Internal Risks`)**, **Tab 3 (`⚠️ Issue Register`)**, and **Tab 4 (`🛡️ Team Google Risks`)**

1. **Click Tab 2 (`Internal Risks`)**:
   * Toggle between **`Inherent`** (gross risk) and **`Residual`** (post-control exposure) on the **5×5 Risk Heatmap Matrix**.
   * Click directly on a high-exposure cell in the 5×5 grid (e.g. `Likelihood 4 × Consequence 5 = Score 20`) or click **`🔴 CRITICAL EXPOSURE RISKS`** to filter the **Live Risk Explorer** below.
   * Toggle between **`📇 Cards View`** and **`📑 Compact Table`**, then click any risk card to open the **Item Detail Modal** (`Governance Action Plan`).
2. **Deep-Link to Authoritative Google Sheets (`Open Sheet ▾`)**:
   * Click **`Open Sheet ▾`** in the top header to show 1-click access to **`📊 Joint Program Register`** and **`🛡️ Team Google Register`**.
3. **Click Tab 3 (`⚠️ Issue Register`) & Tab 4 (`🛡️ Team Google Risks`)**:
   * Briefly show how **Tab 3** isolates realized operational blockers (`I-*`), while **Tab 4** provides a dedicated 5×5 heatmap and task register for internal Google engineering workstreams (`TG-*`) without polluting client-facing joint metrics.

---

## 🎬 Act 3: Trajectory, Blueprint Grounding & Driver Tree (60 Seconds)
**Locations**: **Tab 5 (`📈 Performance Trends`)**, **Tab 6 (`📚 Blueprint Knowledge`)**, and **Tab 7 (`🌳 CD1 Driver Tree`)**

1. **Click Tab 5 (`📈 Performance Trends`)**:
   * Toggle the granularity switcher (`Monthly` / `Bi-Weekly` / `Weekly`) across the **4 Analytical Panels** (Backlog Intake vs. Closures, Mitigation Score Burndown, Cause Category Concentration, and 5×5 Severity Bands).
2. **Click Tab 6 (`📚 Blueprint Knowledge`)**:
   * Show how **Bundles A through L** map contractual solution blueprints directly to active risks, with **`Open in NotebookLM ↗`** for querying source contract annexes.
3. **Click Tab 7 (`🌳 CD1 Driver Tree`)**:
   * Filter between **`All Items`**, **`Level 2 (Primary Gates)`**, and **`Level 3 (Work Packages)`** to show how strategic objectives (`CD1` & `CD1.5`) decompose into tracked deliverables with linked risk/issue counters.

---

## 🎬 Act 4: Data Provenance, Time Machine & PM Ledger (60 Seconds)
**Locations**: Top Header (`Data` & `⏱️ Time Machine`) + Optional **Tab 8 (`📋 Whole Register Ledger`)**

1. **Click `Data` (Top-Right Header)**:
   * Show the **Data Provenance Hub** (`Google Workspace & Pipeline Sources`) and the **`↻ Check for Updates`** button.
2. **Click `⏱️ Time Machine` (Top Header)**:
   * Select a historical reporting week to rewind the entire dashboard, point out the pulsing amber banner, and click **`⚡ Return to Present`**.
3. **Optional — Tab 8 (`📋 Whole Register Ledger` via `?view=pm`)**:
   * Click **Tab 8 (`📋 Whole Register Ledger`)** to show the unified cross-register ledger and **`📥 Export CSV`** for formal board packs.
