import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opencode_runtime import MODEL_ID, MODEL, GLM_MODEL_ID, GLM_MODEL, OpenCodeRuntime, is_free_model


def free_model(model_id=MODEL_ID):
    return {"id": model_id, "providerID": "opencode", "enabled": True, "status": "active",
            "cost": [{"input": 0, "output": 0, "cache": {"read": 0, "write": 0}}],
            "variants": [{"id": "low"}]}


def test_only_exact_active_free_model_is_accepted():
    assert is_free_model(free_model())
    assert is_free_model(free_model(GLM_MODEL_ID))
    for changes in ({"id": "deepseek-v4.1-flash"}, {"id": "glm-5.3-flash"},
                    {"providerID": "other"}, {"enabled": False}, {"status": "deprecated"},
                    {"cost": []}, {"cost": [{"input": 0, "output": 1}]},
                    {"cost": [{"input": 0, "output": 0, "cache": {"read": 1}}]}):
        assert not is_free_model({**free_model(), **changes})


@pytest.mark.parametrize("failed", [False, True])
@pytest.mark.parametrize("model", [MODEL, GLM_MODEL])
def test_transient_generation_uses_free_model_and_removes_its_empty_context_on_close(failed, model):
    calls = []
    def handler(request):
        body = json.loads(request.content) if request.content else None
        calls.append((request.method, request.url.path, body))
        if request.url.path == "/api/model":
            data = {"data": [free_model(), free_model(GLM_MODEL_ID)]}
        elif request.url.path == "/api/session":
            data = {"data": {"id": "ses_test"}}
        elif request.method == "DELETE":
            return httpx.Response(204)
        elif failed:
            return httpx.Response(503)
        else:
            data = {"data": {"text": '```json\n{"reply":"Moien!"}\n```'}}
        return httpx.Response(200, json=data)
    async def run():
        runtime = OpenCodeRuntime()
        runtime.ready = True
        runtime.location = {"directory": "/temporary-empty-directory"}
        async with httpx.AsyncClient(base_url="http://127.0.0.1:9999", transport=httpx.MockTransport(handler)) as client:
            runtime.client = client
            if failed:
                with pytest.raises(httpx.HTTPStatusError):
                    await runtime.generate("Tutor instructions", [{"role": "user", "content": "Moien!"}], {}, model)
            else:
                assert await runtime.generate("Tutor instructions", [{"role": "user", "content": "Moien!"}], {}, model) == '{"reply":"Moien!"}'
            await runtime.close()
    asyncio.run(run())
    assert [c[:2] for c in calls] == [("GET", "/api/model"), ("POST", "/api/session"),
                                     ("POST", "/api/session/ses_test/generate"), ("DELETE", "/api/session/ses_test")]
    assert calls[1][2]["model"]["id"] == model.removeprefix("opencode/")
    assert calls[1][2]["model"]["variant"] == "low"
    assert "Moien!" in calls[2][2]["prompt"]


@pytest.mark.parametrize("catalog", [[], [free_model()], [free_model("glm-5.3-flash")],
                                     [{**free_model(GLM_MODEL_ID), "cost": [{"input": 1, "output": 0}]}]])
def test_missing_selected_free_offer_prevents_generation_without_falling_back(catalog):
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"data": catalog})
    async def run():
        runtime = OpenCodeRuntime()
        runtime.ready = True
        async with httpx.AsyncClient(base_url="http://127.0.0.1:9999", transport=httpx.MockTransport(handler)) as client:
            runtime.client = client
            with pytest.raises(RuntimeError):
                await runtime.generate("Tutor", [], {}, GLM_MODEL)
    asyncio.run(run())
    assert calls == ["/api/model"]


def test_catalog_offers_each_validated_model_independently():
    runtime = OpenCodeRuntime()
    runtime.update_catalog({"data": [free_model(GLM_MODEL_ID), free_model("deepseek-v4.1-flash")]})
    assert list(runtime.available_models) == [GLM_MODEL]
    runtime.update_catalog({"data": [free_model()]})
    assert list(runtime.available_models) == [MODEL]


def test_repeated_turns_reuse_only_empty_context_and_recheck_free_price_each_time():
    calls = []
    def handler(request):
        calls.append((request.method, request.url.path))
        if request.url.path == "/api/model":
            return httpx.Response(200, json={"data": [free_model()]})
        if request.url.path == "/api/session":
            return httpx.Response(200, json={"data": {"id": "ses_empty"}})
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json={"data": {"text": '{"reply":"Moien!"}'}})
    async def run():
        runtime = OpenCodeRuntime()
        runtime.ready = True
        runtime.location = {"directory": "/temporary-empty-directory"}
        runtime.client = httpx.AsyncClient(base_url="http://127.0.0.1:9999", transport=httpx.MockTransport(handler))
        await runtime.generate("Tutor", [{"role": "user", "content": "Moien"}], {}, MODEL)
        await runtime.generate("Tutor", [{"role": "user", "content": "Merci"}], {}, MODEL)
        assert len(runtime.sessions) == 1
        await runtime.close()
        assert not runtime.sessions
    asyncio.run(run())
    assert calls.count(("GET", "/api/model")) == 2
    assert calls.count(("POST", "/api/session")) == 1
    assert calls.count(("POST", "/api/session/ses_empty/generate")) == 2
    assert calls.count(("DELETE", "/api/session/ses_empty")) == 1
    assert not any(path.endswith("/prompt") for _, path in calls)
