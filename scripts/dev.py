"""Cross-platform development commands for Chameleon.lr.

This entry point intentionally uses only the Python standard library. It gives Windows,
macOS, Linux, and HPC users the same commands without requiring Make or a POSIX shell.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SOURCE_ROOT = BACKEND / "src"
LUA_TESTS = (
    "tests/lua/test_json.lua",
    "tests/lua/test_develop_settings.lua",
    "tests/lua/test_plugin_load.lua",
    "tests/lua/test_engine_client.lua",
    "tests/lua/test_workflow.lua",
)


class ToolError(RuntimeError):
    """Raised when a requested local development tool is unavailable."""


def python_environment() -> dict[str, str]:
    environment = os.environ.copy()
    current = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(SOURCE_ROOT) if not current else str(SOURCE_ROOT) + os.pathsep + current
    )
    environment.setdefault("PYTHONUTF8", "1")
    return environment


def run(
    arguments: Sequence[str], *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    command = [str(argument) for argument in arguments]
    print(f"+ {shlex.join(command)}", flush=True)
    return subprocess.run(
        command,
        cwd=ROOT,
        env=python_environment(),
        check=True,
        capture_output=capture,
        text=True,
        encoding="utf-8",
    )


def find_tool(environment_name: str, candidates: Sequence[str]) -> str | None:
    configured = os.environ.get(environment_name)
    if configured:
        resolved = shutil.which(configured)
        if resolved:
            return resolved
        path = Path(configured).expanduser()
        if path.is_file():
            return str(path.resolve())
        raise ToolError(
            f"{environment_name} points to a missing executable: {configured}"
        )

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def require_tool(environment_name: str, candidates: Sequence[str], purpose: str) -> str:
    tool = find_tool(environment_name, candidates)
    if tool is None:
        choices = ", ".join(candidates)
        raise ToolError(
            f"{purpose} requires one of [{choices}] on PATH, or set {environment_name}"
        )
    return tool


def require_lua_51(tool: str) -> None:
    completed = subprocess.run(
        [tool, "-v"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    version = (completed.stdout + completed.stderr).strip()
    if completed.returncode != 0 or "Lua 5.1" not in version:
        raise ToolError(f"Lightroom mocks require Lua 5.1; {tool} reported {version!r}")


def bootstrap(_: argparse.Namespace) -> None:
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-e",
            f"{BACKEND}[dev,release]",
        ]
    )


def test_python(_: argparse.Namespace) -> None:
    run([sys.executable, "-m", "pytest", "backend/tests"])


def test_lua(_: argparse.Namespace) -> None:
    lua = require_tool("CHAMELEON_LUA", ("lua5.1", "lua"), "Lua tests")
    require_lua_51(lua)
    for test in LUA_TESTS:
        run([lua, test])


def test_all(args: argparse.Namespace) -> None:
    test_python(args)
    test_lua(args)


def lint_python(_: argparse.Namespace) -> None:
    run([sys.executable, "-m", "ruff", "check", "backend", "scripts"])
    run([sys.executable, "-m", "ruff", "format", "--check", "backend", "scripts"])


def metadata(_: argparse.Namespace) -> None:
    run([sys.executable, "scripts/sync_version.py", "--check"])
    run([sys.executable, "scripts/check_docs.py"])


def lint_lua(_: argparse.Namespace) -> None:
    luacheck = require_tool("CHAMELEON_LUACHECK", ("luacheck",), "Lua lint")
    luac = require_tool("CHAMELEON_LUAC", ("luac5.1", "luac"), "Lua syntax checks")
    require_lua_51(luac)

    lua_files = sorted((ROOT / "plugin" / "Chameleon.lrplugin").rglob("*.lua"))
    lua_files.extend(sorted((ROOT / "tests" / "lua").glob("*.lua")))
    relative_files = [str(path.relative_to(ROOT)) for path in lua_files]
    run([luacheck, *relative_files])
    for path in relative_files:
        run([luac, "-p", path])


def lint_all(args: argparse.Namespace) -> None:
    lint_python(args)
    lint_lua(args)
    metadata(args)


def demo(_: argparse.Namespace) -> None:
    run(
        [
            sys.executable,
            "-m",
            "chameleon_engine",
            "demo",
            "--output-dir",
            "demo/output",
            "--force",
        ]
    )


def readme_preview(_: argparse.Namespace) -> None:
    run([sys.executable, "scripts/render_readme_preview.py"])


def package_plugin(_: argparse.Namespace) -> None:
    run([sys.executable, "scripts/package_plugin.py", "--output-dir", "dist"])


def package_engine(_: argparse.Namespace) -> None:
    run([sys.executable, "scripts/build_engine.py", "--output-dir", "dist"])


def package_wheel(_: argparse.Namespace) -> None:
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "./backend",
            "--wheel-dir",
            "dist",
        ]
    )


def package_all(args: argparse.Namespace) -> None:
    package_plugin(args)
    package_engine(args)
    package_wheel(args)


def doctor(args: argparse.Namespace) -> None:
    checks: list[tuple[str, bool, str]] = []
    checks.append(
        (
            "Python",
            sys.version_info >= (3, 10),
            f"{platform.python_version()} ({sys.executable})",
        )
    )
    checks.append(("Workspace", ROOT.is_dir(), str(ROOT)))
    checks.append(
        (
            "Platform",
            True,
            f"{platform.system()} {platform.release()} / {platform.machine()}",
        )
    )

    for module, label in (("PIL", "Pillow"), ("pytest", "pytest"), ("ruff", "Ruff")):
        available = importlib.util.find_spec(module) is not None
        checks.append(
            (
                label,
                available or not args.strict,
                "installed" if available else "missing",
            )
        )

    tool_specs = (
        ("CHAMELEON_LUA", ("lua5.1", "lua"), "Lua 5.1"),
        ("CHAMELEON_LUAC", ("luac5.1", "luac"), "Lua compiler"),
        ("CHAMELEON_LUACHECK", ("luacheck",), "Luacheck"),
    )
    for environment_name, candidates, label in tool_specs:
        try:
            executable = find_tool(environment_name, candidates)
            checks.append(
                (
                    label,
                    executable is not None or not args.strict,
                    executable or "optional, missing",
                )
            )
        except ToolError as exc:
            checks.append((label, False, str(exc)))

    try:
        health = run(
            [sys.executable, "backend/chameleon_cli.py", "health", "--json"],
            capture=True,
        )
        payload = json.loads(health.stdout)
        engine_ok = payload.get("status") == "ok"
        engine_detail = f"{payload.get('name')} {payload.get('version')}"
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        engine_ok = False
        engine_detail = str(exc)
    checks.append(("Engine", engine_ok, engine_detail))

    print("\nChameleon.lr environment")
    for label, ok, detail in checks:
        print(f"  {'OK' if ok else 'FAIL':4}  {label:14} {detail}")

    failures = [label for label, ok, _ in checks if not ok]
    if failures:
        raise ToolError("environment checks failed: " + ", ".join(failures))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands: dict[str, tuple[Callable[[argparse.Namespace], None], str]] = {
        "bootstrap": (
            bootstrap,
            "install editable development and release dependencies",
        ),
        "test": (test_all, "run Python and Lua tests"),
        "test-python": (test_python, "run Python tests only"),
        "test-lua": (test_lua, "run Lua 5.1 tests only"),
        "lint": (lint_all, "run all static and metadata checks"),
        "lint-python": (lint_python, "run Ruff checks"),
        "lint-lua": (lint_lua, "run Luacheck and Lua 5.1 syntax checks"),
        "metadata": (metadata, "check versions and Markdown links"),
        "demo": (demo, "generate the deterministic MVP demo"),
        "readme-preview": (readme_preview, "render the README image from demo output"),
        "package": (package_all, "build plugin, native engine, and wheel"),
        "package-plugin": (package_plugin, "build the Lightroom plugin archive"),
        "package-engine": (package_engine, "build the native engine for this platform"),
        "package-wheel": (package_wheel, "build the Python wheel"),
    }
    for name, (handler, help_text) in commands.items():
        command = subparsers.add_parser(name, help=help_text)
        command.set_defaults(handler=handler)

    doctor_command = subparsers.add_parser(
        "doctor", help="diagnose the local toolchain"
    )
    doctor_command.add_argument(
        "--strict",
        action="store_true",
        help="treat optional test and lint tools as required",
    )
    doctor_command.set_defaults(handler=doctor)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except (ToolError, subprocess.CalledProcessError) as exc:
        print(f"chameleon-dev: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
