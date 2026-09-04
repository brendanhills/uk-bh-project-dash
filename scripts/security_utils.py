"""
Common Security Utilities for Project Dash & Data Ingestion Pipelines.

Provides reusable sanitization and path boundary validation to prevent CWE-22
(Path Traversal / Path Injection) and satisfy static analysis tools like CodeQL.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Union


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
