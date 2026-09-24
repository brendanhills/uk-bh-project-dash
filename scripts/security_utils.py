"""
Common Security Utilities for Project Dash & Data Ingestion Pipelines.

Provides reusable sanitization and path boundary validation to prevent CWE-22
(Path Traversal / Path Injection) and satisfy static analysis tools like CodeQL.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Union


_CACHED_GCLOUD_PROJECT: Optional[str] = None


def resolve_default_project(env: Optional[str] = None) -> str:
    """
    Resolves target GCP project ID dynamically from environment variables,
    active gcloud configuration, or project prefix convention.
    """
    global _CACHED_GCLOUD_PROJECT
    env_proj = (
        os.environ.get("GCP_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("CLOUDSDK_CORE_PROJECT")
    )
    if env_proj and not env:
        return env_proj

    if not env_proj:
        is_pytest = "PYTEST_CURRENT_TEST" in os.environ
        if _CACHED_GCLOUD_PROJECT is not None and not is_pytest:
            env_proj = _CACHED_GCLOUD_PROJECT
        else:
            try:
                res = subprocess.run(
                    ["gcloud", "config", "get-value", "project", "--quiet"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if res.returncode == 0 and res.stdout.strip() and res.stdout.strip() != "(unset)":
                    env_proj = res.stdout.strip()
                    if not is_pytest:
                        _CACHED_GCLOUD_PROJECT = env_proj
                elif not is_pytest:
                    _CACHED_GCLOUD_PROJECT = ""
            except Exception:
                if not is_pytest:
                    _CACHED_GCLOUD_PROJECT = ""

    target_env = env or os.environ.get("ENV_TARGET", "dev")
    if env_proj:
        if env_proj.endswith("-dev") or env_proj.endswith("-prod"):
            base_prefix = env_proj.rsplit("-", 1)[0]
            return f"{base_prefix}-{target_env}"
        if not env:
            return env_proj

    base_prefix = os.environ.get("GCP_PROJECT_PREFIX", "monaro-risk")
    return f"{base_prefix}-{target_env}"


def resolve_default_region() -> str:
    """Resolves target GCP region dynamically from environment variables or default."""
    return (
        os.environ.get("GCP_REGION")
        or os.environ.get("GOOGLE_CLOUD_REGION")
        or os.environ.get("CLOUDSDK_COMPUTE_REGION")
        or "australia-southeast1"
    )


def sanitize_slug(name: Optional[str], default: str = 'monaro') -> str:
    """
    Sanitizes and validates an identifier slug (e.g. project name).
    Only allows alphanumeric characters, underscores, and hyphens.
    Rejects any path separators or traversal sequences.
    
    Raises:
        ValueError: If the slug contains illegal characters or path separators.
    """
    raw = str(name if name is not None and str(name).strip() else default).strip()
    if not re.match(r'^[a-zA-Z0-9_-]+$', raw):
        raise ValueError(
            f"Invalid identifier slug '{name}': only alphanumeric, hyphen, and underscore characters are allowed."
        )
    return raw


def validate_safe_path(target_path: Union[str, Path], allowed_parents: Union[str, Path, List[Union[str, Path]]]) -> str:
    """
    Ensures target_path resolves strictly inside one of the allowed parent directories
    using Python standard library pathlib.Path.is_relative_to.
    
    Args:
        target_path: File or directory path to validate.
        allowed_parents: Single parent path or list of allowed parent directory paths.
        
    Returns:
        The canonical string path of target_path.
        
    Raises:
        ValueError: If target_path escapes the allowed parent directories.
    """
    target = Path(target_path).resolve()
    if isinstance(allowed_parents, (str, Path)):
        parents = [Path(allowed_parents).resolve()]
    else:
        parents = [Path(p).resolve() for p in allowed_parents]

    for parent in parents:
        if target == parent or target.is_relative_to(parent):
            return str(target)

    raise ValueError(
        f"Path traversal detected: '{target_path}' resolves to '{target}', "
        f"which is outside allowed roots {[str(p) for p in parents]}"
    )


def safe_join(base_dir: Union[str, Path], *paths: str) -> str:
    """
    Safely joins path components to base_dir using Python standard library pathlib.Path,
    verifying that the resolved path is strictly contained within base_dir.
    
    Args:
        base_dir: The trusted base directory.
        *paths: Relative path components to append.
        
    Returns:
        The canonical path string under base_dir.
        
    Raises:
        ValueError: If any component is absolute, contains null bytes, or escapes base_dir.
    """
    base_resolved = Path(base_dir).resolve()
    for part in paths:
        if "\0" in part:
            raise ValueError(f"Path component contains null byte: {part!r}")
        if Path(part).is_absolute():
            raise ValueError(f"Path component {part!r} is absolute; refusing to join onto {base_resolved}")

    target = base_resolved.joinpath(*paths).resolve()
    if not target.is_relative_to(base_resolved):
        raise ValueError(f"Path traversal detected: '{target}' escapes base '{base_resolved}'")

    return str(target)


def validate_google_sheet_url(url_or_id: Optional[str]) -> str:
    """
    Validates and canonicalizes a Google Sheets URL or Spreadsheet ID.
    Enforces strict HTTPS docs.google.com/spreadsheets/d/<ID> allowlisting to
    prevent Stored XSS (javascript:/data: URIs), SSRF, and injection attacks.

    Returns:
        Canonical Google Sheet edit URL: 'https://docs.google.com/spreadsheets/d/<ID>/edit'

    Raises:
        ValueError: If url_or_id is empty, uses a disallowed scheme/domain, or lacks a valid ID.
    """
    raw = str(url_or_id or "").strip()
    if not raw:
        raise ValueError("Google Sheet URL or ID cannot be empty.")

    if any(ch in raw for ch in ('<', '>', '"', "'", '\0', '\r', '\n', ' ')):
        raise ValueError(f"Invalid characters in Google Sheet URL: {raw!r}")

    # 1. Match full HTTPS Google Sheets URL (preserving optional #gid=<digits>)
    url_match = re.match(
        r'^https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]{15,100})(?:/[^#]*)?(?:#(gid=\d+))?$',
        raw
    )
    if url_match:
        sheet_id = url_match.group(1)
        gid_frag = url_match.group(2)
        base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        return f"{base_url}#{gid_frag}" if gid_frag else base_url

    # 2. Match bare Spreadsheet ID
    id_match = re.match(r'^([a-zA-Z0-9_-]{15,100})$', raw)
    if id_match:
        sheet_id = id_match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

    raise ValueError(
        f"Invalid Google Sheet URL or ID '{raw}'. Must be a valid 'https://docs.google.com/spreadsheets/d/<ID>' URL or Spreadsheet ID."
    )


def validate_drive_folder_id(url_or_id: Optional[str]) -> str:
    """
    Validates and extracts a Google Drive Folder ID from a folder URL or bare ID string.

    Returns:
        Canonical alphanumeric Google Drive Folder ID.

    Raises:
        ValueError: If url_or_id is invalid or contains unsafe characters.
    """
    raw = str(url_or_id or "").strip()
    if not raw:
        raise ValueError("Google Drive folder URL or ID cannot be empty.")

    if any(ch in raw for ch in ('<', '>', '"', "'", '\0', '\r', '\n', ' ')):
        raise ValueError(f"Invalid characters in Google Drive folder identifier: {raw!r}")

    url_match = re.match(
        r'^https://drive\.google\.com/(?:corp/)?drive/(?:u/\d+/)?folders/([a-zA-Z0-9_-]{15,100})(?:[/?].*)?$',
        raw
    )
    if url_match:
        return url_match.group(1)

    id_match = re.match(r'^([a-zA-Z0-9_-]{15,100})$', raw)
    if id_match:
        return id_match.group(1)

    raise ValueError(
        f"Invalid Google Drive Folder URL or ID '{raw}'. Must be a valid Drive folder link or alphanumeric Folder ID."
    )

