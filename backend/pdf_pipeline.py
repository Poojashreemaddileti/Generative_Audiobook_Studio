from pdfminer.high_level import extract_text
import re


def extract_pdf_text(path):
    return extract_text(str(path)) or ""


def clean_text(text):
    text = text.replace("\x00", " ").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
