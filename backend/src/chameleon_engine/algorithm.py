"""Interpretable baseline for adaptive Lightroom develop-setting transfer."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .features import ImageFeatures, extract_features
from .models import FitOptions, PhotoInput
from .settings import clamp, clamp_known_setting, transfer_style_settings


class FitError(ValueError):
    """Raised when a target cannot produce an applicable setting set."""


@dataclass(frozen=True)
class FitResult:
    photo_id: str
    develop_settings: dict[str, Any]
    diagnostics: dict[str, Any]


class AdaptiveStyleEngine:
    """Feature-based baseline with explicit extension points for learned models."""

    def fit(
        self, reference: PhotoInput, targets: tuple[PhotoInput, ...], options: FitOptions
    ) -> tuple[FitResult, ...]:
        reference_features = extract_features(reference.preview_path)
        return tuple(
            self.fit_target(reference, reference_features, target, options) for target in targets
        )

    def fit_target(
        self,
        reference: PhotoInput,
        reference_features: ImageFeatures,
        target: PhotoInput,
        options: FitOptions,
    ) -> FitResult:
        target_features = extract_features(target.preview_path)
        settings = transfer_style_settings(
            reference.develop_settings,
            target.develop_settings,
            options.strength,
        )

        exposure_delta = self._exposure_delta(reference_features, target_features)
        if options.adapt_exposure:
            current_exposure = self._number(target.develop_settings.get("Exposure2012"), 0.0)
            desired_exposure = current_exposure + exposure_delta
            settings["Exposure2012"] = clamp_known_setting(
                "Exposure2012",
                current_exposure + (desired_exposure - current_exposure) * options.strength,
            )

        temperature_delta = 0.0
        tint_delta = 0.0
        if options.adapt_white_balance and options.strength > 0:
            temperature_delta, tint_delta = self._white_balance_delta(
                reference_features, target_features
            )
            self._adapt_white_balance(
                settings,
                target.develop_settings,
                temperature_delta,
                tint_delta,
                options.strength,
            )

        settings = {key: clamp_known_setting(key, value) for key, value in settings.items()}
        if not settings:
            raise FitError(
                "reference and target contain no supported style settings; "
                "enable exposure adaptation or edit the reference first"
            )
        confidence = self._confidence(exposure_delta, temperature_delta, tint_delta)
        return FitResult(
            photo_id=target.id,
            develop_settings=settings,
            diagnostics={
                "confidence": round(confidence, 4),
                "exposure_delta_ev": round(exposure_delta, 4),
                "temperature_delta": round(temperature_delta, 2),
                "tint_delta": round(tint_delta, 2),
                "reference_features": reference_features.to_dict(),
                "target_features": target_features.to_dict(),
            },
        )

    @staticmethod
    def _number(value: object, default: float) -> float:
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
        return default

    @staticmethod
    def _exposure_delta(reference: ImageFeatures, target: ImageFeatures) -> float:
        epsilon = 1.0 / 255.0
        delta = math.log2((reference.luma_median + epsilon) / (target.luma_median + epsilon))
        return clamp(delta, -3.0, 3.0)

    @staticmethod
    def _white_balance_delta(
        reference: ImageFeatures, target: ImageFeatures
    ) -> tuple[float, float]:
        epsilon = 1.0 / 255.0
        ref_r, ref_g, ref_b = reference.rgb_mean
        target_r, target_g, target_b = target.rgb_mean

        ref_rb = (ref_r + epsilon) / (ref_b + epsilon)
        target_rb = (target_r + epsilon) / (target_b + epsilon)
        temperature_delta = clamp(1800.0 * math.log(ref_rb / target_rb), -3000.0, 3000.0)

        ref_magenta_green = (ref_r + ref_b + 2 * epsilon) / (2 * (ref_g + epsilon))
        target_magenta_green = (target_r + target_b + 2 * epsilon) / (2 * (target_g + epsilon))
        tint_delta = clamp(70.0 * math.log(ref_magenta_green / target_magenta_green), -60.0, 60.0)
        return temperature_delta, tint_delta

    def _adapt_white_balance(
        self,
        output: dict[str, Any],
        target_settings: dict[str, Any],
        temperature_delta: float,
        tint_delta: float,
        strength: float,
    ) -> None:
        target_temperature = target_settings.get("Temperature")
        if isinstance(target_temperature, int | float) and not isinstance(target_temperature, bool):
            output["WhiteBalance"] = "Custom"
            output["Temperature"] = clamp_known_setting(
                "Temperature", float(target_temperature) + temperature_delta * strength
            )

        target_tint = target_settings.get("Tint")
        if isinstance(target_tint, int | float) and not isinstance(target_tint, bool):
            output["WhiteBalance"] = "Custom"
            output["Tint"] = clamp_known_setting("Tint", float(target_tint) + tint_delta * strength)

    @staticmethod
    def _confidence(exposure_delta: float, temperature_delta: float, tint_delta: float) -> float:
        distance = (
            abs(exposure_delta) / 3.0 + abs(temperature_delta) / 3000.0 + abs(tint_delta) / 60.0
        ) / 3.0
        return clamp(1.0 - 0.55 * distance, 0.2, 1.0)
