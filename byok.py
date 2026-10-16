"""Request-scoped OpenRouter credentials; no shared key, storage or paid fallback."""
from decimal import Decimal, InvalidOperation
import json

import httpx
from fastapi import HTTPException

PREFIX = "byok/openrouter/"
BASE_URL = "https://openrouter.ai/api/v1"


def is_free(model):
    prices = model.get("pricing", {})
    try:
        return ("prompt" in prices and "completion" in prices
                and all(Decimal(str(value)) == 0 for value in prices.values()))
    except (InvalidOperation, TypeError, ValueError):
        return False


def check_response(response):
    if response.status_code in (401, 403):
        raise HTTPException(401, "OpenRouter rejected this key or its access policy. Check your provider account.")
    if response.status_code == 402:
        raise HTTPException(402, "Your provider account or key has reached its credit limit. No other model was used.")
    if response.status_code == 429:
        raise HTTPException(429, "Your provider's request limit was reached. Wait and retry. No other key was used.")
    if not response.is_success:
        # Never return provider bodies: they can contain request details or credentials.
        raise HTTPException(502, "Your provider could not complete this request. No fallback was used.")


async def catalog(client):
    response = await client.get("models")
    check_response(response)
    return [m for m in response.json()["data"]
            if m.get("architecture", {}).get("output_modalities", ["text"]) == ["text"]]


def new_client(key):
    return httpx.AsyncClient(base_url=BASE_URL + "/", headers={"Authorization": "Bearer " + key},
                            timeout=90, trust_env=False, follow_redirects=False)


async def connect(key, free_only=True):
    async with new_client(key) as client:
        response = await client.get("key")
        check_response(response)
        models = await catalog(client)
    return [{"id": PREFIX + m["id"], "name": m.get("name", m["id"]), "free": is_free(m)}
            for m in models if not free_only or is_free(m)]


async def generate(key, model, free_only, instructions, messages, schema):
    if not model.startswith(PREFIX):
        raise HTTPException(400, "Choose an OpenRouter model from your connection.")
    selected = model.removeprefix(PREFIX)
    async with new_client(key) as client:
        # Recheck pricing on every turn, including after a promotion ends.
        models = await catalog(client)
        metadata = next((m for m in models if m["id"] == selected), None)
        if metadata is None or (free_only and not is_free(metadata)):
            raise HTTPException(409, "This model is unavailable or no longer free. Reconnect to refresh the list.")
        prompt = instructions + "\nReturn JSON only. Schema:\n" + json.dumps(schema)
        payload = {"model": selected, "messages": [{"role": "system", "content": prompt}] + messages,
                   "stream": False, "max_tokens": 800, "provider": {"allow_fallbacks": False}}
        if "response_format" in metadata.get("supported_parameters", []):
            payload["response_format"] = {"type": "json_object"}
        response = await client.post("chat/completions", json=payload)
        check_response(response)
        result = response.json()
        if "error" in result:
            raise HTTPException(502, "Your provider could not finish this reply. No fallback was used.")
        try:
            text = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise HTTPException(502, "Your provider returned an unreadable reply.")
        if not isinstance(text, str) or not text.strip():
            raise HTTPException(502, "Your provider returned an empty reply. Try another model.")
        text = text.strip()
        if text.startswith("```json\n") and text.endswith("```"):
            text = text[8:-3].strip()
        elif text.startswith("```\n") and text.endswith("```"):
            text = text[4:-3].strip()
        return text
