#!/usr/bin/env python3
"""
Standalone Google Drive Synchronization & Turnkey Ingestion Script for Project Dash.

Scans the designated Google Drive folder for weekly report PDFs, extracts metadata and
metrics using Gemini 2.5 Flash, and publishes updated static snapshots.json and config.json.
Designed to run via Cloud Run Job (monaro-risk-sync-job), Cloud Tasks, CLI, or CI/CD.
"""

import os
import sys
import json
import logging
import argparse
import re
# Ensure parent directory is in sys.path when executed directly as a script
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from scripts.pipeline import (
    load_json_file,
    save_json_file,
    get_project_dir,
    parse_report_metadata,
    ingest_report_file,
    DATA_BASE_DIR
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('sync_drive')

DEFAULT_DRIVE_FOLDER_ID = '1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C'


def get_drive_service():
    """Initializes Google Drive v3 API client using Application Default Credentials,
    with automatic service account impersonation fallback for local workstation environments."""
    from googleapiclient.discovery import build
    from google.auth import default
    drive_scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials, _ = default(scopes=drive_scopes)

    target_sa = os.getenv("DRIVE_SERVICE_ACCOUNT", "github-deployer@monaro-risk-dev.iam.gserviceaccount.com")
    try:
        from google.auth import impersonated_credentials
        if hasattr(credentials, 'refresh') and not hasattr(credentials, 'service_account_email'):
            impersonated = impersonated_credentials.Credentials(
                source_credentials=credentials,
                target_principal=target_sa,
                target_scopes=drive_scopes
            )
            return build('drive', 'v3', credentials=impersonated)
    except Exception as e:
        logger.debug(f"Impersonation setup skipped: {e}")

    return build('drive', 'v3', credentials=credentials)


def extract_week_number(name: str) -> Optional[int]:
    """Extracts integer week number from filename using regex heuristics."""
    match = re.search(r'(?:week|w)\s*(\d+)', name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def query_drive_folder_live(folder_id: str) -> List[Dict[str, Any]]:
    """
    Queries Google Drive API v3 for PDF reports in the specified folder.
    Raises exceptions on authentication or access failure so callers/jobs fail visibly.
    """
    service = get_drive_service()
    
    # 1. Verify folder accessibility and discover Drive ID (e.g. Shared Drive)
    drive_id = None
    folder_name = folder_id
    try:
        folder_meta = service.files().get(
            fileId=folder_id,
            supportsAllDrives=True,
            fields="id, name, mimeType, driveId, capabilities, shared"
        ).execute()
        folder_name = folder_meta.get('name', folder_id)
        drive_id = folder_meta.get('driveId')
        logger.info(f"Verified Drive folder '{folder_name}' (ID: {folder_id}, SharedDriveID: {drive_id})")
    except Exception as e:
        logger.error(
            f"Failed to access Google Drive folder '{folder_id}': {e}. "
            f"Ensure this folder is shared with the active service account or user."
        )
        raise

    # 2. Query folder contents with full Shared Drive and pagination support
    logger.info(f"Querying Google Drive folder '{folder_name}' for PDF status reports...")
    q = f"'{folder_id}' in parents and trashed = false"
    
    list_kwargs = {
        'q': q,
        'pageSize': 100,
        'fields': "files(id, name, createdTime, webViewLink, webContentLink, mimeType)",
        'orderBy': "name desc",
        'supportsAllDrives': True,
        'includeItemsFromAllDrives': True
    }
    if drive_id:
        list_kwargs['corpora'] = 'drive'
        list_kwargs['driveId'] = drive_id

    response = service.files().list(**list_kwargs).execute()
    files = response.get('files', [])
    logger.info(f"Drive API returned {len(files)} total file(s) in folder '{folder_name}'.")

    reports = []
    for f in files:
        f_name = f.get('name', '')
        f_mime = f.get('mimeType', '')
        logger.info(f" - Found Drive item: '{f_name}' (MIME: {f_mime}, ID: {f.get('id')})")
        
        # Accept PDF files or Google Slides presentation exports
        is_pdf = f_mime == 'application/pdf' or f_name.lower().endswith('.pdf')
        is_slide = f_mime == 'application/vnd.google-apps.presentation'
        if not (is_pdf or is_slide):
            continue

        week_num = extract_week_number(f_name)
        reports.append({
            'id': f.get('id'),
            'name': f_name,
            'week_number': week_num,
            'week_label': f"Week {week_num}" if week_num else None,
            'createdTime': f.get('createdTime'),
            'webViewLink': f.get('webViewLink') or f"https://drive.google.com/file/d/{f.get('id')}/view",
            'webContentLink': f.get('webContentLink'),
            'mimeType': f_mime
        })

    logger.info(f"Discovered {len(reports)} valid status report(s) in Google Drive folder.")
    return reports


def filter_uningested_reports(
    drive_files: List[Dict[str, Any]],
    snapshots_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Filters discovered Drive files against existing snapshots.
    Returns only reports that have not yet been ingested into snapshots.json.
    """
    existing_weeks = set()
    existing_file_ids = set()
    existing_file_names = set()
    snapshots_dict = snapshots_data.get('snapshots', {})
    for key, snap in snapshots_dict.items():
        if isinstance(snap, dict):
            w_num = snap.get('weekNumber')
            if w_num is not None:
                existing_weeks.add(int(w_num))
            w_label = snap.get('week') or snap.get('weekLabel')
            if w_label:
                m = re.search(r'(\d+)', str(w_label))
                if m:
                    existing_weeks.add(int(m.group(1)))
            fid = snap.get('driveFileId') or (snap.get('driveFile', {}).get('id') if isinstance(snap.get('driveFile'), dict) else None)
            if fid:
                existing_file_ids.add(str(fid).strip())
            fname = snap.get('driveFileName') or (snap.get('driveFile', {}).get('name') if isinstance(snap.get('driveFile'), dict) else None)
            if fname:
                existing_file_names.add(str(fname).strip().lower())

    uningested = []
    for f in drive_files:
        f_id = str(f.get('id') or '').strip()
        f_name = str(f.get('name') or '').strip().lower()
        if f_id and f_id in existing_file_ids:
            continue
        if f_name and f_name in existing_file_names:
            continue
        w_num = f.get('week_number')
        if w_num is not None and w_num in existing_weeks:
            continue
        uningested.append(f)

    # Sort ascending by week number for chronological ingestion
    uningested.sort(key=lambda x: x.get('week_number') or 0)
    return uningested


def ensure_latest_podcast_generated(
    project_name: str = 'monaro',
    data_root: Optional[str] = None,
    model: Optional[str] = None,
    location: Optional[str] = None,
    force: bool = False
) -> bool:
    """
    Ensures that the latest snapshot in snapshots.json has a valid executive podcast
    script generated by Gemini 3.5 Flash.
    
    If the latest snapshot:
      - Has no podcastScript, OR
      - Has a script generated by fallback ('deterministic_rule_engine'), OR
      - Has generatedBy != 'gemini-3.5-flash', OR
      - force is True:
    Calls generate_multispeaker_podcast using Gemini 3.5 Flash (gemini-3.5-flash),
    updates snapshots.json on disk, and marks generatedBy = 'gemini-3.5-flash'.
    
    Returns True if the podcast was newly generated or refreshed, False if already up to date.
    """
    proj_dir = get_project_dir(project_name, data_root)
    snapshots_path = os.path.join(proj_dir, 'snapshots.json')
    snapshots_data = load_json_file(snapshots_path, {})
    if not snapshots_data:
        logger.warning(f"No snapshots found for project '{project_name}' at {snapshots_path}")
        return False

    is_wrapped = 'snapshots' in snapshots_data and isinstance(snapshots_data['snapshots'], dict)
    snapshots_map = snapshots_data['snapshots'] if is_wrapped else snapshots_data

    # Find the latest snapshot
    max_week = -1
    latest_key = None
    latest_snap = None

    for k, v in snapshots_map.items():
        if not isinstance(v, dict):
            continue
        wn = v.get('weekNumber')
        if wn is not None:
            try:
                wn_val = int(wn)
                if wn_val > max_week:
                    max_week = wn_val
                    latest_key = k
                    latest_snap = v
            except (ValueError, TypeError):
                pass
        m = re.search(r'\d+', str(k))
        if m:
            try:
                wn_val = int(m.group(0))
                if wn_val > max_week:
                    max_week = wn_val
                    latest_key = k
                    latest_snap = v
            except (ValueError, TypeError):
                pass

    if not latest_snap:
        logger.warning(f"Could not identify latest snapshot in {snapshots_path}")
        return False

    from scripts.gemini_generator import (
        get_default_gemini_model,
        get_default_gemini_region,
        generate_multispeaker_podcast
    )
    active_model = get_default_gemini_model(model)
    active_region = get_default_gemini_region(location)

    curr_script = latest_snap.get('podcastScript')
    curr_gen = latest_snap.get('generatedBy')

    needs_generation = (
        force or
        not curr_script or
        len(curr_script) == 0 or
        curr_gen != active_model
    )

    if not needs_generation:
        logger.info(f"Latest snapshot '{latest_key}' already has a valid podcast generated by {curr_gen}.")
        return False

    logger.info(f"Generating Gemini 3.5 Flash podcast for latest snapshot '{latest_key}' (week {max_week})...")
    metrics = latest_snap.get('metrics', {})
    if not metrics:
        metrics = {
            'report_week': latest_snap.get('weekLabel') or latest_snap.get('week') or f"Week {max_week}",
            'report_date': latest_snap.get('date', datetime.now().strftime('%d %b %Y')),
            'project_name': project_name
        }

    synthesis_payload = {
        'synthesis': latest_snap.get('synthesis', latest_snap.get('executiveSummary', {})),
        'top3': latest_snap.get('top3', []),
        'sleeperOutlier': latest_snap.get('sleeperOutlier', {})
    }

    try:
        new_script = generate_multispeaker_podcast(
            metrics=metrics,
            synthesis_result=synthesis_payload,
            model=active_model,
            location=active_region
        )
    except Exception as e:
        logger.error(f"Failed to generate Gemini 3.5 Flash podcast for '{latest_key}': {e}")
        return False

    if new_script:
        latest_snap['podcastScript'] = new_script
        latest_snap['generatedBy'] = active_model
        latest_snap['podcastGeneratedBy'] = active_model

        # If flat format with both 'w30' and 'Week 30', update both
        if not is_wrapped:
            alt_key = f"Week {max_week}" if latest_key.startswith('w') else f"w{max_week}"
            if alt_key in snapshots_map and isinstance(snapshots_map[alt_key], dict):
                snapshots_map[alt_key]['podcastScript'] = new_script
                snapshots_map[alt_key]['generatedBy'] = active_model
                snapshots_map[alt_key]['podcastGeneratedBy'] = active_model

        snapshots_data['lastSynced'] = datetime.now(timezone.utc).isoformat()
        save_json_file(snapshots_path, snapshots_data)
        logger.info(f"Successfully saved Gemini 3.5 Flash podcast for '{latest_key}' to {snapshots_path}")
        return True

    return False


def sync_drive_reports(
    folder_id: str = DEFAULT_DRIVE_FOLDER_ID,
    project_name: str = 'monaro',
    data_root: Optional[str] = None,
    dry_run: bool = False,
    allow_empty: bool = False,
    model: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main ingestion engine: queries Drive, identifies new packs, ingests via dynamic Gemini model,
    ensures latest week's Gemini 3.5 Flash podcast is generated, and updates snapshots.json.
    """
    proj_dir = get_project_dir(project_name, data_root)
    snapshots_path = os.path.join(proj_dir, 'snapshots.json')
    snapshots_data = load_json_file(snapshots_path, {'snapshots': {}})

    # 1. Discover Drive Files
    try:
        drive_files = query_drive_folder_live(folder_id)
    except Exception as e:
        logger.error(f"Failed to query Google Drive folder '{folder_id}': {e}")
        if not allow_empty:
            raise
        drive_files = []

    # 2. Filter uningested
    to_ingest = filter_uningested_reports(drive_files, snapshots_data)
    logger.info(f"Found {len(to_ingest)} new report(s) needing ingestion.")

    ingested_reports = []

    if not dry_run:
        for item in to_ingest:
            file_name = item.get('name', 'Report.pdf')
            file_id = item.get('id')
            logger.info(f"Ingesting {file_name} (ID: {file_id}) with dynamic Gemini model...")
            
            # Ingest using pipeline engine
            res = ingest_report_file(
                file_name=file_name,
                file_id=file_id,
                project_name=project_name,
                data_root=data_root,
                model=model,
                location=location
            )
            ingested_reports.append(res)

    # 3. Ensure latest snapshot has a Gemini 3.5 Flash podcast script
    podcast_generated = False
    if not dry_run:
        try:
            podcast_generated = ensure_latest_podcast_generated(
                project_name=project_name,
                data_root=data_root,
                model=model,
                location=location
            )
            if podcast_generated:
                logger.info(f"Generated/refreshed Gemini 3.5 Flash podcast for latest week in project '{project_name}'")
        except Exception as e:
            logger.warning(f"Podcast generation during sync warning: {e}")

    if not dry_run and (to_ingest or podcast_generated):
        snapshots_data = load_json_file(snapshots_path, {'snapshots': {}})

    # Determine true maximum week across all snapshots
    all_week_nums = []
    snapshots_map = snapshots_data.get('snapshots', {}) if isinstance(snapshots_data, dict) else {}
    for k, snap in snapshots_map.items():
        if isinstance(snap, dict):
            wn = snap.get('weekNumber')
            if wn is not None:
                try:
                    all_week_nums.append(int(wn))
                except (ValueError, TypeError):
                    pass
            m = re.search(r'\d+', str(k))
            if m:
                try:
                    all_week_nums.append(int(m.group(0)))
                except (ValueError, TypeError):
                    pass

    if all_week_nums:
        latest_week = f"Week {max(all_week_nums)}"
    else:
        latest_week = snapshots_data.get('current_week') or 'Week 30'

    timestamp_iso = datetime.now(timezone.utc).isoformat()

    summary = {
        'status': 'success',
        'project': project_name,
        'folder_id': folder_id,
        'discovered_count': len(drive_files),
        'new_ingested_count': len(to_ingest) if not dry_run else 0,
        'pending_ingestion_count': len(to_ingest),
        'podcast_generated': podcast_generated,
        'latest_week': latest_week,
        'dry_run': dry_run,
        'timestamp': timestamp_iso
    }

    logger.info(f"Sync complete: {summary}")
    return summary


def run_preflight_diagnostics(
    folder_id: str = DEFAULT_DRIVE_FOLDER_ID,
    project_name: str = 'monaro',
    data_root: Optional[str] = None,
    model: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes end-to-end pre-flight health checks across:
      1. Google Drive access & permissions
      2. Vertex AI / Gemini availability with active model & multi-region endpoint
      3. GCS / Storage filesystem read-write capability
      4. Project dataset schema integrity
    Returns diagnostic summary dict, raising RuntimeError if any critical check fails.
    """
    from scripts.gemini_generator import get_default_gemini_model, get_default_gemini_region, get_gemini_client
    active_model = get_default_gemini_model(model)
    active_region = get_default_gemini_region(location)
    results = {}

    # 1. Drive Check
    logger.info(f"[Doctor 1/4] Checking Google Drive folder access (ID: {folder_id})...")
    try:
        service = get_drive_service()
        folder_meta = service.files().get(
            fileId=folder_id,
            supportsAllDrives=True,
            fields="id, name, mimeType, driveId, capabilities"
        ).execute()
        results['drive'] = {
            'status': 'OK',
            'name': folder_meta.get('name'),
            'id': folder_meta.get('id')
        }
        logger.info(f"  ✓ Drive folder accessible: '{folder_meta.get('name')}'")
    except Exception as e:
        results['drive'] = {'status': 'FAIL', 'error': str(e)}
        logger.error(f"  ✗ Drive folder access failed: {e}")

    # 2. Vertex AI / Gemini Check
    logger.info(f"[Doctor 2/4] Checking Vertex AI / Gemini availability with model '{active_model}' in region '{active_region}'...")
    try:
        client = get_gemini_client(location=location)
        if not client:
            raise RuntimeError("Gemini Client could not be initialized from ADC or GEMINI_API_KEY.")
        resp = client.models.generate_content(
            model=active_model,
            contents="ping"
        )
        results['vertex_ai'] = {'status': 'OK', 'model': active_model, 'region': active_region}
        logger.info(f"  ✓ Vertex AI model '{active_model}' responsive in region '{active_region}'.")
    except Exception as e:
        results['vertex_ai'] = {'status': 'FAIL', 'error': str(e), 'model': active_model, 'region': active_region}
        logger.error(f"  ✗ Vertex AI check failed: {e}")

    # 3. Storage / GCS Mount Check
    logger.info(f"[Doctor 3/4] Checking Storage / GCS volume mount writeability for project '{project_name}'...")
    proj_dir = get_project_dir(project_name, data_root)
    test_file = os.path.join(proj_dir, '.healthcheck.tmp')
    try:
        os.makedirs(proj_dir, exist_ok=True)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('ok')
        os.remove(test_file)
        results['storage'] = {'status': 'OK', 'path': proj_dir}
        logger.info(f"  ✓ Storage read/write confirmed at '{proj_dir}'.")
    except Exception as e:
        results['storage'] = {'status': 'FAIL', 'error': str(e)}
        logger.error(f"  ✗ Storage check failed: {e}")

    # 4. Schema Integrity Check
    logger.info(f"[Doctor 4/4] Validating schema integrity for snapshots.json...")
    snap_path = os.path.join(proj_dir, 'snapshots.json')
    try:
        snap_data = load_json_file(snap_path, {})
        snapshots_dict = snap_data.get('snapshots', {})
        results['schema'] = {
            'status': 'OK',
            'snapshot_count': len(snapshots_dict),
            'current_week': snap_data.get('current_week')
        }
        logger.info(f"  ✓ Schema valid: {len(snapshots_dict)} snapshots present.")
    except Exception as e:
        results['schema'] = {'status': 'FAIL', 'error': str(e)}
        logger.error(f"  ✗ Schema check failed: {e}")

    failures = [k for k, v in results.items() if v.get('status') != 'OK']
    if failures:
        raise RuntimeError(f"Pre-flight diagnostics failed on {failures}: {results}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Standalone Google Drive Scheduled Ingestion Engine")
    parser.add_argument('--folder-id', default=DEFAULT_DRIVE_FOLDER_ID, help="Google Drive folder ID")
    parser.add_argument('--project', default='monaro', help="Project slug")
    parser.add_argument('--data-root', default=None, help="Root directory for project data files")
    parser.add_argument('--dry-run', action='store_true', help="Discover files without executing ingestion")
    parser.add_argument('--allow-empty', action='store_true', help="Do not exit with error if Drive returns no files")
    parser.add_argument('--model', default=None, help="Gemini model override (defaults to GEMINI_MODEL env var or system default)")
    parser.add_argument('--gemini-region', default=None, help="Gemini Vertex AI region override (defaults to GEMINI_REGION env var or 'us-central1')")
    parser.add_argument('--doctor', action='store_true', help="Run comprehensive pre-flight health checks across Drive, Vertex AI, GCS Storage, and Schema")

    args = parser.parse_args()

    try:
        if args.doctor:
            diag = run_preflight_diagnostics(
                folder_id=args.folder_id,
                project_name=args.project,
                data_root=args.data_root,
                model=args.model,
                location=args.gemini_region
            )
            print(json.dumps(diag, indent=2))
            sys.exit(0)

        summary = sync_drive_reports(
            folder_id=args.folder_id,
            project_name=args.project,
            data_root=args.data_root,
            dry_run=args.dry_run,
            allow_empty=args.allow_empty,
            model=args.model,
            location=args.gemini_region
        )
        print(json.dumps(summary, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
