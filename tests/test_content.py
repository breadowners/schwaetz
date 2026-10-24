import content


def test_vault_discovery_prefers_new_clone_and_honours_override(tmp_path, monkeypatch):
    monkeypatch.delenv("SPEAK_VAULT", raising=False)
    legacy = tmp_path / "notes"
    legacy.mkdir()
    assert content.find_vault(tmp_path) == legacy
    cloned = tmp_path / "luxembourgish-notes/notes"
    cloned.mkdir(parents=True)
    assert content.find_vault(tmp_path) == cloned
    monkeypatch.setenv("SPEAK_VAULT", str(tmp_path / "explicit-vault"))
    assert content.find_vault(tmp_path) == tmp_path / "explicit-vault"


def test_new_lessons_supply_words_without_old_test_vocabulary(tmp_path, monkeypatch):
    monkeypatch.setattr(content, "VAULT", tmp_path)
    path = tmp_path / "A2.1/A2.1 Lesson 08.md"
    path.parent.mkdir()
    path.write_text("""## Class notes
PRIVATE RAW CAPTURE
## New words
| Lëtzebuergesch | English | Note |
| --- | --- | --- |
| spullen | wash dishes | Checked vocabulary. |
## Grammar & patterns
### Likes, dislikes and opinions
| Meaning | Sentence |
| --- | --- |
| I don't like washing dishes. | **Ech spullen net gär.** |
### Separable verbs
Hie raumt d’Spullmaschinn a.
## Homework
PRIVATE HOMEWORK
""")
    words = content.vocabulary()
    assert [(w["id"], w["text"]) for w in words] == [(0, "spullen"), (1, "Ech spullen net gär.")]
    assert words[1]["translation"] == "I don't like washing dishes."
    assert all(w["source"] == "A2.1/A2.1 Lesson 08.md" and "audio" not in w for w in words)
    for key in ("chores", "cleaning-rota"):
        excerpt = content.scenario_context(content.SCENARIOS[key])
        assert "Spullmaschinn" in excerpt
        assert "PRIVATE" not in excerpt
    monkeypatch.setattr(content, "PUBLIC_MODE", True)
    assert len(content.vocabulary()) == 5
    assert "Spullmaschinn" not in content.scenario_context(content.SCENARIOS["chores"])


def test_fresh_clone_needs_no_private_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(content, "VAULT", tmp_path / "no-private-vault")
    for scenario in content.SCENARIOS.values():
        assert "No private class notes" in content.scenario_context(scenario)
        assert content.scenario_source(scenario)["source"] == "Built-in fictional practice"
    assert all(item["lesson"] == "General speaking practice" for item in content.public_scenarios())
    words = content.vocabulary()
    assert words and all("audio" not in word for word in words)


def test_configured_private_lesson_keeps_real_source_and_selected_sections(tmp_path, monkeypatch):
    monkeypatch.setattr(content, "VAULT", tmp_path)
    scenario = content.SCENARIOS["restaurant"]
    path = tmp_path / scenario["source"]
    path.parent.mkdir(parents=True)
    path.write_text("# Private capture\nDo not include this.\n## Restaurant dialogue and role practice\nSelected learning content.\n## Other private material\nNot selected.\n")
    assert content.scenario_source(scenario)["source"] == scenario["source"]
    text = content.scenario_context(scenario)
    assert "Selected learning content" in text
    assert "Do not include" not in text and "Not selected" not in text

def test_public_mode_ignores_an_existing_private_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(content, "VAULT", tmp_path)
    scenario = content.SCENARIOS["restaurant"]
    path = tmp_path / scenario["source"]
    path.parent.mkdir(parents=True)
    path.write_text("## Restaurant dialogue and role practice\nPRIVATE CLASS MATERIAL\n")
    monkeypatch.setattr(content, "PUBLIC_MODE", True)
    assert "PRIVATE" not in content.scenario_context(scenario)
    assert content.scenario_source(scenario)["source"] == "Built-in fictional practice"
    assert len(content.vocabulary()) == 5
