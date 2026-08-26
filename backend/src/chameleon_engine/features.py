"""Small, color-managed-enough preview feature extractor for the baseline engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageStat, UnidentifiedImageError


class FeatureError(ValueError):
    """Raised when a preview cannot be analyzed."""


@dataclass(frozen=True)
class ImageFeatures:
    width: int
    height: int
    luma_mean: float
    luma_stddev: float
    luma_p10: float
    luma_median: float
    luma_p90: float
    shadow_fraction: float
    highlight_fraction: float
    saturation_mean: float
    rgb_mean: tuple[float, float, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _percentile(histogram: list[int], quantile: float) -> float:
    total = sum(histogram)
    if total <= 0:
        return 0.0
    threshold = max(1, int(total * quantile + 0.5))
    running = 0
    for value, count in enumerate(histogram):
        running += count
        if running >= threshold:
            return value / 255.0
    return 1.0


def extract_features(path: Path, max_size: int = 512) -> ImageFeatures:
    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    except (OSError, UnidentifiedImageError) as exc:
        raise FeatureError(f"cannot read preview {path}: {exc}") from exc

    if image.width < 1 or image.height < 1:
        raise FeatureError(f"preview has invalid dimensions: {path}")

    luma = image.convert("L")
    luma_hist = luma.histogram()
    pixel_count = image.width * image.height
    luma_stats = ImageStat.Stat(luma)
    rgb_stats = ImageStat.Stat(image)
    saturation_stats = ImageStat.Stat(image.convert("HSV").getchannel("S"))

    return ImageFeatures(
        width=image.width,
        height=image.height,
        luma_mean=luma_stats.mean[0] / 255.0,
        luma_stddev=luma_stats.stddev[0] / 255.0,
        luma_p10=_percentile(luma_hist, 0.10),
        luma_median=_percentile(luma_hist, 0.50),
        luma_p90=_percentile(luma_hist, 0.90),
        shadow_fraction=sum(luma_hist[:13]) / pixel_count,
        highlight_fraction=sum(luma_hist[243:]) / pixel_count,
        saturation_mean=saturation_stats.mean[0] / 255.0,
        rgb_mean=tuple(channel / 255.0 for channel in rgb_stats.mean),
    )
