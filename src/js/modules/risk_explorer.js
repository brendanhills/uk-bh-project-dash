// =============================================================================
// Risk & Delivery Intelligence Platform — Risk Explorer & Filtering Module
// =============================================================================
import { appState, evaluateTargetStaleness } from '../state.js';
import { renderRiskHeatmap, clearActiveCellFilter } from './risk_heatmap.js';

export function isUnactionedRisk(r) {
    if (!r) return false;
    const plan = String(r.treatmentPlan || r.actionPlan || '').trim();
    const owner = String(r.riskOwner || r.owner || '').trim();
    return !plan || plan === '-' || plan.toLowerCase() === 'tbd' || !owner || owner === 'Unassigned';
}

export function setExplorerViewMode(mode) {
    appState.explorerViewMode = mode;
    const btnCards = document.getElementById('expBtnCards');
    const btnTable = document.getElementById('expBtnTable');
    if (btnCards && btnTable) {
        if (mode === 'detailed' || mode === 'cards') {
            btnCards.className = 'px-3 py-1.5 rounded-lg bg-white text-indigo-700 font-bold shadow-xs cursor-pointer';
            btnTable.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer';
        } else {
            btnTable.className = 'px-3 py-1.5 rounded-lg bg-white text-indigo-700 font-bold shadow-xs cursor-pointer';
            btnCards.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer';
        }
    }
    renderRiskExplorer();
}

export function updateQuickFilterButtonsUI() {
    const map = {
        all: 'qfAll',
        high: 'qfHigh',
        trending_worse: 'qfTrending',
        eventuated: 'qfEventuated',
        exec: 'qfExec',
        extreme: 'qfHigh',
        overdue: 'qfTrending',
        unactioned: 'qfEventuated'
    };
    Object.entries(map).forEach(([key, id]) => {
        const el = document.getElementById(id);
        if (!el) return;
        const active = appState.currentQuickFilter === key;
        if (active) {
            el.classList.add('ring-2', 'ring-indigo-500', 'bg-indigo-600', 'text-white');
            el.classList.remove('bg-white');
        } else {
            el.classList.remove('ring-2', 'ring-indigo-500', 'bg-indigo-600', 'text-white');
            el.classList.add('bg-white');
        }
    });
}

export function setQuickFilter(filterType) {
    appState.currentQuickFilter = appState.currentQuickFilter === filterType ? 'all' : filterType;
    updateQuickFilterButtonsUI();
    renderRiskExplorer();
}

export function resetAllFilters() {
    appState.currentQuickFilter = 'all';
    appState.activeMatrixCellFilter = null;
    appState.activeScoreBandFilter = null;

    const searchInput = document.getElementById('explorerSearchInput') || document.getElementById('riskSearchInput');
    if (searchInput) searchInput.value = '';
    const catSelect = document.getElementById('filterCategorySelect') || document.getElementById('riskCategorySelect');
    if (catSelect) catSelect.value = 'all';
    const bundleSelect = document.getElementById('filterBundleSelect') || document.getElementById('riskBundleSelect');
    if (bundleSelect) bundleSelect.value = 'all';
    const govSelect = document.getElementById('filterGovSelect') || document.getElementById('riskGovSelect');
    if (govSelect) govSelect.value = 'all';
    const statusSelect = document.getElementById('filterStatusSelect') || document.getElementById('riskStatusSelect');
    if (statusSelect) statusSelect.value = 'open';

    clearActiveCellFilter();
    updateQuickFilterButtonsUI();
    renderRiskHeatmap();
    renderRiskExplorer();
}

export function toggleCardExpansion(riskId) {
    if (appState.expandedCardIds.has(riskId)) {
        appState.expandedCardIds.delete(riskId);
    } else {
        appState.expandedCardIds.add(riskId);
    }
    renderRiskExplorer();
}

export function toggleRiskCardExpand(riskId) {
    toggleCardExpansion(riskId);
}

export function drillDownToCategory(cat) {
    const catSelect = document.getElementById('filterCategorySelect') || document.getElementById('riskCategorySelect');
    if (catSelect) {
        catSelect.value = cat;
    }
    if (typeof window.switchMainTab === 'function') {
        window.switchMainTab('joint-register');
    }
    renderRiskExplorer();
}

export function drillDownToScoreBand(band) {
    appState.activeScoreBandFilter = appState.activeScoreBandFilter === band ? null : band;
    if (typeof window.switchMainTab === 'function') {
        window.switchMainTab('joint-register');
    }
    renderRiskExplorer();
}

export function renderRiskSeverityProfile() {
    const container = document.getElementById('riskSeverityProfileBar');
    if (!container) return;
    const activeRisks = (appState.LIVE_RISKS || []).filter(r => r && r.status !== 'Closed');
    const total = Math.max(1, activeRisks.length);
    const extreme = activeRisks.filter(r => (r.residualRiskScore || 0) >= 18).length;
    const high = activeRisks.filter(r => (r.residualRiskScore || 0) >= 12 && (r.residualRiskScore || 0) < 18).length;
    const medium = activeRisks.filter(r => (r.residualRiskScore || 0) >= 6 && (r.residualRiskScore || 0) < 12).length;
    const low = Math.max(0, activeRisks.length - extreme - high - medium);

    container.innerHTML = `
        <div class="flex h-2.5 rounded-full overflow-hidden bg-slate-100 border border-slate-200">
            <div onclick="drillDownToScoreBand('extreme')" style="width:${(extreme / total) * 100}%" class="bg-red-600 cursor-pointer" title="Extreme (${extreme})"></div>
            <div onclick="drillDownToScoreBand('high')" style="width:${(high / total) * 100}%" class="bg-amber-500 cursor-pointer" title="High (${high})"></div>
            <div onclick="drillDownToScoreBand('medium')" style="width:${(medium / total) * 100}%" class="bg-yellow-400 cursor-pointer" title="Medium (${medium})"></div>
            <div onclick="drillDownToScoreBand('low')" style="width:${(low / total) * 100}%" class="bg-emerald-500 cursor-pointer" title="Low (${low})"></div>
        </div>
    `;
}

export function renderRiskExplorer() {
    const cardsContainer = document.getElementById('explorerCardsContainer') || document.getElementById('riskExplorerList');
    const tableContainer = document.getElementById('explorerTableContainer');
    if (!cardsContainer && !tableContainer) return;

    const searchVal = (
        document.getElementById('explorerSearchInput')?.value
        || document.getElementById('riskSearchInput')?.value
        || ''
    ).toLowerCase().trim();
    const catVal = document.getElementById('filterCategorySelect')?.value || document.getElementById('riskCategorySelect')?.value || 'all';
    const bundleVal = document.getElementById('filterBundleSelect')?.value || document.getElementById('riskBundleSelect')?.value || 'all';
    const govVal = document.getElementById('filterGovSelect')?.value || document.getElementById('riskGovSelect')?.value || 'all';
    const statusVal = document.getElementById('filterStatusSelect')?.value || document.getElementById('riskStatusSelect')?.value || (appState.currentMatrixStatus === 'open' ? 'Active' : 'all');

    const filtered = (appState.LIVE_RISKS || []).filter(r => {
        if (!r) return false;
        if (statusVal === 'open' && (r.status === 'Closed' || r.status === 'Resolved')) return false;
        if (statusVal === 'Active' && (r.status === 'Closed' || r.status === 'Resolved')) return false;
        if (statusVal !== 'all' && statusVal !== 'open' && statusVal !== 'Active' && r.status !== statusVal) return false;

        if (catVal !== 'all' && !String(r.causeCategory || '').toLowerCase().includes(catVal.toLowerCase())) return false;
        if (bundleVal !== 'all') {
            const b = String(r.contractBundle || r.blueprintBundle || r.bundle || '');
            if (!b.includes(bundleVal)) return false;
        }
        if (govVal !== 'all' && !String(r.governanceLevel || '').toLowerCase().includes(govVal.toLowerCase())) return false;

        if (appState.activeMatrixCellFilter) {
            const { l, c, ratingType } = appState.activeMatrixCellFilter;
            const rl = ratingType === 'inherent' ? (r.inherentLikelihood || 3) : (r.residualLikelihood || 3);
            const rc = ratingType === 'inherent' ? (r.inherentConsequence || 3) : (r.residualConsequence || 3);
            if (rl !== l || rc !== c) return false;
        }

        if (appState.currentQuickFilter === 'high' || appState.currentQuickFilter === 'extreme') {
            if ((r.residualRiskScore || 0) < 18) return false;
        }
        if (appState.currentQuickFilter === 'trending_worse') {
            if (r.trend !== '↑' && !String(r.trend).toLowerCase().includes('worse') && !String(r.trend).toLowerCase().includes('deteriorating')) return false;
        }
        if (appState.currentQuickFilter === 'eventuated') {
            if (r.status !== 'Issue Eventuated') return false;
        }
        if (appState.currentQuickFilter === 'exec') {
            const g = (r.governanceLevel || '').toLowerCase();
            if (!g.includes('psg') && !g.includes('exec') && !g.includes('steering') && !g.includes('coa')) return false;
        }
        if (appState.currentQuickFilter === 'overdue' && !evaluateTargetStaleness(r.targetDate).isOverdue) return false;
        if (appState.currentQuickFilter === 'unactioned' && !isUnactionedRisk(r)) return false;

        if (searchVal) {
            const haystack = [
                r.id,
                r.displayId,
                r.riskName,
                r.riskTitle,
                r.riskDescription,
                r.causeDescription,
                r.causeCategory,
                r.consequenceDescription,
                r.contractBundle,
                r.blueprintBundle,
                r.bundle,
                r.riskOwner,
                r.owner,
                r.treatmentPlan,
                r.driverTreeRef
            ].join(' ').toLowerCase();
            if (!haystack.includes(searchVal)) return false;
        }
        return true;
    });

    const countEl = document.getElementById('explorerMatchCount');
    if (countEl) countEl.innerText = `${filtered.length} Matched`;

    renderRiskSeverityProfile();

    if (filtered.length === 0) {
        const noHtml = `
            <div class="col-span-full p-8 text-center bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
                <p class="text-sm font-bold text-slate-700">No risks match the current filter criteria.</p>
                <button onclick="resetAllFilters()" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg cursor-pointer">Reset All Filters</button>
            </div>
        `;
        if (cardsContainer) cardsContainer.innerHTML = noHtml;
        if (tableContainer) tableContainer.innerHTML = noHtml;
        return;
    }

    const htmlCards = filtered.map(r => {
        const score = r.residualRiskScore || (r.residualLikelihood * r.residualConsequence) || 0;
        const inhScore = r.inherentRiskScore || (r.inherentLikelihood * r.inherentConsequence) || score;
        const isExpanded = appState.expandedCardIds.has(r.id) || appState.explorerViewMode === 'detailed';
        const title = r.riskName || r.riskTitle || r.riskDescription || r.title || 'Program Risk';
        const owner = r.riskOwner || r.owner || 'Joint Team';
        const bundle = r.contractBundle || r.blueprintBundle || r.bundle || 'General Delivery';

        let badgeClass = 'bg-emerald-100 text-emerald-800 border-emerald-300';
        if (score >= 18) badgeClass = 'bg-red-600 text-white font-extrabold';
        else if (score >= 12) badgeClass = 'bg-amber-500 text-white font-extrabold';
        else if (score >= 6) badgeClass = 'bg-yellow-100 text-yellow-900 border-yellow-300';

        const l = appState.currentMatrixRating === 'inherent' ? (r.inherentLikelihood || 3) : (r.residualLikelihood || 3);
        const c = appState.currentMatrixRating === 'inherent' ? (r.inherentConsequence || 3) : (r.residualConsequence || 3);

        return `
            <div onmouseenter="highlightHeatmapCell(${l}, ${c}, true)"
                 onmouseleave="highlightHeatmapCell(${l}, ${c}, false)"
                 class="bg-white rounded-xl border border-slate-200 hover:border-indigo-300 p-4 shadow-2xs transition-all space-y-2.5">
                <div class="flex items-start justify-between gap-3">
                    <div class="space-y-1 flex-1 min-w-0">
                        <div class="flex items-center gap-2 flex-wrap">
                            <span class="text-xs font-mono font-black text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">${r.displayId || r.id}</span>
                            <span class="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">${r.causeCategory || 'Delivery'}</span>
                            <button onclick="jumpToBlueprintBundle('${bundle.replace(/'/g, "\\'")}')" class="text-[11px] font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 px-2 py-0.5 rounded border border-purple-200 cursor-pointer">📘 ${bundle}</button>
                            ${r.driverTreeRef ? `<button onclick="jumpToDriverRef('${r.driverTreeRef}')" class="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-1.5 py-0.5 rounded border border-indigo-200 cursor-pointer">Ref ${r.driverTreeRef} ↗</button>` : ''}
                        </div>
                        <h4 onclick="openItemDetailModal('risk', '${r.id}')" class="text-sm font-bold text-slate-900 hover:text-indigo-700 cursor-pointer">${title}</h4>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                        <span class="text-xs font-mono px-2.5 py-1 rounded-lg border ${badgeClass}">Inh ${inhScore} → Res ${score}</span>
                        <button onclick="openItemDetailModal('risk', '${r.id}')" class="px-2.5 py-1 bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 text-xs font-bold rounded-lg border border-slate-200 cursor-pointer">Details ↗</button>
                    </div>
                </div>
                ${isExpanded ? `
                    <div class="pt-2 border-t border-slate-100 text-xs text-slate-600 space-y-1.5">
                        ${r.riskDescription ? `<p class="leading-relaxed">${r.riskDescription}</p>` : ''}
                        <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                            <span>👤 Owner: <strong class="text-slate-800">${owner}</strong></span>
                            <span>Status: <strong class="text-slate-800">${r.status || 'Active'}</strong></span>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');

    if (cardsContainer) cardsContainer.innerHTML = htmlCards;
}
