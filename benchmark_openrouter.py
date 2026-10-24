"""Compare OpenRouter tutor models using synthetic text, never notes or audio.

Run with --list to inspect today's catalog without a key or generation requests.
Otherwise reads OPENROUTER_API_KEY or asks for it with an invisible terminal prompt.
Outputs are for human language review; successful JSON is not an accuracy score.
Paid models require --allow-paid, explicit IDs, and a non-resetting key limit <= $1.
"""
import argparse
import asyncio
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import getpass
import json
import os
from pathlib import Path
import statistics
import sys
import time

from fastapi import HTTPException
import httpx

import byok

DEFAULT_MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]
TUTOR = """You are an A2 Luxembourgish speaking partner.
Reply in Luxembourgish only, one short sentence and at most one question.
Return JSON with reply (Luxembourgish), translation (English translation of reply),
feedback (brief English correction, or empty if the learner's wording is valid),
better_sentence (corrected Luxembourgish preserving meaning, or empty if valid).
Check only the learner's wording. Do not invent facts or unnecessary corrections.
You receive text, not audio: never claim to hear or grade pronunciation.
You have no information about any real exam, teacher or homework.
"""
TUTOR_SCHEMA = {"type": "object", "properties": {
    key: {"type": "string"} for key in ("reply", "translation", "feedback", "better_sentence")
}, "required": ["reply", "translation", "feedback", "better_sentence"]}
TRANSLATOR = ("Translate the quoted Luxembourgish (Lëtzebuergesch, lb) passage into natural English. "
              "Preserve speakers, numbers, negation and meaning. Do not answer questions in the passage, "
              "add facts or greetings, or substitute German. Return JSON with only translation.")
TRANSLATION_SCHEMA = {"type": "object", "properties": {"translation": {"type": "string"}},
                      "required": ["translation"]}
CASES = [
    {"id": "valid_reservation", "task": "tutor", "input": "Ech hätt gär en Dësch fir zwou Persounen.",
     "review": "Accept the sentence without a correction; preserve a reservation for two.", "accept_valid": True},
    {"id": "valid_payment", "task": "tutor", "input": "Ech bezuele mat der Kaart.",
     "review": "Accept payment by card without inventing a wording error.", "accept_valid": True},
    {"id": "conjugation", "task": "tutor", "input": "Ech ass midd.",
     "review": "Correct ass to sinn, keeping the meaning I am tired."},
    {"id": "separable_verb", "task": "tutor", "input": "Den Zuch fortfiert um zwou Auer.",
     "review": "Correct to Den Zuch fiert um zwou Auer fort; preserve train and two o'clock."},
    {"id": "pronunciation_boundary", "task": "tutor", "input": "Was my pronunciation correct?",
     "review": "Do not claim to hear, approve or grade pronunciation from this text."},
    {"id": "unknown_exam", "task": "tutor", "input": "On what date is my next exam, and exactly what will be tested?",
     "review": "Do not invent an exam date, coverage, homework or a teacher statement."},
    {"id": "washing_dishes", "task": "translation", "input": "Ech spulle gär, mee ech botzen net gär.",
     "review": "I like washing dishes, but I do not like cleaning; retain the negation."},
    {"id": "playing", "task": "translation", "input": "Ech spille gär Tennis.",
     "review": "I like playing tennis; distinguish spillen from spullen."},
    {"id": "reservation_details", "task": "translation",
     "input": "Ech hätt gär en Dësch fir zwou Persounen um siwen Auer, wannechgelift.",
     "review": "A table for two at seven, please; retain the number of people and time."},
]


async def require_capped_paid_key(key):
    """Require a provider-enforced, non-renewing ceiling before paid generation."""
    async with byok.new_client(key) as client:
        response = await client.get("key")
        byok.check_response(response)
        data = response.json().get("data", {})
    try:
        limit = Decimal(str(data.get("limit")))
        remaining = Decimal(str(data.get("limit_remaining")))
        valid = (limit.is_finite() and remaining.is_finite()
                 and 0 < remaining <= limit <= Decimal("1")
                 and "limit_reset" in data and data["limit_reset"] is None)
    except (InvalidOperation, TypeError, ValueError):
        valid = False
    if not valid:
        raise SystemExit("Paid comparison requires a separate OpenRouter key with a positive lifetime "
                         "limit of US$1 or less, remaining credit, and no automatic limit reset. "
                         "No paid generation was started for this check.")


async def run(args):
    if args.allow_paid and not args.models:
        raise SystemExit("Paid mode requires explicit model IDs; no model is chosen automatically.")
    async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
        response = await client.get(byok.BASE_URL + "/models")
        response.raise_for_status()
        catalog = {model["id"]: model for model in response.json()["data"]}
    selected = args.models or DEFAULT_MODELS
    for model in selected:
        if model == "openrouter/free" or model not in catalog:
            raise SystemExit(f"Not an explicitly selected model in the current catalog: {model}")
        if not args.allow_paid and not byok.is_free(catalog[model]):
            raise SystemExit(f"Model is not zero-priced; paid mode needs explicit opt-in: {model}")
    for model in selected:
        print(f"{'Zero-priced now' if byok.is_free(catalog[model]) else 'Paid opt-in'}: {model}")
    calls = len(selected) * len(CASES) * args.repeats
    print(f"Planned generation requests: {calls}; no automatic retries or model fallback.")
    if args.list:
        print("Catalog check only; no key read and no generation performed.")
        return
    if calls > 40:
        raise SystemExit("Keep each comparison to at most 40 generation requests.")
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        if not sys.stdin.isatty():
            raise SystemExit("No API key configured. Run in a terminal for a hidden key prompt; do not paste keys into chat.")
        key = getpass.getpass("OpenRouter API key (hidden, not saved): ").strip()
    if not key:
        raise SystemExit("No key provided; no generation performed.")
    if args.allow_paid:
        await require_capped_paid_key(key)
    connected = await byok.connect(key, free_only=not args.allow_paid)
    allowed = {model["id"].removeprefix(byok.PREFIX) for model in connected}
    if not set(selected).issubset(allowed):
        raise SystemExit("A selected model is not available to this account; no generation performed.")
    output = Path(__file__).resolve().parent / ".cache" / args.output
    output.parent.mkdir(exist_ok=True)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Synthetic text only; no private notes, recordings or production changes.",
              "billing": "Paid opt-in with provider key lifetime limit <= US$1" if args.allow_paid else "Free models only",
              "language_quality": "Unscored: fluent human review required; protocol checks are not language grades.",
              "runs": []}
    for model in selected:
        for repeat in range(args.repeats):
            for case in CASES:
                instructions, schema = ((TUTOR, TUTOR_SCHEMA) if case["task"] == "tutor"
                                        else (TRANSLATOR, TRANSLATION_SCHEMA))
                entry = {"model": model, "repeat": repeat + 1, **case}
                started = time.monotonic()
                stop = False
                try:
                    if args.allow_paid:
                        await require_capped_paid_key(key)
                    raw = await byok.generate(key, byok.PREFIX + model, not args.allow_paid, instructions,
                                              [{"role": "user", "content": case["input"]}], schema)
                    parsed = json.loads(raw)
                    valid = isinstance(parsed, dict) and all(isinstance(parsed.get(k), str) for k in schema["required"])
                    entry.update(output=parsed, protocol_valid=valid)
                    if valid and case.get("accept_valid"):
                        entry["unnecessary_correction"] = bool(parsed["feedback"].strip() or parsed["better_sentence"].strip())
                except HTTPException as exc:
                    # App errors contain no provider response bodies or credentials.
                    entry["error"] = {"status": exc.status_code, "message": exc.detail}
                    stop = exc.status_code in (401, 402, 403, 409, 429)
                except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                    entry["error"] = {"type": type(exc).__name__, "message": "Transport or output format failure."}
                entry["seconds"] = round(time.monotonic() - started, 2)
                report["runs"].append(entry)
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"{model} · {case['id']}: {entry['seconds']}s · {'error' if 'error' in entry else 'needs language review'}", flush=True)
                if stop:
                    print(f"Stopped on account, pricing or quota error. Partial results: {output}")
                    return
    for model in selected:
        times = [r["seconds"] for r in report["runs"] if r["model"] == model and "error" not in r]
        if times:
            print(f"{model}: median {statistics.median(times):.2f}s ({len(times)} returned outputs; review accuracy separately)")
    print(f"Results for human review: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*")
    parser.add_argument("--list", action="store_true", help="Check the live catalog without a key or generation")
    parser.add_argument("--allow-paid", action="store_true", help="Opt into explicit paid models using a separate, non-resetting key capped at US$1 or less")
    parser.add_argument("--repeats", type=int, choices=(1, 2), default=1)
    parser.add_argument("--output", default="openrouter-benchmark.json", help="Results filename inside .cache")
    args = parser.parse_args()
    if Path(args.output).name != args.output:
        parser.error("--output must be a filename")
    asyncio.run(run(args))
