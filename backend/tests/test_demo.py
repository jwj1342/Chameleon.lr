from __future__ import annotations

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

from chameleon_engine.demo import create_demo

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "backend" / "chameleon_cli.py"


class LocalResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.resources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "img" and attributes.get("src"):
            self.resources.append(attributes["src"])
        if tag == "a" and attributes.get("href"):
            self.resources.append(attributes["href"])


def test_demo_generates_visual_report_and_improves_feature_gaps(tmp_path: Path) -> None:
    output = tmp_path / "demo"

    artifacts = create_demo(output)

    response = json.loads(artifacts.response_path.read_text(encoding="utf-8"))
    metrics = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))
    report = artifacts.report_path.read_text(encoding="utf-8")
    assert response["status"] == "ok"
    assert [result["photo_id"] for result in response["results"]] == [
        "dark-cool",
        "bright-green",
    ]
    assert "Adaptive style fitting" in report
    assert "response.json" in report
    parser = LocalResourceParser()
    parser.feed(report)
    assert parser.resources
    assert all((output / resource).is_file() for resource in parser.resources)

    for identifier, values in metrics["targets"].items():
        assert values["after"]["luma_median"] < values["before"]["luma_median"], identifier
        assert values["after"]["rgb_mean"] < values["before"]["rgb_mean"], identifier
        with Image.open(output / "assets" / f"fitted-{identifier}.jpg") as image:
            assert image.size == (960, 600)


def test_demo_cli_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    output = tmp_path / "demo"
    command = [sys.executable, str(CLI), "demo", "--output-dir", str(output)]

    first = subprocess.run(command, check=False, capture_output=True, text=True)
    second = subprocess.run(command, check=False, capture_output=True, text=True)

    assert first.returncode == 0, first.stderr
    assert Path(first.stdout.strip()) == output / "index.html"
    assert second.returncode == 2
    assert "pass --force" in second.stderr
