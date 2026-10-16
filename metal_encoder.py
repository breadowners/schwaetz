"""Run the existing ZLS Whisper encoder on Apple Metal; retain CTranslate2 decoding.

The weight layout follows CTranslate2's public ModelSpec serializer (binary v6,
WhisperSpec revision 3) and its Transformers Whisper converter. MLX Whisper's
AudioEncoder supplies the architecture. No alternative model is downloaded.
"""
import math
from pathlib import Path
import re
import struct

import numpy as np


def read_encoder(path):
    """Memory-map only encoder tensors from a supported, unquantized checkpoint."""
    path = Path(path)
    size = path.stat().st_size
    tensors = {}
    dtypes = {0: np.dtype("<f4"), 1: np.dtype("i1"), 2: np.dtype("<i2"),
              3: np.dtype("<i4"), 4: np.dtype("<f2")}
    with path.open("rb") as source:
        def number(fmt):
            data = source.read(struct.calcsize("<" + fmt))
            if len(data) != struct.calcsize("<" + fmt):
                raise ValueError("Truncated CTranslate2 checkpoint")
            return struct.unpack("<" + fmt, data)[0]

        def string():
            length = number("H")
            data = source.read(length)
            if not length or len(data) != length or data[-1] != 0:
                raise ValueError("Invalid checkpoint tensor name")
            return data[:-1].decode("utf-8")

        if number("I") != 6 or string() != "WhisperSpec" or number("I") != 3:
            raise ValueError("Unsupported Whisper checkpoint format")
        count = number("I")
        if not 0 < count < 10000:
            raise ValueError("Invalid checkpoint tensor count")
        for _ in range(count):
            name = string()
            rank = number("B")
            if rank > 8:
                raise ValueError("Invalid checkpoint tensor rank")
            shape = tuple(number("I") for _ in range(rank))
            type_id, nbytes = number("B"), number("I")
            offset = source.tell()
            if offset + nbytes > size:
                raise ValueError("Truncated checkpoint tensor")
            if name.startswith("encoder/"):
                dtype = dtypes.get(type_id)
                if dtype is None or nbytes != math.prod(shape) * dtype.itemsize:
                    raise ValueError("Unsupported encoder tensor storage")
                if rank and type_id != 0:
                    raise ValueError("The Metal adapter requires the original float32 encoder weights")
                tensors[name] = np.memmap(path, mode="r", dtype=dtype, offset=offset, shape=shape)
            source.seek(nbytes, 1)
        # Resolve aliases without touching or copying decoder weights.
        for _ in range(number("I")):
            alias, original = string(), string()
            if alias.startswith("encoder/"):
                if original not in tensors:
                    raise ValueError("Unsupported encoder tensor alias")
                tensors[alias] = tensors[original]
        if source.tell() != size:
            raise ValueError("Unexpected checkpoint data")
    return tensors


def map_encoder(tensors):
    """Undo Q/K/V fusion and map the official CT2 layout to MLX Whisper names."""
    weights, used = {}, set()

    def get(name):
        name = "encoder/" + name
        used.add(name)
        return tensors[name]

    positions = get("position_encodings/encodings")
    context, width = positions.shape
    heads = int(get("num_heads"))
    layers = sorted({int(match[1]) for name in tensors
                     if (match := re.match(r"encoder/layer_(\d+)/", name))})
    if layers != list(range(len(layers))) or not layers or width % heads:
        raise ValueError("Unsupported encoder architecture")
    for conv in ("conv1", "conv2"):
        weights[conv + ".weight"] = get(conv + "/weight").transpose(0, 2, 1)
        weights[conv + ".bias"] = get(conv + "/bias")

    def norm(target, original):
        weights[target + ".weight"] = get(original + "/gamma")
        weights[target + ".bias"] = get(original + "/beta")

    norm("ln_post", "layer_norm")
    for index in layers:
        original, target = f"layer_{index}/", f"blocks.{index}."
        norm(target + "attn_ln", original + "self_attention/layer_norm")
        norm(target + "mlp_ln", original + "ffn/layer_norm")
        qkv = get(original + "self_attention/linear_0/weight")
        biases = get(original + "self_attention/linear_0/bias")
        if qkv.shape != (width * 3, width) or biases.shape != (width * 3,):
            raise ValueError("Invalid fused attention weights")
        if np.any(biases[width:width * 2] != 0):
            raise ValueError("MLX Whisper expects zero key bias")
        for part, projection in enumerate(("query", "key", "value")):
            weights[target + "attn." + projection + ".weight"] = qkv[part * width:(part + 1) * width]
            if projection != "key":
                weights[target + "attn." + projection + ".bias"] = biases[part * width:(part + 1) * width]
        for target_layer, ct2_layer in (("attn.out", "self_attention/linear_1"),
                                       ("mlp1", "ffn/linear_0"), ("mlp2", "ffn/linear_1")):
            for field in ("weight", "bias"):
                weights[target + target_layer + "." + field] = get(original + ct2_layer + "/" + field)
    if set(tensors) != used:
        raise ValueError("Unmapped encoder tensors; use the CPU fallback")
    dimensions = {"n_mels": weights["conv1.weight"].shape[2], "n_ctx": context,
                  "n_state": width, "n_head": heads, "n_layer": len(layers)}
    return dimensions, weights, positions


class MetalEncoder:
    def __init__(self, checkpoint):
        import mlx.core as mx
        from mlx_whisper.whisper import AudioEncoder
        if not mx.metal.is_available():
            raise RuntimeError("Apple Metal is unavailable")
        dimensions, weights, positions = map_encoder(read_encoder(checkpoint))
        self.mx = mx
        self.dimensions = dimensions
        self.encoder = AudioEncoder(**dimensions, dtype=mx.float32)
        # Keep original precision and the checkpoint's actual positional embeddings.
        self.encoder.load_weights([(name, mx.array(np.ascontiguousarray(value)))
                                   for name, value in weights.items()], strict=True)
        self.encoder._positional_embedding = mx.array(np.ascontiguousarray(positions))
        self.encoder.eval()
        mx.eval(self.encoder.parameters(), self.encoder._positional_embedding)

    def forward(self, features):
        """Whisper's encoder with MLX's fused attention, without attention-map allocation."""
        import mlx.nn as nn
        mx, encoder = self.mx, self.encoder
        x = nn.gelu(encoder.conv1(features))
        x = nn.gelu(encoder.conv2(x))
        if x.shape[1:] != encoder._positional_embedding.shape:
            raise ValueError("Incorrect Whisper feature shape")
        x = x + encoder._positional_embedding
        for block in encoder.blocks:
            normalised = block.attn_ln(x)
            batch, length, width = normalised.shape
            heads = block.attn.n_head
            q, k, v = [projection(normalised).reshape(batch, length, heads, width // heads)
                       .transpose(0, 2, 1, 3) for projection in
                       (block.attn.query, block.attn.key, block.attn.value)]
            attended = mx.fast.scaled_dot_product_attention(q, k, v, scale=(width // heads) ** -0.5)
            x = x + block.attn.out(attended.transpose(0, 2, 1, 3).reshape(batch, length, width))
            x = x + block.mlp2(nn.gelu(block.mlp1(block.mlp_ln(x))))
        return encoder.ln_post(x)

    def encode(self, features):
        import ctranslate2
        if features.ndim == 2:
            features = features[None, :, :]
        output = self.forward(self.mx.array(np.ascontiguousarray(features.transpose(0, 2, 1))))
        self.mx.eval(output)
        encoded = np.ascontiguousarray(np.array(output), dtype=np.float32)
        if not np.isfinite(encoded).all():
            raise RuntimeError("Metal returned non-finite encoder output")
        return ctranslate2.StorageView.from_array(encoded)
