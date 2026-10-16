"""Local, audio-only phone recognition using the university ZIPA checkpoint.

Architecture/forward pass adapted from lingjzhu/zipa's Apache-2.0 icefall code.
No language model, expected transcript or dictionary is passed to recognition.
"""
from pathlib import Path
import sys
import warnings

class PhoneRecognizer:
    def __init__(self, directory):
        import torch
        import sentencepiece
        self.torch = torch
        torch.set_num_threads(6)
        directory = Path(directory)
        sys.path.insert(0, str(directory / "runtime"))
        # The upstream source uses deprecated CUDA decorators even on CPU.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            from subsampling import Conv2dSubsampling
            from zipformer import Zipformer2
        checkpoint = torch.load(directory / "best-valid-loss.pt", weights_only=True,
                                map_location="cpu", mmap=True)
        # Published greedy decoder and torch CTC training use blank=0. The
        # checkpoint's blank_id=1 refers to the SentencePiece <blk> symbol;
        # silence in actual inference occupies class 0. Exclude all specials.
        self.blank_id = 0
        self.tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(directory / "lb_phones.model"))
        if self.tokenizer.piece_to_id("<blk>") != checkpoint["blank_id"]:
            raise RuntimeError("The phonetic checkpoint and tokenizer don't agree.")
        def ints(key):
            value = checkpoint[key]
            return tuple(int(x) for x in str(value).split(","))
        model = torch.nn.Module()
        # Upstream get_model uses ScheduledFloat(default=0) at inference. The
        # embed constructor's plain-float .1 default would keep fused dropout on.
        model.encoder_embed = Conv2dSubsampling(in_channels=80, out_channels=ints("encoder_dim")[0], dropout=0.0)
        model.encoder = Zipformer2(
            output_downsampling_factor=1,
            **{key: ints(key) for key in ["downsampling_factor", "num_encoder_layers", "encoder_dim",
                "encoder_unmasked_dim", "query_head_dim", "pos_head_dim", "value_head_dim", "num_heads",
                "feedforward_dim", "cnn_module_kernel", "chunk_size", "left_context_frames"]},
            pos_dim=checkpoint["pos_dim"], causal=checkpoint["causal"],
        )
        model.ctc_output = torch.nn.Sequential(torch.nn.Dropout(.1),
            torch.nn.Linear(max(ints("encoder_dim")), checkpoint["vocab_size"]), torch.nn.LogSoftmax(dim=-1))
        model.load_state_dict(checkpoint["model"], strict=True)
        self.model = model.eval()
        from lhotse.features.kaldi.extractors import Fbank
        self.extractor = Fbank()

    def predict(self, samples):
        torch = self.torch
        with torch.inference_mode():
            waveform = torch.from_numpy(samples.copy()).float().unsqueeze(0)
            features = self.extractor.extract(waveform, sampling_rate=16000)
            x = features.unsqueeze(0)
            lengths = torch.tensor([len(features)], dtype=torch.int64)
            x, lengths = self.model.encoder_embed(x, lengths)
            padding = torch.arange(x.shape[1]).unsqueeze(0) >= lengths.unsqueeze(1)
            encoded, lengths = self.model.encoder(x.permute(1, 0, 2), lengths, padding)
            probabilities = self.model.ctc_output(encoded.permute(1, 0, 2))[0, :lengths[0]].exp()
            return decode_phones(probabilities.numpy(), self.tokenizer, self.blank_id, len(samples) / 16000)

def decode_phones(probabilities, tokenizer, blank_id, duration):
    """Collapse contiguous CTC runs; timestamps are approximate, not alignment."""
    import numpy as np
    ids = np.argmax(probabilities, axis=-1)
    results = []
    start = 0
    while start < len(ids):
        token_id = int(ids[start])
        end = start + 1
        while end < len(ids) and int(ids[end]) == token_id:
            end += 1
        if token_id != blank_id and not tokenizer.id_to_piece(token_id).startswith("<"):
            phone = tokenizer.decode([token_id]).strip()
            if phone and not phone.startswith("<"):
                results.append({"phone": phone, "start": round(start / len(ids) * duration, 3),
                    "end": round(end / len(ids) * duration, 3),
                    "posterior": float(probabilities[start:end, token_id].max())})
        start = end
    return results
