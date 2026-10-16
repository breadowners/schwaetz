"""Experimental sound feedback from recorded audio and a reference dictionary.

Phone recognition is fallible, particularly with learner accents. Never equate
an ASR match, acoustic posterior, or phone edit distance with a validated grade.
"""
import io
from pathlib import Path
import re
import threading
import time
import unicodedata

from fastapi import HTTPException

DIRECTORY = Path(__file__).resolve().parent / "models/pronunciation"
DICTIONARY_URL = "https://github.com/PeterGilles/Luxembourgish_in_Montreal_Forced_Aligner"
MODEL_URL = "https://huggingface.co/pgilles/zipa-large-crctc-luxembourgish-ipapack20"

TIPS = {
    "ə": "Use a short, relaxed vowel with your tongue near the centre of your mouth.",
    "ɐ": "Use a relaxed, open central vowel; listen closely to the ending in the example.",
    "i": "Keep your tongue high and towards the front, with your lips unrounded. Keep this vowel short.",
    "iː": "Keep your tongue high and towards the front, with your lips unrounded. Hold the vowel longer.",
    "u": "Keep your tongue high and towards the back, and round your lips. Keep this vowel short.",
    "uː": "Keep your tongue high and towards the back, and round your lips. Hold the vowel longer.",
    "e": "Use a front vowel with unrounded lips; keep it short and steady.",
    "eː": "Use a front vowel with unrounded lips. Hold it steady and longer.",
    "ɛ": "Open your mouth more for this front vowel, with your lips unrounded.",
    "ɛː": "Use an open front vowel with unrounded lips, and hold it longer.",
    "ɑ": "Open your mouth and keep the tongue towards the back, with your lips unrounded.",
    "aː": "Open your mouth for a long, unrounded vowel. Hold it rather than cutting it short.",
    "o": "Round your lips for this back vowel and keep it short.",
    "oː": "Round your lips for this back vowel and hold it steady and longer.",
    "əʊ": "Start with a relaxed central vowel, then glide towards a rounded back vowel in one syllable.",
    "ɜɪ": "Start with a central vowel, then glide towards a higher front vowel in one syllable.",
    "uə": "Start with a rounded back vowel, then glide towards a relaxed central vowel.",
    "iə": "Start with a high front vowel, then glide towards a relaxed central vowel.",
    "ʃ": "Make a sh-like sound with your tongue just behind the ridge above your upper teeth.",
    "ɕ": "Make a soft hissing sound with the front of your tongue raised close to the hard palate.",
    "χ": "Let air rub through a narrow opening near the back of your mouth; avoid adding a vowel.",
    "ʀ": "Listen to the Luxembourgish r in the example; this dictionary symbol uses the uvula at the back of the mouth.",
    "ʁ": "Listen to the Luxembourgish r in the example; keep the constriction near the back of the mouth.",
    "ts": "Start with a t closure, then release directly into s, as one joined sound.",
    "ŋ": "Raise the back of your tongue to the soft palate for a nasal sound; avoid adding a separate g.",
}

def canonical(phone):
    # Two ordinary uvular r realisations are accepted, not learner errors.
    return {"ɡ": "g", "d̥": "d̥ː", "ʁ": "ʀ"}.get(phone, phone)

class Lexicon:
    def __init__(self, path):
        self.entries = {}
        for line in Path(path).read_text().splitlines():
            parts = line.split()
            if len(parts) < 2 or parts[0].startswith(("<", "[")):
                continue
            phones = []
            for token in parts[1:]:
                try:
                    float(token)
                    continue
                except ValueError:
                    pass
                for phone in (["æ", "l"] if token == "æl" else [token.replace("ɡ", "g")]):
                    # Match the published model's within-word degemination.
                    if not phones or phones[-1] != phone:
                        phones.append(phone)
            if not phones or "spn" in phones:
                continue
            variants = self.entries.setdefault(parts[0].lower(), [])
            if phones not in variants:
                variants.append(phones)

    def reference(self, text):
        words = re.findall(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", unicodedata.normalize("NFC", text).lower())
        if not words or len(words) > 10 or re.search(r"\d", text):
            return None, "Use a short phrase of up to ten words without digits."
        missing = [word for word in words if word.replace("’", "'") not in self.entries]
        if missing:
            return None, "No dictionary pronunciation for: " + ", ".join(missing) + ". Try a shorter phrase."
        return [(word, self.entries[word.replace("’", "'")]) for word in words], None

def compare_phones(reference, observed):
    """Minimum-edit path through ALL listed variants, with word locations.

    A DAG avoids choosing one dictionary variant in advance or truncating the
    cross-product of phrase variants. Alignment cannot establish correctness.
    """
    edges = [[]]
    previous = 0
    for word, variants in reference:
        ends = []
        for phones in variants:
            node = previous
            for phone in phones:
                child = len(edges)
                edges.append([])
                edges[node].append((child, phone, word))
                node = child
            ends.append(node)
        merge = len(edges)
        edges.append([])
        for end in ends:
            edges[end].append((merge, None, word))
        previous = merge
    count = len(observed)
    costs = [[float("inf")] * (count + 1) for _ in edges]
    back = {}
    costs[0][0] = 0
    def update(node, j, value, parent, operation):
        if value < costs[node][j]:
            costs[node][j] = value
            back[node, j] = (parent, operation)
    for node, arcs in enumerate(edges):
        for j in range(count + 1):
            value = costs[node][j]
            if value == float("inf"):
                continue
            if j < count:
                update(node, j + 1, value + 1, (node, j), {"kind": "extra", "heard_index": j})
            for child, phone, word in arcs:
                if phone is None:
                    update(child, j, value, (node, j), None)
                    continue
                if j < count:
                    same = canonical(phone) == canonical(observed[j]["phone"])
                    update(child, j + 1, value + (0 if same else 1), (node, j),
                           {"kind": "match" if same else "different", "expected": phone, "word": word, "heard_index": j})
                update(child, j, value + 1, (node, j),
                       {"kind": "missing", "expected": phone, "word": word, "heard_index": None})
    path, cursor = [], (previous, count)
    while cursor != (0, 0):
        cursor, operation = back[cursor]
        if operation:
            path.append(operation)
    path.reverse()
    for operation in path:
        index = operation.pop("heard_index")
        if index is not None:
            operation.update(observed[index])
        operation["heard"] = operation.pop("phone", None)
    return path, costs[previous][count]

def feedback(reference, observed):
    path, distance = compare_phones(reference, observed)
    expected = [p["expected"] for p in path if p.get("expected")]
    base = {"expected_ipa": " ".join(expected), "heard_ipa": " ".join(p["phone"] for p in observed),
            "alignment": path, "validated_grade": False}
    if not observed or distance / max(len(expected), len(observed), 1) > .4:
        return {**base, "outcome": "uncertain", "tips": [],
                "summary": "The sound sequence is too different to give a useful correction. Say the displayed phrase once, clearly, and try again."}
    candidates = []
    for part in path:
        # A heuristic, not calibrated learner accuracy: require the observed
        # phone's peak posterior to exceed the other classes' combined mass.
        if part["kind"] != "different" or part.get("posterior", 0) <= .5:
            continue
        expected_phone, heard = part["expected"], part["heard"]
        if expected_phone not in TIPS:
            continue
        candidates.append({"word": part["word"], "expected": expected_phone, "heard": heard,
            "start": max(0, part["start"] - .15), "end": part["end"] + .2,
            "explanation": f"In {part['word']}, the model suggests /{heard}/ where this dictionary variant has /{expected_phone}/.",
            "practice": TIPS[expected_phone] + " Listen to the example, then say the whole word again."})
    if candidates:
        return {**base, "outcome": "possible_difference", "tips": candidates[:2],
                "summary": "Possible sound difference — listen to the highlighted part and try the tip. The model can mishear learner accents."}
    return {**base, "outcome": "no_clear_difference" if not distance else "uncertain", "tips": [],
            "summary": "No clear sound difference was detected. This does not establish that the pronunciation is correct."
                if not distance else "Some sounds differ, but the evidence is too uncertain for a specific correction. Listen and retry."}

class PronunciationEngine:
    def __init__(self):
        self.recognizer = self.lexicon = None
        self.loading = False
        self.error = None
        self.lock = threading.Lock()

    def load(self):
        with self.lock:
            if self.recognizer:
                return
            self.loading = True
            try:
                from phonetic_model import PhoneRecognizer
                self.lexicon = Lexicon(DIRECTORY / "luxembourgish.dict")
                self.recognizer = PhoneRecognizer(DIRECTORY)
                self.error = None
            except Exception as exc:
                self.error = str(exc)
            finally:
                self.loading = False

    def assess(self, data, target):
        if not self.recognizer or not self.lexicon:
            raise HTTPException(503, "Pronunciation model isn't ready. Check Settings.")
        reference, reason = self.lexicon.reference(target)
        base = {"target": target, "feedback_basis": "recorded_audio", "experimental": True,
                "model_source": MODEL_URL, "reference_source": DICTIONARY_URL,
                "limitation": "Experimental phonetic feedback, not a validated pronunciation grade. Timing is approximate; dictionary variants may not cover every connected-speech or regional realisation."}
        if not reference:
            return {**base, "outcome": "unsupported", "summary": reason, "tips": [],
                    "pronunciation_assessed": False}
        from faster_whisper.audio import decode_audio
        import numpy as np
        try:
            samples = decode_audio(io.BytesIO(data), sampling_rate=16000)
        except Exception:
            raise HTTPException(400, "Could not read this recording. Please record again.")
        if len(samples) > 16000 * 20:
            raise HTTPException(413, "For pronunciation, record a short phrase under twenty seconds.")
        if len(samples) < 4800:
            raise HTTPException(400, "Please record at least a short word.")
        if not np.isfinite(samples).all() or np.sqrt(np.mean(samples ** 2)) < .003:
            return {**base, "outcome": "uncertain", "summary": "The recording is too quiet. Move closer to the microphone and retry.",
                    "tips": [], "pronunciation_assessed": False}
        started = time.monotonic()
        with self.lock:
            observed = self.recognizer.predict(samples)
        return {**base, **feedback(reference, observed), "pronunciation_assessed": True,
                "seconds": round(time.monotonic() - started, 2)}
