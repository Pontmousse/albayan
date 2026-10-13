"""Canonical unit discovery must be explicit in public authoring capabilities."""

from __future__ import annotations

from unittest.mock import patch

from app.main import app
from app.routers.math_authoring import read_unit_registry
from app.schemas.math_authoring import MathAuthoringCapabilitiesRead
from app.services.math_authoring_capabilities import get_math_authoring_capabilities


def test_capabilities_advertise_canonical_unit_syntax_and_tool_names():
    raw = get_math_authoring_capabilities()
    response = MathAuthoringCapabilitiesRead.model_validate(raw)
    unit = response.unit_discovery

    assert unit["canonical_syntax"] == r"\mathsf{token}"
    assert unit["token_pattern"] == "^[A-Za-z][A-Za-z0-9]*$"
    assert unit["notation_only"] is True
    assert unit["case_sensitive"] is True
    assert unit["registry_tool"] == "get_unit_registry"
    assert unit["article_tool"] == "get_article_unit_context"
    assert unit["apply_tool"] == "apply_article_unit_conventions"
    assert unit["unknown_explicit_token"] == "preserve_canonical_identity_and_warn"
    assert unit["examples"] == [
        r"v = 30\mathsf{m}/\mathsf{s}",
        r"A = 2\mathsf{m}^2",
        r"E = 5\mathsf{CU}",
    ]
    assert "get_unit_registry" in response.preferred_submission["semantic_conventions"]["unit"]
    assert "get_article_unit_context" in response.preferred_submission["semantic_conventions"]["unit"]
    assert "no numerical" in response.preferred_submission["semantic_conventions"]["unit"].lower()
    unit_command = next(
        item for item in response.round_trip_safe["commands"]["semantic_roles"]
        if item["command"] == r"\mathsf"
    )
    assert "A-Za-z0-9" in unit_command["argument"]


def test_registry_endpoint_requires_read_scope_and_uses_burhan_live_service():
    registry = {
        "version": 1, "canonical_syntax": r"\mathsf{token}",
        "token_pattern": "^[A-Za-z][A-Za-z0-9]*$",
        "notation_only": True,
        "units": {"kg": {"default_display": "كلغ"}},
    }
    actor = object()
    with (
        patch("app.routers.math_authoring.require_actor_scope") as require,
        patch("app.routers.math_authoring.get_unit_registry", return_value=registry) as get,
    ):
        result = read_unit_registry(actor)
    require.assert_called_once_with(actor, "articles:read")
    get.assert_called_once_with()
    assert result is registry


def test_registry_route_is_discoverable_under_math_namespace():
    matching = [
        route for route in app.routes
        if getattr(route, "path", None) == "/api/v1/math/unit-registry"
    ]
    assert len(matching) == 1
    assert "GET" in matching[0].methods
