import io
import wave

import numpy as np
import pytest
from fastapi import HTTPException

from phonetic_model import decode_phones
from pronunciation import Lexicon, PronunciationEngine, compare_phones, feedback

def observed(phones, posterior=.9):
    return [{"phone": p, "posterior": posterior, "start": i * .1, "end": (i + 1) * .1} for i, p in enumerate(phones)]

def test_variants_are_considered_without_false_error_and_r_variation_allowed():
    reference = [("brout", [["b", "ʀ", "əʊ", "t"], ["b", "ʁ", "əʊ", "t"]]),
                 ("zou", [["ts", "əʊ"], ["ts", "uː"]])]
    result = feedback(reference, observed(["b", "ʁ", "əʊ", "t", "ts", "uː"]))
    assert result["outcome"] == "no_clear_difference"
    assert result["tips"] == []
    assert result["validated_grade"] is False
    assert "does not establish" in result["summary"]

def test_sound_substitution_produces_specific_tip_without_transcript_input():
    result = feedback([("brout", [["b", "ʀ", "əʊ", "t"]])], observed(["b", "ʀ", "eː", "t"]))
    assert result["outcome"] == "possible_difference"
    assert result["tips"][0]["expected"] == "əʊ"
    assert result["tips"][0]["heard"] == "eː"
    assert "glide" in result["tips"][0]["practice"]
    assert result["tips"][0]["start"] <= .2

def test_weak_predictions_and_unrelated_speech_get_no_specific_correction():
    reference = [("brout", [["b", "ʀ", "əʊ", "t"]])]
    assert feedback(reference, observed(["b", "ʀ", "eː", "t"], .25))["tips"] == []
    assert feedback(reference, observed(["s", "ə", "n", "z"]))["outcome"] == "uncertain"
    assert feedback(reference, [])["outcome"] == "uncertain"

def test_lexicon_skips_mfa_probabilities_preserves_variants_and_rejects_unknowns(tmp_path):
    path = tmp_path / "sample.dict"
    path.write_text("brout\t0.99\t0.23\t1.0\t1.0\tb ʀ əʊ t\nbrout\tb ʁ əʊ t\ngär\tɡ ɛː ɐ\n<unk>\tspn\n")
    lexicon = Lexicon(path)
    reference, error = lexicon.reference("Brout, gär!")
    assert error is None
    assert len(reference[0][1]) == 2
    assert reference[1][1][0][0] == "g"
    assert lexicon.reference("unlistedword")[0] is None
    assert lexicon.reference("Brout 12")[0] is None
    assert lexicon.reference(" ".join(["Brout"] * 11))[0] is None

def test_decoder_collapses_repeats_but_keeps_blank_separated_phones():
    class Tokenizer:
        def id_to_piece(self, i): return {0: "<unk>", 1: "<blk>", 2: "▁ə"}[i]
        def decode(self, ids): return "ə"
    probabilities = np.array([[.9,.05,.05],[.05,.05,.9],[.05,.05,.9],[.9,.05,.05],[.05,.05,.9]])
    phones = decode_phones(probabilities, Tokenizer(), 0, 1)
    assert len(phones) == 2
    assert [p["phone"] for p in phones] == ["ə", "ə"]
    assert phones[0]["start"] < phones[1]["start"]

def test_quiet_and_overlong_audio_cannot_generate_corrections(tmp_path):
    path = tmp_path / "test.dict"; path.write_text("brout\tb ʀ əʊ t\n")
    engine = PronunciationEngine(); engine.lexicon = Lexicon(path)
    class RejectCalls:
        def predict(self, samples): raise AssertionError("invalid audio reached recognition")
    engine.recognizer = RejectCalls()
    def wav(seconds):
        stream = io.BytesIO()
        with wave.open(stream, "wb") as writer:
            writer.setnchannels(1); writer.setsampwidth(2); writer.setframerate(16000)
            writer.writeframes(b"\0\0" * int(seconds * 16000))
        return stream.getvalue()
    result = engine.assess(wav(1), "Brout")
    assert result["pronunciation_assessed"] is False
    assert "quiet" in result["summary"]
    with pytest.raises(HTTPException) as exc: engine.assess(wav(21), "Brout")
    assert exc.value.status_code == 413
