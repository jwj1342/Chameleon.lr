from __future__ import annotations

from pathlib import Path

from PIL import Image

from chameleon_engine.models import FitOptions, FitRequest, PhotoInput
from chameleon_engine.service import fit_request


def test_service_reports_partial_target_failure(tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.jpg"
    target_path = tmp_path / "target.jpg"
    Image.new("RGB", (32, 32), (128, 128, 128)).save(reference_path)
    Image.new("RGB", (32, 32), (96, 96, 96)).save(target_path)
    request = FitRequest(
        schema_version=1,
        request_id="partial-1",
        reference=PhotoInput("1", reference_path, {"Contrast2012": 20}),
        targets=(
            PhotoInput("2", target_path, {"Exposure2012": 0}),
            PhotoInput("3", tmp_path / "missing.jpg", {"Exposure2012": 0}),
        ),
        options=FitOptions(),
    )

    response = fit_request(request)

    assert response["status"] == "partial"
    assert [item["photo_id"] for item in response["results"]] == ["2"]
    assert response["errors"][0]["photo_id"] == "3"


def test_service_rejects_empty_develop_setting_result(tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.jpg"
    target_path = tmp_path / "target.jpg"
    Image.new("RGB", (32, 32), (128, 128, 128)).save(reference_path)
    Image.new("RGB", (32, 32), (96, 96, 96)).save(target_path)
    request = FitRequest(
        schema_version=1,
        request_id="empty-settings",
        reference=PhotoInput("1", reference_path, {"CropAngle": 12}),
        targets=(PhotoInput("2", target_path, {}),),
        options=FitOptions(adapt_exposure=False, adapt_white_balance=False),
    )

    response = fit_request(request)

    assert response["status"] == "error"
    assert response["results"] == []
    assert response["errors"][0]["photo_id"] == "2"
    assert "no supported style settings" in response["errors"][0]["message"]
