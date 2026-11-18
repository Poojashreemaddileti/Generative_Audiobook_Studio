import io
import re
import threading
import numpy as np
import soundfile as sf
import torch
from transformers import VitsModel, AutoTokenizer
from config import MODEL_NAME


class NeuralTTS:
    """English female-speaker VITS voice. Model loads once and is reused."""
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = VitsModel.from_pretrained(MODEL_NAME).to(self.device)
        self.model.eval()
        self.lock = threading.Lock()

    @staticmethod
    def _chunks(text, max_chars=1100):
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks, current = [], ""
        for sentence in sentences:
            if not sentence:
                continue
            if len(sentence) > max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                while len(sentence) > max_chars:
                    cut = sentence.rfind(" ", 0, max_chars)
                    if cut < max_chars // 2:
                        cut = max_chars
                    chunks.append(sentence[:cut].strip())
                    sentence = sentence[cut:].strip()
            candidate = (current + " " + sentence).strip()
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sentence
        if current:
            chunks.append(current)
        return chunks or [text.strip()]

    def _synthesize_array(self, text):
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.no_grad():
            output = self.model(**inputs).waveform
        return np.asarray(output.squeeze().cpu().numpy(), dtype=np.float32)

    def synthesize(self, text, progress_callback=None):
        chunks = self._chunks(text)
        pieces = []
        sample_rate = int(self.model.config.sampling_rate)
        with self.lock:
            for index, chunk in enumerate(chunks, start=1):
                pieces.append(self._synthesize_array(chunk))
                if index < len(chunks):
                    pieces.append(np.zeros(int(sample_rate * 0.20), dtype=np.float32))
                if progress_callback:
                    progress_callback(index, len(chunks))
        waveform = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
        buffer = io.BytesIO()
        sf.write(buffer, waveform, sample_rate, format="WAV", subtype="PCM_16")
        return {"audio_bytes": buffer.getvalue(), "sample_rate": sample_rate,
                "seconds": round(len(waveform) / sample_rate, 2),
                "device": self.device, "model": MODEL_NAME}


_tts = None
_tts_lock = threading.Lock()


def get_tts():
    global _tts
    if _tts is None:
        with _tts_lock:
            if _tts is None:
                _tts = NeuralTTS()
    return _tts
