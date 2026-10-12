"""The check that keeps the CLI's scripted API honest (see api_contract.py)."""

import api_contract
import httpx2
from cli_fakes import CREW, LEE_ME, S2_PREVIEW, gateway

from mission_control.api.app import API_PREFIX, create_app
from mission_control.infra.settings import Settings


def _response(body=None, status=200):
    return httpx2.Response(status, json=body) if body is not None else httpx2.Response(status)


def test_contract_covers_every_api_route():
    spec = create_app(Settings()).openapi()["paths"]
    served = {
        (method.upper(), path.removeprefix(API_PREFIX))
        for path, operations in spec.items()
        if path.startswith(API_PREFIX)
        for method in operations
    }
    checked = {(m, r.path) for r in api_contract.ROUTES for m in r.methods}
    assert checked == served


def test_seed_shaped_records_match_the_real_models():
    assert api_contract.problems("GET", "/me", _response(LEE_ME)) == []
    assert api_contract.problems("GET", "/crew", _response(CREW)) == []
    assert api_contract.problems("GET", "/missions/1", _response(gateway())) == []
    assert api_contract.problems("GET", "/missions/1/match", _response(S2_PREVIEW)) == []


def test_an_unknown_field_is_drift():
    body = {**LEE_ME, "nickname": "Lee"}
    assert api_contract.problems("GET", "/me", _response(body)) == [
        "GET /me: body.nickname isn't in MeOut"
    ]


def test_a_nested_unknown_field_is_drift():
    body = [{**CREW[0], "skills": [{"skill_id": 1, "skill_name": "Piloting", "level": 5, "x": 1}]}]
    assert api_contract.problems("GET", "/crew", _response(body)) == [
        "GET /crew: body[0].skills[0].x isn't in SkillLevelOut"
    ]


def test_a_missing_field_is_drift():
    body = {k: v for k, v in LEE_ME.items() if k != "role"}
    [found] = api_contract.problems("GET", "/me", _response(body))
    assert found.startswith("GET /me: body doesn't match MeOut")


def test_an_endpoint_the_api_lacks_is_drift():
    assert api_contract.problems("GET", "/missions/1/crew", _response([])) == [
        "GET /missions/1/crew: the API has no such endpoint"
    ]


def test_the_success_status_must_match():
    assert api_contract.problems("POST", "/auth/logout", _response(status=200)) == [
        "POST /auth/logout: answers 204, not 200"
    ]


def test_errors_must_use_the_error_shape():
    good = {
        "error": {
            "code": "not_found",
            "message": "Mission not found",
            "problems": [{"code": "not_found", "message": "Mission not found", "refs": {}}],
        }
    }
    assert api_contract.problems("GET", "/missions/9", _response(good, 404)) == []
    [found] = api_contract.problems("GET", "/missions/9", _response({"detail": "x"}, 404))
    assert "error shape" in found


def test_an_error_code_must_belong_to_its_status():
    body = {
        "error": {
            "code": "overlap",
            "message": "x",
            "problems": [{"code": "overlap", "message": "x", "refs": {}}],
        }
    }
    assert api_contract.problems("POST", "/assignments/2/accept", _response(body, 409)) == [
        "POST /assignments/2/accept: the API doesn't send 'overlap' with a 409"
    ]
