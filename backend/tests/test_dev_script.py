from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "scripts" / "dev.py"


def run_dev(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DEV), command],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_doctor_runs_without_posix_shell_tools() -> None:
    completed = run_dev("doctor")

    assert completed.returncode == 0, completed.stderr
    assert "Chameleon.lr environment" in completed.stdout
    assert "Engine" in completed.stdout
    assert "chameleon-engine 0.1.0" in completed.stdout


def test_metadata_command_checks_repository() -> None:
    completed = run_dev("metadata")

    assert completed.returncode == 0, completed.stderr
    assert "Checked local links" in completed.stdout
