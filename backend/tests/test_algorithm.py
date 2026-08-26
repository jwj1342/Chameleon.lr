from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from chameleon_engine.algorithm import AdaptiveStyleEngine
from chameleon_engine.models import FitOptions, PhotoInput


def photo(path: Path, identifier: str, settings: dict[str, object]) -> PhotoInput:
    return PhotoInput(identifier, path, settings, {})


def test_fit_transfers_style_and_adapts_exposure(tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.jpg"
    target_path = tmp_path / "target.jpg"
    Image.new("RGB", (100, 100), (128, 128, 128)).save(reference_path, quality=100)
    Image.new("RGB", (100, 100), (64, 64, 64)).save(target_path, quality=100)
    reference = photo(
        reference_path,
        "ref",
        {"Exposure2012": 1.0, "Contrast2012": 30, "CropAngle": 12},
    )
    target = photo(target_path, "target", {"Exposure2012": 0.0, "Contrast2012": 0})

    result = AdaptiveStyleEngine().fit(reference, (target,), FitOptions())[0]

    assert result.photo_id == "target"
    assert result.develop_settings["Exposure2012"] == pytest.approx(1.0, abs=0.05)
    assert result.develop_settings["Contrast2012"] == 30
    assert "CropAngle" not in result.develop_settings
    assert result.diagnostics["confidence"] > 0


def test_strength_blends_numeric_style_settings(tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.jpg"
    target_path = tmp_path / "target.jpg"
    Image.new("RGB", (40, 40), (100, 100, 100)).save(reference_path)
    Image.new("RGB", (40, 40), (100, 100, 100)).save(target_path)
    reference = photo(reference_path, "ref", {"Contrast2012": 40})
    target = photo(target_path, "target", {"Contrast2012": 10})

    result = AdaptiveStyleEngine().fit(
        reference,
        (target,),
        FitOptions(strength=0.5, adapt_exposure=False, adapt_white_balance=False),
    )[0]

    assert result.develop_settings["Contrast2012"] == 25
    assert "Exposure2012" not in result.develop_settings


def test_fit_sanitizes_untrusted_reference_settings(tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.jpg"
    target_path = tmp_path / "target.jpg"
    Image.new("RGB", (20, 20), (100, 100, 100)).save(reference_path)
    Image.new("RGB", (20, 20), (100, 100, 100)).save(target_path)
    reference = photo(
        reference_path,
        "ref",
        {
            "Contrast2012": 500,
            "Highlights2012": "maximum",
            "ToneCurvePV2012": [0, 0, 255],
        },
    )
    target = photo(target_path, "target", {})

    result = AdaptiveStyleEngine().fit(
        reference,
        (target,),
        FitOptions(adapt_exposure=False, adapt_white_balance=False),
    )[0]

    assert result.develop_settings == {"Contrast2012": 100}
