import re
from pathlib import Path
from pdfminer.high_level import extract_text


def extract_pdf_text(pdf_path: str | Path) -> str:
    text = extract_text(str(pdf_path)) or ""
    # Normalize common PDF extraction artifacts.
    text = text.replace("\x00", " ")
    text = re.sub(r"-\s*\n\s*", "", text)       # joined hyphenated words
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text(text: str) -> str:
    # Join words split by a PDF line-break before line normalization.
    text = re.sub(r"-\s*\n\s*", "", text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    # Remove simple repeated page-number-only lines.
    cleaned = []
    for line in lines:
        if re.fullmatch(r"(page\s*)?\d{1,4}", line, flags=re.I):
            continue
        cleaned.append(line)

    text = "\n".join(cleaned)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()
