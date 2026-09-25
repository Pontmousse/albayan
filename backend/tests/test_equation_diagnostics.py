from __future__ import annotations

from fastapi import HTTPException

from app.services import equation_diagnostic_service


def _math_object() -> dict:
    return {
        "node_type": "MathObject",
        "math_mode": "$",
        "lines": [
            {
                "node_type": "ChainClass",
                "chain": [{"node_type": "CharObject", "expr": "س"}],
            }
        ],
        "closing": "$",
        "source_side": "arabic",
        "source_owner": "editor",
    }


def _install_successful_pipeline(monkeypatch) -> None:
    def fake_convert(latex, *, display, label, mappings, model_tier=None, diagnostics=None):
        assert latex == "x"
        assert display is False
        assert label is None
        assert mappings == {}
        assert model_tier == "heuristic"
        diagnostics.update(
            {
                "canonical_input": {
                    "latex": "x",
                    "full_match": "$x$",
                    "opening": "$",
                    "inner_content": "x",
                    "closing": "$",
                    "display": False,
                },
                "burhan_request": {
                    "model_tier": "heuristic",
                    "digits_mapping": "digits",
                    "prescanning": True,
                    "mapping_count": 0,
                },
                "english_json": {"node_type": "MathObject"},
                "arabic_json": {"node_type": "MathObject"},
                "arabic_latex": "$س$",
                "mappings": {"x": "س"},
                "warnings": [],
                "resolved_model": None,
                "duration_ms": 1.25,
                "editor_math_object": _math_object(),
            }
        )
        return {
            "kind": "math",
            "source": "$س$",
            "math_object": _math_object(),
        }, {"x": "س"}

    def fake_normalize(document):
        assert document == {"node_type": "DocumentObject", "blocks": []}
        return document

    def fake_apply(document, command):
        if command["op"] == "insert_text_block":
            return {
                "node_type": "DocumentObject",
                "blocks": [
                    {
                        "id": "block_1",
                        "command": "\\paragraph",
                        "value": "",
                        "inline_ids": {"field_id": "field_1", "tokens": []},
                    }
                ],
            }
        assert command["op"] == "insert_inline_token"
        assert command["field_id"] == "field_1"
        assert command["token"]["math_object"] == _math_object()
        return {
            "node_type": "DocumentObject",
            "blocks": [{"id": "block_1", "value": "$س$"}],
        }

    monkeypatch.setattr(
        equation_diagnostic_service.burhan_client,
        "convert_latex_to_math_token",
        fake_convert,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "normalize_document",
        fake_normalize,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_worker_client,
        "apply_document_command",
        fake_apply,
    )
    monkeypatch.setattr(
        equation_diagnostic_service.butex_diagnostic_client,
        "diagnose_math_object",
        lambda math: {
            "ok": True,
            "stage": "mathObjectToEditorSession",
            "editable": True,
            "english_latex": "x",
            "arabic_latex": "س",
        },
    )
    monkeypatch.setattr(
        equation_diagnostic_service.burhan_reverse_client,
        "convert_math_object_to_english",
        lambda math, *, variable_mapping, model_tier=None: ("x", []),
    )


def test_inspect_equation_reports_each_real_pipeline_stage(monkeypatch) -> None:
    _install_successful_pipeline(monkeypatch)

    report = equation_diagnostic_service.inspect_equation(
        latex="x",
        display=False,
        model_tier="heuristic",
    )

    assert report["ok"] is True
    assert report["partial"] is False
    assert report["stages"]["burhan_conversion"]["data"]["english_json"] == {
        "node_type": "MathObject"
    }
    assert report["stages"]["albayan_projection"]["data"]["editor_math_object"] == _math_object()
    assert report["stages"]["document2_command"]["ok"] is True
    assert report["stages"]["headless_butex_validation"]["data"]["editable"] is True
    assert report["stages"]["reverse_conversion"]["data"]["canonical_latex"] == "x"
    assert report["stages"]["browser_validation"]["available"] is False


def test_burhan_unavailable_blocks_downstream_without_fabricating(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise HTTPException(
            status_code=503,
            detail={"code": "burhan_unavailable", "message": "missing"},
        )

    monkeypatch.setattr(
        equation_diagnostic_service.burhan_client,
        "convert_latex_to_math_token",
        fail,
    )

    report = equation_diagnostic_service.inspect_equation(
        latex="x",
        display=False,
        model_tier="heuristic",
    )

    assert report["ok"] is False
    assert report["partial"] is True
    assert report["stages"]["burhan_conversion"]["available"] is False
    for name in (
        "albayan_projection",
        "document2_command",
        "headless_butex_validation",
        "reverse_conversion",
    ):
        assert report["stages"][name]["available"] is False
        assert report["stages"][name]["reason"] == "blocked_by_burhan"


def test_missing_butex_headless_adapter_is_explicit_partial_result(monkeypatch) -> None:
    _install_successful_pipeline(monkeypatch)

    def missing(_math):
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "old worker"},
        )

    monkeypatch.setattr(
        equation_diagnostic_service.butex_diagnostic_client,
        "diagnose_math_object",
        missing,
    )

    report = equation_diagnostic_service.inspect_equation(
        latex="x",
        display=False,
        model_tier="heuristic",
    )

    assert report["ok"] is False
    assert report["partial"] is True
    stage = report["stages"]["headless_butex_validation"]
    assert stage["available"] is False
    assert stage["ok"] is None
    assert "Deploy a BuTeX worker revision" in stage["human_action"]
