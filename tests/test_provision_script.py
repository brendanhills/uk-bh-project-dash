"""
Unit and integration tests for setup.sh CLI flags and options.
"""

import os
import subprocess
import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SETUP_SCRIPT = os.path.join(PROJECT_ROOT, "setup.sh")


def test_setup_script_exists_and_executable():
    """Verify root setup.sh exists and is executable."""
    assert os.path.isfile(SETUP_SCRIPT), f"{SETUP_SCRIPT} does not exist"
    assert os.access(SETUP_SCRIPT, os.X_OK), f"{SETUP_SCRIPT} is not executable"


def test_setup_script_syntax():
    """Verify setup.sh passes bash syntax validation (bash -n)."""
    res = subprocess.run(
        ["bash", "-n", SETUP_SCRIPT],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0, f"bash -n failed: {res.stderr}"


def test_setup_script_help():
    """Verify --help and -h flags display list mode, missing filter, and drive options."""
    res = subprocess.run(
        [SETUP_SCRIPT, "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    output = res.stdout
    assert "-l, --list, --status" in output
    assert "-m, --missing" in output
    assert "--state-only" in output
    assert "--folder-id" in output
    assert "--apis-only" in output


def test_setup_script_unknown_option():
    """Verify unknown option exits with error code 1 and usage."""
    res = subprocess.run(
        [SETUP_SCRIPT, "--invalid-flag-xyz"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 1
    assert "Unknown option" in res.stdout or "Unknown option" in res.stderr

