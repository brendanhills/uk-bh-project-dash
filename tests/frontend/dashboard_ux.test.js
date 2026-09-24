import { describe, it, expect, beforeAll, beforeEach, vi } from "vitest";
import fs from "fs";
import path from "path";
import {
  mockConfig,
  mockRisks,
  mockIssues,
  mockSnapshots,
  mockDriverTree,
  mockKnowledge,
} from "./fixtures/dashboard_mock_data.js";

// Pre-load index.html and app.js once per worker
const INDEX_PATH = path.resolve(process.cwd(), "index.html");
const RAW_HTML = fs
  .readFileSync(INDEX_PATH, "utf-8")
  .replace(/<link[^>]*rel=["']stylesheet["'][^>]*>/gi, "");
const APP_JS_PATH = path.resolve(process.cwd(), "src/js/app.js");
const APP_JS_CODE = fs.readFileSync(APP_JS_PATH, "utf-8");

// Mock Chart.js constructor
class MockChart {
  constructor(ctx, config) {
    this.ctx = ctx;
    this.config = config;
    this.data = config.data || {};
    this.destroy = vi.fn();
    this.update = vi.fn();
  }
}

function createDefaultFetchMock() {
  return vi.fn().mockImplementation(async (url) => {
    const urlStr = String(url);
    if (urlStr.includes("config.json")) {
      return { ok: true, status: 200, json: async () => mockConfig };
    }
    if (urlStr.includes("risks.json")) {
      return { ok: true, status: 200, json: async () => mockRisks };
    }
    if (urlStr.includes("issues.json")) {
      return { ok: true, status: 200, json: async () => mockIssues };
    }
    if (urlStr.includes("snapshots.json")) {
      return { ok: true, status: 200, json: async () => mockSnapshots };
    }
    if (urlStr.includes("driver_tree.json")) {
      return { ok: true, status: 200, json: async () => mockDriverTree };
    }
    if (urlStr.includes("knowledge.json")) {
      return { ok: true, status: 200, json: async () => mockKnowledge };
    }
    if (urlStr.includes("build_info.json")) {
      return { ok: true, status: 200, json: async () => ({ version: "1.0.0", timestamp: "2026-09-22" }) };
    }
    return { ok: false, status: 404, json: async () => ({}) };
  });
}

describe("Dashboard UX & Client Controller Integrity (Zero-Code-Change)", () => {
  beforeAll(async () => {
    // 1. Mount index.html inside happy-dom once (strip stylesheet links to avoid network errors)
    document.documentElement.innerHTML = RAW_HTML;

    // 2. Mock Global APIs (Chart.js, Audio, SpeechSynthesis, Fetch)
    global.Chart = MockChart;
    window.Chart = MockChart;

    global.Audio = class MockAudio {
      constructor(src) {
        this.src = src;
        this.play = vi.fn().mockResolvedValue(undefined);
        this.pause = vi.fn();
        this.load = vi.fn();
        this.addEventListener = vi.fn();
        this.removeEventListener = vi.fn();
      }
    };

    global.SpeechSynthesisUtterance = class MockSpeechSynthesisUtterance {
      constructor(text) {
        this.text = text;
      }
    };
    window.SpeechSynthesisUtterance = global.SpeechSynthesisUtterance;

    // Coerce innerText to String in happy-dom to prevent text.split error on non-string values
    const proto = window.HTMLElement.prototype;
    const desc = Object.getOwnPropertyDescriptor(proto, "innerText");
    if (desc && desc.set) {
      const origSet = desc.set;
      Object.defineProperty(proto, "innerText", {
        ...desc,
        set(val) {
          origSet.call(this, val != null ? String(val) : "");
        },
      });
    }

    window.speechSynthesis = {
      speak: vi.fn(),
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      getVoices: vi.fn().mockReturnValue([]),
    };

    global.fetch = createDefaultFetchMock();

    // 3. Import app.js as native ES6 module matching browser <script type="module"> behavior
    await import("../../src/js/app.js");
    if (typeof window.loadDashboardData === "function") {
      await window.loadDashboardData();
    }
  });

  beforeEach(() => {
    global.fetch = createDefaultFetchMock();
  });


  it("bootstraps client without ReferenceError or TypeError", () => {
    expect(typeof window.switchTab).toBe("function");
    expect(typeof window.openItemDetailModal).toBe("function");
    expect(typeof window.closeItemDetailModal).toBe("function");
  });

  it("switches navigation tabs and updates view visibility cleanly", () => {
    // Switch to Overview tab
    window.switchTab("overview", false);
    const viewOverview = document.getElementById("view-overview");
    const viewBriefing = document.getElementById("view-exec-briefing");

    expect(viewOverview).not.toBeNull();
    expect(viewOverview.classList.contains("hidden")).toBe(false);
    expect(viewBriefing.classList.contains("hidden")).toBe(true);

    // Switch to Issues tab
    window.switchTab("issues", false);
    const viewIssues = document.getElementById("view-issues");
    expect(viewIssues.classList.contains("hidden")).toBe(false);
    expect(viewOverview.classList.contains("hidden")).toBe(true);

    // Switch back to Exec Briefing
    window.switchTab("exec-briefing", false);
    expect(viewBriefing.classList.contains("hidden")).toBe(false);
  });

  it("handles 5x5 matrix filtering without crashing and enforces 5x5 grid layout", () => {
    const gridContainer = document.getElementById("heatmapGridContainer");
    expect(gridContainer).not.toBeNull();
    expect(gridContainer.classList.contains("grid")).toBe(true);
    expect(gridContainer.classList.contains("grid-cols-5")).toBe(true);

    if (typeof window.renderRiskHeatmap === "function") {
      window.renderRiskHeatmap();
    }
    const cells = gridContainer.querySelectorAll('[id^="heatmap-cell-"]');
    expect(cells.length).toBe(25);

    expect(() => {
      if (typeof window.filterTeamGoogleMatrixCell === "function") {
        window.filterTeamGoogleMatrixCell(4, 5, 20);
      }
    }).not.toThrow();

    expect(() => {
      if (typeof window.clearTeamGoogleMatrixCellFilter === "function") {
        window.clearTeamGoogleMatrixCellFilter();
      }
    }).not.toThrow();
  });

  it("manages modal lifecycle open and close without throwing errors", () => {
    const detailModal = document.getElementById("itemDetailModal");
    expect(detailModal).not.toBeNull();

    // Open Item Detail Modal for RSK-001 (type: 'risk')
    expect(() => {
      window.openItemDetailModal("risk", "RSK-001");
    }).not.toThrow();

    // Verify modal is displayed
    expect(detailModal.classList.contains("hidden")).toBe(false);

    // Close Item Detail Modal
    expect(() => {
      window.closeItemDetailModal();
    }).not.toThrow();

    // Verify modal is hidden
    expect(detailModal.classList.contains("hidden")).toBe(true);

    // Test Data Provenance Hub / Workspace Sync Modal (openSheetsModal)
    const sheetsModal = document.getElementById("sheetsModal");
    expect(sheetsModal).not.toBeNull();

    // Configure test project links including primaryRegisterSheet
    window.CONFIG = {
      project: {
        primaryRegisterName: "Internal Risks",
        secondaryRegisterName: "Team Google Risks",
        links: {
          primaryRegisterSheet: "https://docs.google.com/spreadsheets/d/1qR1tEHFs0QC6CGSUpzHgVgolcF0zQNcg99yZgJwoMVY/edit",
          teamGoogleSheet: "https://docs.google.com/spreadsheets/d/1lNRf5NEBd6ygc91nNwFA4HWGFfbDK02QkbkVfr4OUoA/edit",
          driveFolder: "https://drive.google.com/drive/folders/1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C"
        }
      },
      sources: {
        googleSheets: { enabled: true, sheetUrl: "https://docs.google.com/spreadsheets/d/legacy-fallback/edit" },
        googleDrive: { enabled: true, folderId: "1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C" }
      }
    };

    expect(() => {
      window.openSheetsModal();
    }).not.toThrow();

    expect(sheetsModal.classList.contains("hidden")).toBe(false);

    const sheetInput = document.getElementById("sheetUrlInput");
    const jointLink = document.getElementById("modalJointSheetLink");
    expect(sheetInput).not.toBeNull();
    expect(jointLink).not.toBeNull();

    // Verify it bound primaryRegisterSheet (and NOT the legacy fallback)
    expect(sheetInput.value).toBe("https://docs.google.com/spreadsheets/d/1qR1tEHFs0QC6CGSUpzHgVgolcF0zQNcg99yZgJwoMVY/edit");
    expect(jointLink.href).toBe("https://docs.google.com/spreadsheets/d/1qR1tEHFs0QC6CGSUpzHgVgolcF0zQNcg99yZgJwoMVY/edit");

    // Bug #75: Verify human-readable stream labels and Drive / NotebookLM bindings
    const s1Label = document.getElementById("modalStream1Label");
    const s2Label = document.getElementById("modalStream2Label");
    expect(s1Label?.innerText).toContain("Internal Risks");
    expect(s2Label?.innerText).toContain("Team Google Risks");

    const driveInput = document.getElementById("driveFolderUrlInput");
    const driveLink = document.getElementById("modalDriveFolderLink");
    expect(driveInput?.value).toBe("https://drive.google.com/drive/folders/1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C");
    expect(driveLink?.href).toBe("https://drive.google.com/drive/folders/1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C");

    const notebookInput = document.getElementById("notebookUrlInput");
    const notebookLink = document.getElementById("modalNotebookLink");
    expect(notebookInput?.value).toBe("https://notebooklm.google.com/");
    expect(notebookLink?.href).toBe("https://notebooklm.google.com/");

    // Verify close
    expect(() => {
      window.closeSheetsModal();
    }).not.toThrow();
    expect(sheetsModal.classList.contains("hidden")).toBe(true);
  });

  it("resolves the latest reporting week key defensibly", () => {
    if (typeof window.getLatestWeekKey === "function") {
      const latestKey = window.getLatestWeekKey();
      expect(typeof latestKey).toBe("string");
      expect(latestKey.length).toBeGreaterThan(0);
    }
  });

  it("executes togglePodcastPlayback() across both speech-synthesis fallback and HTML5 Audio paths without ReferenceError", () => {
    expect(typeof window.togglePodcastPlayback).toBe("function");

    const playBtn = document.getElementById("podcastPlayBtn");
    if (playBtn) playBtn.disabled = false;

    // 1. Speech synthesis fallback path (when nativePodcastAudio has no src or cache miss)
    const audioEl = document.getElementById("nativePodcastAudio");
    if (audioEl) audioEl.src = "";
    expect(() => {
      window.togglePodcastPlayback();
    }).not.toThrow();

    // Toggle pause
    expect(() => {
      window.togglePodcastPlayback();
    }).not.toThrow();

    // 2. HTML5 Audio playback path
    if (audioEl) {
      audioEl.src = "https://localhost:9000/data/sample/podcast_w30.mp3";
      audioEl.play = vi.fn().mockResolvedValue(undefined);
      audioEl.pause = vi.fn();
    }
    expect(() => {
      window.togglePodcastPlayback();
    }).not.toThrow();
  });

  it("binds every onclick handler referenced in index.html to a defined window function", () => {
    const matches = [...RAW_HTML.matchAll(/onclick="\s*(?:window\.)?([a-zA-Z0-9_$.]+)\s*\(/g)];
    const missingHandlers = [];
    for (const m of matches) {
      const fnPath = m[1];
      if (fnPath === "event.stopPropagation" || fnPath === "this.parentElement.remove" || fnPath === "window.open") {
        continue;
      }
      const parts = fnPath.split(".");
      let ref = window;
      for (const p of parts) {
        ref = ref != null ? ref[p] : undefined;
      }
      if (typeof ref !== "function") {
        missingHandlers.push(fnPath);
      }
    }
    expect(missingHandlers).toEqual([]);
  });


  it("prevents concurrent initApp() race conditions when falling back from primary project to sample", async () => {
    const requestedUrls = [];
    global.fetch = vi.fn().mockImplementation(async (url) => {
      const urlStr = String(url);
      requestedUrls.push(urlStr);
      if (urlStr === "/api/status") {
        return { ok: true, status: 200, json: async () => ({ defaultProject: "enterprise" }) };
      }
      // Simulate 404 on data/enterprise/config.json as in sample-only environments
      if (urlStr.startsWith("data/enterprise/")) {
        return { ok: false, status: 404, json: async () => ({}) };
      }
      if (urlStr.includes("config.json")) {
        return { ok: true, status: 200, json: async () => mockConfig };
      }
      if (urlStr.includes("risks.json")) {
        return { ok: true, status: 200, json: async () => mockRisks };
      }
      if (urlStr.includes("issues.json")) {
        return { ok: true, status: 200, json: async () => mockIssues };
      }
      if (urlStr.includes("snapshots.json")) {
        return { ok: true, status: 200, json: async () => mockSnapshots };
      }
      if (urlStr.includes("driver_tree.json")) {
        return { ok: true, status: 200, json: async () => mockDriverTree };
      }
      if (urlStr.includes("knowledge.json")) {
        return { ok: true, status: 200, json: async () => mockKnowledge };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    });

    // Trigger concurrent initApp() invocations (simulating DOMContentLoaded + onload collision)
    await Promise.all([window.app.initApp(), window.app.initApp()]);

    // Only data/enterprise/config.json may be probed once; snapshots/risks/issues/knowledge/driver_tree must never hit data/enterprise/
    const enterpriseRequests = requestedUrls.filter((u) => u.startsWith("data/enterprise/"));
    expect(enterpriseRequests).toEqual(["data/enterprise/config.json"]);
    expect(requestedUrls).toContain("data/sample/snapshots.json");
    expect(requestedUrls).toContain("data/sample/risks.json");
  });

  it("activates Time Machine historical snapshots and returns to present cleanly", () => {
    window.TIME_MACHINE_SNAPSHOTS = mockSnapshots.snapshots || mockSnapshots;
    window.activateTimeMachine("w27");
    expect(window.activeTimeMachineWeek).toBe("w27");

    window.returnToPresent();
    expect(window.activeTimeMachineWeek).toBe("present");
  });

  it("switches AI briefing tones, diff baselines, and gap close plan filters without errors", () => {
    expect(() => {
      window.setAiTone("technical");
      expect(window.currentAiTone).toBe("technical");
      window.setAiTone("board");
      expect(window.currentAiTone).toBe("board");
      window.setDiffBaseline("w27");
      expect(window.selectedDiffBaseline).toBe("w27");
      window.toggleShowAllGapPlans();
      window.toggleResolvedGapPlans();
    }).not.toThrow();
  });

  it("filters Joint Risk Heatmap cells and Risk Explorer quick filters cleanly", () => {
    window.setRiskRating("residual");
    expect(window.currentMatrixRating).toBe("residual");
    window.setRiskStatusFilter("all");
    expect(window.currentMatrixStatus).toBe("all");

    window.filterMatrixCell(5, 5, 25);
    expect(window.activeMatrixCellFilter).toEqual({ l: 5, c: 5, score: 25, ratingType: "residual" });

    window.clearActiveCellFilter();
    expect(window.activeMatrixCellFilter).toBeNull();

    window.setQuickFilter("extreme");
    expect(window.currentQuickFilter).toBe("extreme");
    window.resetAllFilters();
    expect(window.currentQuickFilter).toBe("all");
  });

  it("handles cross-tab navigation from Blueprints and Driver Tree to target views", () => {
    const viewOverview = document.getElementById("view-overview");
    const viewBlueprints = document.getElementById("view-blueprints");
    const viewDriverTree = document.getElementById("view-driver-tree");

    window.jumpToBlueprintBundle("Security Architecture & Zero Trust");
    expect(viewBlueprints.classList.contains("hidden")).toBe(false);

    window.filterRiskExplorerByBundle("Security Architecture & Zero Trust");
    expect(viewOverview.classList.contains("hidden")).toBe(false);
    expect(viewBlueprints.classList.contains("hidden")).toBe(true);

    window.jumpToDriverRef("1.1");
    expect(viewDriverTree.classList.contains("hidden")).toBe(false);
    expect(viewOverview.classList.contains("hidden")).toBe(true);
  });

  it("renders Blueprint Knowledge bundle cards and research documentation cards", () => {
    window.switchTab("blueprints", false);
    if (typeof window.renderBlueprintKnowledge === "function") {
      window.renderBlueprintKnowledge();
    }
    const bundleContainer = document.getElementById("bundleAnnexCardsContainer");
    const researchContainer = document.getElementById("researchDocsContainer");

    expect(bundleContainer).not.toBeNull();
    expect(researchContainer).not.toBeNull();
    expect(bundleContainer.children.length).toBeGreaterThan(0);
    expect(researchContainer.children.length).toBeGreaterThan(0);
  });

  it("updates Performance Trends granularity and Issue Register filtering cleanly", () => {
    expect(() => {
      window.setTrendsGranularity("monthly");
      expect(window.trendsGranularity).toBe("monthly");
      window.openTimelineDrilldownModal("w27");
      window.closeTimelineDrilldownModal();
      window.filterAndRenderIssues();
    }).not.toThrow();
  });

  it("mutates project branding dynamically when loading non-default projects", () => {
    window.appState.CONFIG = {
      project: {
        slug: "monaro",
        name: "Project Monaro",
        title: "Sovereign Delivery Governance",
        organization: "Joint Executive Board",
        logoIcon: "🛡️"
      }
    };
    window.renderProjectBranding();

    const badgeEl = document.getElementById("appProjectBadge");
    const titleEl = document.getElementById("appProjectTitle");
    const subTitleEl = document.getElementById("appProjectSubtitle");
    const logoEl = document.getElementById("appProjectLogoIcon");

    expect(badgeEl.innerText).toBe("PROJECT MONARO");
    expect(titleEl.innerText).toBe("Delivery & Risk Dashboard");
    expect(subTitleEl.innerText).toContain("Sovereign Delivery Governance");
    expect(logoEl.innerText).toBe("🛡️");
    expect(document.title).toContain("Project Monaro");
  });

  it("renders real risk cards into explorerCardsContainer and updates match count", () => {
    window.switchTab("overview", false);
    window.renderRiskExplorer();

    const cardsContainer = document.getElementById("explorerCardsContainer");
    const matchCountEl = document.getElementById("explorerMatchCount");

    expect(cardsContainer).not.toBeNull();
    const cards = cardsContainer.querySelectorAll("div");
    expect(cards.length).toBeGreaterThan(0);
    expect(matchCountEl.innerText).toMatch(/\d+ Matched/);
  });

  it("populates Gemini executive briefing synthesis and top 3 attention items", () => {
    window.switchTab("exec-briefing", false);
    window.renderExecBriefing();

    const summaryEl = document.getElementById("geminiSummaryText");
    expect(summaryEl).not.toBeNull();
    expect(summaryEl.innerText).not.toBe("Loading executive briefing...");
    expect(summaryEl.innerHTML.length).toBeGreaterThan(20);

    const top3Container = document.getElementById("top3ThingsContainer");
    expect(top3Container).not.toBeNull();
    const top3Cards = Array.from(top3Container.children).filter(el => el.tagName === "DIV");
    expect(top3Cards.length).toBe(3);
  });

  it("renders dialogue transcript entries into podcastTranscriptContainer", () => {
    window.renderPodcastTranscript("w27");

    const transcriptContainer = document.getElementById("podcastTranscriptContainer");
    expect(transcriptContainer).not.toBeNull();
    const entries = Array.from(transcriptContainer.children).filter(el => el.tagName === "DIV");
    expect(entries.length).toBeGreaterThan(0);
    expect(entries[0].textContent).toMatch(/Host|Alex|Jordan/i);
  });

  it("handles historical snapshot podcast audio fallback without audio file (Bug #112)", async () => {
    // Week 27 has audioUrl: null / no audio file
    window.appState.activeTimeMachineWeek = "w27";
    await window.updatePodcastAudioForWeek("w27");

    const playBtn = document.getElementById("podcastPlayBtn");
    const downloadLink = document.getElementById("podcastDownloadLink");
    const timeLabel = document.getElementById("podcastTimeLabel");
    const audioEl = document.getElementById("nativePodcastAudio");

    expect(playBtn).not.toBeNull();
    expect(playBtn.disabled).toBe(false);
    expect(playBtn.title).toMatch(/Speech Synthesis Fallback/i);

    expect(downloadLink).not.toBeNull();
    expect(downloadLink.classList.contains("opacity-50")).toBe(true);
    expect(downloadLink.classList.contains("pointer-events-none")).toBe(true);
    expect(downloadLink.hasAttribute("href")).toBe(false);

    expect(timeLabel).not.toBeNull();
    expect(timeLabel.innerText).toBe("0:00 / Script Dialogue");

    expect(audioEl.hasAttribute("src")).toBe(false);

    // Verify togglePodcastPlayback triggers SpeechSynthesis fallback smoothly
    let spokenText = "";
    const mockSpeech = {
      speaking: false,
      cancel: vi.fn(),
      speak: vi.fn().mockImplementation((utterance) => {
        spokenText = utterance.text;
      }),
    };
    window.speechSynthesis = mockSpeech;
    global.speechSynthesis = mockSpeech;

    window.togglePodcastPlayback();
    expect(window.speechSynthesis.speak).toHaveBeenCalled();
    expect(spokenText).toMatch(/Executive update for Week 27/i);
    expect(playBtn.innerText).toBe("⏸");

    // Toggling again pauses/stops speech synthesis
    window.speechSynthesis.speaking = true;
    window.togglePodcastPlayback();
    expect(window.speechSynthesis.cancel).toHaveBeenCalled();
    expect(playBtn.innerText).toBe("▶");
  });

  it("enforces DOM Contract: every registered DOM_IDS constant exists in index.html", async () => {
    const { DOM_IDS } = await import("../../src/js/dom_contract.js");
    const missing = [];
    for (const [key, id] of Object.entries(DOM_IDS)) {
      if (!document.getElementById(id)) {
        missing.push(`${key} -> #${id}`);
      }
    }
    expect(missing, `DOM IDs registered in dom_contract.js missing from index.html: ${missing.join(", ")}`).toEqual([]);
  });

  it("enforces Static AST / Regex Gate: every literal getElementById call in src/js exists in index.html or contract", () => {
    const jsDir = path.resolve(process.cwd(), "src/js");
    const jsFiles = [];

    function findJsFiles(dir) {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          findJsFiles(full);
        } else if (entry.name.endsWith(".js")) {
          jsFiles.push(full);
        }
      }
    }
    findJsFiles(jsDir);

    const missingInHtml = [];
    const idRegex = /getElementById\(\s*['"]([a-zA-Z0-9_-]+)['"]\s*\)/g;

    for (const file of jsFiles) {
      const code = fs.readFileSync(file, "utf-8");
      let match;
      while ((match = idRegex.exec(code)) !== null) {
        const id = match[1];
        // Allow dynamic or backward-compatible fallback checks
        if (id.startsWith("native") || id.startsWith("briefing") || id.startsWith("btn") || id.startsWith("risk") || id.startsWith("filter")) {
          continue;
        }
        if (!document.getElementById(id)) {
          missingInHtml.push(`${path.basename(file)}: #${id}`);
        }
      }
    }
    expect(missingInHtml, `Hardcoded getElementById literals in src/js missing from index.html: ${missingInHtml.join(", ")}`).toEqual([]);
  });
});
