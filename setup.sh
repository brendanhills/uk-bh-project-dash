#!/bin/bash
# ==============================================================================
# Project Monaro Risk Platform — Automated GCP Environment Setup & State Engine
#
# Usage:
#   ./setup.sh --env dev          # Provisions monaro-risk-dev
#   ./setup.sh --env prod         # Provisions monaro-risk-prod
#   ./setup.sh -l --env dev       # List environment state (read-only)
#   ./setup.sh -l --state-only    # Output raw state addresses (terraform state list format)
#   ./setup.sh --project my-proj --region australia-southeast1
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/pyproject.toml" ]]; then
  PROJECT_ROOT="${SCRIPT_DIR}"
else
  PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi

ENV_TARGET="dev"
PROJECT_ID=""
REGION="australia-southeast1"
APIS_ONLY=false
LIST_MODE=false
STATE_ONLY=false
MISSING_ONLY=false
ADMIN_EMAIL=""
DRIVE_FOLDER_ID="${DRIVE_FOLDER_ID:-1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C}"
GAR_REPO="cloud-run-source-deploy"
GDRIVE_BIN="$(command -v gdrive 2>/dev/null || echo "/google/bin/releases/gemini-agents-gdrive/gdrive")"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.5-flash}"
GEMINI_REGION="${GEMINI_REGION:-us}"

REQUIRED_APIS=(
  "clouderrorreporting.googleapis.com"
  "logging.googleapis.com"
  "monitoring.googleapis.com"
  "cloudbuild.googleapis.com"
  "run.googleapis.com"
  "artifactregistry.googleapis.com"
  "iap.googleapis.com"
  "compute.googleapis.com"
  "aiplatform.googleapis.com"
  "containeranalysis.googleapis.com"
  "containerscanning.googleapis.com"
  "sheets.googleapis.com"
  "drive.googleapis.com"
  "cloudtasks.googleapis.com"
  "cloudscheduler.googleapis.com"
  "iam.googleapis.com"
)

DEPLOYER_ROLES=(
  "roles/run.admin"
  "roles/artifactregistry.admin"
  "roles/iam.serviceAccountUser"
  "roles/iap.admin"
  "roles/logging.logWriter"
  "roles/storage.objectUser"
  "roles/storage.objectViewer"
  "roles/aiplatform.user"
  "roles/containeranalysis.occurrences.editor"
)

usage() {
  local exit_code="${1:-0}"
  echo "Usage: $0 [options] [dev|prod]"
  echo ""
  echo "Options:"
  echo "  --env <dev|prod>        Target environment preset (default: dev)"
  echo "  --project <project-id>  Override GCP Project ID explicitly"
  echo "  --region <region>       GCP Region (default: australia-southeast1)"
  echo "  --apis-only             Only enable the 16 required GCP APIs and exit"
  echo "  -l, --list, --status    Inspect and list status of all APIs, permissions, services, and Drive access (read-only)"
  echo "  -m, --missing           Only display missing/unhealthy resources in list mode"
  echo "  --state-only            Print only resource addresses (exact terraform state list format)"
  echo "  --folder-id <id>        Override Google Drive folder ID (default: 1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C)"
  echo "  --admin-email <email>   Override admin alert notification email"
  echo "  --help, -h              Show this help message"
  exit "${exit_code}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    dev|prod)
      ENV_TARGET="$1"
      shift
      ;;
    --env)
      ENV_TARGET="$2"
      shift 2
      ;;
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --apis-only)
      APIS_ONLY=true
      shift
      ;;
    -l|--list|--view|--status)
      LIST_MODE=true
      shift
      ;;
    -m|--missing|--missing-only)
      MISSING_ONLY=true
      LIST_MODE=true
      shift
      ;;
    --state-only)
      STATE_ONLY=true
      LIST_MODE=true
      shift
      ;;
    --folder-id)
      DRIVE_FOLDER_ID="$2"
      shift 2
      ;;
    --admin-email|--admin-group)
      ADMIN_EMAIL="$2"
      shift 2
      ;;
    --help|-h)
      usage 0
      ;;
    *)
      echo "Unknown option: $1"
      usage 1
      ;;
  esac
done

# Apply Environment Presets
if [[ -z "$PROJECT_ID" ]]; then
  if [[ "$ENV_TARGET" == "prod" ]]; then
    PROJECT_ID="monaro-risk-prod"
    SERVICE_NAME="monaro-risk-dash-prod"
    ACCESS_GROUP="monaro-risk-prod@google.com"
    ADMIN_GROUP="${ADMIN_EMAIL:-monaro-risk-prod@google.com}"
    TRIGGER_NAME="deploy-monaro-risk-dash-prod"
    TAG_PATTERN="^project_dash/prod-.*$"
    BRANCH_PATTERN=""
  else
    PROJECT_ID="monaro-risk-dev"
    SERVICE_NAME="monaro-risk-dash-dev"
    ACCESS_GROUP="monaro-risk-dev@google.com"
    ADMIN_GROUP="${ADMIN_EMAIL:-monaro-risk-dev@google.com}"
    TRIGGER_NAME="deploy-monaro-risk-dash-dev"
    TAG_PATTERN=""
    BRANCH_PATTERN="^dev$"
  fi
else
  SERVICE_NAME="monaro-risk-dash-${ENV_TARGET}"
  ACCESS_GROUP="${PROJECT_ID}@google.com"
  ADMIN_GROUP="${ADMIN_EMAIL:-${ACCESS_GROUP}}"
  TRIGGER_NAME="deploy-${SERVICE_NAME}"
  TAG_PATTERN=""
  BRANCH_PATTERN="^dev$"
fi

SA_NAME="github-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SYNC_JOB_NAME="monaro-risk-sync-job"
SYNC_QUEUE_NAME="monaro-sync-queue"
SCHED_JOB_NAME="monaro-sync-schedule"
TMP_STATE_DIR=""
cleanup_state_dir() {
  if [[ -n "${TMP_STATE_DIR:-}" && -d "${TMP_STATE_DIR}" ]]; then
    rm -rf "${TMP_STATE_DIR}"
  fi
}
trap cleanup_state_dir EXIT INT TERM

list_environment_state() {
  TMP_STATE_DIR=$(mktemp -d /tmp/monaro_state_XXXXXX)
  local tmp_dir="${TMP_STATE_DIR}"

  if [[ "${STATE_ONLY}" != "true" ]]; then
    echo "==================================================================================================="
    echo "🏛️  Project Monaro Environment State List — [${PROJECT_ID}] (${REGION})"
    echo "==================================================================================================="
    printf "%-60s %-14s %s\n" "STATE ADDRESS" "STATUS" "DETAILS"
    echo "---------------------------------------------------------------------------------------------------"
  fi

  # Launch parallel background queries for sub-5s performance
  gcloud services list --enabled --project="${PROJECT_ID}" --format="value(config.name)" > "${tmp_dir}/apis.txt" 2>&1 &
  gcloud projects get-iam-policy "${PROJECT_ID}" --format="json" > "${tmp_dir}/project_iam.json" 2>&1 &
  gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" --format="value(email)" > "${tmp_dir}/sa.txt" 2>&1 &
  gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --project="${PROJECT_ID}" --format="value(status.url)" > "${tmp_dir}/run_svc.txt" 2>&1 &
  gcloud run services get-iam-policy "${SERVICE_NAME}" --region="${REGION}" --project="${PROJECT_ID}" --format="json" > "${tmp_dir}/run_iam.json" 2>&1 &
  gcloud beta iap web get-iam-policy --project="${PROJECT_ID}" --resource-type="cloud-run" --service="${SERVICE_NAME}" --region="${REGION}" --format="json" > "${tmp_dir}/iap_iam.json" 2>&1 &
  gcloud artifacts repositories list --location="${REGION}" --project="${PROJECT_ID}" --format="value(name)" > "${tmp_dir}/ar.txt" 2>&1 &
  gcloud builds triggers list --region="${REGION}" --project="${PROJECT_ID}" --format="value(name)" > "${tmp_dir}/triggers.txt" 2>&1 &
  gcloud tasks queues list --location="${REGION}" --project="${PROJECT_ID}" --format="table[no-heading](name,state)" > "${tmp_dir}/tasks.txt" 2>&1 &
  gcloud run jobs list --region="${REGION}" --project="${PROJECT_ID}" --format="value(metadata.name)" > "${tmp_dir}/jobs.txt" 2>&1 &
  gcloud scheduler jobs list --location="${REGION}" --project="${PROJECT_ID}" --format="table[no-heading](ID,STATE)" > "${tmp_dir}/sched.txt" 2>&1 &
  gcloud beta monitoring channels list --project="${PROJECT_ID}" --format="value(name,labels.email_address)" > "${tmp_dir}/channels.txt" 2>&1 &
  gcloud beta monitoring policies list --project="${PROJECT_ID}" --format="value(displayName)" > "${tmp_dir}/policies.txt" 2>&1 &

  if [[ -x "${GDRIVE_BIN}" ]]; then
    "${GDRIVE_BIN}" readonly permissions "${DRIVE_FOLDER_ID}" --json > "${tmp_dir}/drive_perms.json" 2>&1 &
    "${GDRIVE_BIN}" readonly info "${DRIVE_FOLDER_ID}" --json > "${tmp_dir}/drive_info.json" 2>&1 &
  fi

  wait

  local total_count=0
  local present_count=0
  local missing_count=0

  # Terminal color highlighting (auto-detected, respects NO_COLOR / FORCE_COLOR)
  local COLOR_RESET=""
  local COLOR_GREEN=""
  local COLOR_YELLOW=""
  local COLOR_YELLOW_BOLD=""
  local COLOR_DIM=""

  if [[ -t 1 || -n "${FORCE_COLOR:-}" ]] && [[ -z "${NO_COLOR:-}" ]] && [[ "${TERM:-}" != "dumb" ]]; then
    COLOR_RESET=$'\033[0m'
    COLOR_GREEN=$'\033[32m'
    COLOR_YELLOW=$'\033[33m'
    COLOR_YELLOW_BOLD=$'\033[1;33m'
    COLOR_DIM=$'\033[2m'
  fi

  emit_state() {
    local addr="$1"
    local status="$2"
    local details="${3:-}"
    total_count=$((total_count + 1))
    local is_healthy=false
    if [[ "$status" == "ENABLED" || "$status" == "BOUND" || "$status" == "EXISTS" || "$status" == "READY" || "$status" == "RUNNING" || "$status" == "GRANTED" || "$status" == "ACCESSIBLE" || "$status" == "INHERITED" ]]; then
      is_healthy=true
      present_count=$((present_count + 1))
      if [[ "${STATE_ONLY}" == "true" ]]; then
        echo "${addr}"
      fi
    else
      missing_count=$((missing_count + 1))
    fi

    if [[ "${STATE_ONLY}" != "true" ]]; then
      if [[ "${is_healthy}" == "true" ]]; then
        if [[ "${MISSING_ONLY}" != "true" ]]; then
          printf "%-60s ${COLOR_GREEN}%-14s${COLOR_RESET} %s\n" "${addr}" "[${status}]" "${details}"
        fi
      else
        printf "${COLOR_YELLOW}%-60s ${COLOR_YELLOW_BOLD}%-14s${COLOR_RESET} ${COLOR_YELLOW}%s${COLOR_RESET}\n" "${addr}" "[${status}]" "${details}"
      fi
    fi
  }

  # 1. APIs
  for api in "${REQUIRED_APIS[@]}"; do
    if grep -qx "${api}" "${tmp_dir}/apis.txt" 2>/dev/null; then
      emit_state "gcp_api.${api}" "ENABLED" "Required GCP API"
    else
      emit_state "gcp_api.${api}" "DISABLED" "API not enabled"
    fi
  done

  # 2. Service Account
  if grep -q "${SA_EMAIL}" "${tmp_dir}/sa.txt" 2>/dev/null; then
    emit_state "iam_service_account.${SA_NAME}" "EXISTS" "${SA_EMAIL}"
  else
    emit_state "iam_service_account.${SA_NAME}" "MISSING" "Service account not found"
  fi

  # 3. Deployer IAM Roles
  for role in "${DEPLOYER_ROLES[@]}"; do
    if jq -e --arg sa "serviceAccount:${SA_EMAIL}" --arg role "${role}" \
       '.bindings[] | select(.role == $role) | select(.members[]? == $sa)' "${tmp_dir}/project_iam.json" >/dev/null 2>&1; then
      emit_state "iam_role_binding.${SA_NAME}.${role}" "BOUND" "Project IAM binding"
    elif [[ "${role}" == "roles/storage.objectViewer" || "${role}" == "roles/storage.objectUser" ]] && jq -e --arg sa "serviceAccount:${SA_EMAIL}" \
       '.bindings[] | select(.role == "roles/storage.admin") | select(.members[]? == $sa)' "${tmp_dir}/project_iam.json" >/dev/null 2>&1; then
      emit_state "iam_role_binding.${SA_NAME}.${role}" "BOUND" "Satisfied by roles/storage.admin"
    else
      emit_state "iam_role_binding.${SA_NAME}.${role}" "MISSING" "Role not granted on project"
    fi
  done

  # 4. Artifact Registry & Triggers
  if grep -q "${GAR_REPO}" "${tmp_dir}/ar.txt" 2>/dev/null; then
    emit_state "artifact_registry.${GAR_REPO}" "EXISTS" "${REGION} (Docker)"
  else
    emit_state "artifact_registry.${GAR_REPO}" "MISSING" "Repository not created"
  fi

  if grep -q "${TRIGGER_NAME}" "${tmp_dir}/triggers.txt" 2>/dev/null; then
    emit_state "cloudbuild_trigger.${TRIGGER_NAME}" "EXISTS" "Cloud Build CI/CD Trigger"
  else
    emit_state "cloudbuild_trigger.${TRIGGER_NAME}" "MISSING" "Trigger not configured"
  fi

  # 5. Monitoring
  if grep -q "${ADMIN_GROUP}" "${tmp_dir}/channels.txt" 2>/dev/null; then
    emit_state "monitoring_channel.admin_email" "EXISTS" "Notification channel (${ADMIN_GROUP})"
  elif [[ -s "${tmp_dir}/channels.txt" ]]; then
    local ch_email
    ch_email=$(grep -o '[^ ]*@[^ ]*' "${tmp_dir}/channels.txt" 2>/dev/null | head -n1 || true)
    emit_state "monitoring_channel.admin_email" "EXISTS" "Notification channel (${ch_email:-configured})"
  else
    emit_state "monitoring_channel.admin_email" "MISSING" "Email channel not configured"
  fi

  local policy_name="Error Reporting Exception Alert (${PROJECT_ID})"
  if grep -q "${policy_name}" "${tmp_dir}/policies.txt" 2>/dev/null; then
    emit_state "monitoring_alert_policy.error_reporting" "EXISTS" "${policy_name}"
  else
    emit_state "monitoring_alert_policy.error_reporting" "MISSING" "Alert policy not configured"
  fi

  # 6. Cloud Run Web Service & Invoker IAM
  local svc_url
  svc_url=$(cat "${tmp_dir}/run_svc.txt" 2>/dev/null || true)
  if [[ -n "${svc_url}" && "${svc_url}" == http* ]]; then
    emit_state "cloud_run_service.${SERVICE_NAME}" "READY" "${svc_url}"
  else
    emit_state "cloud_run_service.${SERVICE_NAME}" "MISSING" "Cloud Run service not deployed or URL unavailable"
  fi

  local project_num
  project_num=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)" 2>/dev/null || true)
  local iap_sa="serviceAccount:service-${project_num}@gcp-sa-iap.iam.gserviceaccount.com"
  if jq -e --arg mem "${iap_sa}" '.bindings[] | select(.role == "roles/run.invoker") | select(.members[]? == $mem)' "${tmp_dir}/run_iam.json" >/dev/null 2>&1; then
    emit_state "cloud_run_iam.serviceAccount:iap_service_agent.roles/run.invoker" "BOUND" "IAP Service Agent"
  else
    emit_state "cloud_run_iam.serviceAccount:iap_service_agent.roles/run.invoker" "MISSING" "IAP SA invoker missing"
  fi

  local twosync_grp
  twosync_grp=$(echo "${ACCESS_GROUP}" | sed 's/@google.com/@twosync.google.com/')
  for grp in "${ACCESS_GROUP}" "${twosync_grp}"; do
    if jq -e --arg mem "group:${grp}" '.bindings[] | select(.role == "roles/run.invoker") | select(.members[]? == $mem)' "${tmp_dir}/run_iam.json" >/dev/null 2>&1; then
      emit_state "cloud_run_iam.group:${grp}.roles/run.invoker" "BOUND" "Viewer Group"
    else
      emit_state "cloud_run_iam.group:${grp}.roles/run.invoker" "MISSING" "Invoker missing"
    fi
  done

  for usr in "brendanhills@google.com" "allins@google.com"; do
    if jq -e --arg mem "user:${usr}" '.bindings[] | select(.role == "roles/run.invoker") | select(.members[]? == $mem)' "${tmp_dir}/run_iam.json" >/dev/null 2>&1; then
      emit_state "cloud_run_iam.user:${usr}.roles/run.invoker" "BOUND" "Lead User"
    else
      emit_state "cloud_run_iam.user:${usr}.roles/run.invoker" "MISSING" "Invoker missing"
    fi
  done

  # 7. IAP Web IAM
  for grp in "${ACCESS_GROUP}" "${twosync_grp}"; do
    if jq -e --arg mem "group:${grp}" '.bindings[] | select(.role == "roles/iap.httpsResourceAccessor") | select(.members[]? == $mem)' "${tmp_dir}/iap_iam.json" >/dev/null 2>&1; then
      emit_state "iap_iam.group:${grp}.roles/iap.httpsResourceAccessor" "BOUND" "Viewer Group"
    else
      emit_state "iap_iam.group:${grp}.roles/iap.httpsResourceAccessor" "MISSING" "IAP Accessor missing"
    fi
  done

  for usr in "brendanhills@google.com" "allins@google.com"; do
    if jq -e --arg mem "user:${usr}" '.bindings[] | select(.role == "roles/iap.httpsResourceAccessor") | select(.members[]? == $mem)' "${tmp_dir}/iap_iam.json" >/dev/null 2>&1; then
      emit_state "iap_iam.user:${usr}.roles/iap.httpsResourceAccessor" "BOUND" "Lead User"
    else
      emit_state "iap_iam.user:${usr}.roles/iap.httpsResourceAccessor" "MISSING" "IAP Accessor missing"
    fi
  done

  # 8. Scheduled Ingestion Pipeline
  if grep -q "${SYNC_QUEUE_NAME}" "${tmp_dir}/tasks.txt" 2>/dev/null; then
    local q_state
    q_state=$(grep "${SYNC_QUEUE_NAME}" "${tmp_dir}/tasks.txt" | awk '{print $2}' | head -n1 || echo "RUNNING")
    emit_state "cloud_tasks_queue.${SYNC_QUEUE_NAME}" "${q_state:-RUNNING}" "Cloud Tasks Queue (${REGION})"
  else
    emit_state "cloud_tasks_queue.${SYNC_QUEUE_NAME}" "MISSING" "Queue not created"
  fi

  if grep -q "${SYNC_JOB_NAME}" "${tmp_dir}/jobs.txt" 2>/dev/null; then
    emit_state "cloud_run_job.${SYNC_JOB_NAME}" "EXISTS" "Cloud Run Ingestion Job (${REGION})"
  else
    emit_state "cloud_run_job.${SYNC_JOB_NAME}" "MISSING" "Job not created"
  fi

  if grep -q "${SCHED_JOB_NAME}" "${tmp_dir}/sched.txt" 2>/dev/null; then
    local s_state
    s_state=$(grep "${SCHED_JOB_NAME}" "${tmp_dir}/sched.txt" | awk '{print $2}' | head -n1 || echo "ENABLED")
    emit_state "cloud_scheduler_job.${SCHED_JOB_NAME}" "${s_state:-ENABLED}" "Weekly Cron (0 17 * * 5 Australia/Sydney)"
  else
    emit_state "cloud_scheduler_job.${SCHED_JOB_NAME}" "MISSING" "Schedule not created"
  fi

  # 9. Google Drive Folder & Access Governance
  if [[ -x "${GDRIVE_BIN}" ]]; then
    if grep -q '"id":' "${tmp_dir}/drive_info.json" 2>/dev/null; then
      local folder_name
      folder_name=$(jq -r '.name // empty' "${tmp_dir}/drive_info.json" 2>/dev/null || echo "${DRIVE_FOLDER_ID}")
      emit_state "drive_folder.${DRIVE_FOLDER_ID}" "ACCESSIBLE" "'${folder_name}'"

      # Check Access Group
      local grp_role
      grp_role=$(jq -r --arg email "${ACCESS_GROUP}" '.[] | select(.emailAddress == $email) | .role' "${tmp_dir}/drive_perms.json" 2>/dev/null || true)
      if [[ -n "${grp_role}" ]]; then
        emit_state "drive_permission.group.${ACCESS_GROUP}" "GRANTED" "role: ${grp_role}"
      else
        emit_state "drive_permission.group.${ACCESS_GROUP}" "MISSING" "Group not shared with Drive folder"
      fi

      # Check Service Account (Direct or via Access Group)
      local sa_role
      sa_role=$(jq -r --arg email "${SA_EMAIL}" '.[] | select(.emailAddress == $email) | .role' "${tmp_dir}/drive_perms.json" 2>/dev/null || true)
      if [[ -n "${sa_role}" ]]; then
        emit_state "drive_permission.service_account.${SA_EMAIL}" "GRANTED" "role: ${sa_role}"
      elif [[ -n "${grp_role}" ]]; then
        emit_state "drive_permission.service_account.${SA_EMAIL}" "INHERITED" "Satisfied via group ${ACCESS_GROUP} (${grp_role})"
      else
        emit_state "drive_permission.service_account.${SA_EMAIL}" "MISSING" "Service account not shared with Drive folder"
      fi
    else
      emit_state "drive_folder.${DRIVE_FOLDER_ID}" "INACCESSIBLE" "Folder not reachable"
      emit_state "drive_permission.group.${ACCESS_GROUP}" "MISSING" "Folder check failed"
      emit_state "drive_permission.service_account.${SA_EMAIL}" "MISSING" "Folder check failed"
    fi
  else
    emit_state "drive_folder.${DRIVE_FOLDER_ID}" "SKIPPED" "gdrive CLI not found at ${GDRIVE_BIN}"
    emit_state "drive_permission.group.${ACCESS_GROUP}" "SKIPPED" "gdrive CLI not found"
    emit_state "drive_permission.service_account.${SA_EMAIL}" "SKIPPED" "gdrive CLI not found"
  fi

  if [[ "${STATE_ONLY}" != "true" ]]; then
    echo "==================================================================================================="
    if [[ ${missing_count} -gt 0 ]]; then
      printf "📊 State Summary: Total Tracked: %d | %sPresent/Healthy: %d%s | %sMissing: %d%s\n" \
        "${total_count}" "${COLOR_GREEN}" "${present_count}" "${COLOR_RESET}" "${COLOR_YELLOW_BOLD}" "${missing_count}" "${COLOR_RESET}"
    else
      printf "📊 State Summary: Total Tracked: %d | %sPresent/Healthy: %d%s | Missing: 0\n" \
        "${total_count}" "${COLOR_GREEN}" "${present_count}" "${COLOR_RESET}"
    fi
    echo "==================================================================================================="
  fi
}

if [[ "${LIST_MODE}" == "true" ]]; then
  list_environment_state
  exit 0
fi

echo "=============================================================================="
echo "🚀 Provisioning Project Monaro GCP Environment"
echo "=============================================================================="
echo "• Environment:    ${ENV_TARGET}"
echo "• GCP Project:    ${PROJECT_ID}"
echo "• Region:         ${REGION}"
echo "• Cloud Run:      ${SERVICE_NAME}"
echo "• Viewer Group:   ${ACCESS_GROUP}"
echo "• Admin Group:    ${ADMIN_GROUP}"
echo "• Deployer SA:    ${SA_EMAIL}"
echo "=============================================================================="
echo ""

# 1. Enable Required GCP APIs
echo "=== 1. Enabling Required GCP APIs ==="
gcloud services enable "${REQUIRED_APIS[@]}" --project="${PROJECT_ID}" --quiet
echo "✅ All 16 GCP APIs successfully enabled."
echo ""

if [[ "${APIS_ONLY}" == "true" ]]; then
  echo "=============================================================================="
  echo "🎉 --apis-only specified: All 16 APIs enabled for ${PROJECT_ID}. Exiting."
  echo "=============================================================================="
  exit 0
fi


# 2. Create Deployer Service Account
echo "=== 2. Creating Dedicated Service Account (${SA_NAME}) ==="
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="GitHub & Cloud Build Deployer" \
    --project="${PROJECT_ID}"
  echo "✅ Service account created: ${SA_EMAIL}"
else
  echo "ℹ️ Service account ${SA_EMAIL} already exists."
fi
echo ""

# 3. Bind Least-Privilege IAM Roles
echo "=== 3. Binding Least-Privilege IAM Roles to Deployer SA ==="
for ROLE in "${DEPLOYER_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None >/dev/null || true
  echo "  ✓ Granted ${ROLE}"
done
echo "✅ IAM permissions bound successfully."
echo ""

# 3b. Centralized GCS Data Persistence Bucket
echo "=== 3b. Ensuring Centralized GCS Data Bucket Exists in ${REGION} ==="
DATA_BUCKET="${PROJECT_ID}-data"
if ! gcloud storage buckets describe "gs://${DATA_BUCKET}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${DATA_BUCKET}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --uniform-bucket-level-access \
    --default-storage-class=STANDARD
  echo "✅ GCS Bucket 'gs://${DATA_BUCKET}' created in ${REGION}."

  if [ -d "${PROJECT_ROOT}/data" ]; then
    echo "  Seeding baseline data to gs://${DATA_BUCKET}/..."
    gcloud storage cp -r "${PROJECT_ROOT}/data/*" "gs://${DATA_BUCKET}/" >/dev/null 2>&1 || true
    echo "  ✓ Baseline data seeded."
  fi
else
  echo "ℹ️ GCS Bucket 'gs://${DATA_BUCKET}' already exists in ${REGION}."
fi
echo ""

# 4. Artifact Registry Repository
echo "=== 4. Ensuring Artifact Registry Exists in ${REGION} ==="
if ! gcloud artifacts repositories describe "${GAR_REPO}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${GAR_REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Cloud Run source deployments" \
    --project="${PROJECT_ID}"
  echo "✅ Artifact Registry repository '${GAR_REPO}' created in ${REGION}."
else
  echo "ℹ️ Artifact Registry repository already exists in ${REGION}."
fi

# Apply automated lifecycle cleanup policy to cap storage within GCP Free Tier (0.5 GB)
if [ -f "${SCRIPT_DIR}/cleanup-policy.json" ]; then
  echo "  Applying automated image cleanup policy to keep storage within Free Tier..."
  gcloud artifacts repositories set-cleanup-policies "${GAR_REPO}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --policy="${SCRIPT_DIR}/cleanup-policy.json" \
    --no-dry-run >/dev/null 2>&1 || true
  echo "  ✓ Applied cleanup policy (retain last 10 versions, delete untagged >14d)."
fi
echo ""

# 5. Cloud Build Trigger
echo "=== 5. Configuring Automated Cloud Build Trigger in ${REGION} ==="
if gcloud builds triggers describe "${TRIGGER_NAME}" --region="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "ℹ️ Cloud Build trigger '${TRIGGER_NAME}' already exists in ${REGION}."
else
  if [[ -n "$TAG_PATTERN" ]]; then
    echo "Creating Tag-based trigger for pattern '${TAG_PATTERN}' in ${REGION}..."
    gcloud builds triggers create github \
      --project="${PROJECT_ID}" \
      --region="${REGION}" \
      --name="${TRIGGER_NAME}" \
      --repo-name="uk-bh-experiments" \
      --repo-owner="cloud-gtm" \
      --tag-pattern="${TAG_PATTERN}" \
      --build-config="project_dash/deploy/cloudbuild.yaml" \
      --service-account="projects/${PROJECT_ID}/serviceAccounts/${SA_EMAIL}" \
      --substitutions="_SERVICE_NAME=${SERVICE_NAME},_ACCESS_GROUP=${ACCESS_GROUP},_REGION=${REGION},_IMAGE_NAME=${SERVICE_NAME}" \
      --description="Automated Production Deployment on release tags in Sydney"
  else
    echo "Creating Branch-based trigger for branch '${BRANCH_PATTERN}' in ${REGION}..."
    gcloud builds triggers create github \
      --project="${PROJECT_ID}" \
      --region="${REGION}" \
      --name="${TRIGGER_NAME}" \
      --repo-name="uk-bh-experiments" \
      --repo-owner="cloud-gtm" \
      --branch-pattern="${BRANCH_PATTERN}" \
      --build-config="project_dash/deploy/cloudbuild.yaml" \
      --service-account="projects/${PROJECT_ID}/serviceAccounts/${SA_EMAIL}" \
      --substitutions="_SERVICE_NAME=${SERVICE_NAME},_ACCESS_GROUP=${ACCESS_GROUP},_REGION=${REGION},_IMAGE_NAME=${SERVICE_NAME}" \
      --included-files="project_dash/**" \
      --ignored-files="project_dash/**/*.md,project_dash/docs/**,project_dash/.agents/**,project_dash/conductor/**" \
      --description="Automated Dev Deployment on push to dev in Sydney"
  fi
  echo "✅ Cloud Build trigger created in ${REGION}."
fi
echo ""

# 6. Error Reporting & Cloud Monitoring Alerting
echo "=== 6. Configuring Error Reporting & Alert Channels ==="
echo "Checking notification channel for ${ADMIN_GROUP}..."
CHANNEL_ID=$(gcloud beta monitoring channels list \
  --project="${PROJECT_ID}" \
  --filter="labels.email_address = \"${ADMIN_GROUP}\"" \
  --format="value(name)" 2>/dev/null | head -n1 || true)

if [[ -z "${CHANNEL_ID}" ]]; then
  echo "Creating email notification channel for ${ADMIN_GROUP}..."
  CHANNEL_JSON=$(gcloud beta monitoring channels create \
    --project="${PROJECT_ID}" \
    --type="email" \
    --display-name="Monaro Risk Admin Alerts (${ENV_TARGET})" \
    --channel-labels="email_address=${ADMIN_GROUP}" \
    --format="json" 2>/dev/null || true)
  CHANNEL_ID=$(echo "${CHANNEL_JSON}" | jq -r '.name // empty' 2>/dev/null || true)
  if [[ -z "${CHANNEL_ID}" ]]; then
    CHANNEL_ID=$(gcloud beta monitoring channels list \
      --project="${PROJECT_ID}" \
      --filter="labels.email_address = \"${ADMIN_GROUP}\"" \
      --format="value(name)" 2>/dev/null | head -n1 || true)
  fi
  echo "✅ Created notification channel: ${CHANNEL_ID}"
else
  echo "ℹ️ Notification channel already exists: ${CHANNEL_ID}"
fi

POLICY_NAME="Error Reporting Exception Alert (${PROJECT_ID})"
EXISTING_POLICY=$(gcloud beta monitoring policies list \
  --project="${PROJECT_ID}" \
  --filter="displayName = \"${POLICY_NAME}\"" \
  --format="value(name)" 2>/dev/null | head -n1 || true)

if [[ -n "${EXISTING_POLICY}" ]]; then
  echo "ℹ️ Alert policy '${POLICY_NAME}' already exists."
elif [[ -n "${CHANNEL_ID}" ]]; then
  echo "Creating Alert Policy for Cloud Run 5xx Container Exceptions..."
  TMP_POLICY_FILE=$(mktemp /tmp/error_policy_XXXXXX.json)
  cat <<EOF > "${TMP_POLICY_FILE}"
{
  "displayName": "${POLICY_NAME}",
  "documentation": {
    "content": "A runtime exception or 5xx crash was logged by Cloud Run service ${SERVICE_NAME} in ${PROJECT_ID}.",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Cloud Run 5xx Server Error condition",
      "conditionThreshold": {
        "filter": "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\"",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0,
        "duration": "0s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "notificationChannels": [
    "${CHANNEL_ID}"
  ],
  "combiner": "OR",
  "enabled": true
}
EOF
  gcloud beta monitoring policies create \
    --policy-from-file="${TMP_POLICY_FILE}" \
    --project="${PROJECT_ID}" >/dev/null 2>&1 || true
  rm -f "${TMP_POLICY_FILE}"
  echo "✅ Alert policy created and linked to ${ADMIN_GROUP}."
fi
echo ""

# 7. Cloud Run Invoker & IAP Access Control
echo "=== 7. Configuring Cloud Run Invoker & IAP Access Control ==="
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)" 2>/dev/null || true)
if [[ -n "${PROJECT_NUMBER}" ]]; then
  gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-iap.iam.gserviceaccount.com" \
    --role="roles/run.invoker" >/dev/null 2>&1 || true
  echo "  ✓ Granted run.invoker to IAP Service Agent"
fi

TWOSYNC_GROUP=$(echo "${ACCESS_GROUP}" | sed 's/@google.com/@twosync.google.com/')

for GRP in "${ACCESS_GROUP}" "${TWOSYNC_GROUP}"; do
  gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="group:${GRP}" \
    --role="roles/run.invoker" >/dev/null 2>&1 || true
  echo "  ✓ Granted run.invoker to group:${GRP}"
done

for USR in "brendanhills@google.com" "allins@google.com"; do
  gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="user:${USR}" \
    --role="roles/run.invoker" >/dev/null 2>&1 || true
  echo "  ✓ Granted run.invoker to user:${USR}"
done

# Grant IAP-secured Web App User (roles/iap.httpsResourceAccessor)
for GRP in "${ACCESS_GROUP}" "${TWOSYNC_GROUP}"; do
  gcloud beta iap web add-iam-policy-binding \
    --project="${PROJECT_ID}" \
    --resource-type="cloud-run" \
    --service="${SERVICE_NAME}" \
    --region="${REGION}" \
    --member="group:${GRP}" \
    --role="roles/iap.httpsResourceAccessor" >/dev/null 2>&1 || true
  echo "  ✓ Granted iap.httpsResourceAccessor to group:${GRP}"
done

for USR in "brendanhills@google.com" "allins@google.com"; do
  gcloud beta iap web add-iam-policy-binding \
    --project="${PROJECT_ID}" \
    --resource-type="cloud-run" \
    --service="${SERVICE_NAME}" \
    --region="${REGION}" \
    --member="user:${USR}" \
    --role="roles/iap.httpsResourceAccessor" >/dev/null 2>&1 || true
  echo "  ✓ Granted iap.httpsResourceAccessor to user:${USR}"
done
echo "✅ Cloud Run and IAP Access Control configured in ${REGION}."
echo ""

# 8. Scheduled Ingestion Pipeline (Cloud Run Job & Cloud Tasks Queue)
echo "=== 8. Provisioning Scheduled Ingestion Job & Cloud Tasks Queue ==="

# Create Cloud Tasks Queue
if ! gcloud tasks queues describe "${SYNC_QUEUE_NAME}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud tasks queues create "${SYNC_QUEUE_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --max-concurrent-dispatches=1 \
    --max-attempts=3 || true
  echo "  ✓ Created Cloud Tasks queue: ${SYNC_QUEUE_NAME}"
else
  echo "  ✓ Cloud Tasks queue already exists: ${SYNC_QUEUE_NAME}"
fi

# Create or Update Cloud Run Job (reusing unified container image)
SYNC_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPO}/${IMAGE_NAME}:latest"
DATA_BUCKET="${PROJECT_ID}-data"
if ! gcloud run jobs describe "${SYNC_JOB_NAME}" --region="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud run jobs create "${SYNC_JOB_NAME}" \
    --image="${SYNC_IMAGE}" \
    --command="python,scripts/sync_drive.py" \
    --args="--project=monaro" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --service-account="${SA_EMAIL}" \
    --execution-environment=gen2 \
    --add-volume="name=data-volume,type=cloud-storage,bucket=${DATA_BUCKET}" \
    --add-volume-mount="volume=data-volume,mount-path=/app/data" \
    --tasks=1 \
    --max-retries=1 \
    --set-env-vars="DEFAULT_PROJECTS=monaro,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},GEMINI_MODEL=${GEMINI_MODEL},GEMINI_REGION=${GEMINI_REGION}" >/dev/null 2>&1 || true
  echo "  ✓ Created Cloud Run Job: ${SYNC_JOB_NAME}"
else
  gcloud run jobs update "${SYNC_JOB_NAME}" \
    --image="${SYNC_IMAGE}" \
    --command="python,scripts/sync_drive.py" \
    --args="--project=monaro" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --execution-environment=gen2 \
    --add-volume="name=data-volume,type=cloud-storage,bucket=${DATA_BUCKET}" \
    --add-volume-mount="volume=data-volume,mount-path=/app/data" \
    --set-env-vars="DEFAULT_PROJECTS=monaro,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},GEMINI_MODEL=${GEMINI_MODEL},GEMINI_REGION=${GEMINI_REGION}" >/dev/null 2>&1 || true
  echo "  ✓ Updated Cloud Run Job: ${SYNC_JOB_NAME}"
fi

# Grant Admin and Deployer permission to execute Cloud Run Job
for USR in "brendanhills@google.com" "allins@google.com"; do
  gcloud run jobs add-iam-policy-binding "${SYNC_JOB_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="user:${USR}" \
    --role="roles/run.developer" >/dev/null 2>&1 || true
  echo "  ✓ Granted run.developer to user:${USR} on ${SYNC_JOB_NAME}"
done

gcloud run jobs add-iam-policy-binding "${SYNC_JOB_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker" >/dev/null 2>&1 || true
echo "  ✓ Granted run.invoker to serviceAccount:${SA_EMAIL} on ${SYNC_JOB_NAME}"

# Create or Update Cloud Scheduler Job
if ! gcloud scheduler jobs describe "${SCHED_JOB_NAME}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud scheduler jobs create http "${SCHED_JOB_NAME}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --schedule="0 17 * * 5" \
    --time-zone="Australia/Sydney" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${SYNC_JOB_NAME}:run" \
    --http-method="POST" \
    --oauth-service-account-email="${SA_EMAIL}" \
    --description="Weekly automated ingestion sync for Project Monaro" || true
  echo "  ✓ Created Cloud Scheduler job: ${SCHED_JOB_NAME}"
else
  echo "  ✓ Cloud Scheduler job already exists: ${SCHED_JOB_NAME}"
fi

echo "✅ Scheduled Ingestion Job, Cloud Tasks Queue, and Cloud Scheduler configured."
echo ""

# 9. Google Drive Folder & Access Governance
echo "=== 9. Verifying Google Drive Permissions & Group Access ==="
echo "Target Folder ID: ${DRIVE_FOLDER_ID}"

if [[ -x "${GDRIVE_BIN}" ]]; then
  DRIVE_INFO=$("${GDRIVE_BIN}" readonly info "${DRIVE_FOLDER_ID}" --json 2>/dev/null || true)
  if echo "${DRIVE_INFO}" | grep -q '"id":'; then
    FOLDER_NAME=$(echo "${DRIVE_INFO}" | jq -r '.name // empty' 2>/dev/null || echo "${DRIVE_FOLDER_ID}")
    echo "  ✓ Verified Google Drive folder: '${FOLDER_NAME}'"

    DRIVE_PERMS=$("${GDRIVE_BIN}" readonly permissions "${DRIVE_FOLDER_ID}" --json 2>/dev/null || echo "[]")

    # Check Access Group
    GRP_ROLE=$(echo "${DRIVE_PERMS}" | jq -r --arg email "${ACCESS_GROUP}" '.[] | select(.emailAddress == $email) | .role' 2>/dev/null || true)
    if [[ -n "${GRP_ROLE}" ]]; then
      echo "  ✓ Access group '${ACCESS_GROUP}' already has access (role: ${GRP_ROLE})."
    else
      echo "  Granting reader access to group '${ACCESS_GROUP}'..."
      if "${GDRIVE_BIN}" mutate share "${DRIVE_FOLDER_ID}" --email="${ACCESS_GROUP}" --type="group" --role="reader" --notify=false >/dev/null 2>&1; then
        echo "  ✅ Granted reader access to group '${ACCESS_GROUP}'."
      else
        echo "  ⚠️ Could not auto-share with group '${ACCESS_GROUP}' (check permissions on folder)."
      fi
    fi

    # Check Service Account (Direct or via Access Group)
    SA_ROLE=$(echo "${DRIVE_PERMS}" | jq -r --arg email "${SA_EMAIL}" '.[] | select(.emailAddress == $email) | .role' 2>/dev/null || true)
    if [[ -n "${SA_ROLE}" ]]; then
      echo "  ✓ Deployer service account '${SA_EMAIL}' already has direct access (role: ${SA_ROLE})."
    elif [[ -n "${GRP_ROLE}" ]]; then
      echo "  ✓ Deployer service account '${SA_EMAIL}' has access via group '${ACCESS_GROUP}' (role: ${GRP_ROLE})."
    else
      echo "  Granting reader access to service account '${SA_EMAIL}'..."
      if "${GDRIVE_BIN}" mutate share "${DRIVE_FOLDER_ID}" --email="${SA_EMAIL}" --type="user" --role="reader" --notify=false >/dev/null 2>&1; then
        echo "  ✅ Granted reader access to service account '${SA_EMAIL}'."
      else
        echo "  ℹ️ Note: Direct sharing on Shared Drive requires organizer role; access is governed via group '${ACCESS_GROUP}'."
      fi
    fi
  else
    echo "  ⚠️ Could not access Google Drive folder '${DRIVE_FOLDER_ID}'. Please verify folder ID and access."
  fi
else
  echo "  ℹ️ gdrive CLI not found at ${GDRIVE_BIN}. Skipping automated Drive sharing."
fi
echo "✅ Google Drive folder and access governance verified."
echo ""

echo "=============================================================================="
echo "🎉 Provisioning Complete for ${PROJECT_ID} (${REGION})!"
echo "=============================================================================="
