// =============================================================================
// Risk & Delivery Intelligence Platform — Risk Heatmap Module
// =============================================================================
import { appState, store } from '../state.js';
import { DOM_IDS, getRequiredElement } from '../dom_contract.js';

export const MATRIX_SCORES_TABLE = {
    5: [9, 14, 18, 23, 25],
    4: [6, 11, 16, 20, 24],
    3: [4, 8, 13, 17, 22],
    2: [2, 5, 10, 15, 21],
    1: [1, 3, 7, 12, 19]
};

export const CONSEQUENCE_NAMES = ['', 'Minor', 'Moderate', 'Major', 'Critical', 'Catastrophic'];

export function setRiskRating(rating) {
    appState.currentMatrixRating = rating;
    store.set('matrixRating', rating);
    const btnInh = document.getElementById(DOM_IDS.R_BTN_INHERENT) || document.getElementById('btnInherent');
    const btnRes = document.getElementById(DOM_IDS.R_BTN_RESIDUAL) || document.getElementById('btnResidual');
    if (btnInh && btnRes) {
        if (rating === 'inherent') {
            btnInh.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white shadow-xs cursor-pointer';
            btnRes.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        } else {
            btnRes.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white shadow-xs cursor-pointer';
            btnInh.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        }
    }
    renderRiskHeatmap();
}

export function setRiskStatusFilter(status) {
    appState.currentMatrixStatus = status;
    store.set('matrixStatus', status);
    const btnOpen = document.getElementById(DOM_IDS.R_BTN_OPEN) || document.getElementById('btnStatusOpen');
    const btnAll = document.getElementById(DOM_IDS.R_BTN_ALL) || document.getElementById('btnStatusAll');
    if (btnOpen && btnAll) {
        if (status === 'open') {
            btnOpen.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white shadow-xs cursor-pointer';
            btnAll.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        } else {
            btnAll.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white shadow-xs cursor-pointer';
            btnOpen.className = 'px-3 py-1.5 rounded-lg hover:text-slate-900 cursor-pointer text-slate-600';
        }
    }
    const statusSelect = document.getElementById('filterStatusSelect') || document.getElementById('riskStatusSelect');
    if (statusSelect) {
        statusSelect.value = status === 'open' ? 'Active' : 'all';
    }
    renderRiskHeatmap();
    if (typeof window.renderRiskExplorer === 'function') {
        window.renderRiskExplorer();
    }
}

export function renderRiskHeatmap() {
    const grid = getRequiredElement(DOM_IDS.HEATMAP_GRID_CONTAINER, 'renderRiskHeatmap');
    if (!grid) return;

    const risks = (appState.LIVE_RISKS || []).filter(r => {
        if (!r) return false;
        if (appState.currentMatrixStatus === 'open') {
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
        const l = appState.currentMatrixRating === 'inherent' ? (r.inherentLikelihood || 3) : (r.residualLikelihood || 3);
        const c = appState.currentMatrixRating === 'inherent' ? (r.inherentConsequence || 3) : (r.residualConsequence || 3);
        const key = `${Math.min(5, Math.max(1, l))}-${Math.min(5, Math.max(1, c))}`;
        if (cellCounts[key]) cellCounts[key].push(r);
    });

    let html = `
        <div class="col-span-full flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 px-1">
            <span>Consequence (Y) ↓ / Likelihood (X) →</span>
            <span>Rare → Almost Certain</span>
        </div>
    `;
    for (let l = 5; l >= 1; l--) {
        for (let c = 1; c <= 5; c++) {
            const score = MATRIX_SCORES_TABLE[l][c - 1];
            const items = cellCounts[`${l}-${c}`] || [];
            const count = items.length;

            let bgClass = 'bg-emerald-50 border-emerald-200 text-emerald-900 hover:bg-emerald-100';
            if (score >= 18) bgClass = 'bg-red-50 border-red-300 text-red-950 hover:bg-red-100';
            else if (score >= 12) bgClass = 'bg-amber-50 border-amber-300 text-amber-950 hover:bg-amber-100';
            else if (score >= 6) bgClass = 'bg-yellow-50 border-yellow-300 text-yellow-900 hover:bg-yellow-100';

            const isSelected = appState.activeMatrixCellFilter &&
                appState.activeMatrixCellFilter.l === l &&
                appState.activeMatrixCellFilter.c === c;
            const ringClass = isSelected ? 'ring-2 ring-indigo-600 ring-offset-1 shadow-md scale-[1.02]' : '';

            html += `
                <div onclick="filterMatrixCell(${l}, ${c}, ${score})"
                     id="heatmap-cell-${l}-${c}"
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

export function filterMatrixCell(l, c, score) {
    if (appState.activeMatrixCellFilter && appState.activeMatrixCellFilter.l === l && appState.activeMatrixCellFilter.c === c) {
        clearActiveCellFilter();
        return;
    }
    appState.activeMatrixCellFilter = { l, c, score, ratingType: appState.currentMatrixRating };
    const banner = document.getElementById('activeCellFilterBanner');
    const textEl = document.getElementById('activeCellFilterText');
    if (banner && textEl) {
        banner.classList.remove('hidden');
        textEl.innerText = `L${l} × ${CONSEQUENCE_NAMES[c] || 'C' + c} (Score ${score}, ${appState.currentMatrixRating === 'inherent' ? 'Inherent' : 'Residual'})`;
    }
    renderRiskHeatmap();
    if (typeof window.renderRiskExplorer === 'function') {
        window.renderRiskExplorer();
    }
}

export function highlightHeatmapCell(l, c, shouldHighlight) {
    const cell = document.getElementById(`heatmap-cell-${l}-${c}`);
    if (!cell) return;
    if (shouldHighlight) {
        cell.classList.add('ring-2', 'ring-indigo-500', 'scale-105');
    } else {
        cell.classList.remove('ring-2', 'ring-indigo-500', 'scale-105');
    }
}

export function clearActiveCellFilter() {
    appState.activeMatrixCellFilter = null;
    const banner = document.getElementById('activeCellFilterBanner');
    if (banner) banner.classList.add('hidden');
    renderRiskHeatmap();
    if (typeof window.renderRiskExplorer === 'function') {
        window.renderRiskExplorer();
    }
}

export function renderMatrix(containerId = 'riskMatrixGrid') {
    if (typeof document !== 'undefined' && document.getElementById(containerId)) {
        renderRiskHeatmap();
    }
}
