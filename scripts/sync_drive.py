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
    """Initializes Google Drive v3 API client using Application Default Credentials."""
    from googleapiclient.discovery import build
    from google.auth import default
    credentials, _ = default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
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
    q = f"'{folder_id}' in parents and mimeType = 'application/pdf' and trashed = false"
    
    logger.info(f"Querying Google Drive folder '{folder_id}' for PDF files...")
    response = service.files().list(
        q=q,
        pageSize=100,
        fields="files(id, name, createdTime, webViewLink, webContentLink, mimeType)",
        orderBy="name desc"
    ).execute()

    files = response.get('files', [])
    reports = []
    for f in files:
        week_num = extract_week_number(f.get('name', ''))
        reports.append({
            'id': f.get('id'),
            'name': f.get('name'),
            'week_number': week_num,
            'week_label': f"Week {week_num}" if week_num else None,
            'createdTime': f.get('createdTime'),
            'webViewLink': f.get('webViewLink') or f"https://drive.google.com/file/d/{f.get('id')}/view",
            'webContentLink': f.get('webContentLink'),
            'mimeType': f.get('mimeType')
        })

    logger.info(f"Discovered {len(reports)} PDF files in Google Drive folder.")
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

    uningested = []
    for f in drive_files:
        w_num = f.get('week_number')
        if w_num is not None and w_num in existing_weeks:
            continue
        uningested.append(f)

    # Sort ascending by week number for chronological ingestion
    uningested.sort(key=lambda x: x.get('week_number') or 0)
    return uningested


def sync_drive_reports(
    folder_id: str = DEFAULT_DRIVE_FOLDER_ID,
    project_name: str = 'monaro',
    data_root: Optional[str] = None,
    dry_run: bool = False,
    allow_empty: bool = False
) -> Dict[str, Any]:
    """
    Main ingestion engine: queries Drive, identifies new packs, ingests via Gemini 2.5 Flash,
    and updates snapshots.json.
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
    latest_week = snapshots_data.get('current_week') or 'Week 29'

    if not dry_run:
        for item in to_ingest:
            file_name = item.get('name', 'Report.pdf')
            file_id = item.get('id')
            logger.info(f"Ingesting {file_name} (ID: {file_id}) with Gemini 3.7 Flash...")
            
            # Ingest using pipeline engine
            res = ingest_report_file(
                file_name=file_name,
                file_id=file_id,
                project_name=project_name,
                data_root=data_root,
                model='gemini-3.7-flash'
            )
            ingested_reports.append(res)
            if res.get('week'):
                latest_week = res.get('week')

    timestamp_iso = datetime.now(timezone.utc).isoformat()

    summary = {
        'status': 'success',
        'project': project_name,
        'folder_id': folder_id,
        'discovered_count': len(drive_files),
        'new_ingested_count': len(to_ingest) if not dry_run else 0,
        'pending_ingestion_count': len(to_ingest),
        'latest_week': latest_week,
        'dry_run': dry_run,
        'timestamp': timestamp_iso
    }

    logger.info(f"Sync complete: {summary}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Standalone Google Drive Scheduled Ingestion Engine")
    parser.add_argument('--folder-id', default=DEFAULT_DRIVE_FOLDER_ID, help="Google Drive folder ID")
    parser.add_argument('--project', default='monaro', help="Project slug")
    parser.add_argument('--data-root', default=None, help="Root directory for project data files")
    parser.add_argument('--dry-run', action='store_true', help="Discover files without executing ingestion")
    parser.add_argument('--allow-empty', action='store_true', help="Do not exit with error if Drive returns no files")

    args = parser.parse_args()

    try:
        summary = sync_drive_reports(
            folder_id=args.folder_id,
            project_name=args.project,
            data_root=args.data_root,
            dry_run=args.dry_run,
            allow_empty=args.allow_empty
        )
        print(json.dumps(summary, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
