// =============================================================================
// Risk & Delivery Intelligence Platform — Team Google Internal Risks Module
// =============================================================================
import { appState, store } from '../state.js';
import { MATRIX_SCORES_TABLE, CONSEQUENCE_NAMES } from './risk_heatmap.js';

export function setTeamGoogleRating(rating) {
    appState.teamGoogleMatrixRating = rating;
    store.set('teamGoogleMatrixRating', rating);
    const btnInh = document.getElementById('tgBtnInherent') || document.getElementById('btnTeamGoogleInherent');
    const btnRes = document.getElementById('tgBtnResidual') || document.getElementById('btnTeamGoogleResidual');
    if (btnInh && btnRes) {
        if (rating === 'inherent') {
            btnInh.className = 'px-3 py-1.5 rounded-lg bg-white text-blue-700 shadow-xs cursor-pointer font-bold';
            btnRes.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        } else {
            btnRes.className = 'px-3 py-1.5 rounded-lg bg-white text-blue-700 shadow-xs cursor-pointer font-bold';
            btnInh.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        }
    }
    renderTeamGoogleHeatmap();
    renderTeamGoogleRiskExplorer();
}

export function setTeamGoogleStatusFilter(status) {
    appState.teamGoogleMatrixStatus = status;
    store.set('teamGoogleMatrixStatus', status);
    const btnOpen = document.getElementById('tgBtnOpen') || document.getElementById('btnTeamGoogleStatusOpen');
    const btnAll = document.getElementById('tgBtnAll') || document.getElementById('btnTeamGoogleStatusAll');
    if (btnOpen && btnAll) {
        if (status === 'open') {
            btnOpen.className = 'px-3 py-1.5 rounded-lg bg-blue-600 text-white shadow-xs cursor-pointer';
            btnAll.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        } else {
            btnAll.className = 'px-3 py-1.5 rounded-lg bg-blue-600 text-white shadow-xs cursor-pointer';
            btnOpen.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        }
    }
    renderTeamGoogleHeatmap();
    renderTeamGoogleRiskExplorer();
}

export function renderTeamGoogleHeatmap() {
    const grid = document.getElementById('matrixGridTeamGoogle');
    if (!grid) return;

    const risks = (appState.LIVE_TEAM_GOOGLE_RISKS || []).filter(r => {
        if (!r) return false;
        if (appState.teamGoogleMatrixStatus === 'open') {
            return r.status !== 'Closed' && r.status !== 'Resolved';
        }
        return true;
    });

    const cellCounts = {};
    for (let l = 1; l <= 5; l++) {
        for (let c = 1; c <= 5; c++) {
            cellCounts[`${l}-${c}`] = [];
        }
    }

    risks.forEach(r => {
        const l = appState.teamGoogleMatrixRating === 'inherent' ? (r.inherentLikelihood || 3) : (r.residualLikelihood || 3);
        const c = appState.teamGoogleMatrixRating === 'inherent' ? (r.inherentConsequence || 3) : (r.residualConsequence || 3);
        const key = `${Math.min(5, Math.max(1, l))}-${Math.min(5, Math.max(1, c))}`;
        if (cellCounts[key]) cellCounts[key].push(r);
    });

    let html = '';
    for (let l = 5; l >= 1; l--) {
        for (let c = 1; c <= 5; c++) {
            const score = MATRIX_SCORES_TABLE[l][c - 1];
            const items = cellCounts[`${l}-${c}`] || [];
            const count = items.length;

            let bgClass = 'bg-emerald-50 border-emerald-200 text-emerald-900 hover:bg-emerald-100';
            if (score >= 18) bgClass = 'bg-red-50 border-red-300 text-red-950 hover:bg-red-100';
            else if (score >= 12) bgClass = 'bg-amber-50 border-amber-300 text-amber-950 hover:bg-amber-100';
            else if (score >= 6) bgClass = 'bg-yellow-50 border-yellow-300 text-yellow-900 hover:bg-yellow-100';

            const isSelected = appState.teamGoogleActiveMatrixCellFilter &&
                appState.teamGoogleActiveMatrixCellFilter.l === l &&
                appState.teamGoogleActiveMatrixCellFilter.c === c;
            const ringClass = isSelected ? 'ring-2 ring-blue-600 ring-offset-1 shadow-md scale-[1.02]' : '';

            html += `
                <div onclick="filterTeamGoogleMatrixCell(${l}, ${c}, ${score})"
                     id="tg-heatmap-cell-${l}-${c}"
                     class="p-2 rounded-xl border ${bgClass} ${ringClass} flex flex-col justify-between min-h-[64px] cursor-pointer transition-all select-none">
                    <div class="flex justify-between items-center text-[10px] font-mono opacity-75">
                        <span>L${l}×C${c}</span>
                        <span class="font-bold">#${score}</span>
                    </div>
                    <div class="text-center my-1">
                        <span class="text-lg font-black ${count > 0 ? '' : 'opacity-25'}">${count}</span>
                    </div>
                </div>
            `;
        }
    }
    grid.innerHTML = html;
}

export function filterTeamGoogleMatrixCell(l, c, score) {
    if (appState.teamGoogleActiveMatrixCellFilter &&
        appState.teamGoogleActiveMatrixCellFilter.l === l &&
        appState.teamGoogleActiveMatrixCellFilter.c === c) {
        clearTeamGoogleActiveCellFilter();
        return;
    }
    appState.teamGoogleActiveMatrixCellFilter = { l, c, score, ratingType: appState.teamGoogleMatrixRating };
    const banner = document.getElementById('teamGoogleMatrixFilterNotice');
    const textEl = document.getElementById('teamGoogleMatrixFilterText');
    if (banner && textEl) {
        banner.classList.remove('hidden');
        textEl.innerText = `L${l} × ${CONSEQUENCE_NAMES[c] || 'C' + c} (Score ${score})`;
    }
    renderTeamGoogleHeatmap();
    renderTeamGoogleRiskExplorer();
}

export function clearTeamGoogleActiveCellFilter() {
    appState.teamGoogleActiveMatrixCellFilter = null;
    const banner = document.getElementById('teamGoogleMatrixFilterNotice');
    if (banner) banner.classList.add('hidden');
    renderTeamGoogleHeatmap();
    renderTeamGoogleRiskExplorer();
}

export function clearTeamGoogleMatrixCellFilter() {
    clearTeamGoogleActiveCellFilter();
}

export function highlightTeamGoogleHeatmapCell(l, c, shouldHighlight) {
    const cell = document.getElementById(`tg-heatmap-cell-${l}-${c}`);
    if (!cell) return;
    if (shouldHighlight) {
        cell.classList.add('ring-2', 'ring-blue-500', 'scale-105');
    } else {
        cell.classList.remove('ring-2', 'ring-blue-500', 'scale-105');
    }
}

export function renderTeamGoogleRiskExplorer() {
    const container = document.getElementById('teamGoogleRiskListContainer');
    if (!container) return;

    const searchVal = (document.getElementById('teamGoogleRiskSearchInput')?.value || '').toLowerCase().trim();
    const catVal = document.getElementById('teamGoogleRiskCategoryFilter')?.value || 'all';

    const filtered = (appState.LIVE_TEAM_GOOGLE_RISKS || []).filter(r => {
        if (!r) return false;
        if (appState.teamGoogleMatrixStatus === 'open' && (r.status === 'Closed' || r.status === 'Resolved')) return false;
        if (catVal !== 'all' && r.causeCategory !== catVal) return false;

        if (appState.teamGoogleActiveMatrixCellFilter) {
            const { l, c, ratingType } = appState.teamGoogleActiveMatrixCellFilter;
            const rl = ratingType === 'inherent' ? (r.inherentLikelihood || 3) : (r.residualLikelihood || 3);
            const rc = ratingType === 'inherent' ? (r.inherentConsequence || 3) : (r.residualConsequence || 3);
            if (rl !== l || rc !== c) return false;
        }

        if (searchVal) {
            const haystack = [
                r.id,
                r.displayId,
                r.riskName,
                r.riskTitle,
                r.riskDescription,
                r.causeCategory,
                r.riskOwner,
                r.owner,
                r.treatmentPlan
            ].join(' ').toLowerCase();
            if (!haystack.includes(searchVal)) return false;
        }
        return true;
    });

    const countEl = document.getElementById('teamGoogleExplorerCount');
    if (countEl) countEl.innerText = `${filtered.length} risk${filtered.length === 1 ? '' : 's'}`;

    if (filtered.length === 0) {
        container.innerHTML = '<div class="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">No Team Google internal risks match the current filters.</div>';
        return;
    }

    container.innerHTML = filtered.map(r => {
        const score = r.residualRiskScore || (r.residualLikelihood * r.residualConsequence) || 0;
        const title = r.riskName || r.riskTitle || r.riskDescription || r.title || 'Internal Google Risk';
        const owner = r.riskOwner || r.owner || 'Google Cloud Delivery';
        const l = appState.teamGoogleMatrixRating === 'inherent' ? (r.inherentLikelihood || 3) : (r.residualLikelihood || 3);
        const c = appState.teamGoogleMatrixRating === 'inherent' ? (r.inherentConsequence || 3) : (r.residualConsequence || 3);

        return `
            <div onmouseenter="highlightTeamGoogleHeatmapCell(${l}, ${c}, true)"
                 onmouseleave="highlightTeamGoogleHeatmapCell(${l}, ${c}, false)"
                 onclick="openItemDetailModal('google-risk', '${r.id}')"
                 class="bg-white rounded-xl border border-slate-200 hover:border-blue-300 p-4 shadow-2xs cursor-pointer transition-all space-y-2">
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-mono font-black text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">${r.displayId || r.id}</span>
                        <span class="text-xs font-medium text-slate-500">${r.causeCategory || 'Engineering'}</span>
                    </div>
                    <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">Score: ${score}</span>
                </div>
                <h4 class="text-sm font-bold text-slate-900">${title}</h4>
                <div class="text-[11px] text-slate-500 flex justify-between">
                    <span>👤 ${owner}</span>
                    <span>Status: <strong>${r.status || 'Active'}</strong></span>
                </div>
            </div>
        `;
    }).join('');
}
