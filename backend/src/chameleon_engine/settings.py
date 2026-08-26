"""Develop-setting policy shared by the baseline transfer algorithm."""

from __future__ import annotations

import math
from typing import Any

HUES = ("Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta")

BASIC_SETTINGS = {
    "ProcessVersion",
    "WhiteBalance",
    "Temperature",
    "Tint",
    "Exposure2012",
    "Contrast2012",
    "Highlights2012",
    "Shadows2012",
    "Whites2012",
    "Blacks2012",
    "Texture",
    "Clarity2012",
    "Dehaze",
    "Vibrance",
    "Saturation",
}

HSL_SETTINGS = {
    f"{channel}Adjustment{hue}" for channel in ("Hue", "Saturation", "Luminance") for hue in HUES
}

CURVE_SETTINGS = {
    "ToneCurveName2012",
    "ToneCurvePV2012",
    "ToneCurvePV2012Red",
    "ToneCurvePV2012Green",
    "ToneCurvePV2012Blue",
    "ParametricShadows",
    "ParametricDarks",
    "ParametricLights",
    "ParametricHighlights",
    "ParametricShadowSplit",
    "ParametricMidtoneSplit",
    "ParametricHighlightSplit",
}

COLOR_GRADING_SETTINGS = {
    "ColorGradeBlending",
    "ColorGradeGlobalHue",
    "ColorGradeGlobalLum",
    "ColorGradeGlobalSat",
    "ColorGradeHighlightLum",
    "ColorGradeHighlightHue",
    "ColorGradeHighlightSat",
    "ColorGradeMidtoneHue",
    "ColorGradeMidtoneLum",
    "ColorGradeMidtoneSat",
    "ColorGradeShadowLum",
    "ColorGradeShadowHue",
    "ColorGradeShadowSat",
}

ALLOWED_SETTINGS = BASIC_SETTINGS | HSL_SETTINGS | CURVE_SETTINGS | COLOR_GRADING_SETTINGS

SETTING_RANGES: dict[str, tuple[float, float]] = {
    "Exposure2012": (-5.0, 5.0),
    "Temperature": (2_000.0, 50_000.0),
    "Tint": (-150.0, 150.0),
    "Contrast2012": (-100.0, 100.0),
    "Highlights2012": (-100.0, 100.0),
    "Shadows2012": (-100.0, 100.0),
    "Whites2012": (-100.0, 100.0),
    "Blacks2012": (-100.0, 100.0),
    "Texture": (-100.0, 100.0),
    "Clarity2012": (-100.0, 100.0),
    "Dehaze": (-100.0, 100.0),
    "Vibrance": (-100.0, 100.0),
    "Saturation": (-100.0, 100.0),
}

STRING_SETTINGS = {"ProcessVersion", "WhiteBalance", "ToneCurveName2012"}
ARRAY_SETTINGS = {
    "ToneCurvePV2012",
    "ToneCurvePV2012Red",
    "ToneCurvePV2012Green",
    "ToneCurvePV2012Blue",
}


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _range_for(key: str) -> tuple[float, float] | None:
    if key in SETTING_RANGES:
        return SETTING_RANGES[key]
    if "Adjustment" in key or (key.startswith("Parametric") and not key.endswith("Split")):
        return (-100.0, 100.0)
    if key.startswith("Parametric") and key.endswith("Split"):
        return (0.0, 100.0)
    if key.startswith("ColorGrade") and key.endswith("Hue"):
        return (0.0, 360.0)
    if key.startswith("ColorGrade") and (key.endswith("Sat") or key == "ColorGradeBlending"):
        return (0.0, 100.0)
    if key.startswith("ColorGrade") and key.endswith("Lum"):
        return (-100.0, 100.0)
    return None


def _valid_curve(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 4
        and len(value) % 2 == 0
        and all(
            isinstance(item, int | float)
            and not isinstance(item, bool)
            and math.isfinite(float(item))
            and 0 <= item <= 255
            for item in value
        )
    )


def normalize_setting(key: str, value: Any) -> Any | None:
    if key in STRING_SETTINGS:
        return value if isinstance(value, str) else None
    if key in ARRAY_SETTINGS:
        return list(value) if _valid_curve(value) else None
    if not isinstance(value, int | float) or isinstance(value, bool):
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    bounds = _range_for(key)
    return clamp(numeric, *bounds) if bounds else numeric


def _blend_sequence(current: list[Any], desired: list[Any], strength: float) -> list[Any]:
    if len(current) != len(desired):
        return desired if strength >= 0.5 else current
    return [blend_value(old, new, strength) for old, new in zip(current, desired, strict=True)]


def blend_value(current: Any, desired: Any, strength: float) -> Any:
    if (
        isinstance(current, int | float)
        and not isinstance(current, bool)
        and isinstance(desired, int | float)
        and not isinstance(desired, bool)
    ):
        return float(current) + (float(desired) - float(current)) * strength
    if isinstance(current, list) and isinstance(desired, list):
        return _blend_sequence(current, desired, strength)
    return desired if strength >= 0.5 else current


def transfer_style_settings(
    reference: dict[str, Any], target: dict[str, Any], strength: float
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in sorted(ALLOWED_SETTINGS):
        if key not in reference:
            continue
        desired = normalize_setting(key, reference[key])
        if desired is None:
            continue
        current = normalize_setting(key, target.get(key, desired))
        if current is None:
            current = desired
        result[key] = blend_value(current, desired, strength)
    return result


def clamp_known_setting(key: str, value: Any) -> Any:
    bounds = _range_for(key)
    if bounds and isinstance(value, int | float) and not isinstance(value, bool):
        return clamp(float(value), *bounds)
    return value
