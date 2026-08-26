from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "backend" / "chameleon_cli.py"


def test_cli_fit_end_to_end(tmp_path: Path) -> None:
    reference = tmp_path / "reference.jpg"
    target = tmp_path / "target.jpg"
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    Image.new("RGB", (64, 64), (150, 130, 110)).save(reference)
    Image.new("RGB", (64, 64), (80, 90, 120)).save(target)
    request_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "request_id": "e2e-1",
                "reference": {
                    "id": "10",
                    "preview_path": str(reference),
                    "develop_settings": {"Contrast2012": 20, "Vibrance": 12},
                    "metadata": {},
                },
                "targets": [
                    {
                        "id": "11",
                        "preview_path": str(target),
                        "develop_settings": {
                            "Exposure2012": 0,
                            "Temperature": 5500,
                            "Tint": 0,
                        },
                        "metadata": {},
                    }
                ],
                "options": {
                    "strength": 1,
                    "adapt_exposure": True,
                    "adapt_white_balance": True,
                },
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "fit",
            "--request",
            str(request_path),
            "--output",
            str(response_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["status"] == "ok"
    assert response["request_id"] == "e2e-1"
    assert response["results"][0]["photo_id"] == "11"
    assert response["results"][0]["develop_settings"]["Contrast2012"] == 20


def test_cli_writes_structured_error(tmp_path: Path) -> None:
    request_path = tmp_path / "bad-request.json"
    response_path = tmp_path / "response.json"
    request_path.write_text('{"schema_version":99,"request_id":"bad"}', encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "fit",
            "--request",
            str(request_path),
            "--output",
            str(response_path),
        ],
        check=False,
    )

    assert completed.returncode == 2
    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["status"] == "error"
    assert response["request_id"] == "bad"
