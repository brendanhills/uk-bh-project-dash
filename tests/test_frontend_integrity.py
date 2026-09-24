"""
Tests for Frontend JavaScript integrity, AST syntax, and UX event regressions.
Ensures that missing quotes, brackets, or undeclared variables
are caught in the automated pytest test suite.
"""

from concurrent.futures import ThreadPoolExecutor
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
    and can be parsed by Node in a single V8 process without syntax errors.
    """
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js runtime not installed in environment; skipping AST syntax check.")

    js_files = []
    for js_dir in FRONTEND_JS_DIRS:
        if js_dir.exists():
            js_files.extend(sorted(js_dir.glob("*.js")))

    assert len(js_files) > 0, f"No JavaScript files found in {FRONTEND_JS_DIRS}"

    # Parse all JS files in a single Node V8 invocation (stripping top-level import/export keywords for vm.Script)
    checker_script = (
        "const fs = require('fs'), vm = require('vm');\n"
        "for (const f of process.argv.slice(1)) {\n"
        "  const src = fs.readFileSync(f, 'utf8')\n"
        "    .replace(/^\\s*import\\s+[^;]+;/gm, '')\n"
        "    .replace(/^\\s*export\\s+(default\\s+)?/gm, '');\n"
        "  try { new vm.Script(src, { filename: f }); } catch (e) {\n"
        "    console.error(`Syntax error in ${f}:\\n`, e);\n"
        "    process.exit(1);\n"
        "  }\n"
        "}"
    )
    result = subprocess.run(
        [node_bin, "-e", checker_script, *[str(f) for f in js_files]],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"JavaScript syntax check failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )



def test_frontend_eslint_and_vitest_suite():
    """
    Executes ESLint (with incremental file cache) and the Vitest UX test suite concurrently
    directly via node_modules/.bin to avoid corepack/npm subshell startup overhead.
    """
    eslint_bin = PROJECT_ROOT / "node_modules" / ".bin" / "eslint"
    vitest_bin = PROJECT_ROOT / "node_modules" / ".bin" / "vitest"

    if not eslint_bin.exists() or not vitest_bin.exists():
        pytest.skip("eslint or vitest not present in node_modules; skipping verification.")

    eslint_proc = subprocess.Popen(
        [
            str(eslint_bin),
            "--cache",
            "--cache-location",
            str(PROJECT_ROOT / ".pytest_cache" / "eslintcache"),
            "src/js",
        ],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    vitest_proc = subprocess.Popen(
        [str(vitest_bin), "run"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    eslint_out, eslint_err = eslint_proc.communicate()
    vitest_out, vitest_err = vitest_proc.communicate()

    assert eslint_proc.returncode == 0, (
        f"ESLint verification failed:\nSTDOUT: {eslint_out}\nSTDERR: {eslint_err}"
    )
    assert vitest_proc.returncode == 0, (
        f"Vitest UX suite failed:\nSTDOUT: {vitest_out}\nSTDERR: {vitest_err}"
    )

