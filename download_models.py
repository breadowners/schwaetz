"""Download public models only; never upload notes or audio."""
import os
import argparse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from huggingface_hub import snapshot_download, hf_hub_download

ASR_REPO = "ZLSCompLing/Whisper-Large-V3-Turbo-Luxembourgish"
VOICE_REPO = "mbarnig/lb_rhasspy_piper_tts"
VOICE_NAME = "lb_LU-femaleLOD-medium.onnx"

def download_pronunciation():
    """Public research weights/code and a pronunciation lexicon; no user data."""
    target = ROOT / "models" / "pronunciation"
    snapshot_download("pgilles/zipa-large-crctc-luxembourgish-ipapack20", revision="4e79729",
                      local_dir=target, allow_patterns=["*.json", "*.pt", "*.model", "*.vocab", "*.txt", "README.md"])
    runtime = target / "runtime"
    runtime.mkdir(exist_ok=True)
    revision = "21e9e8aa4cc6c130cb05d836a1979886f9245302"
    for name in ["zipformer.py", "scaling.py", "subsampling.py", "encoder_interface.py", "scaling_converter.py"]:
        url = f"https://raw.githubusercontent.com/lingjzhu/zipa/{revision}/zipformer_crctc/{name}"
        with urllib.request.urlopen(url) as response:
            data = response.read()
            if name == "scaling.py":
                data = data.replace(b"import k2\n", b"import zipa_inference_ops as k2\n")
            (runtime / name).write_bytes(data)
    (runtime / "revision.txt").write_text(revision)
    for name, url in {
        "luxembourgish.dict": "https://raw.githubusercontent.com/PeterGilles/Luxembourgish_in_Montreal_Forced_Aligner/main/dictionary/luxembourgish_mfa_run6.dict",
        "dictionary-LICENSE": "https://raw.githubusercontent.com/PeterGilles/Luxembourgish_in_Montreal_Forced_Aligner/main/LICENSE",
        "runtime-LICENSE": f"https://raw.githubusercontent.com/lingjzhu/zipa/{revision}/LICENSE",
    }.items():
        with urllib.request.urlopen(url) as response:
            (target / name).write_bytes(response.read())
    print("Pronunciation models downloaded. No audio or notes were uploaded.", flush=True)

def main():
    print("Downloading ZLS Luxembourgish recognition model (about 3.2 GB).", flush=True)
    snapshot_download(
        ASR_REPO, local_dir=ROOT / "models" / "asr",
        allow_patterns=["*.json", "model.bin", "vocabulary.*", "README.md", "LICENSE*"],
    )
    print("Downloading Luxembourgish voice (about 64 MB).", flush=True)
    for name in (VOICE_NAME, VOICE_NAME + ".json"):
        downloaded = hf_hub_download(
            VOICE_REPO, f"lb/lb_LU/femaleLOD/medium/{name}",
            local_dir=ROOT / "models" / "voice-source",
        )
        target = ROOT / "models" / name
        target.write_bytes(Path(downloaded).read_bytes())
    print("Models ready. No audio or notes were uploaded.", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pronunciation", action="store_true")
    args = parser.parse_args()
    if args.pronunciation:
        download_pronunciation()
    else:
        main()
