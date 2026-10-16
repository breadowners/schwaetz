import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException

import byok

KEY_A = "test-only-alpha-1234567890"
KEY_B = "test-only-beta-1234567890"


def model(name="test/free:free", price="0"):
    return {"id": name, "name": name, "pricing": {"prompt": price, "completion": price}}


def transport(monkeypatch, handler):
    client_type = httpx.AsyncClient
    monkeypatch.setattr(byok, "new_client", lambda key: client_type(
        base_url=byok.BASE_URL + "/", headers={"Authorization": "Bearer " + key},
        transport=httpx.MockTransport(handler)))


def test_free_check_fails_closed_for_missing_or_nonzero_prices():
    assert byok.is_free(model())
    for value in ({}, {"pricing": {}}, model(price="0.001"), model(price="unknown"),
                  {**model(), "pricing": {"prompt": "0", "completion": "0", "request": "1"}}):
        assert not byok.is_free(value)


def test_keys_are_request_scoped_and_model_calls_use_only_the_requesting_key(monkeypatch):
    calls = []
    def handler(request):
        calls.append((request.url.path, request.headers["authorization"]))
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [model()]})
        body = json.loads(request.content)
        assert body["model"] == "test/free:free"
        assert body["provider"]["allow_fallbacks"] is False
        assert "models" not in body and "tools" not in body
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"reply":"Moien!"}'}}]})
    transport(monkeypatch, handler)
    async def run():
        for key in (KEY_A, KEY_B):
            assert await byok.generate(key, byok.PREFIX + "test/free:free", True, "Tutor", [], {}) == '{"reply":"Moien!"}'
    asyncio.run(run())
    assert calls == [("/api/v1/models", "Bearer " + KEY_A), ("/api/v1/chat/completions", "Bearer " + KEY_A),
                     ("/api/v1/models", "Bearer " + KEY_B), ("/api/v1/chat/completions", "Bearer " + KEY_B)]


@pytest.mark.parametrize("models", [[], [model(price="0.01")]])
def test_removed_or_newly_paid_model_never_triggers_generation(monkeypatch, models):
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"data": models})
    transport(monkeypatch, handler)
    with pytest.raises(HTTPException) as error:
        asyncio.run(byok.generate(KEY_A, byok.PREFIX + "test/free:free", True, "Tutor", [], {}))
    assert error.value.status_code == 409
    assert calls == ["/api/v1/models"]


@pytest.mark.parametrize("status", [401, 403, 402, 429, 500])
def test_provider_errors_never_echo_credentials_or_raw_details(status):
    response = httpx.Response(status, text=KEY_A)
    with pytest.raises(HTTPException) as error:
        byok.check_response(response)
    assert KEY_A not in error.value.detail


def test_connection_checks_key_without_generating_and_filters_paid_models(monkeypatch):
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"data": {"private_account_detail": "hidden"} if request.url.path.endswith("/key") else [model(), model("test/paid", "1")]})
    transport(monkeypatch, handler)
    result = asyncio.run(byok.connect(KEY_A))
    assert result == [{"id": byok.PREFIX + "test/free:free", "name": "test/free:free", "free": True}]
    assert calls == ["/api/v1/key", "/api/v1/models"]


def test_paid_model_needs_explicit_opt_in_and_never_changes_model(monkeypatch):
    calls = []
    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [model("test/paid", "1")]})
        payload = json.loads(request.content)
        assert KEY_A not in request.content.decode()
        calls.append(payload["model"])
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"reply":"Moien!"}'}}]})
    transport(monkeypatch, handler)
    asyncio.run(byok.generate(KEY_A, byok.PREFIX + "test/paid", False, "Tutor", [], {}))
    assert calls == ["test/paid"]
