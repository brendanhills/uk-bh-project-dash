// =============================================================================
// Risk & Delivery Intelligence Platform — DOM Contract & Fail-Fast Accessors
// Google Standards Compliant (go/totw/136, go/js-practices)
// =============================================================================

export const DOM_IDS = {
    // Executive Briefing
    TOP3_THINGS_CONTAINER: 'top3ThingsContainer',
    GEMINI_SUMMARY_TEXT: 'geminiSummaryText',
    EXEC_OVERALL_BADGE: 'execOverallBadge',
    EXEC_COCKPIT_DATE: 'execCockpitDate',
    EXEC_SYNTHESIS_COUNTS: 'execSynthesisCounts',
    DIFF_BASELINE_SELECTOR: 'diffBaselineSelector',
    EXEC_GAP_CLOSE_PLANS_LIST: 'execGapClosePlansList',
    EXEC_TOP_RISKS_FULL_LIST: 'execTopRisksFullList',

    // 5x5 Heatmap Matrix
    HEATMAP_GRID_CONTAINER: 'heatmapGridContainer',
    ACTIVE_CELL_FILTER_BANNER: 'activeCellFilterBanner',
    ACTIVE_CELL_FILTER_TEXT: 'activeCellFilterText',
    R_BTN_INHERENT: 'rBtnInherent',
    R_BTN_RESIDUAL: 'rBtnResidual',
    R_BTN_OPEN: 'rBtnOpen',
    R_BTN_ALL: 'rBtnAll',

    // Team Google Internal Heatmap
    MATRIX_GRID_TEAM_GOOGLE: 'matrixGridTeamGoogle',
    TG_BTN_INHERENT: 'tgBtnInherent',
    TG_BTN_RESIDUAL: 'tgBtnResidual',
    TG_BTN_OPEN: 'tgBtnOpen',
    TG_BTN_ALL: 'tgBtnAll',

    // Risk Explorer
    EXPLORER_CARDS_CONTAINER: 'explorerCardsContainer',
    EXPLORER_MATCH_COUNT: 'explorerMatchCount',

    // Time Machine Modal
    TIME_MACHINE_MODAL: 'timeMachineModal',
    TIME_MACHINE_SNAPSHOTS_LIST: 'timeMachineSnapshotsList',
    TIME_MACHINE_BANNER: 'timeMachineBanner',
    TIME_MACHINE_BANNER_WEEK: 'timeMachineBannerWeek',

    // Podcast Player & Transcript Modal
    TRANSCRIPT_MODAL: 'transcriptModal',
    PODCAST_TRANSCRIPT_CONTAINER: 'podcastTranscriptContainer',
    PODCAST_PLAY_BTN: 'podcastPlayBtn',
    NATIVE_PODCAST_AUDIO: 'nativePodcastAudio',
    PODCAST_DOWNLOAD_LINK: 'podcastDownloadLink',
    PODCAST_TRANSCRIPT_BTN: 'podcastTranscriptBtn',
    PODCAST_TITLE_TEXT: 'podcastTitleText',
    PODCAST_TIME_LABEL: 'podcastTimeLabel',

    // Blueprint Knowledge & Research Docs
    BLUEPRINT_BUNDLES_CONTAINER: 'bundleAnnexCardsContainer',
    RESEARCH_DOCS_CONTAINER: 'researchDocsContainer',

    // Issue Register
    ISSUE_TABLE_BODY: 'issueTableBody',
    ISSUE_SEARCH_INPUT: 'issueSearchInput',
    ISSUE_RESULT_COUNT: 'issueResultCount',

    // Global / Shell Branding
    APP_PROJECT_BADGE: 'appProjectBadge',
    APP_PROJECT_TITLE: 'appProjectTitle',
    APP_PROJECT_SUBTITLE: 'appProjectSubtitle',
    APP_PROJECT_LOGO_ICON: 'appProjectLogoIcon',
    ITEM_DETAIL_MODAL: 'itemDetailModal',

    // Risk Explorer Controls & Presets
    EXPLORER_SEARCH_INPUT: 'explorerSearchInput',
    FILTER_CATEGORY_SELECT: 'filterCategorySelect',
    FILTER_BUNDLE_SELECT: 'filterBundleSelect',
    FILTER_GOV_SELECT: 'filterGovSelect',
    FILTER_STATUS_SELECT: 'filterStatusSelect',
    EXPLORER_TABLE_CONTAINER: 'explorerTableContainer',
    EXPLORER_CARDS_VIEW_BTN: 'expBtnCards',
    EXPLORER_TABLE_VIEW_BTN: 'expBtnTable',
    TIMELINE_DRILLDOWN_MODAL: 'timelineDrilldownModal'
};

/**
 * Access a required DOM element with a loud warning/exception if missing.
 * Prevents silent early returns and enforces the HTML-JS DOM contract.
 *
 * @param {string} id - The DOM element ID.
 * @param {string} [context='App'] - Component or module context for error reporting.
 * @param {boolean} [throwOnMissing=false] - Whether to throw an Error instead of logging error.
 * @returns {HTMLElement|null}
 */
export function getRequiredElement(id, context = 'App', throwOnMissing = false) {
    if (typeof document === 'undefined') return null;
    const el = document.getElementById(id);
    if (!el) {
        const msg = `[DOM Contract Violation] Missing element #${id} required by ${context}`;
        console.error(msg);
        if (throwOnMissing) {
            throw new Error(msg);
        }
    }
    return el;
}
