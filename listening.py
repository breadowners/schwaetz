"""Official source catalog and selected, read-only listening support."""
import json
from pathlib import Path
import re

import content

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".cache/listening"
DATA = json.loads((ROOT / "listening_catalog.json").read_text(encoding="utf-8"))
EPISODES = {episode["id"]: episode for episode in DATA["episodes"]}
TRANSLATED_NOTE = "A2.1/Tests/A2.1 Mock Test 02.md"


def audio_path(episode):
    name = episode.get("audio_file", "")
    if name:
        path = (CACHE / name).resolve()
        if path.is_relative_to(CACHE.resolve()) and path.is_file():
            return path
    if not content.PUBLIC_MODE and episode.get("local_audio"):
        path = (content.VAULT / episode["local_audio"]).resolve()
        if path.is_relative_to((content.VAULT / "A2.1/Materials").resolve()) and path.is_file():
            return path
    return None


def translated_rows(episode):
    """Use only the user's already translated transcript, never test answers."""
    path = content.VAULT / TRANSLATED_NOTE
    if content.PUBLIC_MODE or not episode.get("note_heading") or not path.is_file():
        return []
    text = content.section_text(path.read_text(encoding="utf-8"), episode["note_heading"])
    marker = re.search(r"(?m)^Transkript:?\s*$", text)
    if not marker:
        return []
    rows, pending = [], ""
    for raw in text[marker.end():].splitlines():
        line = raw.strip()
        if re.match(r"\*\*L\d+\.", line):
            break
        if not line:
            continue
        if line.startswith("*") and not line.startswith("**") and line.endswith("*"):
            if pending:
                rows.append({"text": pending, "translation": line[1:-1]})
                pending = ""
        else:
            pending = line
    return rows


def public_episode(episode):
    keys = ("id", "title", "publisher_title", "topics", "level", "guide", "published",
            "duration", "publisher_url", "transcript_url", "audio_url")
    return {**{key: episode.get(key, "") for key in keys},
            "publisher": DATA["publisher"], "audio_available": audio_path(episode) is not None,
            "has_translated_transcript": bool(translated_rows(episode)),
            "question_count": len(episode["questions"])}


def catalog():
    return {"episodes": [public_episode(episode) for episode in EPISODES.values()],
            "books": DATA["books"], "checked_on": DATA["checked_on"]}


def detail(episode):
    return {**public_episode(episode), "transcript": translated_rows(episode),
            "translation_note": "English study translations from your existing notes; not official INLL translations.",
            "questions": [{"id": i, "prompt": q["prompt"], "options": q["options"]}
                          for i, q in enumerate(episode["questions"])]}
