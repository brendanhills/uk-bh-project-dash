// =============================================================================
// Risk & Delivery Intelligence Platform — Executive Briefing & Gap Close Plans Module
// =============================================================================
import { appState, getLatestWeekKey, evaluateTargetStaleness, updateSystemTimeBadges } from '../state.js';
import { updatePodcastAudioForWeek } from './podcast_player.js';
import { DOM_IDS, getRequiredElement } from '../dom_contract.js';

export function getGeminiParagraphsForWeek(weekKey, tone = 'board') {
    const activeKey = (!weekKey || weekKey === 'present') ? getLatestWeekKey() : weekKey;
    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};
    const paragraphsByTone = snap.geminiBriefing || {};

    if (paragraphsByTone[tone] && Array.isArray(paragraphsByTone[tone]) && paragraphsByTone[tone].length >= 2) {
        return paragraphsByTone[tone];
    }

    const cycleLabel = snap.label || snap.week || activeKey.toUpperCase();
    const openCount = (appState.LIVE_RISKS || []).filter(r => r && r.status !== 'Closed').length;
    const extremeCount = (appState.LIVE_RISKS || []).filter(r => r && r.status !== 'Closed' && (r.residualRiskScore || 0) >= 18).length;

    if (tone === 'technical') {
        return [
            `[${cycleLabel} — Technical Engineering Assessment] Sovereign landing zone controls and CDS cross-domain gateways remain on the critical path. Currently tracking ${openCount} active program risks (${extremeCount} rated Extreme ≥18), with primary technical bottlenecks concentrated in ISM Maturity Level 3 cryptographic attestation and hardware security module (HSM) key ceremonies.`,
            `Engineering remediation is focused on automating Terraform compliance guardrails, completing security architecture Annex B.2 artefacts ahead of the IRAP assessment window, and decoupling high-side identity federation from legacy perimeter firewall dependencies.`
        ];
    }

    return [
        `[${cycleLabel} — Board & Steering Committee Summary] Program delivery remains at AMBER-RED readiness heading into the upcoming Authority to Operate (ATO) gate. Across ${openCount} open Joint Register risks (${extremeCount} Extreme exposure), executive intervention is focused on closing inter-agency clearance bottlenecks and locking down sovereign supply chain commitments.`,
        `All Critical Gap Close Plans have designated SES/Director owners and weekly burn-down milestones. Immediate steering committee attention is requested on commercial risk-sharing thresholds (Annex D.1) and AGSVA NV2/PV vetting fast-track allocations.`
    ];
}

export function setAiTone(tone) {
    appState.currentAiTone = tone;
    renderExecBriefing();
}

export function copyGeminiParagraph(idx) {
    const paragraphs = getGeminiParagraphsForWeek(appState.activeTimeMachineWeek, appState.currentAiTone);
    const text = paragraphs[idx] || paragraphs.join('\n\n');
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
    }
}

export function copyExecSummaryNote(idx) {
    const el = document.getElementById(`execSummaryNoteText-${idx}`);
    if (el && navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(el.innerText || el.textContent || '');
    }
}

export function updateAtoGateKpi() {
    const activeKey = appState.activeTimeMachineWeek === 'present' ? getLatestWeekKey() : appState.activeTimeMachineWeek;
    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};
    const score = snap.atoGateScore ?? 78;
    const kAto = document.getElementById('kpiAto');
    if (kAto && !snap.kpis?.ato) kAto.innerText = `${score}%`;
}

export function renderExecBriefing() {
    updateSystemTimeBadges();
    updateAtoGateKpi();

    const activeKey = appState.activeTimeMachineWeek === 'present' ? getLatestWeekKey() : appState.activeTimeMachineWeek;
    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};
    const paragraphs = getGeminiParagraphsForWeek(activeKey, appState.currentAiTone);

    const summaryEl = document.getElementById('geminiSummaryText');
    if (summaryEl) {
        summaryEl.innerHTML = paragraphs.map(p => `<p class="leading-relaxed mb-3">${p}</p>`).join('');
    }

    const badgeEl = document.getElementById('execOverallBadge');
    if (badgeEl && snap.overallStatus) {
        badgeEl.innerText = snap.overallStatus;
    }
    const dateEl = document.getElementById('execCockpitDate');
    if (dateEl && snap) {
        dateEl.innerText = `${snap.week || snap.weekLabel || activeKey.toUpperCase()} (${snap.date || 'Current Cycle'})`;
    }
    if (snap.kpis) {
        const kCom = document.getElementById('kpiCommercial');
        if (kCom && snap.kpis.commercial) kCom.innerText = snap.kpis.commercial;
        const kIbr = document.getElementById('kpiIbr');
        if (kIbr && snap.kpis.ibr) kIbr.innerText = snap.kpis.ibr;
        const kAto = document.getElementById('kpiAto');
        if (kAto && snap.kpis.ato) kAto.innerText = snap.kpis.ato;
        const kEsc = document.getElementById('kpiEscalations');
        if (kEsc && snap.kpis.escalations) kEsc.innerText = snap.kpis.escalations;
    }

    const top3Container = getRequiredElement(DOM_IDS.TOP3_THINGS_CONTAINER, 'renderExecBriefing');
    if (top3Container) {
        const top3List = (Array.isArray(snap.top3) && snap.top3.length > 0)
            ? snap.top3
            : [];
        if (top3List.length === 0) {
            top3Container.innerHTML = `
                <div class="col-span-full p-4 rounded-xl border border-slate-200 bg-slate-50 text-center text-slate-500 text-xs">
                    No critical executive attention items flagged for this reporting cycle.
                </div>
            `;
        } else {
            top3Container.innerHTML = top3List.map((item, idx) => {
                const num = item.num || (idx + 1);
                const tag = item.tag || (num === 1 ? '🚨 Immediate Action' : (num === 2 ? '⚡ Schedule Alignment' : '🚀 Delivery Win'));
                const borderClass = num === 1 ? 'border-red-200/90 border-l-4 border-l-red-500' : (num === 2 ? 'border-amber-200/90 border-l-4 border-l-amber-500' : 'border-emerald-200/90 border-l-4 border-l-emerald-500');
                return `
                    <div class="bg-white border ${borderClass} rounded-xl p-3.5 flex flex-col justify-between space-y-2.5 hover:shadow-xs transition-all">
                        <div class="space-y-1.5">
                            <div class="flex flex-wrap items-center gap-2">
                                <span class="font-extrabold text-[#1f1f1f] text-xs sm:text-sm">${num}. ${item.title || 'Attention Item'}</span>
                                ${item.ref ? `<button onclick="jumpToDriverRef('${item.ref}')" class="font-mono text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200 px-2 py-0.5 rounded-md cursor-pointer transition-all shadow-2xs">Ref ${item.ref} ↗</button>` : ''}
                            </div>
                            <p class="text-xs text-[#444746] leading-relaxed font-normal">${item.action || item.impact || item.text || ''}</p>
                        </div>
                        <div class="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-lg text-[11px] font-bold text-slate-700">
                            ${tag}
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    const countsEl = document.getElementById('execSynthesisCounts');
    if (countsEl) {
        const rCount = (appState.LIVE_RISKS || []).length;
        const iCount = (appState.LIVE_ISSUES || []).length;
        const dCount = (appState.DRIVER_TREE || []).length;
        countsEl.innerHTML = `Synthesized from: <strong class="text-[#1f1f1f]">${rCount} Risks</strong>, <strong class="text-[#1f1f1f]">${iCount} Issues</strong>, <strong class="text-[#1f1f1f]">${dCount} Driver Gates</strong>`;
    }

    const slContainer = document.getElementById('sleeperOutlierContainer');
    if (slContainer && Array.isArray(snap.sleepers) && snap.sleepers.length > 0) {
        slContainer.innerHTML = snap.sleepers.map(sl => `
            <div class="p-2.5 bg-amber-50/80 border border-amber-200 rounded-lg text-xs">
                <strong class="text-amber-900">${sl.risk || sl.description || 'Sleeper Risk'}</strong>
                <p class="text-amber-800 mt-0.5">${sl.warning || ''}</p>
            </div>
        `).join('');
    }

    updatePodcastAudioForWeek(activeKey);
    renderExecGapClosePlans();
    renderTop5Risks();
    renderTop5Issues();
}

export function renderDiffBaselineSelector() {
    const select = document.getElementById(DOM_IDS.DIFF_BASELINE_SELECTOR);
    if (!select) return;
    const keys = Object.keys(appState.TIME_MACHINE_SNAPSHOTS || {}).sort((a, b) => {
        const wnA = parseInt(String(a).replace(/\D/g, ''), 10) || 0;
        const wnB = parseInt(String(b).replace(/\D/g, ''), 10) || 0;
        return wnB - wnA;
    });
    let opts = '<option value="auto">Previous Cycle (Auto)</option>';
    keys.forEach(k => {
        const snap = appState.TIME_MACHINE_SNAPSHOTS[k] || {};
        opts += `<option value="${k}" ${appState.selectedDiffBaseline === k ? 'selected' : ''}>${snap.label || k.toUpperCase()}</option>`;
    });
    select.innerHTML = opts;
}

export function setDiffBaseline(val) {
    appState.selectedDiffBaseline = val || 'auto';
    renderExecGapClosePlans();
}

export function toggleShowAllGapPlans() {
    appState.showAllGapPlans = !appState.showAllGapPlans;
    renderExecGapClosePlans();
}

export function toggleResolvedGapPlans() {
    appState.showResolvedGapPlans = !appState.showResolvedGapPlans;
    renderExecGapClosePlans();
}

export function renderExecGapClosePlans() {
    const container = getRequiredElement(DOM_IDS.EXEC_GAP_CLOSE_PLANS_LIST, 'renderExecGapClosePlans');
    if (!container) return;

    const sortedKeys = Object.keys(appState.TIME_MACHINE_SNAPSHOTS || {}).sort((a, b) => {
        const wnA = parseInt(String(a).replace(/\D/g, ''), 10) || 0;
        const wnB = parseInt(String(b).replace(/\D/g, ''), 10) || 0;
        return wnB - wnA;
    });

    const activeKey = appState.activeTimeMachineWeek === 'present' ? (sortedKeys[0] || 'w30') : appState.activeTimeMachineWeek;
    const activeIdx = Math.max(0, sortedKeys.indexOf(activeKey));
    const baseKey = (appState.selectedDiffBaseline && appState.selectedDiffBaseline !== 'auto')
        ? appState.selectedDiffBaseline
        : (sortedKeys[activeIdx + 1] || sortedKeys[activeIdx] || 'w29');

    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};
    const baseSnap = appState.TIME_MACHINE_SNAPSHOTS[baseKey] || {};
    const activeWeekName = snap.week || activeKey.toUpperCase();
    const baseWeekName = baseSnap.week || baseKey.toUpperCase();

    const plans = Array.isArray(snap.plans) ? snap.plans : [];
    const filteredPlans = plans.filter(p => {
        if (!appState.showResolvedGapPlans && p.status === 'BLUE') return false;
        return true;
    });

    const visiblePlans = appState.showAllGapPlans ? filteredPlans : filteredPlans.slice(0, 4);

    if (visiblePlans.length === 0) {
        container.innerHTML = `<div class="col-span-full p-4 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">All Gap Close Plans recorded for ${activeWeekName} (${plans.length} total).</div>`;
        return;
    }

    let html = `
        <div class="col-span-full mb-2 flex items-center justify-between text-xs bg-indigo-50/70 border border-indigo-200 rounded-xl px-3 py-2">
            <span class="font-bold text-indigo-950">⚡ Active Outstanding Gap Close Plans — Baseline Diff vs <strong>${baseWeekName}</strong></span>
            <span class="font-mono text-[10px] text-indigo-700 bg-white px-2 py-0.5 rounded border border-indigo-200">${activeWeekName} (${visiblePlans.length}/${filteredPlans.length})</span>
        </div>
    `;

    visiblePlans.forEach(p => {
        const staleness = evaluateTargetStaleness(p.target);
        const statusBadge = p.status === 'RED'
            ? 'bg-red-600 text-white'
            : (p.status === 'BLUE' ? 'bg-emerald-600 text-white' : 'bg-amber-500 text-white');
        const refClean = String(p.ref || '1.1').split(' ')[0];

        html += `
            <div id="gapPlan_${p.num}" class="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs hover:border-indigo-300 transition-all flex flex-col justify-between space-y-3">
                <div class="space-y-1.5">
                    <div class="flex items-center justify-between gap-2">
                        <div class="flex items-center gap-1.5">
                            <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase ${statusBadge}">${p.status || 'AMBER'}</span>
                            <span class="text-xs font-mono font-bold text-slate-700">Plan #${p.num || '1'}</span>
                            <button onclick="jumpToDriverRef('${refClean}')" class="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-1.5 py-0.5 rounded border border-indigo-200 cursor-pointer">Ref ${p.ref || refClean} ↗</button>
                        </div>
                        <span class="text-[10px] font-mono ${staleness.isOverdue ? 'text-red-600 font-bold' : 'text-slate-500'}">${p.target || 'TBD'}</span>
                    </div>
                    <h4 class="text-xs font-extrabold text-slate-900">${p.title || 'Mitigation Action Plan'}</h4>
                    <p class="text-xs text-slate-600 leading-relaxed">${p.plan || ''}</p>
                </div>
                <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                    <span>👤 <strong>${p.owner || 'Joint Team'}</strong></span>
                    <button onclick="jumpToDriverRef('${refClean}')" class="text-indigo-600 hover:text-indigo-800 font-bold cursor-pointer">Inspect Gate ↗</button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

export function renderTop5Risks() {
    const container = document.getElementById('execTopRisksFullList');
    if (!container) return;
    const sorted = [...(appState.LIVE_RISKS || [])]
        .filter(r => r && r.status !== 'Closed')
        .sort((a, b) => ((b.residualRiskScore || (b.residualLikelihood * b.residualConsequence) || 0) - (a.residualRiskScore || (a.residualLikelihood * a.residualConsequence) || 0)))
        .slice(0, 5);

    if (sorted.length === 0) {
        container.innerHTML = '<div class="p-4 text-center text-slate-400 text-xs italic bg-slate-50 rounded-xl border border-slate-200">No active risks recorded in current reporting cycle.</div>';
        return;
    }

    container.innerHTML = sorted.map(r => {
        const score = r.residualRiskScore || (r.residualLikelihood * r.residualConsequence) || 0;
        let scoreBadgeClass = 'bg-emerald-100 text-emerald-800 border-emerald-300';
        if (score >= 18) scoreBadgeClass = 'bg-red-600 text-white font-extrabold shadow-2xs';
        else if (score >= 12) scoreBadgeClass = 'bg-amber-500 text-white font-extrabold shadow-2xs';
        else if (score >= 6) scoreBadgeClass = 'bg-yellow-100 text-yellow-900 border-yellow-300';

        const title = r.riskName || r.riskTitle || r.riskDescription || r.title || 'Risk Exposure';
        const owner = r.riskOwner || r.owner || 'Joint Team';

        return `
            <div onclick="openItemDetailModal('risk', '${r.id}')" class="p-3 bg-slate-50 hover:bg-indigo-50/60 border border-slate-200 hover:border-indigo-300 rounded-xl flex items-center justify-between gap-3 cursor-pointer transition-all group">
                <div class="space-y-0.5 flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-mono font-black text-indigo-700 bg-white px-2 py-0.5 rounded border border-indigo-200">${r.displayId || r.id}</span>
                        <span class="text-xs font-medium text-slate-500 truncate">${r.causeCategory || 'Platform'}</span>
                        ${r.driverTreeRef ? `<button onclick="event.stopPropagation(); jumpToDriverRef('${r.driverTreeRef}')" class="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-1.5 py-0.2 rounded border border-indigo-200">Ref ${r.driverTreeRef} ↗</button>` : ''}
                    </div>
                    <h4 class="text-xs font-bold text-slate-800 group-hover:text-indigo-700 transition-colors truncate">${title}</h4>
                </div>
                <div class="text-right shrink-0 flex items-center gap-3">
                    <div>
                        <span class="text-xs font-mono font-bold px-2 py-0.5 rounded border ${scoreBadgeClass}">Score: ${score}</span>
                        <span class="text-[10px] text-slate-400 block mt-0.5">👤 ${owner}</span>
                    </div>
                    <button onclick="event.stopPropagation(); openItemDetailModal('risk', '${r.id}')" class="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs rounded-lg border border-indigo-200 cursor-pointer transition-all shadow-2xs">
                        <span>Inspect ↗</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

export function renderTop5Issues() {
    const container = document.getElementById('execTopIssuesFullList');
    if (!container) return;
    const sorted = [...(appState.LIVE_ISSUES || [])]
        .filter(i => i && i.status !== 'Closed' && i.status !== 'Resolved')
        .slice(0, 5);

    if (sorted.length === 0) {
        container.innerHTML = '<div class="p-4 text-center text-slate-400 text-xs italic bg-slate-50 rounded-xl border border-slate-200">No active escalations or blockers recorded.</div>';
        return;
    }

    container.innerHTML = sorted.map(i => {
        const title = i.issueName || i.issueDescription || i.issueStatement || i.title || 'Escalated Blocker';
        const owner = i.issueOwner || i.owner || 'Program Director';
        return `
            <div onclick="openItemDetailModal('issue', '${i.id}')" class="p-3 bg-slate-50 hover:bg-rose-50/60 border border-slate-200 hover:border-rose-300 rounded-xl flex items-center justify-between gap-3 cursor-pointer transition-all group">
                <div class="space-y-0.5 flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-mono font-black text-rose-700 bg-white px-2 py-0.5 rounded border border-rose-200">${i.displayId || i.id}</span>
                        <span class="text-xs font-bold text-rose-600">${i.severity || 'High'}</span>
                    </div>
                    <h4 class="text-xs font-bold text-slate-800 group-hover:text-rose-700 transition-colors truncate">${title}</h4>
                </div>
                <div class="text-right shrink-0 flex items-center gap-3">
                    <span class="text-[10px] text-slate-500">👤 ${owner}</span>
                    <button onclick="event.stopPropagation(); openItemDetailModal('issue', '${i.id}')" class="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs rounded-lg border border-rose-200 cursor-pointer transition-all shadow-2xs">
                        <span>Inspect ↗</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}
