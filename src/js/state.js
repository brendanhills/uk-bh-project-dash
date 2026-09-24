// =============================================================================
// Risk & Delivery Intelligence Platform — Centralized Runtime State & Time Utils
// =============================================================================

export const appState = {
    CURRENT_PROJECT: 'sample',
    CONFIG: null,
    NOTEBOOK_CATALOG: null,
    BUNDLE_ANNEX_MAPPING: {
        'Security Architecture & Zero Trust': {
            annex: 'Annex B.1 — Clinical Data Protection & HIPAA/My Health Record Controls',
            bundleDesc: 'Governs High-Assurance Health Record Cryptographic Controls, FHIR Security Gateways, and Patient Data Sovereignty compliance.'
        },
        'Program Delivery & Supply Chain': {
            annex: 'Annex A.1 — Integrated Clinical Rollout Schedule (ICRS)',
            bundleDesc: 'Tracks Critical Path Hospital Go-Lives, Clinical Workstation Hardware Procurement, and Multi-Vendor EHR Integration Dependencies.'
        },
        'Workforce & Clearances': {
            annex: 'Annex C.2 — Clinical Informatics Workforce & FHIR Integration Team',
            bundleDesc: 'Monitors Clinical Informatics Specialists, Hospital Onboarding Timelines, and Digital Health Operations Staffing.'
        },
        'Commercial & Governance': {
            annex: 'Annex D.1 — Healthcare Service Level Agreements (SLA) & Data Custodianship',
            bundleDesc: 'Addresses Clinical Availability Guarantees, SLA Penalty Thresholds, and Regional Health Network Data Sharing MOUs.'
        }
    },
    LIVE_RISKS: [],
    LIVE_TEAM_GOOGLE_RISKS: [],
    LIVE_ISSUES: [],
    TIME_MACHINE_SNAPSHOTS: {},
    DRIVER_TREE: [],
    DRIVER_TREE_ITEMS: [],
    DRIVE_REPORTS: [],
    currentMatrixRating: 'inherent',
    currentMatrixStatus: 'open',
    teamGoogleMatrixRating: 'inherent',
    teamGoogleMatrixStatus: 'open',
    teamGoogleActiveMatrixCellFilter: null,
    trendsGranularity: 'weekly',
    currentDriverTreeLevel: 'all',
    activeTimeMachineWeek: 'present',
    showAllGapPlans: false,
    showResolvedGapPlans: false,
    selectedDiffBaseline: 'auto',
    activeMatrixCellFilter: null,
    currentQuickFilter: 'all',
    explorerViewMode: 'detailed',
    expandedRiskIds: new Set(),
    expandedCardIds: new Set(),
    currentAiTone: 'board',
    isPodcastPlaying: false,
    podcastPlaybackSpeed: 1.0,
    PODCAST_AUDIO_CACHE: {},
    activeScoreBandFilter: null,
    podcastAnimationInterval: null
};

export const store = {
    get: (key) => (key ? appState[key] : appState),
    set: (keyOrObj, val) => {
        if (typeof keyOrObj === 'string') appState[keyOrObj] = val;
        else if (keyOrObj && typeof keyOrObj === 'object') Object.assign(appState, keyOrObj);
    }
};

if (typeof window !== 'undefined') {
    for (const key of Object.keys(appState)) {
        if (!(key in window)) {
            Object.defineProperty(window, key, {
                get: () => appState[key],
                set: (val) => { appState[key] = val; },
                configurable: true
            });
        }
    }
    window.BUNDLE_ANNEX_MAPPING = appState.BUNDLE_ANNEX_MAPPING;
}

export function cleanField(val, fallback = '') {
    if (val === null || val === undefined) return fallback;
    const str = String(val).trim();
    return (!str || ['-', 'n/a', 'none', 'null'].includes(str.toLowerCase())) ? fallback : str;
}

export function getLatestWeekKey() {
    const keys = Object.keys(appState.TIME_MACHINE_SNAPSHOTS || {});
    if (keys.length === 0) return 'w30';
    return keys.sort((a, b) => (parseInt(b.replace(/\D/g, ''), 10) || 0) - (parseInt(a.replace(/\D/g, ''), 10) || 0))[0];
}

export function getSystemTimeContext() {
    const now = new Date();
    const formattedDate = now.toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' });
    const latestKey = getLatestWeekKey();
    const activeSnap = appState.activeTimeMachineWeek === 'present'
        ? (appState.TIME_MACHINE_SNAPSHOTS[latestKey] || {})
        : (appState.TIME_MACHINE_SNAPSHOTS[appState.activeTimeMachineWeek] || {});
    return {
        now,
        formattedDate,
        latestKey,
        activeReportingCycle: activeSnap.label || activeSnap.week || 'W30 — Present Cycle',
        isHistorical: appState.activeTimeMachineWeek !== 'present'
    };
}

export function evaluateTargetStaleness(targetStr) {
    if (!targetStr) return { isOverdue: false, isDueSoon: false, daysDelta: null, label: '' };
    const clean = String(targetStr).trim();
    const parsed = new Date(clean);
    if (isNaN(parsed.getTime())) return { isOverdue: false, isDueSoon: false, daysDelta: null, label: clean };
    const daysDelta = Math.ceil((parsed.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    return { isOverdue: daysDelta < 0, isDueSoon: daysDelta >= 0 && daysDelta <= 14, daysDelta, label: clean };
}

export function updateSystemTimeBadges() {
    const ctx = getSystemTimeContext();
    const dateEl = document.getElementById('execCockpitDate');
    if (dateEl) {
        dateEl.innerText = `${ctx.activeReportingCycle} (${ctx.formattedDate})`;
    }
}
