"""Compare CPU and Metal encoding locally, using explicitly supplied audio files."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio, pad_or_trim

from metal_encoder import MetalEncoder

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/asr-metal-validation.json")
    args = parser.parse_args()
    checkpoint = ROOT / "models/asr/model.bin"
    with checkpoint.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    model = WhisperModel(str(checkpoint.parent), device="cpu", compute_type="float32",
                         cpu_threads=4, local_files_only=True)
    cpu = model.encode
    metal = MetalEncoder(checkpoint)
    parity, rows = [], []
    for index, path in enumerate(args.audio):
        audio = decode_audio(str(path), sampling_rate=16000)
        features = pad_or_trim(model.feature_extractor(audio))
        expected, observed = np.array(cpu(features)), np.array(metal.encode(features))
        rmse = float(np.sqrt(np.mean((expected - observed) ** 2)))
        max_abs = float(np.max(np.abs(expected - observed)))
        if rmse > 0.0005 or max_abs > 0.02:
            raise RuntimeError(f"Encoder numerical parity failed for {path.name}")
        parity.append({"file": path.name, "rmse": rmse, "max_abs": max_abs})
        backends = [("CPU", cpu), ("Metal GPU", metal.encode)]
        if index % 2:
            backends.reverse()
        transcripts = []
        for backend, encode in backends:
            model.encode = encode
            started = time.monotonic()
            segments, _ = model.transcribe(audio, language="lb", beam_size=3, vad_filter=True,
                                           condition_on_previous_text=False, word_timestamps=False)
            text = " ".join(s.text.strip() for s in segments if s.no_speech_prob < .8).strip()
            row = {"file": path.name, "backend": backend,
                   "seconds": round(time.monotonic() - started, 3), "text": text}
            rows.append(row)
            transcripts.append(text)
            print(json.dumps(row, ensure_ascii=False), flush=True)
        if transcripts[0] != transcripts[1]:
            raise RuntimeError(f"Transcript parity failed for {path.name}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"checkpoint_sha256": digest, "numerical_parity": parity,
                                      "results": rows}, ensure_ascii=False, indent=2))
    print(f"Parity checks passed. Results: {args.output}")


if __name__ == "__main__":
    main()
