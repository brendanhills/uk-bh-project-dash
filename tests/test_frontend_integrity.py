"""
Tests for Frontend JavaScript integrity, AST syntax, and UX event regressions.
Ensures that missing quotes, brackets, or undeclared variables
are caught in the automated pytest test suite.
"""

import shutil
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_JS_DIRS = [
    PROJECT_ROOT / "src" / "js",
    PROJECT_ROOT / "src" / "js" / "modules",
]


def test_frontend_javascript_syntax_check():
    """
    Validates that all JavaScript files in src/js and src/js/modules have valid syntax
    and can be parsed by Node without syntax errors (unclosed brackets, quotes, etc.).
    """
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js runtime not installed in environment; skipping AST syntax check.")

    js_files = []
    for js_dir in FRONTEND_JS_DIRS:
        if js_dir.exists():
            js_files.extend(list(js_dir.glob("*.js")))

    assert len(js_files) > 0, f"No JavaScript files found in {FRONTEND_JS_DIRS}"

    for js_file in js_files:
        result = subprocess.run(
            [node_bin, "--check", str(js_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"JavaScript syntax error in {js_file.name}:\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )


def test_frontend_eslint_and_vitest_suite():
    """
    Executes the npm verify command (eslint scope check + vitest UX test suite).
    Catches undeclared variables and frontend runtime crashes.
    """
    npm_bin = shutil.which("npm") or shutil.which("corepack")
    node_modules = PROJECT_ROOT / "node_modules"

    if not npm_bin or not node_modules.exists():
        pytest.skip("npm or node_modules not present; skipping Vitest & ESLint verification.")

    cmd = [npm_bin, "run", "verify"] if shutil.which("npm") else ["corepack", "npm", "run", "verify"]
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Frontend verification failed:\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )
