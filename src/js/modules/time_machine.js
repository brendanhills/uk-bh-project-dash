// =============================================================================
// Risk & Delivery Intelligence Platform — Time Machine & Historical Snapshots Module
// =============================================================================
import { appState, store, getLatestWeekKey, updateSystemTimeBadges } from '../state.js';
import { DOM_IDS, getRequiredElement } from '../dom_contract.js';

export function toggleTimeMachineModal() {
    const modal = document.getElementById(DOM_IDS.TIME_MACHINE_MODAL);
    if (!modal) return;
    const isHidden = modal.classList.contains('hidden');
    if (isHidden) {
        renderTimeMachineModalList();
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

export function closeTimeMachineModal() {
    const modal = document.getElementById(DOM_IDS.TIME_MACHINE_MODAL);
    if (modal) modal.classList.add('hidden');
}

export function renderTimeMachineModalList() {
    const container = getRequiredElement(DOM_IDS.TIME_MACHINE_SNAPSHOTS_LIST, 'renderTimeMachineModalList');
    if (!container) return;

    const snapshots = appState.TIME_MACHINE_SNAPSHOTS || {};
    const keys = Object.keys(snapshots).sort((a, b) => {
        const wnA = parseInt(String(a).replace(/\D/g, ''), 10) || 0;
        const wnB = parseInt(String(b).replace(/\D/g, ''), 10) || 0;
        return wnB - wnA;
    });

    const latestKey = getLatestWeekKey();
    let html = `
        <div onclick="returnToPresent(); closeTimeMachineModal();"
             class="p-3.5 rounded-xl border ${appState.activeTimeMachineWeek === 'present' ? 'bg-indigo-50 border-indigo-400 ring-2 ring-indigo-500/20' : 'bg-white border-slate-200 hover:border-indigo-300'} flex items-center justify-between cursor-pointer transition-all">
            <div>
                <div class="flex items-center gap-2">
                    <span class="text-xs font-black text-indigo-700 uppercase">Live Present Cycle (${latestKey.toUpperCase()})</span>
                    ${appState.activeTimeMachineWeek === 'present' ? '<span class="text-[10px] font-bold bg-indigo-600 text-white px-2 py-0.5 rounded-full">Active</span>' : ''}
                </div>
                <p class="text-xs text-slate-600 mt-0.5">${snapshots[latestKey]?.label || 'Current Active Reporting State'}</p>
            </div>
            <span class="text-xs font-bold text-indigo-600">Select →</span>
        </div>
    `;

    keys.forEach(wk => {
        const snap = snapshots[wk] || {};
        const isCurrent = appState.activeTimeMachineWeek === wk;
        html += `
            <div onclick="activateTimeMachine('${wk}'); closeTimeMachineModal();"
                 class="p-3.5 rounded-xl border ${isCurrent ? 'bg-amber-50 border-amber-400 ring-2 ring-amber-500/20' : 'bg-white border-slate-200 hover:border-amber-300'} flex items-center justify-between cursor-pointer transition-all">
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-mono font-bold text-slate-800 uppercase">${wk.toUpperCase()}</span>
                        <span class="text-xs font-bold text-slate-700">${snap.label || snap.week || wk}</span>
                        ${isCurrent ? '<span class="text-[10px] font-bold bg-amber-600 text-white px-2 py-0.5 rounded-full">Viewing</span>' : ''}
                    </div>
                    <p class="text-[11px] text-slate-500 mt-0.5">ATO Score: ${snap.atoGateScore ?? 78}% • Open Risks: ${snap.openRisksCount ?? (appState.LIVE_RISKS || []).length}</p>
                </div>
                <span class="text-xs font-bold text-amber-700">Inspect Snapshot →</span>
            </div>
        `;
    });

    container.innerHTML = html;
}

export function activateTimeMachine(weekKey) {
    if (!weekKey || weekKey === 'present') {
        returnToPresent();
        return;
    }
    appState.activeTimeMachineWeek = weekKey;
    store.set('activeTimeMachineWeek', weekKey);

    const banner = document.getElementById('timeMachineBanner');
    const bannerWeek = document.getElementById('timeMachineBannerWeek');
    const snap = appState.TIME_MACHINE_SNAPSHOTS[weekKey] || {};

    if (banner) banner.classList.remove('hidden');
    if (bannerWeek) bannerWeek.innerText = snap.label || snap.week || weekKey.toUpperCase();

    updateSystemTimeBadges();
    if (typeof window.renderExecBriefing === 'function') window.renderExecBriefing();
    if (typeof window.renderExecGapClosePlans === 'function') window.renderExecGapClosePlans();
    if (typeof window.updatePodcastAudioForWeek === 'function') window.updatePodcastAudioForWeek(weekKey);
    if (typeof window.renderRiskHeatmap === 'function') window.renderRiskHeatmap();
    if (typeof window.renderRiskExplorer === 'function') window.renderRiskExplorer();
}

export function returnToPresent() {
    appState.activeTimeMachineWeek = 'present';
    store.set('activeTimeMachineWeek', 'present');

    const banner = document.getElementById('timeMachineBanner');
    if (banner) banner.classList.add('hidden');

    updateSystemTimeBadges();
    if (typeof window.renderExecBriefing === 'function') window.renderExecBriefing();
    if (typeof window.renderExecGapClosePlans === 'function') window.renderExecGapClosePlans();
    if (typeof window.updatePodcastAudioForWeek === 'function') window.updatePodcastAudioForWeek('present');
    if (typeof window.renderRiskHeatmap === 'function') window.renderRiskHeatmap();
    if (typeof window.renderRiskExplorer === 'function') window.renderRiskExplorer();
}
