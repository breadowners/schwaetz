import content


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
