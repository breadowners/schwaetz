from pathlib import Path

import content
import listening


def test_only_translated_user_transcript_is_read_not_exam_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(content, "VAULT", tmp_path)
    monkeypatch.setattr(content, "PUBLIC_MODE", False)
    path = tmp_path / listening.TRANSLATED_NOTE
    path.parent.mkdir(parents=True)
    episode = listening.EPISODES["restaurant-bank"]
    path.write_text(f"""# Private notes
PRIVATE MATERIAL
### {episode['note_heading']}
Audio instructions.
Transkript:
*English study translations appear beneath each sentence.*
Am Restaurant
Client: Moien!
*Hello!*
Serveur: Gudden Owend.
*Good evening.*
**L1. PRIVATE TEST ANSWER**
Do not include this.
### Other audio
OTHER PRIVATE MATERIAL
""")
    rows = listening.translated_rows(episode)
    assert rows == [{"text": "Client: Moien!", "translation": "Hello!"},
                    {"text": "Serveur: Gudden Owend.", "translation": "Good evening."}]
    monkeypatch.setattr(content, "PUBLIC_MODE", True)
    assert listening.translated_rows(episode) == []
    assert not listening.detail(episode)["has_translated_transcript"]


def test_catalog_does_not_reveal_answer_keys_or_private_source_paths():
    catalog = listening.catalog()
    assert len(catalog["episodes"]) == 8
    for episode in catalog["episodes"]:
        assert "questions" not in episode and "local_audio" not in episode and "note_heading" not in episode
        detail = listening.detail(listening.EPISODES[episode["id"]])
        assert detail["questions"]
        assert all("answer" not in question and "explanation" not in question for question in detail["questions"])
        assert episode["publisher_url"].startswith("https://")


def test_audio_cache_rejects_paths_outside_its_directory(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    outside = tmp_path / "private.mp3"
    outside.write_bytes(b"private")
    monkeypatch.setattr(listening, "CACHE", cache)
    assert listening.audio_path({"audio_file": "../private.mp3"}) is None
    (cache / "link.mp3").symlink_to(outside)
    assert listening.audio_path({"audio_file": "link.mp3"}) is None
    (cache / "episode.mp3").write_bytes(b"official-audio")
    assert listening.audio_path({"audio_file": "episode.mp3"}) == cache / "episode.mp3"
