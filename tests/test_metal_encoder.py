import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from metal_encoder import read_encoder, map_encoder
import server


def test_checkpoint_reader_rejects_truncation_and_wrong_formats(tmp_path):
    path = tmp_path / "model.bin"
    for content in (b"", struct.pack("<I", 5), struct.pack("<IH", 6, 50) + b"short"):
        path.write_bytes(content)
        with pytest.raises(ValueError):
            read_encoder(path)


def tiny_encoder():
    tensors = {"encoder/num_heads": np.array(2, dtype=np.int16),
               "encoder/position_encodings/encodings": np.zeros((6, 4), dtype=np.float32)}
    def linear(name, shape):
        tensors["encoder/" + name + "/weight"] = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
        tensors["encoder/" + name + "/bias"] = np.zeros(shape[0], dtype=np.float32)
    def norm(name):
        tensors["encoder/" + name + "/gamma"] = np.ones(4, dtype=np.float32)
        tensors["encoder/" + name + "/beta"] = np.zeros(4, dtype=np.float32)
    linear("conv1", (4, 3, 3)); linear("conv2", (4, 4, 3))
    norm("layer_norm")
    norm("layer_0/self_attention/layer_norm"); norm("layer_0/ffn/layer_norm")
    linear("layer_0/self_attention/linear_0", (12, 4))
    linear("layer_0/self_attention/linear_1", (4, 4))
    linear("layer_0/ffn/linear_0", (16, 4)); linear("layer_0/ffn/linear_1", (4, 16))
    return tensors


def test_encoder_mapping_preserves_convolution_and_attention_values():
    source = tiny_encoder()
    dims, weights, positions = map_encoder(source)
    assert dims == {"n_mels": 3, "n_ctx": 6, "n_state": 4, "n_head": 2, "n_layer": 1}
    np.testing.assert_array_equal(weights["conv1.weight"][2, :, 1], source["encoder/conv1/weight"][2, 1, :])
    qkv = source["encoder/layer_0/self_attention/linear_0/weight"]
    for i, projection in enumerate(("query", "key", "value")):
        np.testing.assert_array_equal(weights[f"blocks.0.attn.{projection}.weight"], qkv[i*4:(i+1)*4])
    assert positions is source["encoder/position_encodings/encodings"]


def test_encoder_mapping_refuses_silent_parameter_loss_or_unsupported_key_bias():
    source = tiny_encoder()
    source["encoder/unexpected"] = np.zeros(1)
    with pytest.raises(ValueError, match="Unmapped"):
        map_encoder(source)
    source = tiny_encoder()
    source["encoder/layer_0/self_attention/linear_0/bias"][5] = 1
    with pytest.raises(ValueError, match="key bias"):
        map_encoder(source)


def test_gpu_failure_retries_original_features_then_keeps_future_turns_on_cpu(monkeypatch):
    calls = []
    class FakeMetal:
        dimensions = {"n_mels": 2, "n_ctx": 2}
        def __init__(self, path):
            self.warm = True
        def encode(self, features):
            if self.warm:
                self.warm = False
                return "warmed"
            raise RuntimeError("Synthetic GPU failure")
    monkeypatch.setattr(server, "APPLE_SILICON", True)
    monkeypatch.delenv("SPEAK_METAL_ENCODER", raising=False)
    monkeypatch.setattr(sys.modules["metal_encoder"], "MetalEncoder", FakeMetal)
    engine = server.SpeechEngine()
    engine.asr = SimpleNamespace(encode=lambda features: calls.append(features) or "cpu-result")
    engine.enable_metal_encoder()
    assert engine.encoder_backend == "Metal GPU"
    features = np.zeros((2, 4))
    assert engine.asr.encode(features) == "cpu-result"
    assert engine.encoder_backend == "CPU"
    assert calls[0] is features
    assert engine.asr.encode(features) == "cpu-result"
    assert len(calls) == 2
