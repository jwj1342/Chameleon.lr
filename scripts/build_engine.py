#!/usr/bin/env python3
"""Build, smoke-test, and archive a native Chameleon engine executable."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = ROOT / "backend" / "chameleon_cli.py"
SOURCE_ROOT = ROOT / "backend" / "src"


def platform_key() -> tuple[str, str, str]:
    system_names = {"darwin": "macos", "linux": "linux", "win32": "windows"}
    system = system_names.get(sys.platform)
    if system is None:
        raise RuntimeError(f"unsupported build platform: {sys.platform}")

    machine = platform.machine().lower()
    architecture_names = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    architecture = architecture_names.get(machine)
    if architecture is None:
        raise RuntimeError(f"unsupported build architecture: {machine}")
    executable_name = (
        "chameleon-engine.exe" if system == "windows" else "chameleon-engine"
    )
    return system, architecture, executable_name


def build(output_directory: Path) -> Path:
    system, architecture, executable_name = platform_key()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    build_root = ROOT / "build" / "pyinstaller" / f"{system}-{architecture}"
    dist_root = build_root / "dist"
    work_root = build_root / "work"
    spec_root = build_root / "spec"
    shutil.rmtree(build_root, ignore_errors=True)
    output_directory.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--name",
            "chameleon-engine",
            "--paths",
            str(SOURCE_ROOT),
            "--distpath",
            str(dist_root),
            "--workpath",
            str(work_root),
            "--specpath",
            str(spec_root),
            str(ENTRY_POINT),
        ],
        cwd=ROOT,
        check=True,
    )

    executable = dist_root / executable_name
    completed = subprocess.run(
        [str(executable), "health", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    health = json.loads(completed.stdout)
    if health.get("status") != "ok" or health.get("version") != version:
        raise RuntimeError(f"unexpected packaged engine health response: {health}")

    with tempfile.TemporaryDirectory(prefix="chameleon-demo-") as temporary_directory:
        demo_directory = Path(temporary_directory) / "demo"
        subprocess.run(
            [str(executable), "demo", "--output-dir", str(demo_directory)],
            check=True,
            capture_output=True,
            text=True,
        )
        demo_response = json.loads(
            (demo_directory / "response.json").read_text(encoding="utf-8")
        )
        if (
            demo_response.get("status") != "ok"
            or not (demo_directory / "index.html").is_file()
        ):
            raise RuntimeError("packaged engine did not produce a valid MVP demo")

    stem = f"chameleon-engine-{version}-{system}-{architecture}"
    instructions = (
        f"Chameleon.lr engine {version} for {system} {architecture}.\n"
        "Extract the executable, select Standalone executable in the Lightroom "
        "plug-in settings, and enter its absolute path.\n"
        "This development build is not code-signed.\n"
    )
    if system == "windows":
        destination = output_directory / f"{stem}.zip"
        with zipfile.ZipFile(
            destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            archive.write(executable, executable.name)
            archive.writestr("README.txt", instructions)
    else:
        destination = output_directory / f"{stem}.tar.gz"
        readme = build_root / "README.txt"
        readme.write_text(instructions, encoding="utf-8")
        with tarfile.open(destination, "w:gz") as archive:
            archive.add(executable, arcname=executable.name)
            archive.add(readme, arcname=readme.name)

    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    destination = build(args.output_dir.resolve())
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
