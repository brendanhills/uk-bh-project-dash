"""
Unit tests for reusable security utilities (sanitize_slug, validate_safe_path, safe_join).
Verifies defense against CWE-22 Path Traversal and path injection vulnerabilities.
"""

import os
import pytest
from scripts.security_utils import sanitize_slug, validate_safe_path, safe_join


def test_sanitize_slug_valid():
    assert sanitize_slug('monaro') == 'monaro'
    assert sanitize_slug('sample-project_2') == 'sample-project_2'
    assert sanitize_slug('Project123') == 'Project123'
    assert sanitize_slug(None, default='fallback') == 'fallback'
    assert sanitize_slug('', default='fallback') == 'fallback'


def test_sanitize_slug_rejects_path_traversal():
    with pytest.raises(ValueError, match="Invalid identifier slug"):
        sanitize_slug('../../etc/passwd')

    with pytest.raises(ValueError, match="Invalid identifier slug"):
        sanitize_slug('project/subfolder')

    with pytest.raises(ValueError, match="Invalid identifier slug"):
        sanitize_slug('project;rm -rf /')

    with pytest.raises(ValueError, match="Invalid identifier slug"):
        sanitize_slug('project name with spaces')


def test_validate_safe_path_containment(tmp_path):
    parent = str(tmp_path)
    child = os.path.join(parent, 'sub', 'file.txt')
    os.makedirs(os.path.dirname(child), exist_ok=True)
    with open(child, 'w') as f:
        f.write('data')

    # Valid child
    validated = validate_safe_path(child, [parent])
    assert validated == os.path.realpath(child)

    # Valid parent itself
    assert validate_safe_path(parent, [parent]) == os.path.realpath(parent)

    # Path traversal outside parent
    outside = os.path.join(parent, '..', 'outside.txt')
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(outside, [parent])


def test_validate_safe_path_multiple_allowed_parents(tmp_path):
    parent1 = str(tmp_path / "dir1")
    parent2 = str(tmp_path / "dir2")
    os.makedirs(parent1, exist_ok=True)
    os.makedirs(parent2, exist_ok=True)

    file1 = os.path.join(parent1, "file1.json")
    file2 = os.path.join(parent2, "file2.json")

    assert validate_safe_path(file1, [parent1, parent2]) == os.path.realpath(file1)
    assert validate_safe_path(file2, [parent1, parent2]) == os.path.realpath(file2)

    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path("/etc/passwd", [parent1, parent2])


def test_safe_join_valid(tmp_path):
    base = str(tmp_path)
    joined = safe_join(base, "nested", "file.json")
    assert joined.startswith(os.path.realpath(base))
    assert joined.endswith(os.path.join("nested", "file.json"))


def test_safe_join_prevents_escape(tmp_path):
    base = str(tmp_path)
    with pytest.raises(ValueError, match="Path traversal detected"):
        safe_join(base, "..", "escaped.txt")

    with pytest.raises(ValueError, match="Path traversal detected"):
        safe_join(base, "nested", "..", "..", "escaped.txt")
