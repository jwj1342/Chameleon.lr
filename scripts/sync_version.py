#!/usr/bin/env python3
"""Keep release versions synchronized across Python and Lightroom metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
PYPROJECT_FILE = ROOT / "backend" / "pyproject.toml"
PACKAGE_FILE = ROOT / "backend" / "src" / "chameleon_engine" / "__init__.py"
INFO_FILE = ROOT / "plugin" / "Chameleon.lrplugin" / "Info.lua"
SEMVER_PATTERN = re.compile(r"^(?:v)?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def parse_version(raw_version: str) -> tuple[str, tuple[int, int, int]]:
    match = SEMVER_PATTERN.fullmatch(raw_version.strip())
    if not match:
        raise ValueError(
            "version must use stable semantic version syntax, for example v1.2.3"
        )
    numbers = tuple(int(value) for value in match.groups())
    return ".".join(str(value) for value in numbers), numbers


def replace_once(path: Path, pattern: str, replacement: str) -> None:
    contents = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        pattern, replacement, contents, count=1, flags=re.MULTILINE
    )
    if count != 1:
        raise RuntimeError(
            f"could not find a unique version field in {path.relative_to(ROOT)}"
        )
    path.write_text(updated, encoding="utf-8")


def synchronize(raw_version: str) -> str:
    version, (major, minor, patch) = parse_version(raw_version)
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    replace_once(PYPROJECT_FILE, r'^version = "[^"]+"$', f'version = "{version}"')
    replace_once(PACKAGE_FILE, r'^__version__ = "[^"]+"$', f'__version__ = "{version}"')
    replace_once(
        INFO_FILE,
        r"^\s*VERSION = \{ major = \d+, minor = \d+, revision = \d+, build = \d+ \},$",
        f"\tVERSION = {{ major = {major}, minor = {minor}, revision = {patch}, build = 0 }},",
    )
    return version


def discovered_versions() -> dict[str, str]:
    values = {"VERSION": VERSION_FILE.read_text(encoding="utf-8").strip()}
    pyproject = PYPROJECT_FILE.read_text(encoding="utf-8")
    package = PACKAGE_FILE.read_text(encoding="utf-8")
    info = INFO_FILE.read_text(encoding="utf-8")

    pyproject_match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    package_match = re.search(r'^__version__ = "([^"]+)"$', package, re.MULTILINE)
    info_match = re.search(
        r"^\s*VERSION = \{ major = (\d+), minor = (\d+), revision = (\d+), build = (\d+) \},$",
        info,
        re.MULTILINE,
    )
    if not pyproject_match or not package_match or not info_match:
        raise RuntimeError("one or more version fields could not be parsed")

    values["backend/pyproject.toml"] = pyproject_match.group(1)
    values["chameleon_engine/__init__.py"] = package_match.group(1)
    values["Info.lua"] = ".".join(info_match.groups()[:3])
    if info_match.group(4) != "0":
        values["Info.lua build"] = info_match.group(4)
    return values


def check() -> str:
    versions = discovered_versions()
    canonical, _ = parse_version(versions["VERSION"])
    mismatches = {name: value for name, value in versions.items() if value != canonical}
    if mismatches:
        details = ", ".join(f"{name}={value}" for name, value in mismatches.items())
        raise RuntimeError(
            f"version metadata differs from VERSION ({canonical}): {details}"
        )
    return canonical


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--check", action="store_true", help="fail if metadata versions differ"
    )
    action.add_argument(
        "--version",
        help="write a stable X.Y.Z version (an optional v prefix is accepted)",
    )
    args = parser.parse_args()

    version = check() if args.check else synchronize(args.version)
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
