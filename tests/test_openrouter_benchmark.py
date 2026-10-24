import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

import benchmark_openrouter as benchmark
import byok


@pytest.mark.parametrize("data", [
    {},
    {"limit": None, "limit_remaining": None, "limit_reset": None},
    {"limit": 20, "limit_remaining": 20, "limit_reset": None},
    {"limit": 1, "limit_remaining": 1, "limit_reset": "daily"},
    {"limit": 1, "limit_remaining": 1},
    {"limit": 1, "limit_remaining": 0, "limit_reset": None},
    {"limit": "NaN", "limit_remaining": 1, "limit_reset": None},
    {"limit": 1, "limit_remaining": 2, "limit_reset": None},
])
def test_paid_benchmark_rejects_unbounded_resetting_exhausted_or_unknown_key(monkeypatch, data):
    client_type = httpx.AsyncClient
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"data": data})
    monkeypatch.setattr(byok, "new_client", lambda key: client_type(
        base_url=byok.BASE_URL + "/", transport=httpx.MockTransport(handler)))
    with pytest.raises(SystemExit, match="lifetime"):
        asyncio.run(benchmark.require_capped_paid_key("test-only-key"))
    assert calls == ["/api/v1/key"]


def test_paid_benchmark_uses_only_explicit_model_and_does_not_save_key(tmp_path, monkeypatch):
    key = "test-only-benchmark-owner-key"
    monkeypatch.setenv("OPENROUTER_API_KEY", key)
    monkeypatch.setattr(benchmark, "__file__", str(tmp_path / "benchmark_openrouter.py"))
    monkeypatch.setattr(benchmark, "CASES", benchmark.CASES[:1])
    requests = []
    model = {"id": "test/paid", "pricing": {"prompt": "0.000001", "completion": "0.000001"}}
    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/key"):
            return httpx.Response(200, json={"data": {"limit": 1, "limit_remaining": .95, "limit_reset": None}})
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [model]})
        body = json.loads(request.content)
        assert body["model"] == "test/paid" and body["provider"]["allow_fallbacks"] is False
        assert body["max_tokens"] == 800
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "reply": "Moien!", "translation": "Hello!", "feedback": "", "better_sentence": ""})}}]})
    client_type = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client_type(
        transport=httpx.MockTransport(handler), **kwargs))
    args = SimpleNamespace(models=["test/paid"], allow_paid=True, list=False, repeats=1, output="results.json")
    asyncio.run(benchmark.run(args))
    report = (tmp_path / ".cache/results.json").read_text()
    assert key not in report and "limit_remaining" not in report
    assert json.loads(report)["runs"][0]["protocol_valid"]
    assert len([r for r in requests if r.method == "POST"]) == 1
    assert len([r for r in requests if r.url.path.endswith("/key")]) == 3


def test_paid_mode_never_selects_models_implicitly():
    with pytest.raises(SystemExit, match="explicit model IDs"):
        asyncio.run(benchmark.run(SimpleNamespace(models=[], allow_paid=True)))
