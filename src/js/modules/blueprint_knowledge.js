// =============================================================================
// Risk & Delivery Intelligence Platform — Blueprint & Knowledge Grounding Module
// =============================================================================
import { appState } from '../state.js';
import { DOM_IDS, getRequiredElement } from '../dom_contract.js';

export function renderBlueprintKnowledge() {
    renderBlueprintBundleCards();
    renderResearchDocsCards();
}

export function renderBlueprintBundleCards() {
    const container = getRequiredElement(DOM_IDS.BLUEPRINT_BUNDLES_CONTAINER, 'renderBlueprintBundleCards');
    if (!container) return;

    const mapping = appState.BUNDLE_ANNEX_MAPPING || {};
    const risks = appState.LIVE_RISKS || [];

    container.innerHTML = Object.entries(mapping).map(([bundleName, meta]) => {
        const matchingRisks = risks.filter(r =>
            r && (r.contractBundle === bundleName || r.blueprintBundle === bundleName) && r.status !== 'Closed'
        );
        const count = matchingRisks.length;
        const safeBundle = bundleName.replace(/'/g, "\\'");

        return `
            <div onclick="filterRiskExplorerByBundle('${safeBundle}')"
                 class="bg-white rounded-2xl border border-slate-200 hover:border-purple-400 p-5 shadow-2xs cursor-pointer transition-all flex flex-col justify-between space-y-3 group">
                <div class="space-y-1.5">
                    <div class="flex items-center justify-between gap-2">
                        <span class="text-[11px] font-mono font-bold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded border border-purple-200">${meta.annex}</span>
                        <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 group-hover:bg-purple-600 group-hover:text-white transition-all">${count} Active Risk${count === 1 ? '' : 's'}</span>
                    </div>
                    <h3 class="text-sm font-black text-slate-900 group-hover:text-purple-700 transition-colors">📘 ${bundleName}</h3>
                    <p class="text-xs text-slate-600 leading-relaxed">${meta.bundleDesc}</p>
                </div>
                <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-purple-700">
                    <span>Filter Joint Register by Bundle</span>
                    <span>Inspect Risks →</span>
                </div>
            </div>
        `;
    }).join('');
}

export function renderResearchDocsCards() {
    const container = getRequiredElement(DOM_IDS.RESEARCH_DOCS_CONTAINER, 'renderResearchDocsCards');
    if (!container) return;

    const catalog = appState.NOTEBOOK_CATALOG || {};
    const sources = Array.isArray(catalog.sources) ? catalog.sources : [
        {
            title: 'Contract Blueprint Annex B.2 — Sovereign Cloud & ISM Controls',
            type: 'Contract Annex',
            updated: '2026-09-15',
            summary: 'High-Assurance Cryptographic Controls, Cross-Domain CDS Gateways, and ASD Essential Eight Maturity Level 3 compliance requirements.'
        },
        {
            title: 'Integrated Master Schedule (IMS) & Gate 3 Readiness Criteria',
            type: 'Governance Baseline',
            updated: '2026-09-18',
            summary: 'Milestone verification gates, critical path procurement dependencies, and ATO compliance evidence matrix.'
        }
    ];

    container.innerHTML = sources.map(src => `
        <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-2">
            <div class="flex items-center justify-between text-[11px]">
                <span class="font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">${src.type || 'Grounded Source'}</span>
                <span class="font-mono text-slate-400">${src.updated || 'Synced'}</span>
            </div>
            <h4 class="text-xs font-extrabold text-slate-900">${src.title || src.name || 'Grounded Document'}</h4>
            <p class="text-xs text-slate-600 leading-relaxed">${src.summary || src.description || 'Verified NotebookLM source artefact.'}</p>
        </div>
    `).join('');
}

export function filterRiskExplorerByBundle(bundleName) {
    const bundleSelect = getRequiredElement(DOM_IDS.FILTER_BUNDLE_SELECT, 'filterRiskExplorerByBundle');
    if (bundleSelect) {
        bundleSelect.value = bundleName;
    }
    if (typeof window.switchMainTab === 'function') {
        window.switchMainTab('joint-register');
    }
    if (typeof window.renderRiskExplorer === 'function') {
        window.renderRiskExplorer();
    }
}

export function jumpToBlueprintBundle(bundleName) {
    if (typeof window.switchMainTab === 'function') {
        window.switchMainTab('blueprint-knowledge');
    }
    renderBlueprintKnowledge();
    const el = document.getElementById(DOM_IDS.BLUEPRINT_BUNDLES_CONTAINER);
    if (el && typeof el.scrollIntoView === 'function') {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    if (bundleName && typeof window.showSyncToast === 'function') {
        window.showSyncToast(`Viewing Contract Blueprint: ${bundleName}`, 'info');
    }
}
