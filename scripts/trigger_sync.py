#!/usr/bin/env python3
"""
CLI Trigger Tool for Monaro Risk Dashboard Ingestion Sync.

Allows developers and administrators to trigger an immediate on-demand synchronization:
  1. Google Cloud Run Job (gcloud run jobs execute monaro-risk-sync-job)
  2. Local standalone execution (scripts/sync_drive.py)
  3. Google Cloud Tasks HTTP enqueue
"""

import os
import sys
import subprocess
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('trigger_sync')

DEFAULT_PROJECT = "monaro-risk-dev"
DEFAULT_REGION = "australia-southeast1"
DEFAULT_JOB_NAME = "monaro-risk-sync-job"


def trigger_cloud_run_job(job_name: str, project: str, region: str) -> int:
    """Executes Cloud Run Job via gcloud CLI."""
    cmd = [
        "gcloud", "run", "jobs", "execute", job_name,
        f"--project={project}",
        f"--region={region}",
        "--wait"
    ]
    logger.info(f"Triggering Cloud Run Job: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def trigger_local_sync(project_slug: str = "monaro", dry_run: bool = False) -> int:
    """Executes sync_drive.py locally."""
    script_path = os.path.join(os.path.dirname(__file__), "sync_drive.py")
    cmd = [sys.executable, script_path, f"--project={project_slug}"]
    if dry_run:
        cmd.append("--dry-run")
    logger.info(f"Executing local sync: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Trigger Monaro Risk Dashboard Data Ingestion")
    parser.add_argument("--mode", choices=["cloud", "local"], default="local", help="Execution target (cloud or local)")
    parser.add_argument("--job", default=DEFAULT_JOB_NAME, help="Cloud Run Job name")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP Project ID")
    parser.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")
    parser.add_argument("--dry-run", action="store_true", help="Run local sync in dry-run discovery mode")

    args = parser.parse_args()

    if args.mode == "cloud":
        code = trigger_cloud_run_job(args.job, args.project, args.region)
    else:
        code = trigger_local_sync(dry_run=args.dry_run)

    sys.exit(code)


if __name__ == "__main__":
    main()
