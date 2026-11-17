import re
import re
import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


def sentence_split(text: str) -> list[str]:
    # Prefer NLTK Punkt. If its language data is unavailable in an offline
    # environment, use a deterministic punctuation fallback rather than fail.
    try:
        return [s.strip() for s in nltk.sent_tokenize(text) if s.strip()]
    except LookupError:
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in parts if s.strip()]


def make_chapters(text: str, max_chars: int = 5500) -> list[dict]:
    sentences = sentence_split(text)
    chapters = []
    current = []
    current_len = 0

    for sentence in sentences:
        # Keep sentence boundaries intact for narration.
        if current and current_len + len(sentence) + 1 > max_chars:
            chapters.append({
                "title": f"Chapter {len(chapters) + 1}",
                "text": " ".join(current),
            })
            current = []
            current_len = 0

        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chapters.append({
            "title": f"Chapter {len(chapters) + 1}",
            "text": " ".join(current),
        })

    return chapters


def summarize_for_ui(text: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[:limit].rsplit(" ", 1)[0] + "…"
