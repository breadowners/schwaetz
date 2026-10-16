"""Compare local tutor models using synthetic, lesson-grounded turns. Never uploads audio.

Run: .venv/bin/python benchmark_models.py MODEL [MODEL ...]
Writes timings and outputs to git-ignored .cache/model-benchmark.json.
Language quality must be reviewed separately; timings are not an accuracy score.
"""
import argparse
import json
from pathlib import Path
import statistics
import time

import httpx
from content import SCENARIOS
from server import OLLAMA_URL, TutorReply, tutor_prompt

CASES = [
    {"id": "valid_reservation", "scenario": "restaurant", "attempt": "Ech hätt gär en Dësch fir zwou Persounen.",
     "check": "Accept this valid phrase. Do not invent a formal Dir form in the learner's sentence."},
    {"id": "valid_bill", "scenario": "restaurant", "attempt": "Kann ech d'Rechnung kréien, wgl.? Ech bezuele mat der Kaart.",
     "check": "Respond to paying by card. Both phrases occur in Lesson 04's restaurant phrase table."},
    {"id": "valid_ticket", "scenario": "transport", "attempt": "Ech huelen déi zweet Klass. Ech bezuele mat der Kaart.",
     "check": "Accept these Lesson 02 speaking-support phrases without inventing mistakes."},
    {"id": "separable_verb", "scenario": "transport", "attempt": "Den Zuch fortfiert um 2 Auer.",
     "check": "Correct to Den Zuch fiert um 2 Auer fort, following Lesson 02, separable verbs, item 3."},
    {"id": "pronunciation_boundary", "scenario": "free", "attempt": "Was my pronunciation correct?",
     "check": "Do not claim to hear, grade, or approve pronunciation from text."},
    {"id": "unknown_exam", "scenario": "free", "attempt": "What exactly will be on my next exam, and on which date?",
     "check": "Do not invent the next exam date, coverage, homework, or teacher statements."},
]

def benchmark(models, output, prompts=None):
    results = []
    with httpx.Client(timeout=180) as client:
        installed = {m["name"] for m in client.get(OLLAMA_URL + "/api/tags").json()["models"]}
        for model in models:
            if model not in installed:
                raise SystemExit(f"Model is not installed: {model}")
            print(f"Testing {model}", flush=True)
            # Unload only this benchmark's model, so its first request measures a cold start.
            client.post(OLLAMA_URL + "/api/generate", json={"model": model, "keep_alive": 0}).raise_for_status()
            runs = []
            for case in CASES:
                scenario = SCENARIOS[case["scenario"]]
                payload = {"model": model, "stream": False, "think": False, "keep_alive": "10m",
                           "format": TutorReply.model_json_schema(),
                           "options": {"temperature": 0.4, "num_predict": 400, "num_ctx": 8192},
                           "messages": [{"role": "system", "content": prompts[case["id"]] if prompts else tutor_prompt(scenario)},
                                        {"role": "assistant", "content": scenario["opening"]},
                                        {"role": "user", "content": case["attempt"]}]}
                started = time.monotonic()
                response = None
                try:
                    response = client.post(OLLAMA_URL + "/api/chat", json=payload)
                    response.raise_for_status()
                    raw = response.json()
                    reply = TutorReply.model_validate_json(raw["message"]["content"]).model_dump()
                    entry = {**case, "wall_seconds": round(time.monotonic() - started, 2), "reply": reply,
                             "metrics_seconds": {k: round(raw.get(k, 0) / 1e9, 2) for k in
                                                 ["load_duration", "prompt_eval_duration", "eval_duration"]},
                             "tokens": raw.get("eval_count"), "done_reason": raw.get("done_reason")}
                    print(f"  {case['id']}: {entry['wall_seconds']}s", flush=True)
                except (httpx.HTTPError, ValueError, KeyError) as exc:
                    entry = {**case, "wall_seconds": round(time.monotonic() - started, 2), "error": str(exc)}
                    if response is not None:
                        entry["response_excerpt"] = response.text[:1000]
                    print(f"  {case['id']}: failed: {exc}", flush=True)
                runs.append(entry)
                # Persist progress so a failed runner never destroys previous results.
                output.write_text(json.dumps(results + [{"model": model, "runs": runs}], ensure_ascii=False, indent=2))
                if "error" in entry:
                    break
            successful = [r["wall_seconds"] for r in runs[1:] if "error" not in r]
            results.append({"model": model, "runs": runs,
                            "warm_median_seconds": round(statistics.median(successful), 2) if successful else None})
            output.write_text(json.dumps(results, ensure_ascii=False, indent=2))
            client.post(OLLAMA_URL + "/api/generate", json={"model": model, "keep_alive": 0}).raise_for_status()
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="+")
    parser.add_argument("--output", default="model-benchmark.json", help="Filename in the local .cache folder")
    parser.add_argument("--prompt-set", help="Frozen prompt JSON filename in .cache for a fair comparison after app edits")
    args = parser.parse_args()
    if Path(args.output).name != args.output:
        parser.error("--output must be a filename")
    target = Path(__file__).resolve().parent / ".cache" / args.output
    target.parent.mkdir(exist_ok=True)
    prompts = None
    if args.prompt_set:
        if Path(args.prompt_set).name != args.prompt_set:
            parser.error("--prompt-set must be a filename")
        prompts = json.loads((target.parent / args.prompt_set).read_text())
    benchmark(args.models, target, prompts)
    print(f"Results: {target}")
