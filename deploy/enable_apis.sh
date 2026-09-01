#!/bin/bash
# ==============================================================================
# Project Monaro — Dedicated GCP API Enablement Helper
#
# Fast, idempotent script to enable all 16 required Google Cloud APIs for
# Project Dash without interactive prompts.
#
# Usage:
#   ./deploy/enable_apis.sh --project monaro-risk-dev
#   ./deploy/enable_apis.sh --project monaro-risk-prod
# ==============================================================================
set -euo pipefail

PROJECT_ID=""

usage() {
  echo "Usage: $0 --project <project-id>"
  echo ""
  echo "Enables all 16 required GCP APIs for Project Dash in a single operation."
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project|-p)
      PROJECT_ID="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ Error: --project flag is required."
  usage
fi

echo "=============================================================================="
echo "🔌 Enabling 16 Required GCP APIs for [${PROJECT_ID}]..."
echo "=============================================================================="

APIS=(
  # 1. Compute & Serverless
  "run.googleapis.com"                  # Cloud Run (Web frontend & Sync worker job)
  "compute.googleapis.com"              # Compute Engine infrastructure (IAP backend routing)
  
  # 2. Scheduling & Task Orchestration
  "cloudscheduler.googleapis.com"       # Cloud Scheduler (Recurring weekly ingestion trigger)
  "cloudtasks.googleapis.com"           # Cloud Tasks (Queueing, throttling & retries)
  
  # 3. Data & AI Integrations
  "drive.googleapis.com"                # Google Drive API v3 (Weekly PDF status packs)
  "sheets.googleapis.com"               # Google Sheets API v4 (Risk & Issue registers)
  "aiplatform.googleapis.com"           # Vertex AI (Gemini 3.7 Flash multimodal engine)
  
  # 4. CI/CD & Artifact Management
  "cloudbuild.googleapis.com"           # Cloud Build (Automated container builds in Sydney)
  "artifactregistry.googleapis.com"     # Artifact Registry (Docker images)
  "containeranalysis.googleapis.com"    # Container Analysis (Vulnerability scanning)
  "containerscanning.googleapis.com"    # Container Scanning (On-demand vulnerability scans)
  
  # 5. Security & Access Governance
  "iap.googleapis.com"                  # Identity-Aware Proxy (Google SSO zero-trust auth)
  "iam.googleapis.com"                  # IAM API (Service account & role bindings)
  
  # 6. Observability, Logging & SRE
  "logging.googleapis.com"              # Cloud Logging (Centralized structured execution logs)
  "clouderrorreporting.googleapis.com"  # Cloud Error Reporting (Container crash alerts)
  "monitoring.googleapis.com"           # Cloud Monitoring (Uptime metrics & alerts)
)

echo "Sending batch enablement request to Google Service Management..."
gcloud services enable "${APIS[@]}" --project="${PROJECT_ID}" --quiet

echo ""
echo "✅ All 16 GCP APIs successfully enabled on [${PROJECT_ID}]!"
echo "=============================================================================="
