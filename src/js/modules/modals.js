// =============================================================================
// Risk & Delivery Intelligence Platform — Item Detail & Risk Modals Module
// =============================================================================
import { appState } from '../state.js';

export function openRiskModal(riskId) {
    openItemDetailModal('risk', riskId);
}

export function openItemDetailModal(type, id) {
    const modal = document.getElementById('itemDetailModal');
    if (!modal) return;

    const isIssue = type === 'issue';
    const isGoogleRisk = type === 'google-risk';
    const list = isIssue
        ? (appState.LIVE_ISSUES || [])
        : (isGoogleRisk ? (appState.LIVE_TEAM_GOOGLE_RISKS || []) : (appState.LIVE_RISKS || []));

    const item = list.find(x => x && (String(x.id) === String(id) || String(x.displayId) === String(id)));
    if (!item) return;

    const headerTitle = item.riskName || item.riskTitle || item.issueName || item.issueDescription || item.riskDescription || item.title || 'Governance Item';
    const bundleName = item.contractBundle || item.blueprintBundle || 'Security Architecture & Zero Trust';
    const bundleMeta = (appState.BUNDLE_ANNEX_MAPPING && appState.BUNDLE_ANNEX_MAPPING[bundleName]) || {
        annex: 'Annex B.2 — Sovereign Cloud & ISM Controls',
        bundleDesc: 'Governs High-Assurance Cryptographic Controls, Cross-Domain CDS Gateways, and ASD Essential Eight Maturity Level 3 compliance.'
    };
    const mappedAnnex = bundleMeta.annex;
    const mappedBundleDesc = bundleMeta.bundleDesc;
    const notebookDocUrl = appState.CONFIG?.notebookLmUrl || 'https://notebooklm.google.com/';

    modal.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh] m-4">
            <div class="bg-slate-900 p-5 text-white flex justify-between items-center shrink-0">
                <div class="flex items-center gap-3">
                    <div class="p-2 bg-white/10 rounded-xl text-xl">${isIssue ? '⚠️' : (isGoogleRisk ? '🛡️' : '📋')}</div>
                    <div>
                        <div class="flex items-center gap-2 flex-wrap">
                            <span class="text-sm font-black font-mono px-2 py-0.5 bg-white/20 rounded">${item.displayId || item.id}</span>
                            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/30 text-emerald-200 border border-emerald-400/40">${item.status || 'Active'}</span>
                            ${isGoogleRisk ? '<span class="text-xs font-bold px-2 py-0.5 rounded bg-blue-600 text-white">Team Google</span>' : ''}
                            ${item.residualRiskScore ? `<span class="text-xs font-mono font-black px-2 py-0.5 rounded bg-indigo-600 text-white">Score: ${item.residualRiskScore}</span>` : ''}
                        </div>
                        <h2 class="text-base font-bold text-white mt-1 line-clamp-1">${headerTitle}</h2>
                    </div>
                </div>
                <button onclick="closeItemDetailModal()" class="text-white/80 hover:text-white p-1 rounded-lg text-lg cursor-pointer">✕</button>
            </div>

            <div class="p-6 overflow-y-auto space-y-4 text-xs">
                ${(item.riskDescription || item.issueStatement) ? `
                    <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs text-slate-700 space-y-1">
                        <span class="font-bold text-slate-500 uppercase text-[10px] block">Full Statement:</span>
                        <p class="leading-relaxed">${item.riskDescription || item.issueStatement}</p>
                    </div>
                ` : ''}

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div class="bg-slate-50/70 p-3 rounded-xl border border-slate-200 space-y-1">
                        <span class="font-bold text-slate-500 uppercase text-[10px] block">Root Cause / Trigger:</span>
                        <p class="text-slate-800 leading-relaxed">${item.causeDescription || item.impactDescription || 'N/A'}</p>
                    </div>
                    <div class="bg-emerald-50/50 p-3 rounded-xl border border-emerald-200 space-y-1">
                        <span class="font-bold text-emerald-800 uppercase text-[10px] block">Treatment Plan / Mitigation:</span>
                        <p class="text-slate-800 leading-relaxed">${item.treatmentPlan || item.actionPlan || item.governanceNextSteps || 'Under active governance remediation.'}</p>
                    </div>
                </div>

                <!-- Contract Blueprint Grounding Card -->
                <div class="bg-purple-50/70 border border-purple-200 rounded-xl p-4 space-y-2">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="text-sm">📘</span>
                            <strong class="text-xs font-bold text-purple-900">Contract Blueprint Traceability</strong>
                            <span class="text-[10px] font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded border border-purple-200 font-mono">${mappedAnnex}</span>
                        </div>
                        <a href="${notebookDocUrl}" target="_blank" rel="noopener noreferrer" class="text-xs font-bold text-purple-700 hover:text-purple-900 bg-white border border-purple-200 px-2.5 py-1 rounded-lg shadow-2xs flex items-center gap-1">
                            <span>Open in NotebookLM</span>
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                        </a>
                    </div>
                    <p class="text-xs text-purple-950/80 leading-relaxed">${mappedBundleDesc}</p>
                </div>

                <div class="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
                    <span>Lead Owner: <strong class="text-slate-800">👤 ${item.riskOwner || item.issueOwner || item.owner || 'Joint Team'}</strong></span>
                    <div class="flex items-center gap-3">
                        ${item.targetDate ? `<span>Target Date: <strong class="font-mono text-slate-800">${item.targetDate}</strong></span>` : ''}
                        <button onclick="closeItemDetailModal()" class="px-4 py-1.5 bg-slate-800 hover:bg-slate-900 text-white font-bold rounded-lg cursor-pointer">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    modal.classList.remove('hidden');
}

export function closeItemDetailModal() {
    const modal = document.getElementById('itemDetailModal');
    if (modal) modal.classList.add('hidden');
}
