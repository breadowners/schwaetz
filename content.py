"""Read selected lesson sections without modifying the Obsidian vault."""
from pathlib import Path
import os
import re

def find_vault(workspace=None):
    """Prefer an explicit vault, then the separately cloned notes repository."""
    if "SPEAK_VAULT" in os.environ:
        return Path(os.environ["SPEAK_VAULT"]).expanduser()
    workspace = workspace or Path(__file__).resolve().parent.parent
    candidates = (workspace / "luxembourgish-notes/notes", workspace / "notes")
    return next((path for path in candidates if path.is_dir()), candidates[-1])


VAULT = find_vault()
PUBLIC_MODE = os.environ.get("SPEAK_PUBLIC") == "1"
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
    "housing": {
        "title": "Your home and dream home", "icon": "home", "lesson": "A2.1 · Lesson 07",
        "description": "Describe your home, rooms and ideal place to live.",
        "mission": "Describe your home in complete sentences: type of home, rooms or features, and an adjective. Then describe your dream home. You may invent details.",
        "role": "You are a friendly neighbour discussing homes. Ask about the learner's home and dream home, one question at a time. Practise noun articles, adjectives and negation using the selected examples. Use informal du/dir.",
        "opening": "Moien!", "translation": "Hello!",
        "source": "A2.1/A2.1 Lesson 07.md", "section": "Grammar & patterns",
        "sections": ["1. Determine the gender from the articles", "2. Write the indefinite and definite articles", "New words", "Grammar & patterns"],
        "hint": "Name your type of home, then describe a room or feature with an adjective.",
    },
    "chores": {
        "title": "Household chores and preferences", "icon": "home", "lesson": "A2.1 · Lesson 08",
        "description": "Say which chores you like and dislike.",
        "mission": "Discuss two household chores. Say what you like and dislike with gär / net gär, give an opinion, and ask your partner a question.",
        "role": "You are a friend talking about housework. Ask about chores and preferences, one question at a time. Use the selected examples to distinguish gär from gutt and practise separable verbs. Use informal du/dir.",
        "opening": "Wat méchs du gär?", "translation": "What do you like doing?",
        "source": "A2.1/A2.1 Lesson 08.md", "section": "Grammar & patterns",
        "sections": ["New words", "Grammar & patterns"],
        "hint": "Choose a chore and say whether you like doing it with gär or net gär.",
    },
    "cleaning-rota": {
        "title": "Plan the housework", "icon": "home", "lesson": "A2.1 · Lesson 08",
        "description": "Share chores and agree on a cleaning rota.",
        "mission": "Plan a fictional shared-flat cleaning rota. Choose a chore, explain a preference, and agree who does what this week.",
        "role": "You are the learner's flatmate planning a fictional weekly cleaning rota. Discuss the kitchen, bathroom, living room and bins. Rotate duties and negotiate preferences, one question at a time. Use informal du/dir. Do not present the invented rota as the course dialogue or a teacher quotation.",
        "opening": "Moien!", "translation": "Hello!",
        "source": "A2.1/A2.1 Lesson 08.md", "section": "Separable verbs",
        "sections": ["New words", "Grammar & patterns"],
        "hint": "Choose a shared room or the bins, and say which task you would like to do.",
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

FALLBACK_CONTEXT = ("Built-in fictional speaking practice. No private class notes are configured for this scenario. "
                    "Use the role and mission for general practice; do not claim course, teacher, homework or exam evidence.")


def scenario_context(scenario):
    path = VAULT / scenario["source"]
    if PUBLIC_MODE or not path.is_file():
        return FALLBACK_CONTEXT
    text = path.read_text(encoding="utf-8")
    return "\n\n".join(filter(None, (section_text(text, heading) for heading in scenario["sections"])))[:10000] or FALLBACK_CONTEXT

def scenario_source(scenario):
    if not PUBLIC_MODE and (VAULT / scenario["source"]).is_file():
        return {"source": scenario["source"], "section": scenario["section"]}
    return {"source": "Built-in fictional practice", "section": scenario["title"]}

def public_scenarios():
    return [{"id": key, **{k: v for k, v in value.items() if k not in {"role", "sections"}},
             **scenario_source(value),
             **({"lesson": "General speaking practice"} if PUBLIC_MODE or not (VAULT / value["source"]).is_file() else {})}
            for key, value in SCENARIOS.items()]

def table_rows(text):
    """Yield data cells from Markdown tables, excluding headers and dividers."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if i + 1 < len(lines) and re.match(r"^\|\s*:?-{3,}", lines[i + 1]):
            continue
        yield [re.sub(r"\*\*|`", "", cell) for cell in cells]


# Read only curated tables; raw captures, uncertain prose and test answers stay out.
LESSON_VOCABULARY = [
    ("A2.1/A2.1 Lesson 07.md", "1. Determine the gender from the articles", "Housing · nouns", 0, 3),
    ("A2.1/A2.1 Lesson 07.md", "New words", "Housing · descriptions", 0, 1),
    ("A2.1/A2.1 Lesson 08.md", "New words", "Household chores", 0, 1),
    ("A2.1/A2.1 Lesson 08.md", "Likes, dislikes and opinions", "Chores · preferences", 1, 0),
]


def lesson_vocabulary():
    items = []
    for source, heading, group, word_column, meaning_column in LESSON_VOCABULARY:
        path = VAULT / source
        if not path.is_file():
            continue
        for cells in table_rows(section_text(path.read_text(encoding="utf-8"), heading)):
            if len(cells) <= max(word_column, meaning_column):
                continue
            word = cells[word_column].removesuffix(" — example")
            if not word:
                continue
            meaning = cells[meaning_column]
            if group == "Housing · nouns":
                word = cells[1].split(" / ")[0] + " " + word
                meaning = "a/an " + meaning
            items.append({"text": word, "translation": meaning, "group": group,
                          "source": source, "section": heading})
    return items


def vocabulary():
    """Reuse old synthetic clips and synthesise new lesson words on demand."""
    path = VAULT / "A2.1/Tests/A2.1 First Test Vocabulary.md"
    items, group = [], "Vocabulary"
    if not PUBLIC_MODE and path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                group = line[3:]
            if not line.startswith("|") or "![[" not in line:
                continue
            parts = line.split("|")
            audio = re.search(r"!\[\[([^\]]+)\]\]", line)
            if audio and len(parts) > 3:
                items.append({"text": parts[1].strip(), "translation": parts[2].strip(),
                              "group": group, "audio": audio.group(1),
                              "source": "A2.1/Tests/A2.1 First Test Vocabulary.md"})
    if not PUBLIC_MODE:
        items.extend(lesson_vocabulary())
    if not items:
        items = [{"text": word, "translation": meaning, "group": "Starter words",
                 "source": "Built-in starter vocabulary · synthetic Piper examples"}
                for i, (word, meaning) in enumerate([
                    ("Moien", "Hello"), ("Merci", "Thank you"), ("Jo", "Yes"), ("Nee", "No"), ("Äddi", "Goodbye")])]
    return [{"id": i, **item} for i, item in enumerate(items)]
