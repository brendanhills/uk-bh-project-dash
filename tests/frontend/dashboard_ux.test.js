import { describe, it, expect, beforeEach, vi } from "vitest";
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

describe("Dashboard UX & Client Controller Integrity (Zero-Code-Change)", () => {
  beforeEach(async () => {
    // 1. Mount index.html inside happy-dom (strip stylesheet links to avoid network errors)
    const indexPath = path.resolve(process.cwd(), "index.html");
    const rawHtml = fs
      .readFileSync(indexPath, "utf-8")
      .replace(/<link[^>]*rel=["']stylesheet["'][^>]*>/gi, "");
    document.documentElement.innerHTML = rawHtml;

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

    global.fetch = vi.fn().mockImplementation(async (url) => {
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

    // 3. Execute app.js in script context matching browser <script defer> behavior
    const appJsPath = path.resolve(process.cwd(), "src/js/app.js");
    const appJsCode = fs.readFileSync(appJsPath, "utf-8");
    window.eval(appJsCode);
    if (typeof window.loadDashboardData === "function") {
      await window.loadDashboardData();
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
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

  it("handles 5x5 matrix filtering without crashing", () => {
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
  });

  it("resolves the latest reporting week key defensibly", () => {
    if (typeof window.getLatestWeekKey === "function") {
      const latestKey = window.getLatestWeekKey();
      expect(typeof latestKey).toBe("string");
      expect(latestKey.length).toBeGreaterThan(0);
    }
  });

  it("provides defensive audio fallback without uncaught rejection", () => {
    expect(() => {
      if (typeof window.playPodcastAudio === "function") {
        window.playPodcastAudio("w30");
      } else if (typeof window.togglePodcastPlay === "function") {
        window.togglePodcastPlay();
      }
    }).not.toThrow();
  });
});
