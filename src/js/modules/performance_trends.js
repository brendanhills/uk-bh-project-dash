// =============================================================================
// Risk & Delivery Intelligence Platform — Performance Trends & Timeline Analytics Module
// =============================================================================
import { appState } from '../state.js';

export function setTrendsGranularity(granularity) {
    appState.trendsGranularity = granularity;
    ['weekly', 'monthly'].forEach(g => {
        const btn = document.getElementById(`trendsGranBtn-${g}`);
        if (!btn) return;
        if (g === granularity) {
            btn.className = 'px-2.5 py-1 rounded text-xs font-bold bg-indigo-600 text-white shadow-2xs cursor-pointer transition-all';
        } else {
            btn.className = 'px-2.5 py-1 rounded text-xs font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer transition-all';
        }
    });
    renderTrendsCharts();
}

export function computeTimelineMetrics() {
    const snapshots = appState.TIME_MACHINE_SNAPSHOTS || {};
    const sortedKeys = Object.keys(snapshots).sort((a, b) => {
        const wnA = parseInt(String(a).replace(/\D/g, ''), 10) || 0;
        const wnB = parseInt(String(b).replace(/\D/g, ''), 10) || 0;
        return wnA - wnB;
    });

    return sortedKeys.map(k => {
        const s = snapshots[k] || {};
        return {
            weekKey: k,
            label: s.week || s.label || k.toUpperCase(),
            atoScore: s.atoGateScore ?? 78,
            openRisks: s.openRisksCount ?? (appState.LIVE_RISKS || []).length,
            extremeRisks: s.extremeRisksCount ?? 2
        };
    });
}

let trendsChartBurndown = null;
let trendsChartBacklog = null;

export function renderTrendsCharts() {
    const canvasBurndown = document.getElementById('chartBurndownTimeline');
    const canvasBacklog = document.getElementById('chartBacklogTimeline');
    if (!canvasBurndown && !canvasBacklog) return;

    if (typeof Chart === 'undefined') return;

    const metrics = computeTimelineMetrics();
    if (!metrics || metrics.length === 0) return;

    const labels = metrics.map(m => m.label);

    if (canvasBurndown) {
        if (trendsChartBurndown) trendsChartBurndown.destroy();
        trendsChartBurndown = new Chart(canvasBurndown, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'ATO Gate Score (%)',
                        data: metrics.map(m => m.atoScore),
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { min: 0, max: 100 }
                }
            }
        });
    }

    if (canvasBacklog) {
        if (trendsChartBacklog) trendsChartBacklog.destroy();
        trendsChartBacklog = new Chart(canvasBacklog, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Open Risks',
                        data: metrics.map(m => m.openRisks),
                        backgroundColor: '#6366f1',
                        borderRadius: 4
                    },
                    {
                        label: 'Extreme Risks',
                        data: metrics.map(m => m.extremeRisks),
                        backgroundColor: '#ef4444',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

export function openTimelineDrilldownModal(weekKey) {
    const modal = document.getElementById('timelineDrilldownModal');
    if (!modal) return;
    const snap = (appState.TIME_MACHINE_SNAPSHOTS || {})[weekKey] || {};
    const titleEl = document.getElementById('drilldownModalTitle');
    if (titleEl) titleEl.innerText = snap.label || snap.week || weekKey.toUpperCase();
    modal.classList.remove('hidden');
}

export function closeTimelineDrilldownModal() {
    const modal = document.getElementById('timelineDrilldownModal');
    if (modal) modal.classList.add('hidden');
}
