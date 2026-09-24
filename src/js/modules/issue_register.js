// =============================================================================
// Risk & Delivery Intelligence Platform — Issue Register & Executive Exports Module
// =============================================================================
import { appState } from '../state.js';

export function renderIssueTable() {
    const searchVal = (document.getElementById('issueSearchInput')?.value || '').toLowerCase().trim();
    const tbody = document.getElementById('issueTableBody');
    if (!tbody) return;

    const filtered = (appState.LIVE_ISSUES || []).filter(i => {
        if (!i) return false;
        if (!searchVal) return true;
        const matchText = [
            i.id,
            i.displayId,
            i.issueName,
            i.issueDescription,
            i.issueStatement,
            i.owner,
            i.issueOwner,
            i.driverTreeRef,
            i.severity,
            i.actionPlan,
            i.governanceNextSteps
        ].join(' ').toLowerCase();
        return matchText.includes(searchVal);
    });

    const countEl = document.getElementById('issueResultCount');
    if (countEl) countEl.innerText = `${filtered.length} issue${filtered.length === 1 ? '' : 's'}`;

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-6 text-center text-xs text-slate-400 italic">No active issues or escalations match your query.</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(i => {
        const title = i.issueName || i.issueDescription || i.issueStatement || i.title || 'Escalated Blocker';
        const owner = i.issueOwner || i.owner || 'Program Director';
        const sev = i.severity || 'High';
        const sevClass = sev === 'Critical' || sev === 'Extreme'
            ? 'bg-red-600 text-white'
            : (sev === 'High' ? 'bg-amber-500 text-white' : 'bg-yellow-100 text-yellow-900');

        return `
            <tr onclick="openItemDetailModal('issue', '${i.id}')" class="hover:bg-slate-50 cursor-pointer transition-colors border-b border-slate-100 text-xs">
                <td class="p-3 font-mono font-bold text-rose-700">${i.displayId || i.id}</td>
                <td class="p-3 font-bold text-slate-900">${title}</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${sevClass}">${sev}</span></td>
                <td class="p-3 text-slate-600">👤 ${owner}</td>
                <td class="p-3 font-mono text-slate-500">${i.targetDate || 'Immediate'}</td>
                <td class="p-3 text-right">
                    <button onclick="event.stopPropagation(); openItemDetailModal('issue', '${i.id}')" class="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold rounded border border-rose-200 cursor-pointer">Inspect ↗</button>
                </td>
            </tr>
        `;
    }).join('');
}

export function filterAndRenderIssues() {
    renderIssueTable();
}

export function renderLedger() {
    renderIssueTable();
}

export function exportCSV() {
    const risks = appState.LIVE_RISKS || [];
    const headers = ['ID', 'Title', 'Status', 'Category', 'InherentScore', 'ResidualScore', 'Owner', 'ContractBundle'];
    const rows = [headers.join(',')];
    risks.forEach(r => {
        if (!r) return;
        const vals = [
            r.displayId || r.id || '',
            `"${String(r.riskName || r.riskTitle || '').replace(/"/g, '""')}"`,
            r.status || 'Active',
            `"${String(r.causeCategory || '').replace(/"/g, '""')}"`,
            r.inherentRiskScore || '',
            r.residualRiskScore || '',
            `"${String(r.riskOwner || r.owner || '').replace(/"/g, '""')}"`,
            `"${String(r.contractBundle || '').replace(/"/g, '""')}"`
        ];
        rows.push(vals.join(','));
    });

    const csvContent = rows.join('\n');
    if (typeof Blob !== 'undefined' && typeof URL !== 'undefined' && URL.createObjectURL) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${appState.CURRENT_PROJECT || 'project'}_risk_register.csv`;
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    if (typeof window.showSyncToast === 'function') {
        window.showSyncToast('Exported Risk Register CSV', 'success');
    }
}

export function exportDeckPDF() {
    if (typeof window.print === 'function') {
        window.print();
    }
}

export function exportExecutiveDeck() {
    exportDeckPDF();
}
