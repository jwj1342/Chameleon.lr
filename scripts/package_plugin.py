"""Create the versioned Lightroom plugin release archive."""

from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugin" / "Chameleon.lrplugin"


def repository_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def package_plugin(output_directory: Path) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / f"Chameleon.lrplugin-{repository_version()}.zip"

    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for source in sorted(path for path in PLUGIN_ROOT.rglob("*") if path.is_file()):
            relative = source.relative_to(PLUGIN_ROOT.parent).as_posix()
            entry = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(entry, source.read_bytes())

    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    destination = package_plugin(args.output_dir.resolve())
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
