// =============================================================================
// Risk & Delivery Intelligence Platform — API, Workspace Sync & Data Loader Module
// =============================================================================
import { appState, store, updateSystemTimeBadges } from './state.js';
import { renderExecBriefing, renderDiffBaselineSelector } from './modules/exec_briefing.js';
import { renderRiskHeatmap } from './modules/risk_heatmap.js';
import { renderRiskExplorer } from './modules/risk_explorer.js';
import { renderTeamGoogleHeatmap, renderTeamGoogleRiskExplorer } from './modules/team_google.js';
import { renderBlueprintKnowledge } from './modules/blueprint_knowledge.js';
import { renderDriverTree } from './modules/driver_tree.js';
import { renderIssueTable } from './modules/issue_register.js';
import { renderTrendsCharts } from './modules/performance_trends.js';

let inFlightInitPromise = null;

export function resolveInitialProjectSlug(explicitSlug) {
    if (explicitSlug) return explicitSlug;
    if (typeof window !== 'undefined') {
        const params = new URLSearchParams(window.location?.search || '');
        const urlProject = params.get('project');
        if (urlProject) return urlProject;
        if (window.DEFAULT_PROJECT) return window.DEFAULT_PROJECT;
    }
    return '';
}

export function showSyncToast(message, type = 'info') {
    if (typeof console !== 'undefined') {
        console.log(`[Sync Toast: ${type}] ${message}`);
    }
}

export function renderProjectBranding() {
    const cfg = appState.CONFIG || {};
    const p = cfg.project || cfg;
    if (!p) return;

    if (p.name) {
        document.title = `${p.name} - ${p.title || 'Risk & Delivery Dashboard'}`;
    }
    const badgeEl = document.getElementById('appProjectBadge');
    if (badgeEl && p.name) {
        badgeEl.innerText = p.name.toUpperCase();
    }
    const titleEl = document.getElementById('appProjectTitle');
    if (titleEl) {
        titleEl.innerText = p.title ? 'Delivery & Risk Dashboard' : (p.name || 'Delivery & Risk Dashboard');
    }
    const subTitleEl = document.getElementById('appProjectSubtitle');
    if (subTitleEl) {
        let displayTitle = p.title || '';
        if (displayTitle.toLowerCase() === (p.name || '').toLowerCase()) {
            displayTitle = '';
        }
        const subtitleParts = [displayTitle, p.organization || '', p.heroTag || ''].filter(Boolean);
        subTitleEl.innerText = subtitleParts.join(' • ') || (p.subtitle || p.heroTag || '');
    }
    const logoEl = document.getElementById('appProjectLogoIcon');
    if (logoEl && p.logoIcon) {
        logoEl.innerText = p.logoIcon;
    }
}

export function renderFeatureTabs() {
    const features = appState.CONFIG?.features || {};
    const tgBtn = document.getElementById('tab-team-google');
    if (tgBtn && features.enableTeamGoogleTab === false) {
        tgBtn.classList.add('hidden');
    }
}

export function updateAllDynamicCounters() {
    const activeRisks = (appState.LIVE_RISKS || []).filter(r => r && r.status !== 'Closed');
    const activeIssues = (appState.LIVE_ISSUES || []).filter(i => i && i.status !== 'Closed' && i.status !== 'Resolved');
    const activeTgRisks = (appState.LIVE_TEAM_GOOGLE_RISKS || []).filter(r => r && r.status !== 'Closed');

    const badgeRisks = document.getElementById('tabPrimaryRegisterBadge');
    if (badgeRisks) badgeRisks.innerText = String(activeRisks.length);

    const badgeIssues = document.getElementById('tabIssuesBadge');
    if (badgeIssues) badgeIssues.innerText = String(activeIssues.length);

    const badgeTg = document.getElementById('tabTeamGoogleBadge');
    if (badgeTg) badgeTg.innerText = String(activeTgRisks.length);
}

export function checkUrlViewParameters() {
    if (typeof window === 'undefined' || !window.location) return;
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab') || params.get('view');
    if (tab && typeof window.switchTab === 'function') {
        window.switchTab(tab, false);
    }
}

export async function loadProjectData(projectSlug) {
    let slug = resolveInitialProjectSlug(projectSlug);
    try {
        if (!slug) {
            try {
                const statusResp = await fetch('/api/status');
                if (statusResp && statusResp.ok) {
                    const statusData = await statusResp.json();
                    slug = statusData?.project || statusData?.defaultProject || 'sample';
                } else {
                    slug = 'sample';
                }
            } catch {
                slug = 'sample';
            }
        }

        let configResp = await fetch(`data/${slug}/config.json`);
        if (!configResp || !configResp.ok) {
            slug = 'sample';
            configResp = await fetch(`data/${slug}/config.json`);
        }
        if (configResp && configResp.ok) {
            appState.CONFIG = await configResp.json();
            store.set('config', appState.CONFIG);
        }

        const [risksResp, issuesResp, snapsResp, dtResp, knowResp] = await Promise.all([
            fetch(`data/${slug}/risks.json`),
            fetch(`data/${slug}/issues.json`),
            fetch(`data/${slug}/snapshots.json`),
            fetch(`data/${slug}/driver_tree.json`),
            fetch(`data/${slug}/knowledge.json`)
        ]);

        if (risksResp && risksResp.ok) {
            const rData = await risksResp.json();
            if (Array.isArray(rData)) {
                appState.LIVE_RISKS = rData;
                // Partition into Team Google if explicit sourceRegister or TG- prefix present
                const tgRisks = rData.filter(r => r && (
                    r.sourceRegister === 'team_google' ||
                    (typeof r.id === 'string' && (r.id.startsWith('TG-') || r.id.includes('-TG-')))
                ));
                if (tgRisks.length > 0) {
                    appState.LIVE_TEAM_GOOGLE_RISKS = tgRisks;
                }
            } else if (rData && typeof rData === 'object') {
                appState.LIVE_RISKS = rData.risks || rData.jointRisks || rData.LIVE_RISKS || [];
                if (rData.teamGoogleRisks || rData.LIVE_TEAM_GOOGLE_RISKS) {
                    appState.LIVE_TEAM_GOOGLE_RISKS = rData.teamGoogleRisks || rData.LIVE_TEAM_GOOGLE_RISKS;
                }
            }
        }
        if (issuesResp && issuesResp.ok) {
            const iData = await issuesResp.json();
            appState.LIVE_ISSUES = Array.isArray(iData) ? iData : (iData.issues || iData.LIVE_ISSUES || []);
        }
        if (snapsResp && snapsResp.ok) {
            const sData = await snapsResp.json();
            appState.TIME_MACHINE_SNAPSHOTS = sData.snapshots || sData || {};
        }
        if (dtResp && dtResp.ok) {
            const dData = await dtResp.json();
            if (Array.isArray(dData)) {
                appState.DRIVER_TREE = dData;
                appState.DRIVER_TREE_ITEMS = dData;
            } else if (dData && typeof dData === 'object') {
                appState.DRIVER_TREE = dData;
                if (Array.isArray(dData.nodes)) {
                    appState.DRIVER_TREE_ITEMS = dData.nodes;
                } else if (Array.isArray(dData.items)) {
                    appState.DRIVER_TREE_ITEMS = dData.items;
                } else if (Array.isArray(dData.capabilityDrops)) {
                    const extractedGates = [];
                    dData.capabilityDrops.forEach(cd => {
                        if (Array.isArray(cd.gates)) {
                            cd.gates.forEach(g => extractedGates.push({ ...g, dropName: cd.name, lead: cd.lead }));
                        }
                    });
                    appState.DRIVER_TREE_ITEMS = extractedGates;
                } else {
                    appState.DRIVER_TREE_ITEMS = [];
                }
            } else {
                appState.DRIVER_TREE = [];
                appState.DRIVER_TREE_ITEMS = [];
            }
        }
        if (knowResp && knowResp.ok) {
            appState.NOTEBOOK_CATALOG = await knowResp.json();
        }
        appState.CURRENT_PROJECT = slug;
        store.set({
            projectSlug: slug,
            liveRisks: appState.LIVE_RISKS,
            teamGoogleRisks: appState.LIVE_TEAM_GOOGLE_RISKS,
            liveIssues: appState.LIVE_ISSUES,
            timeMachineSnapshots: appState.TIME_MACHINE_SNAPSHOTS,
            driverTree: appState.DRIVER_TREE
        });
    } catch (err) {
        console.warn('[API] Fallback state during loadProjectData:', err);
    }

    renderProjectBranding();
    renderFeatureTabs();
    updateSystemTimeBadges();
    updateAllDynamicCounters();
    renderDiffBaselineSelector();
    renderExecBriefing();
    renderRiskHeatmap();
    renderRiskExplorer();
    renderTeamGoogleHeatmap();
    renderTeamGoogleRiskExplorer();
    renderBlueprintKnowledge();
    renderDriverTree();
    renderIssueTable();
    renderTrendsCharts();
    checkUrlViewParameters();
}

export async function initApp(projectSlug) {
    if (inFlightInitPromise) {
        return inFlightInitPromise;
    }
    inFlightInitPromise = loadProjectData(projectSlug).finally(() => {
        inFlightInitPromise = null;
    });
    return inFlightInitPromise;
}

export async function loadDashboardData(projectSlug) {
    return initApp(projectSlug);
}

export function openSheetsModal() {
    const modal = document.getElementById('sheetsModal');
    if (modal) modal.classList.remove('hidden');

    const cfg = appState.CONFIG || (typeof window !== 'undefined' ? window.CONFIG : null) || {};
    const primaryName = cfg?.project?.primaryRegisterName || 'Joint Program Risk & Issue Register';
    const secondaryName = cfg?.project?.secondaryRegisterName || 'Team Google Risk Register';
    const primaryUrl = cfg?.project?.links?.primaryRegisterSheet || cfg?.sources?.googleSheets?.sheetUrl || '';
    const teamGoogleUrl = cfg?.project?.links?.teamGoogleSheet || '';
    const driveUrl = cfg?.project?.links?.driveFolder || (cfg?.sources?.googleDrive?.folderId ? `https://drive.google.com/drive/folders/${cfg.sources.googleDrive.folderId}` : '');
    const notebookUrl = cfg?.project?.links?.notebookLm || cfg?.notebookLmUrl || 'https://notebooklm.google.com/';

    // Stream 1: Joint Program Risk & Issue Register
    const s1Label = document.getElementById('modalStream1Label');
    if (s1Label) {
        s1Label.innerText = `1. ${primaryName} (Google Sheet):`;
    }
    const sheetInput = document.getElementById('sheetUrlInput');
    if (sheetInput && primaryUrl) {
        sheetInput.value = primaryUrl;
    }
    const jointLink = document.getElementById('modalJointSheetLink');
    if (jointLink && primaryUrl) {
        jointLink.href = primaryUrl;
    }

    // Stream 2: Team Google Risk Register
    const s2Label = document.getElementById('modalStream2Label');
    if (s2Label) {
        s2Label.innerText = `2. ${secondaryName} (Google Sheet):`;
    }
    const tgInput = document.getElementById('teamGoogleSheetUrlInput');
    if (tgInput && teamGoogleUrl) {
        tgInput.value = teamGoogleUrl;
    }
    const tgLink = document.getElementById('modalTeamGoogleSheetLink');
    if (tgLink && teamGoogleUrl) {
        tgLink.href = teamGoogleUrl;
    }

    // Stream 3: Drive Folder
    const driveInput = document.getElementById('driveFolderUrlInput');
    if (driveInput && driveUrl) {
        driveInput.value = driveUrl;
    }
    const driveLink = document.getElementById('modalDriveFolderLink');
    if (driveLink && driveUrl) {
        driveLink.href = driveUrl;
    }

    // Stream 4: NotebookLM
    const notebookInput = document.getElementById('notebookUrlInput');
    if (notebookInput && notebookUrl) {
        notebookInput.value = notebookUrl;
    }
    const notebookLink = document.getElementById('modalNotebookLink');
    if (notebookLink && notebookUrl) {
        notebookLink.href = notebookUrl;
    }
}

export function closeSheetsModal() {
    const modal = document.getElementById('sheetsModal');
    if (modal) modal.classList.add('hidden');
}

export function toggleSheetDropdown() {
    const menu = document.getElementById('sheetDropdownMenu');
    if (menu) menu.classList.toggle('hidden');
}

export async function checkForUpdates() {
    const statusText = document.getElementById('btnCheckUpdatesText');
    if (statusText) {
        statusText.innerText = 'Checking for updates...';
    }
    showSyncToast('Checking for updates...', 'info');
    try {
        const resp = await fetch(`/api/check-drive-sync?project=${encodeURIComponent(appState.CURRENT_PROJECT)}`);
        if (resp && resp.ok) {
            const data = await resp.json();
            appState.DRIVE_REPORTS = data.allReports || data.files || [];
            renderDriveReportsInModal();
            if (statusText) {
                statusText.innerText = `Up to date (${appState.DRIVE_REPORTS.length} reports)`;
            }
        }
    } catch {
        if (statusText) {
            statusText.innerText = 'Offline / Cached State';
        }
    }
}

export async function checkDriveSyncStatus() {
    return checkForUpdates();
}

export function renderDriveReportsInModal() {
    const container = document.getElementById('driveReportsModalList');
    if (!container) return;
    const reports = appState.DRIVE_REPORTS || [];
    if (reports.length === 0) {
        container.innerHTML = '<div class="p-3 text-xs text-slate-500">All Google Drive weekly reports are synchronized.</div>';
        return;
    }
    container.innerHTML = reports.map(f => `
        <div class="p-2.5 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
            <span class="font-medium text-slate-800">${f.name || f.title || 'Weekly Status Report'}</span>
            <span class="font-mono text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">Synced</span>
        </div>
    `).join('');
}

export async function syncGoogleSheet() {
    showSyncToast('Syncing Google Sheets Risk Register...', 'info');
    try {
        const resp = await fetch('/api/sync-sheet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project: appState.CURRENT_PROJECT })
        });
        if (resp && resp.ok) {
            await loadDashboardData(appState.CURRENT_PROJECT);
            showSyncToast('Google Sheets Risk Register synchronized.', 'success');
        }
    } catch {
        showSyncToast('Sheet sync failed or offline.', 'error');
    }
}

export async function refreshNotebookSources() {
    showSyncToast('Refreshing NotebookLM Grounded Sources...', 'info');
    try {
        const resp = await fetch(`/api/project-data?project=${encodeURIComponent(appState.CURRENT_PROJECT)}&file=sources_catalog.json`);
        if (resp && resp.ok) {
            appState.NOTEBOOK_CATALOG = await resp.json();
            renderBlueprintKnowledge();
            showSyncToast('NotebookLM sources refreshed.', 'success');
        }
    } catch {
        showSyncToast('NotebookLM catalog using cached state.', 'info');
    }
}

export async function syncAllWorkspaceSources() {
    await syncGoogleSheet();
    await checkForUpdates();
    await refreshNotebookSources();
}
