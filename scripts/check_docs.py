"""Check that repository-local links in maintained Markdown files resolve."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
DOC_ROOTS = (ROOT / "docs", ROOT / "backend", ROOT / "demo", ROOT / ".github")


def markdown_files() -> list[Path]:
    files = list(ROOT.glob("*.md"))
    for directory in DOC_ROOTS:
        if directory.exists():
            files.extend(directory.rglob("*.md"))
    return sorted(set(files))


def local_target(raw_target: str) -> str | None:
    target = raw_target.strip().strip("<>")
    if not target or target.startswith(("#", "http://", "https://", "mailto:")):
        return None

    target = target.split("#", 1)[0]
    if not target:
        return None

    return unquote(target)


def main() -> int:
    failures: list[str] = []
    files = markdown_files()

    for document in files:
        text = document.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue

            resolved = (document.parent / target).resolve()
            if not resolved.exists():
                failures.append(
                    f"{document.relative_to(ROOT)}: broken link {match.group(1)!r}"
                )

    if failures:
        print("Documentation link check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Checked local links in {len(files)} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
