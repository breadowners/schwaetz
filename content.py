"""Read selected lesson sections without modifying the Obsidian vault."""
from pathlib import Path
import os
import re

VAULT = Path(os.environ.get("SPEAK_VAULT", Path(__file__).resolve().parent.parent / "notes")).expanduser()
SCENARIOS = {
    "restaurant": {
        "title": "At the restaurant", "icon": "restaurant", "lesson": "A2.1 · Lesson 04",
        "description": "Order, ask about ingredients, and pay.",
        "mission": "You are the customer. Order something to drink and eat, ask about ingredients, then ask for the bill.",
        "role": "You are a waiter in a fictional restaurant. The learner is your customer. Use formal Dir/Iech.",
        "opening": "Moien! Hätt Dir gär en Aperitif?", "translation": "Hello! Would you like an aperitif?",
        "source": "A2.1/A2.1 Lesson 04.md", "section": "Restaurant dialogue and role practice",
        "sections": ["Restaurant dialogue and role practice", "Expressing opinions about food"],
        "hint": "Try asking for what you would like. You can ask about ingredients too.",
    },
    "reservation": {
        "title": "Reserve a table", "icon": "phone", "lesson": "A2.1 · Lesson 04",
        "description": "Make a reservation and handle a change of time.",
        "mission": "Reserve a table for two. Choose a time and use an invented name. Handle an unavailable time.",
        "role": "You answer the telephone at a fictional restaurant. Help the learner reserve a table; make their first time unavailable and offer another. Use formal Dir/Iech. Ask one question at a time; do not ask for a real phone number.",
        "opening": "Moien!", "translation": "Hello!",
        "source": "A2.1/A2.1 Lesson 04.md", "section": "Reserving a table",
        "sections": ["Reserving a table", "Restaurant dialogue and role practice"],
        "hint": "Say that you would like a table, then say how many people it is for.",
    },
    "transport": {
        "title": "At the ticket counter", "icon": "train", "lesson": "A2.1 · Lesson 02",
        "description": "Choose a destination, a ticket, and how to pay.",
        "mission": "Buy a train ticket for one person. Choose your destination, travel class, and payment method. Prices in this role-play are fictional.",
        "role": "You work at a fictional train ticket counter. The learner buys a ticket. Ask about destination, number of travellers, class, and payment, one question at a time. Any timetable and price is fictional; never present it as actual travel information. Use formal Dir/Iech.",
        "opening": "Moien! Wuer wëllt Dir fueren?", "translation": "Hello! Where would you like to travel to?",
        "source": "A2.1/A2.1 Lesson 02.md", "section": "Buying a ticket — speaking support",
        "sections": ["New words & useful questions", "Buying a ticket — speaking support", "Separable verbs — written exercise"],
        "hint": "Choose a destination and say where you would like to travel.",
    },
    "neighbourhood": {
        "title": "Your neighbourhood", "icon": "home", "lesson": "A2.1 · Lesson 01",
        "description": "Talk about nearby shops and opening hours.",
        "mission": "Describe the shops near you. Say what you can get there and when a shop opens. You may use fictional details.",
        "role": "You are a friendly neighbour. Ask the learner about nearby shops, what they buy there, and opening hours. Use informal du/dir consistently. Ask one question at a time.",
        "opening": "Wat fir Butteker gëtt et an dengem Quartier?", "translation": "What kinds of shops are in your neighbourhood?",
        "source": "A2.1/A2.1 Lesson 01  Butteker an Administratiounen a Butteker.md", "section": "Useful language",
        "sections": ["Useful language", "Reading the clock", "At / from … to / until"],
        "hint": "Name one or two shops near you. Then explain what you buy there.",
    },
    "free": {
        "title": "A little everyday chat", "icon": "chat", "lesson": "A2.1 · Everyday speaking",
        "description": "Talk about your day, food, or getting around.",
        "mission": "Have a short conversation. Use simple sentences and ask your partner a question too.",
        "role": "Be a friendly conversation partner. Talk about the learner's day, food, neighbourhood or travel. Start simply and adapt to their language. Use informal du/dir. Ask one question at a time.",
        "opening": "Moien!", "translation": "Hello!",
        "source": "A2.1/A2.1 Lesson 04.md", "section": "Restaurant dialogue and role practice",
        "sections": ["Restaurant dialogue and role practice"],
        "hint": "Tell your partner one thing about your day, then ask a question.",
    },
}

def section_text(text, heading):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if re.sub(r"^#+\s*", "", line) == heading), None)
    if start is None:
        return ""
    depth = len(lines[start]) - len(lines[start].lstrip("#"))
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r"^#{1," + str(depth) + r"}\s", lines[i])), len(lines))
    return "\n".join(lines[start:end])

def scenario_context(scenario):
    path = VAULT / scenario["source"]
    if not path.is_file():
        return ("Built-in fictional speaking practice. No private class notes are configured for this scenario. "
                "Use the role and mission for general practice; do not claim course, teacher, homework or exam evidence.")
    text = path.read_text(encoding="utf-8")
    return "\n\n".join(section_text(text, heading) for heading in scenario["sections"])[:10000]

def scenario_source(scenario):
    if (VAULT / scenario["source"]).is_file():
        return {"source": scenario["source"], "section": scenario["section"]}
    return {"source": "Built-in fictional practice", "section": scenario["title"]}

def public_scenarios():
    return [{"id": key, **{k: v for k, v in value.items() if k not in {"role", "sections"}},
             **scenario_source(value),
             **({"lesson": "General speaking practice"} if not (VAULT / value["source"]).is_file() else {})}
            for key, value in SCENARIOS.items()]

def vocabulary():
    """Reuse existing audio; this is generated study support, not teacher audio."""
    path = VAULT / "A2.1/Tests/A2.1 First Test Vocabulary.md"
    if not path.exists():
        return [{"id": i, "text": word, "translation": meaning, "group": "Starter words",
                 "source": "Built-in starter vocabulary · synthetic Piper examples"}
                for i, (word, meaning) in enumerate([
                    ("Moien", "Hello"), ("Merci", "Thank you"), ("Jo", "Yes"), ("Nee", "No"), ("Äddi", "Goodbye")])]
    items, group = [], "Vocabulary"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            group = line[3:]
        if not line.startswith("|") or "![[" not in line:
            continue
        parts = line.split("|")
        audio = re.search(r"!\[\[([^\]]+)\]\]", line)
        if audio and len(parts) > 3:
            items.append({"id": len(items), "text": parts[1].strip(), "translation": parts[2].strip(),
                          "group": group, "audio": audio.group(1),
                          "source": "A2.1/Tests/A2.1 First Test Vocabulary.md"})
    return items
