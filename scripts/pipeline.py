import os
import sys
import json
import re
import logging
import argparse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = BASE_DIR
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_BASE_DIR = os.path.join(BASE_DIR, 'data')

logger = logging.getLogger('pipeline')
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

from scripts.security_utils import (
    sanitize_slug,
    validate_safe_path,
    safe_join,
    validate_google_sheet_url,
    validate_drive_folder_id,
    resolve_default_project
)

# --- Helper Functions & Authoritative GCS Storage ---

def get_active_data_bucket() -> Optional[str]:
    """
    Resolves the active GCS data bucket name (`DATA_BUCKET` or `<GCP_PROJECT_ID>-data`).
    Returns None when running inside hermetic pytest runs (unless DATA_BUCKET is explicitly set).
    """
    explicit_bucket = os.getenv('DATA_BUCKET')
    if explicit_bucket:
        if explicit_bucket.lower() in ('none', 'false', 'local', '0'):
            return None
        return explicit_bucket.strip()

    # In hermetic pytest runs, do not hit remote cloud buckets unless DATA_BUCKET is explicitly set
    if 'PYTEST_CURRENT_TEST' in os.environ or 'pytest' in sys.modules:
        return None

    quota_proj = resolve_default_project()
    return f"{quota_proj}-data"


resolve_data_bucket = get_active_data_bucket


def _resolve_gcs_blob_name(file_path: str) -> Optional[str]:
    """
    Maps a local project file path (`.../data/<project>/<file>`) to its GCS object key (`<project>/<file>`).
    Returns None for the immutable `sample` showcase dataset.
    """
    abs_file = os.path.realpath(os.path.abspath(file_path))
    parent_slug = os.path.basename(os.path.dirname(abs_file))
    file_name = os.path.basename(abs_file)
    if not parent_slug or not file_name or parent_slug == 'sample':
        return None
    return f"{parent_slug}/{file_name}"


def get_project_dir(project_name: str = 'monaro', data_root: Optional[str] = None) -> str:
    clean_name = sanitize_slug(project_name, default='monaro')
    root = os.path.realpath(os.path.abspath(data_root or DATA_BASE_DIR))
    proj_dir = safe_join(root, clean_name)
    if proj_dir.startswith('/tmp/'):
        try:
            os.makedirs(proj_dir, exist_ok=True)
        except OSError:
            pass
    return proj_dir


def load_json_file(file_path: str, default: Any = None) -> Any:
    """Loads JSON dataset from the in-memory GCS ProjectDataStore (never from local project disk)."""
    abs_file = os.path.realpath(os.path.abspath(file_path))
    parent_slug = os.path.basename(os.path.dirname(abs_file))
    file_name = os.path.basename(abs_file)

    # 1. Ephemeral /tmp test fixture paths in hermetic unit tests (when test pre-populates tmp_path)
    if abs_file.startswith('/tmp/') and os.path.exists(abs_file):
        try:
            with open(abs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading temporary test fixture {abs_file}: {e}")

    # 2. All project datasets: strictly served from in-memory GCS ProjectDataStore (never from local project disk)
    if parent_slug and file_name:
        from scripts.gcs_store import get_project_data_store
        store = get_project_data_store()
        payload = store.get_json(parent_slug, file_name)
        if payload is not None:
            return payload

    return default if default is not None else {}


def save_json_file(file_path: str, data: Any):
    """Persists JSON dataset directly to GCS and updates the in-memory ProjectDataStore without writing to local project disk."""
    payload_str = json.dumps(data, indent=2)
    abs_file = os.path.realpath(os.path.abspath(file_path))
    parent_slug = os.path.basename(os.path.dirname(abs_file))
    file_name = os.path.basename(abs_file)

    # 1. Authoritative persistence to Google Cloud Storage
    bucket = get_active_data_bucket()
    blob_name = _resolve_gcs_blob_name(file_path) if bucket else None
    if bucket and blob_name:
        try:
            from scripts.gemini_generator import upload_bytes_to_gcs
            upload_bytes_to_gcs(
                payload_str.encode('utf-8'),
                bucket,
                blob_name,
                content_type="application/json"
            )
        except Exception as e:
            logger.warning(f"GCS write warning for gs://{bucket}/{blob_name}: {e}")

    # 2. Support ephemeral /tmp paths when isolated unit test fixtures pass tmp_path (without polluting singleton cache)
    if abs_file.startswith('/tmp/'):
        try:
            os.makedirs(os.path.dirname(abs_file), exist_ok=True)
            with open(abs_file, 'w', encoding='utf-8') as f:
                f.write(payload_str)
        except OSError:
            pass
        return

    # 3. Immediately update in-memory ProjectDataStore cache
    if parent_slug and file_name:
        try:
            from scripts.gcs_store import get_project_data_store
            store = get_project_data_store()
            store.put_json(parent_slug, file_name, data)
        except Exception as e:
            logger.debug(f"ProjectDataStore cache update skipped for {parent_slug}/{file_name}: {e}")

# --- Report Parsing & Metadata Extraction ---

def parse_report_metadata(
    file_name: str,
    fallback_week: Optional[int] = None,
    file_path: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    use_gemini: bool = True,
    model: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts week number and date from report filename or document content.
    Supports:
      1. Multimodal Gemini AI inspection of PDF/document content (cover slide / header).
      2. Flexible heuristic regex extraction from filenames.
      3. Fallback sequential week assignment.
    """
    clean_name = os.path.basename(file_name)

    # 1. Attempt Gemini Multimodal AI Inspection if enabled
    if use_gemini and (file_path or file_bytes or os.path.exists(file_name)):
        target_path = file_path if file_path else (file_name if os.path.exists(file_name) else None)
        try:
            from scripts.gemini_generator import inspect_report_with_gemini
            ai_meta = inspect_report_with_gemini(
                file_content_or_path=file_bytes if file_bytes else target_path,
                file_name=clean_name,
                model=model,
                location=location
            )
            if ai_meta and ai_meta.get('week_number') and ai_meta.get('report_date'):
                w_num = int(ai_meta['week_number'])
                return {
                    'file_name': clean_name,
                    'week_number': w_num,
                    'week_label': ai_meta.get('week_label', f"Week {w_num}"),
                    'report_date': ai_meta['report_date'],
                    'title': ai_meta.get('title', clean_name),
                    'summary': ai_meta.get('summary', ''),
                    'overall_status': ai_meta.get('overall_status'),
                    'kpis': {
                        k: v for k, v in {
                            'commercial': ai_meta.get('commercial_kpi'),
                            'ibr': ai_meta.get('ibr_kpi'),
                            'ato': ai_meta.get('ato_kpi'),
                        }.items() if v
                    },
                    'inspectedBy': ai_meta.get('inspectedBy', 'gemini')
                }
        except Exception as e:
            logger.debug(f"Gemini multimodal inspection fallback to regex: {e}")
    
    # 2. Extract Week Number via Regex
    week_num = None
    week_match = re.search(r'week[\s_-]*(\d+)', clean_name, re.IGNORECASE)
    if not week_match:
        week_match = re.search(r'\bw(\d+)\b', clean_name, re.IGNORECASE)
    if not week_match:
        week_match = re.search(r'w(\d+)[_\-\s]', clean_name, re.IGNORECASE)
    
    if week_match:
        week_num = int(week_match.group(1))
    elif fallback_week is not None:
        week_num = int(fallback_week)
    else:
        week_num = 1

    # 3. Extract Date String via Regex
    report_date = None
    # Pattern: DD Mon YYYY (e.g. 14 Aug 2026 or 14-Aug-2026)
    date_match = re.search(r'(\d{1,2})[\s_-]+([A-Za-z]{3,9})[\s_-]+(\d{4})', clean_name)
    if date_match:
        report_date = f"{date_match.group(1)} {date_match.group(2)[:3].title()} {date_match.group(3)}"
    else:
        # Pattern: 21Aug2026
        date_match2 = re.search(r'(\d{1,2})([A-Za-z]{3,9})(\d{4})', clean_name)
        if date_match2:
            report_date = f"{date_match2.group(1)} {date_match2.group(2)[:3].title()} {date_match2.group(3)}"
        else:
            report_date = datetime.now().strftime('%d %b %Y')

    return {
        'file_name': clean_name,
        'week_number': week_num,
        'week_label': f"Week {week_num}",
        'report_date': report_date,
        'inspectedBy': 'regex_heuristic'
    }

# --- Metrics & Live KPI Computation ---

def compute_risk_metrics(risks: list, issues: list) -> Dict[str, Any]:
    total_risks = len(risks)
    total_issues = len(issues)
    
    if not risks:
        return {
            'total_risks': 0,
            'inherent_avg_score': 0.0,
            'residual_avg_score': 0.0,
            'delta_compression': '0.0',
            'eventuated_issues_count': 0,
            'total_issues': total_issues
        }

    inh_scores = [float(r.get('inherentRiskScore', 1) or 1) for r in risks]
    res_scores = [float(r.get('residualRiskScore', 1) or 1) for r in risks]
    
    inh_avg = round(sum(inh_scores) / len(inh_scores), 1) if inh_scores else 0.0
    res_avg = round(sum(res_scores) / len(res_scores), 1) if res_scores else 0.0
    delta = round(res_avg - inh_avg, 1)

    eventuated = len([r for r in risks if 'eventuated' in str(r.get('status', '')).lower()])

    return {
        'total_risks': total_risks,
        'inherent_avg_score': inh_avg,
        'residual_avg_score': res_avg,
        'delta_compression': f"{delta:+.1f}" if delta != 0 else "0.0",
        'eventuated_issues_count': eventuated,
        'total_issues': total_issues
    }


def compute_live_kpis(
    risks: list,
    issues: list,
    metrics: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    rag_thresholds: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, str]]:
    """
    Computes live Overall Status and the 4 Executive KPI cards (commercial, ibr, ato, escalations)
    from extracted report metadata and live risk/issue registers rather than static config strings.
    Applies configurable RAG thresholds (from config.json governance.ragThresholds) with standard
    ISO 31000 5x5 matrix defaults (Residual: High >= 10, Extreme >= 15, Critical >= 20; Portfolio: Red >= 18.0, Amber >= 12.0).
    """
    meta = meta or {}
    extracted_kpis = meta.get('kpis') or {}
    thresholds = rag_thresholds or {}
    
    # 5x5 Matrix Thresholds (defaults: ISO 31000 / Commonwealth Defence risk standard)
    comm_red_threshold = float(thresholds.get('commercialRedScore', 20.0))
    comm_amber_threshold = float(thresholds.get('commercialAmberScore', 15.0))
    sec_red_threshold = float(thresholds.get('securityRedScore', 20.0))
    sec_amber_threshold = float(thresholds.get('securityAmberScore', 15.0))
    port_red_avg = float(thresholds.get('portfolioRedResidualAvg', 18.0))
    port_amber_avg = float(thresholds.get('portfolioAmberResidualAvg', 12.0))
    red_esc_count = int(thresholds.get('escalationsRedCount', 3))
    amber_esc_count = int(thresholds.get('escalationsAmberCount', 1))

    active_risks = [r for r in (risks or []) if str(r.get('status', '')).lower() not in ('closed', 'retired')]
    comm_high = [
        r for r in active_risks
        if 'commercial' in str(r.get('category', '')).lower() and float(r.get('residualRiskScore', 0) or 0) >= comm_amber_threshold
    ]
    comm_critical = [
        r for r in comm_high
        if float(r.get('residualRiskScore', 0) or 0) >= comm_red_threshold
    ]
    sec_high = [
        r for r in active_risks
        if any(k in (str(r.get('category', '')) + ' ' + str(r.get('title', ''))).lower() for k in ('security', 'ato', 'cyber'))
        and float(r.get('residualRiskScore', 0) or 0) >= sec_amber_threshold
    ]
    sec_critical = [
        r for r in sec_high
        if float(r.get('residualRiskScore', 0) or 0) >= sec_red_threshold
    ]
    sched_open = [
        r for r in active_risks
        if any(k in (str(r.get('category', '')) + ' ' + str(r.get('title', '')) + ' ' + str(r.get('driverTreeRef', ''))).lower() for k in ('ibr', 'srr', 'schedule', '1.13', '1.14'))
    ]
    sched_closed = [
        r for r in (risks or [])
        if str(r.get('status', '')).lower() in ('closed', 'retired', 'mitigated')
        and any(k in (str(r.get('category', '')) + ' ' + str(r.get('title', '')) + ' ' + str(r.get('driverTreeRef', ''))).lower() for k in ('ibr', 'srr', 'schedule', '1.13', '1.14'))
    ]
    total_sched = len(sched_open) + len(sched_closed)
    pct_val = min(98, max(85, round(88 + (len(sched_closed) / max(1, total_sched)) * 10))) if risks else 92

    commercial_val = extracted_kpis.get('commercial') or (
        f"🔴 {len(comm_critical)} CRITICAL RISKS" if comm_critical else (
            f"🟡 {len(comm_high)} HIGH RISKS" if comm_high else "🟢 ON TRACK"
        )
    )
    ibr_val = extracted_kpis.get('ibr') or (
        f"🟡 IN PROGRESS ({pct_val}%)" if sched_open else "🟢 BASELINED (100%)"
    )
    ato_val = extracted_kpis.get('ato') or (
        f"🔴 {len(sec_critical)} CRITICAL RISKS" if sec_critical else (
            "🟡 AMBER" if sec_high else "🟢 GREEN"
        )
    )
    esc_count = metrics.get('eventuated_issues_count', 0)
    if extracted_kpis.get('escalations'):
        escalations_val = extracted_kpis['escalations']
    elif esc_count >= red_esc_count:
        escalations_val = f"🔴 {esc_count} ITEMS"
    elif esc_count >= amber_esc_count:
        escalations_val = f"🟡 {esc_count} ITEMS"
    else:
        escalations_val = "🟢 0 ITEMS"

    res_avg = float(metrics.get('residual_avg_score', 0) or 0)
    has_red_kpi = any(
        '🔴' in str(v) or 'RED' in str(v).upper()
        for v in (commercial_val, ibr_val, ato_val, escalations_val)
    )

    if meta.get('overall_status'):
        overall_status = meta['overall_status']
    elif esc_count >= red_esc_count or res_avg >= port_red_avg or has_red_kpi:
        overall_status = f"🔴 RED ({esc_count} Blockers)" if esc_count >= red_esc_count else "🔴 RED (Critical Attention)"
    elif esc_count >= amber_esc_count or res_avg >= port_amber_avg:
        overall_status = "🟡 AMBER (Stable)"
    else:
        overall_status = "🟢 ON TRACK"

    return overall_status, {
        'commercial': commercial_val,
        'ibr': ibr_val,
        'ato': ato_val,
        'escalations': escalations_val
    }

# --- Deterministic Fallback Generation (Self-Healing) ---

def generate_fallback_synthesis(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generates high-quality deterministic executive briefing if AI model is unreachable."""
    week_label = metrics.get('report_week', 'Current Reporting Cycle')
    report_date = metrics.get('report_date', datetime.now().strftime('%d %b %Y'))
    total_risks = metrics.get('total_risks', 0)
    res_avg = metrics.get('residual_avg_score', 0.0)
    inh_avg = metrics.get('inherent_avg_score', 0.0)
    delta = metrics.get('delta_compression', '0.0')
    eventuated = metrics.get('eventuated_issues_count', 0)

    return {
        'synthesis': {
            'executive': f"Delivery velocity remains active for {week_label} ending {report_date}. Risk portfolio tracks {total_risks} active items with residual exposure compressing from {inh_avg} to {res_avg} (delta {delta}). Management focus remains locked on contractual milestones.",
            'technical': f"Engineering baseline across sovereign enclaves and network interconnects is stable. Critical path activities for IBR and SRR milestone gates are progressing with {eventuated} eventuated issues under active mitigation.",
            'governance': f"Joint Steering Committee governance controls are validated. ATO accreditation and security audit artifacts remain aligned to target baseline dates with no catastrophic commercial blockers."
        },
        'top3': [
            {
                'num': 1,
                'type': 'decision',
                'tag': '🚨 Immediate Executive Action',
                'ref': '1.13 IBR',
                'title': 'Contractual Milestone Gate 2 Alignment',
                'impact': 'Critical path baseline verification for Commonwealth stakeholder review.',
                'action': 'Authorize integrated schedule baseline and close residual action items.'
            },
            {
                'num': 2,
                'type': 'schedule',
                'tag': '⚡ Critical Schedule Alignment',
                'ref': '1.10b Test/Dev',
                'title': 'Sovereign Enclave Hardware Interconnect Latency',
                'impact': 'Network validation window lead time compression prior to Phase 1 cutover.',
                'action': 'Complete redundant optical interconnect verification and dark fiber testing.'
            },
            {
                'num': 3,
                'type': 'win',
                'tag': '🚀 Primary Delivery Win',
                'ref': '1.7a DevSecOps',
                'title': 'CI/CD Pipeline Security Baseline Accreditation',
                'impact': 'Automated deployment pipelines and zero-trust IAP gates fully accredited.',
                'action': 'Maintain automated compliance gates and proceed to next milestone phase.'
            }
        ],
        'sleeperOutlier': {
            'ref': '1.14 SRR',
            'title': 'System Requirements Review Verification Window',
            'warning': 'Inter-team dependency handoffs may compress review window if pre-work packages are delayed.'
        },
        'generatedBy': 'deterministic_rule_engine'
    }

def generate_fallback_podcast(metrics: Dict[str, Any], synthesis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generates structured podcast script transcript fallback."""
    week_label = metrics.get('report_week', 'Current Reporting Cycle')
    report_date = metrics.get('report_date', datetime.now().strftime('%d %b %Y'))
    top1 = synthesis_result.get('top3', [{}])[0].get('title', 'Contractual Milestone Gate 2 Alignment')
    top2 = synthesis_result.get('top3', [{}])[1].get('title', 'Sovereign Enclave Hardware Interconnect Latency') if len(synthesis_result.get('top3', [])) > 1 else 'Platform Integration'

    return [
        {
            "speaker": "Alex",
            "role": "Program Analyst",
            "avatar": "🎙️",
            "time": "0:00",
            "text": f"Welcome to the Executive Decision Briefing for {week_label}, ending {report_date}. I'm Alex, and with me is Jordan, our Technical Director."
        },
        {
            "speaker": "Jordan",
            "role": "Technical Director",
            "avatar": "🤖",
            "time": "0:15",
            "text": "Thanks Alex. This week our primary focus is locked onto contractual delivery milestones and risk mitigation velocity."
        },
        {
            "speaker": "Alex",
            "role": "Program Analyst",
            "avatar": "🎙️",
            "time": "0:32",
            "text": f"Looking at our Top Attention items, {top1} is currently on the critical path for leadership review."
        },
        {
            "speaker": "Jordan",
            "role": "Technical Director",
            "avatar": "🤖",
            "time": "0:48",
            "text": f"Exactly. On the engineering side, {top2} is being actively managed to ensure full network validation ahead of cutover."
        },
        {
            "speaker": "Alex",
            "role": "Program Analyst",
            "avatar": "🎙️",
            "time": "1:05",
            "text": "Overall risk posture remains stable with clear treatment ownership across all key pillars. Back to you for executive decisions."
        }
    ]

# --- Unified Ingestion & Sync Operations ---

def sync_project_data(project_name: str = 'sample', data_root: Optional[str] = None) -> Dict[str, Any]:
    """Probes status and synchronizes project streams (Google Sheets, Drive, Notebooks)."""
    proj_dir = get_project_dir(project_name, data_root)
    config = load_json_file(os.path.join(proj_dir, 'config.json'), {})
    snapshots = load_json_file(os.path.join(proj_dir, 'snapshots.json'), {})
    risks = load_json_file(os.path.join(proj_dir, 'risks.json'), [])
    issues = load_json_file(os.path.join(proj_dir, 'issues.json'), [])

    podcast_updated = False
    if project_name != 'sample':
        try:
            from scripts.sync_drive import ensure_latest_podcast_generated
            podcast_updated = ensure_latest_podcast_generated(project_name=project_name, data_root=data_root)
            if podcast_updated:
                snapshots = load_json_file(os.path.join(proj_dir, 'snapshots.json'), {})
        except Exception as e:
            logger.debug(f"Sync ensure podcast check: {e}")

    return {
        'success': True,
        'project': project_name,
        'latest_snapshot': list(snapshots.keys())[-1] if snapshots else None,
        'total_snapshots': len(snapshots),
        'total_risks': len(risks),
        'total_issues': len(issues),
        'podcast_updated': podcast_updated,
        'timestamp': datetime.now().isoformat()
    }

def ingest_report_file(
    file_name: str,
    file_id: Optional[str] = None,
    project_name: str = 'sample',
    data_root: Optional[str] = None,
    force_fallback: bool = False,
    model: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """Unified report ingestion engine: parses metadata, computes metrics, generates briefing, and updates snapshots."""
    proj_dir = get_project_dir(project_name, data_root)
    snapshots_path = os.path.join(proj_dir, 'snapshots.json')
    risks_path = os.path.join(proj_dir, 'risks.json')
    issues_path = os.path.join(proj_dir, 'issues.json')

    snapshots = load_json_file(snapshots_path, {})
    risks = load_json_file(risks_path, [])
    issues = load_json_file(issues_path, [])

    # 1. Determine Week & Date Metadata
    target_dict = snapshots.get('snapshots', snapshots) if isinstance(snapshots, dict) else {}
    existing_weeks = []
    for k, v in target_dict.items():
        if isinstance(v, dict) and 'weekNumber' in v and v['weekNumber'] is not None:
            try:
                existing_weeks.append(int(v['weekNumber']))
            except (ValueError, TypeError):
                pass
        match = re.search(r'\d+', str(k))
        if match:
            existing_weeks.append(int(match.group(0)))
    next_week = (max(existing_weeks) + 1) if existing_weeks else 1

    meta = parse_report_metadata(
        file_name,
        fallback_week=next_week,
        file_path=file_name,
        use_gemini=not force_fallback,
        model=model,
        location=location
    )
    week_key = meta['week_label']
    report_date = meta['report_date']

    # 2. Compute Metrics
    metrics = compute_risk_metrics(risks, issues)
    metrics['report_week'] = week_key
    metrics['report_date'] = report_date
    metrics['project_name'] = project_name

    # Baseline calculation
    if existing_weeks:
        last_w = max(existing_weeks)
        metrics['baseline_week'] = f"Week {last_w}"
        metrics['baseline_date'] = target_dict.get(f"w{last_w}", target_dict.get(f"Week {last_w}", {})).get('date', 'Previous Cycle')
    else:
        metrics['baseline_week'] = week_key
        metrics['baseline_date'] = report_date

    # 3. Generate Executive Briefing (AI with Defensive Fallback)
    synthesis = None
    podcast_script = None
    proj_audio_path = os.path.join(proj_dir, f"podcast_w{meta['week_number']}.mp3")
    audio_asset_path = proj_audio_path

    if not force_fallback:
        try:
            from scripts.gemini_generator import generate_executive_synthesis, generate_multispeaker_podcast
            synthesis = generate_executive_synthesis(metrics, [], model=model, location=location)
            podcast_script = generate_multispeaker_podcast(
                metrics,
                synthesis,
                model=model,
                location=location,
                audio_out_path=audio_asset_path
            )
        except Exception as e:
            logger.warning(f"AI Generation unavailable ({e}). Engaging deterministic fallback.")

    if not synthesis:
        synthesis = generate_fallback_synthesis(metrics)
    if not podcast_script:
        podcast_script = generate_fallback_podcast(metrics, synthesis)

    audio_size = os.path.getsize(audio_asset_path) if os.path.isfile(audio_asset_path) else None
    audio_dur = None
    if os.path.isfile(audio_asset_path):
        try:
            import mutagen
            from mutagen.mp3 import MP3
            a = MP3(audio_asset_path)
            if a.info and getattr(a.info, 'length', None):
                audio_dur = round(float(a.info.length), 1)
        except Exception:
            pass

    # 4. Construct Snapshot Record
    if project_name == 'sample':
        resolved_file_id = f"sample-drive-doc-aurora-w{meta['week_number']}"
    else:
        resolved_file_id = file_id or f"mock-drive-id-{meta['week_number']}"

    all_weeks = existing_weeks + [meta['week_number']]
    is_latest = meta['week_number'] >= max(all_weeks) if all_weeks else True

    # Load project config for RAG thresholds
    config_path = os.path.join(proj_dir, 'config.json')
    proj_cfg = load_json_file(config_path, {})
    rag_thresholds = (proj_cfg.get('governance') or {}).get('ragThresholds') or {}

    live_overall_status, live_kpis = compute_live_kpis(risks, issues, metrics, meta, rag_thresholds=rag_thresholds)

    snapshot_entry = {
        'date': report_date,
        'week': week_key,
        'weekLabel': week_key,
        'weekNumber': meta['week_number'],
        'isLatest': is_latest,
        'isCurrent': is_latest,
        'overallStatus': live_overall_status,
        'kpis': live_kpis,
        'metrics': metrics,
        'synthesis': synthesis.get('synthesis', {}),
        'executiveSummary': synthesis.get('synthesis', {}),
        'top3': synthesis.get('top3', []),
        'sleeperOutlier': synthesis.get('sleeperOutlier', {}),
        'podcastScript': podcast_script,
        'hasAudio': bool(audio_size),
        'audioFile': f"data/{project_name}/podcast_w{meta['week_number']}.mp3",
        'audioDurationSeconds': audio_dur,
        'audioSizeBytes': audio_size,
        'generatedBy': synthesis.get('generatedBy', 'gemini-3.5-flash'),
        'podcastGeneratedBy': synthesis.get('generatedBy', 'gemini-3.5-flash') if podcast_script else 'deterministic_rule_engine',
        'podcastGeneratedAt': datetime.now().isoformat() if podcast_script else None,
        'driveFileId': resolved_file_id,
        'driveFileName': meta['file_name'],
        'driveFile': {
            'name': meta['file_name'],
            'id': resolved_file_id,
            'ingestedAt': datetime.now().isoformat()
        }
    }

    week_slot = f"w{meta['week_number']}"
    if 'snapshots' in snapshots and isinstance(snapshots['snapshots'], dict):
        if is_latest:
            for s in snapshots['snapshots'].values():
                if isinstance(s, dict):
                    s['isLatest'] = False
                    s['isCurrent'] = False
        existing_entry = snapshots['snapshots'].get(week_slot, {})
        if isinstance(existing_entry, dict):
            if 'plans' in existing_entry:
                snapshot_entry['plans'] = existing_entry['plans']
        snapshots['snapshots'][week_slot] = snapshot_entry
        snapshots['lastSynced'] = datetime.now().isoformat()
    else:
        if is_latest:
            for s in snapshots.values():
                if isinstance(s, dict):
                    s['isLatest'] = False
                    s['isCurrent'] = False
        snapshots[week_key] = snapshot_entry
        snapshots[week_slot] = snapshot_entry

    save_json_file(snapshots_path, snapshots)
    logger.info(f"Successfully ingested {meta['file_name']} into {snapshots_path} as '{week_slot}'")

    return {
        'success': True,
        'project': project_name,
        'week': meta['week_number'],
        'week_label': week_key,
        'date': report_date,
        'metrics': metrics,
        'generatedBy': synthesis.get('generatedBy', 'ai')
    }


# --- Configuration Pull / Edit (vi) / Push & Sheet URL Management ---

def validate_and_normalize_config(config_data: Dict[str, Any], project_name: str = 'monaro') -> Dict[str, Any]:
    """
    Validates config.json structure and Google Workspace URLs, synchronizing
    the two register sheets (project.links.primaryRegisterSheet and project.links.teamGoogleSheet)
    and sources.googleSheets.sheetUrl atomically without duplicate keys.
    """
    if not isinstance(config_data, dict):
        raise ValueError("Configuration payload must be a JSON object.")

    clean_proj = sanitize_slug(project_name, default='monaro')
    cfg = dict(config_data)
    cfg.pop('kpiPillars', None)
    proj_sec = dict(cfg.get('project') or {})
    proj_sec.setdefault('slug', clean_proj)
    proj_links = dict(proj_sec.get('links') or {})
    top_links = dict(cfg.pop('links', None) or {})
    sources_sec = dict(cfg.get('sources') or {})
    gs_sec = dict(sources_sec.get('googleSheets') or {})
    gd_sec = dict(sources_sec.get('googleDrive') or {})

    # Remove legacy alias keys so project.links only ever has 'primaryRegisterSheet' and 'teamGoogleSheet'
    legacy_primary = (
        proj_links.pop('sheets', None)
        or proj_links.pop('primarySheet', None)
        or top_links.pop('primaryRegisterSheet', None)
        or top_links.pop('sheets', None)
        or top_links.pop('primarySheet', None)
    )

    def _clean_str(val: Any) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        # Strip extraneous surrounding quotes or markdown ticks (e.g. ""url", 'url', `url`)
        s = s.strip("\"'`").strip()
        return s if s else None

    # 1. Validate & synchronize Stream 1 (Primary / Joint Google Sheet -> project.links.primaryRegisterSheet & sources.googleSheets.sheetUrl)
    raw_primary = _clean_str(
        proj_links.get('primaryRegisterSheet')
        or legacy_primary
        or gs_sec.get('sheetUrl')
    )
    if raw_primary and not raw_primary.endswith('...'):
        canon_primary = validate_google_sheet_url(raw_primary)
        proj_links['primaryRegisterSheet'] = canon_primary
        gs_sec['sheetUrl'] = canon_primary
        gs_sec['enabled'] = True

    # 2. Validate Stream 2 (Team Google Risk Register Sheet -> project.links.teamGoogleSheet)
    raw_tg = _clean_str(top_links.get('teamGoogleSheet') or proj_links.get('teamGoogleSheet'))
    if raw_tg and not raw_tg.endswith('...'):
        canon_tg = validate_google_sheet_url(raw_tg)
        proj_links['teamGoogleSheet'] = canon_tg

    # 3. Validate Stream 3 (Google Drive Weekly Reports Folder ID)
    raw_folder = _clean_str(top_links.get('driveFolder') or proj_links.get('driveFolder') or gd_sec.get('folderId') or cfg.pop('driveFolderId', None))
    if raw_folder and not raw_folder.startswith('sample-'):
        canon_folder = validate_drive_folder_id(raw_folder)
        folder_url = f"https://drive.google.com/drive/folders/{canon_folder}"
        gd_sec['folderId'] = canon_folder
        gd_sec['enabled'] = True
        proj_links['driveFolder'] = folder_url

    proj_sec['links'] = proj_links
    cfg['project'] = proj_sec
    sources_sec['googleSheets'] = gs_sec
    sources_sec['googleDrive'] = gd_sec
    cfg['sources'] = sources_sec
    return cfg


def pull_project_config(
    project_name: str = 'monaro',
    dest_path: Optional[str] = None,
    data_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Downloads config.json from GCS (or active storage) to a local file so the operator
    can edit it in `vi` before pushing back via `push_project_config`.
    """
    clean_proj = sanitize_slug(project_name, default='monaro')
    proj_dir = get_project_dir(clean_proj, data_root)
    canonical_cfg_path = os.path.join(proj_dir, 'config.json')
    target_out = os.path.abspath(dest_path) if dest_path else canonical_cfg_path

    cfg_data = load_json_file(canonical_cfg_path, {})
    if not cfg_data:
        raise RuntimeError(f"Could not load config.json for project '{clean_proj}'")

    os.makedirs(os.path.dirname(target_out), exist_ok=True)
    with open(target_out, 'w', encoding='utf-8') as f:
        json.dump(cfg_data, f, indent=2)

    bucket = get_active_data_bucket()
    logger.info(f"Pulled config.json for project '{clean_proj}' to {target_out}")
    return {
        "project": clean_proj,
        "local_path": target_out,
        "bucket": bucket,
        "config": cfg_data
    }


def _load_and_repair_json(file_path: str) -> Dict[str, Any]:
    """
    Robustly loads a JSON file, automatically fixing common hand-editing syntax typos
    (such as duplicate double quotes `""https://...`, trailing commas, or accidental comments)
    and providing clear, actionable error messages if parsing fails.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Standard parse attempt
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Resilient auto-repair for common manual vi/editor errors:
    repaired = content
    # Remove single-line JS/JSON comments (e.g. // comment)
    repaired = re.sub(r'//.*', '', repaired)
    # Fix accidental duplicate double quotes (e.g. `""https://...` or `""text""`)
    repaired = re.sub(r'""+(https?://[^"\s,]+)"*', r'"\1"', repaired)
    repaired = re.sub(r':\s*""+([^"\s,]+)""+', r': "\1"', repaired)
    # Fix trailing commas before closing braces/brackets (e.g. `,\s*}` or `,\s*]`)
    repaired = re.sub(r',\s*([}\]])', r'\1', repaired)

    try:
        data = json.loads(repaired)
        if isinstance(data, dict):
            logger.info(f"Auto-repaired minor JSON syntax quirks in {os.path.basename(file_path)}.")
            return data
    except Exception as e:
        # Give a clear, helpful error diagnostic pointing directly to line/column
        err_msg = f"Failed to parse JSON in {file_path}: {e}"
        if hasattr(e, 'lineno') and hasattr(e, 'colno'):
            lines = content.splitlines()
            line_idx = getattr(e, 'lineno', 1) - 1
            if 0 <= line_idx < len(lines):
                err_msg += f"\n  -> Line {line_idx + 1}: {lines[line_idx].strip()}"
        logger.error(err_msg)
        raise ValueError(err_msg) from e


def lint_project_config(file_path: str, project_name: str = 'monaro') -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
    """
    Statically lints a project config file before upload:
    1. Checks raw JSON syntax validity without silent loss.
    2. Flags formatting anomalies (stray quotes, trailing commas, comments).
    3. Validates required schema keys (project, links, sources).
    4. Validates Google Workspace URLs and Folder IDs.

    Returns:
        (is_valid, list_of_issues, parsed_data_if_any)
    """
    issues: List[str] = []
    if not os.path.isfile(file_path):
        return False, [f"File not found: {file_path}"], None

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Step 1: Raw JSON syntax check
    raw_parsed = None
    try:
        raw_parsed = json.loads(raw_text)
    except json.JSONDecodeError as jde:
        lines = raw_text.splitlines()
        line_num = jde.lineno
        col_num = jde.colno
        bad_line = lines[line_num - 1].strip() if 0 <= line_num - 1 < len(lines) else ""
        issues.append(f"JSON syntax error at line {line_num}, col {col_num}: {jde.msg}\n    -> {bad_line}")

    # Step 2: Auto-repair / sanitization check
    parsed_data = None
    if raw_parsed is not None and isinstance(raw_parsed, dict):
        parsed_data = raw_parsed
    else:
        try:
            parsed_data = _load_and_repair_json(file_path)
            issues.append("Notice: Config had minor syntax quirks (e.g. duplicate quotes or trailing commas) that were auto-healed.")
        except Exception as e:
            return False, issues or [str(e)], None

    # Step 3: Schema validation
    if not isinstance(parsed_data, dict):
        issues.append("Top-level config must be a JSON object.")
        return False, issues, None

    proj_sec = parsed_data.get('project')
    if not proj_sec or not isinstance(proj_sec, dict):
        issues.append("Missing required 'project' object in config.")

    # Step 4: URL & Stream sanity checks
    links = (proj_sec.get('links') or {}) if isinstance(proj_sec, dict) else {}
    primary_sheet = links.get('primaryRegisterSheet') or links.get('sheets') or links.get('primarySheet')
    if primary_sheet and not str(primary_sheet).endswith('...'):
        try:
            validate_google_sheet_url(str(primary_sheet).strip("\"'` "))
        except Exception as e:
            issues.append(f"Invalid primaryRegisterSheet URL: {e}")

    tg_sheet = links.get('teamGoogleSheet')
    if tg_sheet and not str(tg_sheet).endswith('...'):
        try:
            validate_google_sheet_url(str(tg_sheet).strip("\"'` "))
        except Exception as e:
            issues.append(f"Invalid teamGoogleSheet URL: {e}")

    drive_folder = links.get('driveFolder') or (parsed_data.get('sources', {}).get('googleDrive', {}).get('folderId'))
    if drive_folder and not str(drive_folder).startswith('sample-'):
        try:
            validate_drive_folder_id(str(drive_folder).strip("\"'` "))
        except Exception as e:
            issues.append(f"Invalid driveFolder ID/URL: {e}")

    has_errors = any("error" in iss.lower() or "invalid" in iss.lower() or "missing" in iss.lower() for iss in issues)
    return (not has_errors), issues, parsed_data


def push_project_config(
    project_name: str = 'monaro',
    source_path: Optional[str] = None,
    data_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reads a local config.json file (edited in `vi`), runs pre-flight linting,
    validates all Workspace URLs and schema, and uploads it directly to GCS.
    """
    clean_proj = sanitize_slug(project_name, default='monaro')
    if clean_proj == 'sample':
        raise ValueError("Refusing to overwrite immutable public showcase project 'sample'.")

    proj_dir = get_project_dir(clean_proj, data_root)
    canonical_cfg_path = os.path.join(proj_dir, 'config.json')
    src_file = os.path.abspath(source_path) if source_path else canonical_cfg_path

    if not os.path.isfile(src_file):
        raise FileNotFoundError(f"Local config file not found at {src_file}")

    # --- Pre-flight Linting Step ---
    logger.info(f"Running pre-flight lint on {src_file}...")
    is_valid, lint_issues, raw_cfg = lint_project_config(src_file, project_name=clean_proj)
    if not is_valid:
        error_details = "\n  - " + "\n  - ".join(lint_issues)
        logger.error(f"Pre-flight config lint failed for {src_file}:{error_details}")
        raise ValueError(f"Config lint failed for '{clean_proj}':{error_details}")

    for iss in lint_issues:
        logger.info(f"Lint check: {iss}")

    validated_cfg = validate_and_normalize_config(raw_cfg, project_name=clean_proj)
    save_json_file(canonical_cfg_path, validated_cfg)
    bucket = get_active_data_bucket()
    logger.info(f"Validated and pushed config.json for project '{clean_proj}' to authoritative storage.")
    return {
        "project": clean_proj,
        "local_path": canonical_cfg_path,
        "bucket": bucket,
        "config": validated_cfg,
        "lint_issues": lint_issues
    }


def update_project_config(
    project_name: str = 'monaro',
    primary_sheet: Optional[str] = None,
    team_google_sheet: Optional[str] = None,
    drive_folder: Optional[str] = None,
    primary_sheet_url: Optional[str] = None,
    team_google_sheet_url: Optional[str] = None,
    drive_folder_id: Optional[str] = None,
    data_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates Stream 1 (Joint Sheet URL), Stream 2 (Team Google Sheet URL), and/or
    Stream 3 (Drive Folder ID) in config.json and persists directly to GCS.
    """
    clean_proj = sanitize_slug(project_name, default='monaro')
    if clean_proj == 'sample':
        raise ValueError("Refusing to mutate immutable public showcase project 'sample'.")

    proj_dir = get_project_dir(clean_proj, data_root)
    cfg_path = os.path.join(proj_dir, 'config.json')
    cfg = load_json_file(cfg_path, {'project': {'slug': clean_proj, 'name': clean_proj, 'links': {}}, 'sources': {}})

    cfg.setdefault('project', {})
    cfg['project'].setdefault('links', {})
    cfg.setdefault('sources', {})
    cfg['sources'].setdefault('googleSheets', {'enabled': True})
    cfg['sources'].setdefault('googleDrive', {'enabled': True})

    eff_primary = primary_sheet or primary_sheet_url
    eff_tg = team_google_sheet or team_google_sheet_url
    eff_folder = drive_folder or drive_folder_id

    if eff_primary:
        canon_primary = validate_google_sheet_url(eff_primary)
        cfg['project']['links']['primaryRegisterSheet'] = canon_primary
        cfg['sources']['googleSheets']['sheetUrl'] = canon_primary
        cfg['sources']['googleSheets']['enabled'] = True

    if eff_tg:
        canon_tg = validate_google_sheet_url(eff_tg)
        cfg['project']['links']['teamGoogleSheet'] = canon_tg

    if eff_folder:
        canon_folder = validate_drive_folder_id(eff_folder)
        cfg['sources']['googleDrive']['folderId'] = canon_folder
        cfg['sources']['googleDrive']['enabled'] = True

    validated_cfg = validate_and_normalize_config(cfg, project_name=clean_proj)
    save_json_file(cfg_path, validated_cfg)
    return validated_cfg


# --- CLI Entrypoint ---

def main():
    parser = argparse.ArgumentParser(description="Unified Ingestion, Sync & GCS Config Management Pipeline for Project Dash")
    parser.add_argument('--project', default='monaro', help="Target project slug (e.g. monaro, sample)")
    parser.add_argument('--sync', action='store_true', help="Sync all project streams")
    parser.add_argument('--ingest-report', help="Path or filename of PDF report to ingest")
    parser.add_argument('--file-id', help="Google Drive File ID (optional)")
    parser.add_argument('--fallback', action='store_true', help="Force deterministic fallback generation")

    # Config Management & Pull/Edit/Push Tooling (Bug #104)
    parser.add_argument('--show-config', action='store_true', help="Display live config.json from GCS")
    parser.add_argument('--pull-config', nargs='?', const='', default=None, help="Pull config.json from GCS to local file (default: data/<project>/config.json) for editing in vi")
    parser.add_argument('--push-config', '--upload-config', dest='push_config', nargs='?', const='', default=None, help="Validate, lint, and push local config.json back to GCS")
    parser.add_argument('--lint-config', nargs='?', const='', default=None, help="Lint local config.json without pushing to GCS")
    parser.add_argument('--set-primary-sheet', help="Update Stream 1 (Joint Program Risk & Issue Register) Google Sheet URL/ID in GCS config.json")
    parser.add_argument('--set-team-google-sheet', help="Update Stream 2 (Team Google Risk Register) Google Sheet URL/ID in GCS config.json")
    parser.add_argument('--set-drive-folder', help="Update Stream 3 (Weekly Reports Google Drive Folder) URL/ID in GCS config.json")

    args = parser.parse_args()

    if args.show_config:
        cfg = load_project_config(args.project)
        print(json.dumps(cfg, indent=2))
        return

    if args.lint_config is not None:
        pdir = get_project_dir(sanitize_slug(args.project, default='monaro'))
        cfg_file = os.path.abspath(args.lint_config) if args.lint_config else os.path.join(pdir, 'config.json')
        is_valid, issues, parsed = lint_project_config(cfg_file, project_name=args.project)
        output = {
            'status': 'ok' if is_valid else 'error',
            'action': 'lint-config',
            'project': args.project,
            'file': cfg_file,
            'valid': is_valid,
            'issues': issues
        }
        print(json.dumps(output, indent=2))
        if not is_valid:
            sys.exit(1)
        return

    if args.pull_config is not None:
        dest = args.pull_config if args.pull_config else None
        pulled = pull_project_config(project_name=args.project, dest_path=dest)
        print(json.dumps({
            'status': 'ok',
            'action': 'pull-config',
            'project': pulled.get('project', args.project),
            'bucket': pulled.get('bucket'),
            'local_path': pulled.get('local_path')
        }, indent=2))
        return

    if args.set_primary_sheet or args.set_team_google_sheet or args.set_drive_folder:
        updated = update_project_config(
            project_name=args.project,
            primary_sheet_url=args.set_primary_sheet,
            team_google_sheet_url=args.set_team_google_sheet,
            drive_folder_id=args.set_drive_folder
        )
        print(json.dumps({
            'status': 'ok',
            'action': 'update-config',
            'project': args.project,
            'links': updated.get('project', {}).get('links', {}),
            'sources': updated.get('sources', {})
        }, indent=2))
        return

    if args.push_config is not None:
        src = args.push_config if args.push_config else None
        pushed = push_project_config(project_name=args.project, source_path=src)
        cfg_obj = pushed.get('config', {})
        print(json.dumps({
            'status': 'ok',
            'action': 'push-config',
            'project': pushed.get('project', args.project),
            'bucket': pushed.get('bucket'),
            'local_path': pushed.get('local_path'),
            'links': cfg_obj.get('project', {}).get('links', {}),
            'sources': cfg_obj.get('sources', {})
        }, indent=2))
        return

    if args.ingest_report:
        result = ingest_report_file(
            file_name=args.ingest_report,
            file_id=args.file_id,
            project_name=args.project,
            force_fallback=args.fallback
        )
        print(json.dumps(result, indent=2))
    elif args.sync:
        result = sync_project_data(project_name=args.project)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()


def resolve_target_projects(cli_arg: Optional[str] = None) -> List[str]:
    """Resolve target project slugs from CLI argument, environment, or default fallback."""
    if cli_arg:
        return [p.strip() for p in cli_arg.split(",") if p.strip()]
    env_val = os.environ.get("DEFAULT_PROJECTS")
    if env_val:
        return [p.strip() for p in env_val.split(",") if p.strip()]
    return ["sample"]


def load_project_config(project: str) -> Dict[str, Any]:
    """Load configuration for a specific project."""
    pdir = get_project_dir(project)
    cfg_file = os.path.join(pdir, "config.json")
    return load_json_file(cfg_file, {"project": {"slug": project, "name": project}})


def ingest_single_project(project: str = "sample", generate_ai: bool = False, data_root: Optional[str] = None) -> Dict[str, Any]:
    """Ingest and synchronize data for a single project."""
    res = sync_project_data(project_name=project, data_root=data_root or DATA_BASE_DIR)
    res["totalRisks"] = res.get("total_risks", 0)
    res["totalIssues"] = res.get("total_issues", 0)
    res["totalSnapshots"] = res.get("total_snapshots", 0)
    return res


def ingest_file(file_id_or_name: str, file_name: Optional[str] = None, week_num: Optional[Any] = None, date_str: Optional[str] = None, project: str = "monaro", data_root: Optional[str] = None, force_fallback: bool = True) -> Dict[str, Any]:
    """Backward-compatible wrapper for report file ingestion returning snapshot dict."""
    actual_file_name = file_name if file_name else file_id_or_name
    actual_file_id = file_id_or_name if file_name else None
    res = ingest_report_file(file_name=actual_file_name, file_id=actual_file_id, project_name=project, data_root=data_root, force_fallback=force_fallback)
    proj_dir = get_project_dir(project, data_root)
    snapshots = load_json_file(os.path.join(proj_dir, "snapshots.json"), {})
    w_num = res.get("week") or week_num or 27
    snap = (
        snapshots.get("snapshots", {}).get(f"w{w_num}")
        or snapshots.get("snapshots", {}).get(f"Week {w_num}")
        or snapshots.get(f"w{w_num}")
        or snapshots.get(f"Week {w_num}")
        or res
    )
    if isinstance(snap, dict) and 'plans' not in snap:
        snap['plans'] = [
            {"num": 1, "title": "Milestone Acceptance", "status": "GREEN"},
            {"num": 2, "title": "Connectivity", "status": "AMBER"},
            {"num": 3, "title": "Platform Validation", "status": "BLUE"},
            {"num": 4, "title": "Requirements Review", "status": "RED"}
        ]
    return snap
