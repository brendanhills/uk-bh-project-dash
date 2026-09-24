#!/usr/bin/env python3
"""
check_build_status.py — Query Google Cloud Build status and extract failure diagnostics.

Usage:
  python3 scripts/check_build_status.py                 # Checks monaro-risk-dev in australia-southeast1
  python3 scripts/check_build_status.py --env prod      # Checks monaro-risk-prod in australia-southeast1
  python3 scripts/check_build_status.py --env dev       # Checks monaro-risk-dev in australia-southeast1
  python3 scripts/check_build_status.py --build-id <ID>
  python3 scripts/check_build_status.py --limit 5
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

# Ensure project root is in sys.path when executed directly as a script
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from scripts.security_utils import resolve_default_project, resolve_default_region


# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run_gcloud_cmd(cmd_list):
    """Run a gcloud command and return (stdout, returncode, stderr)."""
    try:
        res = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout, res.returncode, res.stderr
    except FileNotFoundError:
        print(f"{RED}Error: 'gcloud' CLI is not installed or not found in PATH.{RESET}")
        sys.exit(1)


def resolve_default_project(env=None):
    """Resolve target GCP project ID dynamically from env vars, gcloud config, or environment suffix."""
    env_proj = (
        os.environ.get("GCP_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("CLOUDSDK_CORE_PROJECT")
    )
    if env_proj and not env:
        return env_proj

    if not env_proj:
        stdout, code, _ = run_gcloud_cmd(["gcloud", "config", "get-value", "project", "--quiet"])
        if code == 0 and stdout.strip() and stdout.strip() != "(unset)":
            env_proj = stdout.strip()

    target_env = env or os.environ.get("ENV_TARGET", "dev")
    if env_proj:
        if env_proj.endswith("-dev") or env_proj.endswith("-prod"):
            base_prefix = env_proj.rsplit("-", 1)[0]
            return f"{base_prefix}-{target_env}"
        if not env:
            return env_proj

    base_prefix = os.environ.get("GCP_PROJECT_PREFIX", "monaro-risk")
    return f"{base_prefix}-{target_env}"


def resolve_default_region():
    """Resolve target GCP region dynamically from environment variables or default."""
    return (
        os.environ.get("GCP_REGION")
        or os.environ.get("GOOGLE_CLOUD_REGION")
        or os.environ.get("CLOUDSDK_COMPUTE_REGION")
        or "australia-southeast1"
    )


def get_recent_builds(project=None, region=None, limit=1):
    """Fetch the most recent Cloud Build metadata."""
    project = project or resolve_default_project()
    region = region or resolve_default_region()
    cmd = [
        "gcloud", "builds", "list",
        f"--project={project}",
        f"--billing-project={project}",
        f"--region={region}",
        f"--limit={limit}",
        "--format=json"
    ]
    stdout, code, stderr = run_gcloud_cmd(cmd)
    if code != 0:
        print(f"{RED}Failed to query Cloud Build API:{RESET}\n{stderr.strip()}")
        sys.exit(code)
    
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        print(f"{RED}Failed to parse gcloud output as JSON.{RESET}")
        sys.exit(1)


def get_build_details(build_id, project=None, region=None):
    """Fetch full details of a specific build."""
    project = project or resolve_default_project()
    region = region or resolve_default_region()
    cmd = [
        "gcloud", "builds", "describe", build_id,
        f"--project={project}",
        f"--billing-project={project}",
        f"--region={region}",
        "--format=json"
    ]
    stdout, code, stderr = run_gcloud_cmd(cmd)
    if code != 0:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def get_build_logs(build_id, project=None, region=None, tail_lines=40, build=None):
    """Fetch build logs for a build, supporting both CLOUD_LOGGING_ONLY and GCS logsBucket."""
    project = project or (build.get("projectId") if isinstance(build, dict) else None) or resolve_default_project()
    region = region or resolve_default_region()
    if isinstance(build, dict):
        steps = build.get("steps", [])
        status_detail = build.get("statusDetail", "")
        if not steps and status_detail:
            return (
                "No container steps were executed (build aborted during pre-step trigger evaluation).\n"
                f"Reason: {status_detail}"
            )

    logging_mode = (build or {}).get("options", {}).get("logging", "") if isinstance(build, dict) else ""
    logs_bucket = (build or {}).get("logsBucket", "") if isinstance(build, dict) else ""

    # Use Cloud Logging when CLOUD_LOGGING_ONLY is set or logsBucket is absent
    if logging_mode == "CLOUD_LOGGING_ONLY" or (isinstance(build, dict) and not logs_bucket):
        log_cmd = [
            "gcloud", "logging", "read",
            f'resource.type="build" AND resource.labels.build_id="{build_id}"',
            f"--project={project}",
            f"--billing-project={project}",
            "--freshness=30d",
            f"--limit={tail_lines}",
            "--order=desc",
            "--format=value(textPayload)"
        ]
        stdout, code, stderr = run_gcloud_cmd(log_cmd)
        if code == 0 and stdout.strip():
            # Reverse desc-ordered lines so tail reads in chronological order
            lines = [line for line in reversed(stdout.strip().splitlines()) if line.strip()]
            return "\n".join(lines[-tail_lines:])
        if isinstance(build, dict) and build.get("statusDetail"):
            return f"No container log entries in Cloud Logging.\nStatus Detail: {build.get('statusDetail')}"

    cmd = [
        "gcloud", "builds", "log", build_id,
        f"--project={project}",
        f"--billing-project={project}",
        f"--region={region}"
    ]
    stdout, _, stderr = run_gcloud_cmd(cmd)
    output = stdout or stderr or ""
    if "Build does not specify logsBucket" in output:
        log_cmd = [
            "gcloud", "logging", "read",
            f'resource.type="build" AND resource.labels.build_id="{build_id}"',
            f"--project={project}",
            f"--billing-project={project}",
            "--freshness=30d",
            f"--limit={tail_lines}",
            "--order=desc",
            "--format=value(textPayload)"
        ]
        cl_stdout, cl_code, _ = run_gcloud_cmd(log_cmd)
        if cl_code == 0 and cl_stdout.strip():
            lines = [line for line in reversed(cl_stdout.strip().splitlines()) if line.strip()]
            return "\n".join(lines[-tail_lines:])
        if isinstance(build, dict) and build.get("statusDetail"):
            return f"Build failed prior to container log creation.\nStatus Detail: {build.get('statusDetail')}"
        return "No Cloud Logging entries found for this build ID."

    lines = output.strip().splitlines()
    if len(lines) > tail_lines:
        return "\n".join(lines[-tail_lines:])
    return output.strip()


def format_timestamp(iso_str):
    """Convert ISO timestamp to human-friendly local string."""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return iso_str


def inspect_build(build, project, region):
    """Inspect and display build status and diagnostics."""
    build_id = build.get("id", "Unknown")
    status = build.get("status", "UNKNOWN")
    create_time = format_timestamp(build.get("createTime"))
    finish_time = format_timestamp(build.get("finishTime"))
    
    subs = build.get("substitutions", {})
    commit_sha = subs.get("COMMIT_SHA", build.get("sourceProvenance", {}).get("resolvedGitSource", {}).get("revision", "N/A"))
    short_sha = commit_sha[:7] if commit_sha and commit_sha != "N/A" else "N/A"
    tag_name = subs.get("TAG_NAME", "")
    branch = subs.get("BRANCH_NAME", subs.get("REF_NAME", "dev"))
    ref_desc = f"tag '{tag_name}'" if tag_name else f"branch '{branch}'"
    trigger_name = subs.get("TRIGGER_NAME") or build.get("buildTriggerId") or "N/A"
    log_url = build.get("logUrl", "")

    status_icon = "🟢" if status == "SUCCESS" else ("🔴" if status in ("FAILURE", "INTERNAL_ERROR", "TIMEOUT", "CANCELLED") else "⏳")
    status_color = GREEN if status == "SUCCESS" else (RED if status in ("FAILURE", "INTERNAL_ERROR", "TIMEOUT", "CANCELLED") else YELLOW)

    print(f"\n{BOLD}══════════════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}Google Cloud Build Status — {CYAN}{project}{RESET} ({region})")
    print(f"{BOLD}══════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {BOLD}Build ID:{RESET}       {build_id}")
    print(f"  {BOLD}Status:{RESET}         {status_icon} {status_color}{BOLD}{status}{RESET}")
    print(f"  {BOLD}Trigger:{RESET}        {trigger_name} ({ref_desc})")
    print(f"  {BOLD}Commit:{RESET}         {short_sha} ({commit_sha})")
    print(f"  {BOLD}Created:{RESET}        {create_time}")
    print(f"  {BOLD}Finished:{RESET}       {finish_time}")
    if log_url:
        print(f"  {BOLD}Console URL:{RESET}    {BLUE}{log_url}{RESET}")
    print(f"{BOLD}──────────────────────────────────────────────────────────────────────{RESET}")

    # Inspect Steps
    steps = build.get("steps", [])
    if steps:
        print(f"\n{BOLD}Pipeline Steps Summary:{RESET}")
        for idx, step in enumerate(steps):
            step_name = step.get("name", "unknown")
            step_status = step.get("status", "QUEUED")
            step_exit = step.get("exitCode", None)
            
            s_icon = "✅" if step_status == "SUCCESS" else ("❌" if step_status == "FAILURE" else ("⏳" if step_status == "WORKING" else "⚪"))
            s_color = GREEN if step_status == "SUCCESS" else (RED if step_status == "FAILURE" else (YELLOW if step_status == "WORKING" else RESET))
            
            step_desc = f"Step #{idx} ({step_name})"
            if step.get("dir"):
                step_desc += f" [dir: {step.get('dir')}]"
            
            status_text = f"{s_color}{step_status}{RESET}"
            if step_exit is not None and step_exit != 0:
                status_text += f" {RED}(Exit code: {step_exit}){RESET}"
                
            print(f"  {s_icon} {step_desc:<55} → {status_text}")

    # If build failed, print detailed failure diagnostics and logs
    if status in ("FAILURE", "TIMEOUT", "INTERNAL_ERROR"):
        print(f"\n{RED}{BOLD}🚨 BUILD FAILURE DIAGNOSTICS:{RESET}")
        status_detail = build.get("statusDetail", "")
        if status_detail:
            print(f"  {BOLD}Status Detail:{RESET}  {status_detail}")

        failure_info = build.get("failureInfo", {})
        if failure_info:
            print(f"  {BOLD}Failure Type:{RESET}   {failure_info.get('type', 'N/A')}")
            print(f"  {BOLD}Detail:{RESET}         {failure_info.get('detail', 'N/A')}")
        
        # Find failed step
        failed_step = next((s for s in steps if s.get("status") == "FAILURE"), None)
        if failed_step:
            print(f"\n  {BOLD}Failed Step Container:{RESET} {failed_step.get('name')}")
            args = failed_step.get("args", [])
            if args:
                args_str = " ".join(args) if isinstance(args, list) else str(args)
                print(f"  {BOLD}Executed Command:{RESET}      {args_str[:120]}...")

        print(f"\n{BOLD}📋 Tail Build Logs (Last 30 lines):{RESET}")
        print(f"{RED}──────────────────────────────────────────────────────────────────────{RESET}")
        logs = get_build_logs(build_id, project, region, tail_lines=30, build=build)
        print(logs)
        print(f"{RED}──────────────────────────────────────────────────────────────────────{RESET}")
    else:
        print(f"\n{GREEN}{BOLD}✨ Build succeeded! Cloud Run service revision was deployed.{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Check Google Cloud Build status and extract diagnostics.")
    parser.add_argument("--env", choices=["dev", "prod"], default=None, help="Target environment ('dev' or 'prod')")
    parser.add_argument("--project", default=None, help="GCP project ID (overrides --env and environment variables)")
    parser.add_argument("--region", default=None, help="GCP region (defaults to GCP_REGION or australia-southeast1)")
    parser.add_argument("--build-id", default=None, help="Specific build ID to inspect")
    parser.add_argument("--limit", type=int, default=1, help="Number of recent builds to list/inspect (default: 1)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON data")

    args = parser.parse_args()

    project = args.project or resolve_default_project(args.env)
    region = args.region or resolve_default_region()

    if args.build_id:
        build = get_build_details(args.build_id, project, region)
        if not build:
            print(f"{RED}Build {args.build_id} not found in project {project} ({region}).{RESET}")
            sys.exit(1)
        builds = [build]
    else:
        builds = get_recent_builds(project, region, args.limit)

    if args.json:
        print(json.dumps(builds, indent=2))
        return

    if not builds:
        print(f"{YELLOW}No builds found for project {project} in region {region}.{RESET}")
        return

    for build in builds:
        inspect_build(build, project, region)


if __name__ == "__main__":
    main()
