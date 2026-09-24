// =============================================================================
// Risk & Delivery Intelligence Platform — ES6 Entrypoint & Event Delegation Orchestrator
// Google Standards Compliant (go/tsstyle, go/js-practices)
// =============================================================================
import * as stateMod from './state.js';
import * as apiMod from './api.js';
import * as execBriefingMod from './modules/exec_briefing.js';
import * as podcastPlayerMod from './modules/podcast_player.js';
import * as timeMachineMod from './modules/time_machine.js';
import * as riskHeatmapMod from './modules/risk_heatmap.js';
import * as riskExplorerMod from './modules/risk_explorer.js';
import * as teamGoogleMod from './modules/team_google.js';
import * as blueprintKnowledgeMod from './modules/blueprint_knowledge.js';
import * as driverTreeMod from './modules/driver_tree.js';
import * as issueRegisterMod from './modules/issue_register.js';
import * as modalsMod from './modules/modals.js';
import * as performanceTrendsMod from './modules/performance_trends.js';

const TAB_ALIASES = {
    'joint-register': 'overview',
    'issue-register': 'issues',
    'blueprint-knowledge': 'blueprints',
    'performance-trends': 'trends'
};

export function switchTab(rawTabId, _updateUrl = true) {
    const tabId = TAB_ALIASES[rawTabId] || rawTabId;
    stateMod.store.set('activeTab', tabId);
    const tabs = [
        'exec-briefing',
        'overview',
        'team-google',
        'issues',
        'driver-tree',
        'blueprints',
        'trends'
    ];

    tabs.forEach(t => {
        const viewEl = document.getElementById(`view-${t}`);
        const btnEl = document.getElementById(`tabBtn-${t}`) || document.getElementById(`tab-${t}`);
        if (viewEl) {
            viewEl.classList.toggle('hidden', t !== tabId);
        }
        if (btnEl) {
            btnEl.classList.toggle('active', t === tabId);
        }
    });

    if (tabId === 'exec-briefing') execBriefingMod.renderExecBriefing();
    else if (tabId === 'overview') {
        riskHeatmapMod.renderRiskHeatmap();
        riskExplorerMod.renderRiskExplorer();
    } else if (tabId === 'team-google') {
        teamGoogleMod.renderTeamGoogleHeatmap();
        teamGoogleMod.renderTeamGoogleRiskExplorer();
    } else if (tabId === 'issues') issueRegisterMod.renderIssueTable();
    else if (tabId === 'driver-tree') driverTreeMod.renderDriverTree();
    else if (tabId === 'blueprints') blueprintKnowledgeMod.renderBlueprintKnowledge();
    else if (tabId === 'trends') performanceTrendsMod.renderTrendsCharts();
}

export const switchMainTab = switchTab;

export function initApp(projectSlug) {
    return apiMod.initApp(projectSlug);
}

// Expose domain module handlers on window for HTML inline event attributes & tests
if (typeof window !== 'undefined') {
    const appExports = {
        ...stateMod,
        ...apiMod,
        ...execBriefingMod,
        ...podcastPlayerMod,
        ...timeMachineMod,
        ...riskHeatmapMod,
        ...riskExplorerMod,
        ...teamGoogleMod,
        ...blueprintKnowledgeMod,
        ...driverTreeMod,
        ...issueRegisterMod,
        ...modalsMod,
        ...performanceTrendsMod,
        switchTab,
        switchMainTab,
        initApp
    };

    window.app = appExports;
    Object.assign(window, appExports);

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                initApp();
            });
        } else {
            initApp();
        }
    }
}
