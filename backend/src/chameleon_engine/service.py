"""Application service that converts protocol models into JSON-ready responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import __version__
from .algorithm import AdaptiveStyleEngine, FitError
from .features import FeatureError, extract_features
from .models import FitRequest


def fit_request(request: FitRequest) -> dict[str, Any]:
    engine = AdaptiveStyleEngine()
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    reference_features = extract_features(request.reference.preview_path)
    for target in request.targets:
        try:
            result = engine.fit_target(
                request.reference, reference_features, target, request.options
            )
            results.append(
                {
                    "photo_id": result.photo_id,
                    "develop_settings": result.develop_settings,
                    "diagnostics": result.diagnostics,
                }
            )
        except (FeatureError, FitError) as exc:
            errors.append({"photo_id": target.id, "message": str(exc)})

    return {
        "schema_version": 1,
        "request_id": request.request_id,
        "status": "ok" if not errors else ("partial" if results else "error"),
        "engine": {"name": "chameleon-engine", "version": __version__},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "errors": errors,
    }
