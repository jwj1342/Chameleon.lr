"""Command-line interface used by Lightroom and developers."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __version__
from .models import FitRequest, ProtocolError
from .service import fit_request


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"cannot read request {path}: {exc}") from exc


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _error_response(request_id: str, message: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "request_id": request_id,
        "status": "error",
        "engine": {"name": "chameleon-engine", "version": __version__},
        "results": [],
        "errors": [{"photo_id": "", "message": message}],
    }


def _fit(args: argparse.Namespace) -> int:
    request_id = "unknown"
    try:
        raw_request = _read_json(args.request)
        if isinstance(raw_request, dict) and isinstance(raw_request.get("request_id"), str):
            request_id = raw_request["request_id"]
        request = FitRequest.from_dict(raw_request)
        response = fit_request(request)
        _write_json_atomic(args.output, response)
        return 0 if response["status"] in {"ok", "partial"} else 1
    except (ProtocolError, OSError, ValueError) as exc:
        _write_json_atomic(args.output, _error_response(request_id, str(exc)))
        print(f"chameleon-engine: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        message = f"internal engine error: {exc}"
        _write_json_atomic(args.output, _error_response(request_id, message))
        print(f"chameleon-engine: {message}", file=sys.stderr)
        return 3


def _demo(args: argparse.Namespace) -> int:
    from .demo import DemoError, create_demo

    try:
        artifacts = create_demo(args.output_dir, force=args.force)
    except (DemoError, OSError, ValueError) as exc:
        print(f"chameleon-engine: {exc}", file=sys.stderr)
        return 2
    print(artifacts.report_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chameleon-engine")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    health = subparsers.add_parser("health", help="check that the engine can start")
    health.add_argument("--json", action="store_true", help="emit machine-readable output")

    fit = subparsers.add_parser("fit", help="fit reference style to target previews")
    fit.add_argument("--request", required=True, type=Path)
    fit.add_argument("--output", required=True, type=Path)
    fit.set_defaults(handler=_fit)

    demo = subparsers.add_parser("demo", help="generate a self-contained adaptive-style demo")
    demo.add_argument("--output-dir", type=Path, default=Path("demo-output"))
    demo.add_argument("--force", action="store_true", help="replace generated demo files")
    demo.set_defaults(handler=_demo)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "health":
        payload = {"status": "ok", "name": "chameleon-engine", "version": __version__}
        print(json.dumps(payload, separators=(",", ":")) if args.json else "chameleon-engine ok")
        return 0
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
