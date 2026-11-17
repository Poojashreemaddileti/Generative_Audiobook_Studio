import io
import re
import numpy as np
import soundfile as sf
import torch
from transformers import VitsModel, AutoTokenizer

from config import MODEL_NAME


class NeuralTTS:
    """Free English neural TTS using a female-speaker MMS VITS checkpoint."""

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = VitsModel.from_pretrained(MODEL_NAME).to(self.device)
        self.model.eval()

    @staticmethod
    def _chunks(text: str, max_chars: int = 1300):
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks, current = [], ""
        for sentence in sentences:
            if not sentence:
                continue
            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + " " + sentence).strip()
            else:
                if current:
                    chunks.append(current)
                while len(sentence) > max_chars:
                    chunks.append(sentence[:max_chars])
                    sentence = sentence[max_chars:]
                current = sentence
        if current:
            chunks.append(current)
        return chunks or [text.strip()]

    def _synthesize_array(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            output = self.model(**inputs).waveform
        return np.asarray(output.squeeze().cpu().numpy(), dtype=np.float32)

    def synthesize(self, text: str) -> dict:
        pieces = []
        sample_rate = int(self.model.config.sampling_rate)
        for chunk in self._chunks(text):
            pieces.append(self._synthesize_array(chunk))
            pieces.append(np.zeros(int(sample_rate * 0.20), dtype=np.float32))

        waveform = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
        buffer = io.BytesIO()
        sf.write(buffer, waveform, sample_rate, format="WAV", subtype="PCM_16")
        return {
            "audio_bytes": buffer.getvalue(),
            "sample_rate": sample_rate,
            "seconds": round(len(waveform) / sample_rate, 2),
            "device": self.device,
            "model": MODEL_NAME,
        }


_tts = None


def get_tts() -> NeuralTTS:
    global _tts
    if _tts is None:
        _tts = NeuralTTS()
    return _tts
