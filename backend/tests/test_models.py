from __future__ import annotations

import pytest

from chameleon_engine.models import FitRequest, ProtocolError


def request_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "request_id": "request-1",
        "reference": {
            "id": "1",
            "preview_path": "fixtures/ref.jpg",
            "develop_settings": {},
            "metadata": {},
        },
        "targets": [
            {
                "id": "2",
                "preview_path": "fixtures/target.jpg",
                "develop_settings": {},
                "metadata": {},
            }
        ],
        "options": {"strength": 0.75},
    }


def test_request_parses_and_normalizes_ids() -> None:
    payload = request_payload()
    payload["reference"]["id"] = 1  # type: ignore[index]

    request = FitRequest.from_dict(payload)

    assert request.reference.id == "1"
    assert request.targets[0].id == "2"
    assert request.options.strength == 0.75


@pytest.mark.parametrize("strength", [-0.1, 1.1, "full"])
def test_request_rejects_invalid_strength(strength: object) -> None:
    payload = request_payload()
    payload["options"]["strength"] = strength  # type: ignore[index]

    with pytest.raises(ProtocolError):
        FitRequest.from_dict(payload)


def test_request_rejects_reference_as_target() -> None:
    payload = request_payload()
    payload["targets"][0]["id"] = "1"  # type: ignore[index]

    with pytest.raises(ProtocolError, match="must not also be a target"):
        FitRequest.from_dict(payload)
