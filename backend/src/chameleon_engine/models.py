"""Protocol models and validation without a runtime framework dependency."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ProtocolError(ValueError):
    """Raised when a request does not satisfy the wire contract."""


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolError(f"{name} must be an object")
    return value


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str | int) or isinstance(value, bool):
        raise ProtocolError(f"{name} must be a string or integer")
    result = str(value)
    if not result:
        raise ProtocolError(f"{name} must not be empty")
    return result


def _finite_number(value: object, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ProtocolError(f"{name} must be a number")
    result = float(value)
    if result != result or result in (float("inf"), float("-inf")):
        raise ProtocolError(f"{name} must be finite")
    return result


@dataclass(frozen=True)
class PhotoInput:
    id: str
    preview_path: Path
    develop_settings: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: object, name: str) -> PhotoInput:
        data = _mapping(value, name)
        preview_path = data.get("preview_path")
        if not isinstance(preview_path, str) or not preview_path:
            raise ProtocolError(f"{name}.preview_path must be a non-empty string")

        return cls(
            id=_identifier(data.get("id"), f"{name}.id"),
            preview_path=Path(preview_path),
            develop_settings=_mapping(data.get("develop_settings", {}), f"{name}.develop_settings"),
            metadata=_mapping(data.get("metadata", {}), f"{name}.metadata"),
        )


@dataclass(frozen=True)
class FitOptions:
    strength: float = 1.0
    adapt_exposure: bool = True
    adapt_white_balance: bool = True

    @classmethod
    def from_dict(cls, value: object) -> FitOptions:
        data = _mapping(value, "options")
        strength = _finite_number(data.get("strength", 1.0), "options.strength")
        if not 0.0 <= strength <= 1.0:
            raise ProtocolError("options.strength must be between 0 and 1")

        adapt_exposure = data.get("adapt_exposure", True)
        adapt_white_balance = data.get("adapt_white_balance", True)
        if not isinstance(adapt_exposure, bool):
            raise ProtocolError("options.adapt_exposure must be a boolean")
        if not isinstance(adapt_white_balance, bool):
            raise ProtocolError("options.adapt_white_balance must be a boolean")

        return cls(
            strength=strength,
            adapt_exposure=adapt_exposure,
            adapt_white_balance=adapt_white_balance,
        )


@dataclass(frozen=True)
class FitRequest:
    schema_version: int
    request_id: str
    reference: PhotoInput
    targets: tuple[PhotoInput, ...]
    options: FitOptions

    @classmethod
    def from_dict(cls, value: object) -> FitRequest:
        data = _mapping(value, "request")
        schema_version = data.get("schema_version")
        if schema_version != 1:
            raise ProtocolError(f"unsupported schema_version: {schema_version!r}")

        raw_targets = data.get("targets")
        if not isinstance(raw_targets, list) or not raw_targets:
            raise ProtocolError("targets must be a non-empty array")

        request = cls(
            schema_version=schema_version,
            request_id=_identifier(data.get("request_id"), "request_id"),
            reference=PhotoInput.from_dict(data.get("reference"), "reference"),
            targets=tuple(
                PhotoInput.from_dict(item, f"targets[{index}]")
                for index, item in enumerate(raw_targets)
            ),
            options=FitOptions.from_dict(data.get("options", {})),
        )

        target_ids = [target.id for target in request.targets]
        if len(target_ids) != len(set(target_ids)):
            raise ProtocolError("target photo ids must be unique")
        if request.reference.id in target_ids:
            raise ProtocolError("reference photo must not also be a target")
        return request
