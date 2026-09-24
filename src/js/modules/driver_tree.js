// =============================================================================
// Risk & Delivery Intelligence Platform — Driver Tree & ATO Gates Module
// =============================================================================
import { appState } from '../state.js';
import { DOM_IDS } from '../dom_contract.js';

export function setDriverTreeLevelFilter(level) {
    appState.currentDriverTreeLevel = level;
    ['all', 'L1', 'L2', 'L3'].forEach(lvl => {
        const btn = document.getElementById(`dtFilterBtn-${lvl}`);
        if (!btn) return;
        if (lvl === level) {
            btn.className = 'px-2.5 py-1 rounded text-xs font-bold bg-indigo-600 text-white shadow-2xs cursor-pointer transition-all';
        } else {
            btn.className = 'px-2.5 py-1 rounded text-xs font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer transition-all';
        }
    });
    renderDriverTree();
}

export function renderDriverTree() {
    const container = document.getElementById('driverTreeContainer');
    if (!container) return;

    const rawItems = (appState.DRIVER_TREE_ITEMS && appState.DRIVER_TREE_ITEMS.length > 0)
        ? appState.DRIVER_TREE_ITEMS
        : (appState.DRIVER_TREE || []);
    const items = Array.isArray(rawItems) ? rawItems : [];

    const filtered = items.filter(item => {
        if (!item) return false;
        if (appState.currentDriverTreeLevel !== 'all' && item.level && item.level !== appState.currentDriverTreeLevel) {
            return false;
        }
        return true;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">No Driver Tree nodes match the active filter criteria.</div>';
        return;
    }

    container.innerHTML = filtered.map(node => {
        const ref = node.ref || node.id || '1.1';
        const safeId = `driver-ref-${String(ref).replace(/[^a-zA-Z0-9_-]/g, '-')}`;
        const linkedRisks = (appState.LIVE_RISKS || []).filter(r => r && r.driverTreeRef === ref);
        const linkedIssues = (appState.LIVE_ISSUES || []).filter(i => i && i.driverTreeRef === ref);

        let ragClass = 'bg-emerald-100 text-emerald-800 border-emerald-300';
        if (node.status === 'RED' || node.status === 'At Risk') ragClass = 'bg-red-600 text-white font-bold';
        else if (node.status === 'AMBER' || node.status === 'In Progress') ragClass = 'bg-amber-500 text-white font-bold';

        return `
            <div id="${safeId}" class="bg-white rounded-xl border border-slate-200 hover:border-indigo-300 p-4 shadow-2xs transition-all space-y-2.5">
                <div class="flex flex-wrap items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-mono font-black text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">Ref ${ref}</span>
                        <span class="text-xs px-2 py-0.5 rounded border ${ragClass}">${node.status || 'AMBER'}</span>
                        <h4 class="text-sm font-bold text-slate-900">${node.name || node.title || node.deliverable || 'ATO Milestone Deliverable'}</h4>
                    </div>
                    <span class="text-xs text-slate-500">👤 <strong>${node.owner || 'Joint Delivery'}</strong></span>
                </div>
                ${node.notes ? `<p class="text-xs text-slate-600 leading-relaxed">${node.notes}</p>` : ''}
                <div class="flex flex-wrap items-center gap-2 pt-1">
                    ${linkedRisks.map(r => `
                        <button onclick="openItemDetailModal('risk', '${r.id}')" class="text-[11px] font-mono font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-2 py-0.5 rounded border border-indigo-200 cursor-pointer">
                            📋 ${r.displayId || r.id} (Score ${r.residualRiskScore || 15}) ↗
                        </button>
                    `).join('')}
                    ${linkedIssues.map(i => `
                        <button onclick="openItemDetailModal('issue', '${i.id}')" class="text-[11px] font-mono font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 px-2 py-0.5 rounded border border-rose-200 cursor-pointer">
                            ⚠️ ${i.displayId || i.id} ↗
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');
}

export function jumpToDriverRef(ref) {
    if (typeof window.switchMainTab === 'function') {
        window.switchMainTab('driver-tree');
    }
    renderDriverTree();
    const safeId = `driver-ref-${String(ref).replace(/[^a-zA-Z0-9_-]/g, '-')}`;
    const el = document.getElementById(safeId);
    if (el) {
        el.classList.add('ring-2', 'ring-indigo-600', 'bg-indigo-50/40');
        if (typeof el.scrollIntoView === 'function') {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

export function jumpToGapClose(ref) {
    if (typeof window.switchMainTab === 'function') {
        window.switchMainTab('exec-briefing');
    }
    const el = document.getElementById(DOM_IDS.EXEC_GAP_CLOSE_PLANS_LIST);
    if (el && typeof el.scrollIntoView === 'function') {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    if (ref && typeof window.showSyncToast === 'function') {
        window.showSyncToast(`Viewing Gap Close Plan for Ref ${ref}`, 'info');
    }
}

export function jumpToRiskExplorer(searchQuery) {
    if (typeof window.switchMainTab === 'function') {
        window.switchMainTab('joint-register');
    }
    const input = document.getElementById('riskSearchInput');
    if (input && searchQuery) {
        input.value = searchQuery;
    }
    if (typeof window.renderRiskExplorer === 'function') {
        window.renderRiskExplorer();
    }
}

export function filterByDriverTreeDeliverable(deliverableRef) {
    jumpToRiskExplorer(deliverableRef);
}
