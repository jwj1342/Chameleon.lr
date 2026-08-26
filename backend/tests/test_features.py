from __future__ import annotations

from pathlib import Path

from PIL import Image

from chameleon_engine.features import extract_features


def test_extract_features_from_uniform_image(tmp_path: Path) -> None:
    path = tmp_path / "gray.jpg"
    Image.new("RGB", (80, 40), (128, 128, 128)).save(path, quality=100)

    features = extract_features(path)

    assert features.width == 80
    assert features.height == 40
    assert 0.49 < features.luma_median < 0.52
    assert features.luma_stddev < 0.01
    assert features.saturation_mean < 0.01


def test_extract_features_resizes_large_preview(tmp_path: Path) -> None:
    path = tmp_path / "large.jpg"
    Image.new("RGB", (1600, 800), (200, 20, 20)).save(path)

    features = extract_features(path, max_size=200)

    assert (features.width, features.height) == (200, 100)
    assert features.rgb_mean[0] > features.rgb_mean[1]
