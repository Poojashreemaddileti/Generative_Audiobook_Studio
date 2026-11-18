import re

HEADING = re.compile(r"(?im)^\s*((?:chapter|part|section)\s+[\wivxlcdm.-]+[^\n]*|[0-9]{1,2}[.)]\s+[^\n]{2,80})\s*$")


def _split_long_text(text, limit):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        while len(paragraph) > limit:
            if current:
                chunks.append(current.strip())
                current = ""
            cut = paragraph.rfind(" ", 0, limit)
            if cut < limit // 2:
                cut = limit
            chunks.append(paragraph[:cut].strip())
            paragraph = paragraph[cut:].strip()
        candidate = (current + "\n\n" + paragraph).strip() if current else paragraph
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = paragraph
    if current:
        chunks.append(current.strip())
    return chunks


def make_chapters(text, max_chars=5500):
    matches = list(HEADING.finditer(text))
    sections = []
    if matches:
        if text[:matches[0].start()].strip():
            sections.append(("Introduction", text[:matches[0].start()].strip()))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[match.end():end].strip()
            if body:
                sections.append((match.group(1).strip(), body))
    if not sections:
        sections = [("Chapter 1", text.strip())]

    result = []
    for title, body in sections:
        parts = _split_long_text(body, max_chars)
        for part_index, part in enumerate(parts):
            part_title = title if len(parts) == 1 else f"{title} · Part {part_index + 1}"
            result.append({"title": part_title, "text": part})
    return result


def summarize_for_ui(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    summary = " ".join(s for s in sentences[:3] if s)
    return (summary[:500] + "…") if len(summary) > 500 else summary
