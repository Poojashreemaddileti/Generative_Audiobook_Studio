import io
import os
import re
import uuid
from pathlib import Path
from threading import Thread, Lock

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from config import MAX_UPLOAD_MB, MAX_CHAPTER_CHARS, MODEL_NAME
from database import (
    init_db, insert_book, get_book, list_books, get_pdf,
    update_chapter_status, save_audio, get_audio,
)
from pdf_pipeline import extract_pdf_text, clean_text
from nlp_pipeline import make_chapters, summarize_for_ui
from tts_engine import get_tts

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

jobs = {}
jobs_lock = Lock()
init_db()


def public_book(book_id):
    row, chapter_rows = get_book(book_id)
    if row is None:
        raise FileNotFoundError(book_id)
    return {
        "id": row["id"],
        "filename": row["filename"],
        "title": row["title"],
        "status": row["status"],
        "word_count": row["word_count"],
        "character_count": row["character_count"],
        "chapter_count": len(chapter_rows),
        "summary": row["summary"],
        "created_at": row["created_at"],
        "tts": {"model": row["tts_model"], "device": row["tts_device"]} if row["tts_model"] else None,
        "pdf_url": f"/api/books/{book_id}/pdf",
        "chapters": [
            {
                "index": c["chapter_index"],
                "title": c["title"],
                "characters": c["characters"],
                "preview": c["preview"],
                "audio": f"/api/books/{book_id}/audio/{c['chapter_index']}" if c["audio_data"] else None,
                "duration": c["duration"],
                "status": c["status"],
            }
            for c in chapter_rows
        ],
    }


def update_job(job_id, **values):
    with jobs_lock:
        jobs.setdefault(job_id, {}).update(values)


def get_job(job_id):
    with jobs_lock:
        return dict(jobs.get(job_id, {"status": "missing"}))


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "generative-audiobook", "tts_model": MODEL_NAME, "database": "SQLite"})


@app.get("/api/library")
def library():
    return jsonify({"books": [
        {
            "id": r["id"], "filename": r["filename"], "title": r["title"],
            "word_count": r["word_count"], "chapter_count": r["chapter_count"],
            "status": r["status"], "created_at": r["created_at"],
        } for r in list_books()
    ]})


@app.post("/api/books")
def upload_book():
    pdf = request.files.get("pdf")
    if not pdf or not pdf.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file."}), 400

    pdf_data = pdf.read()
    if not pdf_data:
        return jsonify({"error": "The PDF is empty."}), 400

    book_id = uuid.uuid4().hex[:10]
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", pdf.filename)
    temp_path = Path(__file__).resolve().parent.parent / "data" / f"_{book_id}_{safe_name}"
    temp_path.write_bytes(pdf_data)
    try:
        raw = extract_pdf_text(temp_path)
        text = clean_text(raw)
        if not text:
            raise ValueError("No readable text was found. This may be a scanned/image-only PDF.")

        chapters = make_chapters(text, MAX_CHAPTER_CHARS)
        title = Path(pdf.filename).stem.replace("_", " ").replace("-", " ").title()
        book = {
            "id": book_id,
            "filename": pdf.filename,
            "title": title,
            "word_count": len(text.split()),
            "character_count": len(text),
            "summary": summarize_for_ui(text),
        }
        insert_book(book, pdf_data, chapters)
        return jsonify(public_book(book_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/books/<book_id>")
def get_book_route(book_id):
    try:
        return jsonify(public_book(book_id))
    except FileNotFoundError:
        return jsonify({"error": "Book not found."}), 404


@app.get("/api/books/<book_id>/pdf")
def pdf_route(book_id):
    row = get_pdf(book_id)
    if row is None:
        return jsonify({"error": "Book not found."}), 404
    return send_file(io.BytesIO(row["pdf_data"]), mimetype=row["mime_type"], download_name=row["filename"])


def generate_chapter_worker(book_id, chapter_index, job_id):
    try:
        book_row, chapters = get_book(book_id)
        if book_row is None or chapter_index < 0 or chapter_index >= len(chapters):
            raise ValueError("Chapter does not exist.")
        chapter = chapters[chapter_index]
        update_chapter_status(book_id, chapter_index, "generating")
        update_job(job_id, status="loading", message="Loading the female neural voice model…", progress=10)
        tts = get_tts()
        update_job(job_id, status="generating", message="Creating clear, natural narration…", progress=45)
        result = tts.synthesize(chapter["text"])
        save_audio(book_id, chapter_index, result["audio_bytes"], result["seconds"], result["sample_rate"], result["model"], result["device"])
        update_job(job_id, status="done", message="Chapter ready to play.", progress=100, book=public_book(book_id))
    except Exception as exc:
        update_chapter_status(book_id, chapter_index, "error")
        update_job(job_id, status="error", message=str(exc), progress=100)


@app.post("/api/books/<book_id>/generate")
def generate(book_id):
    try:
        book = public_book(book_id)
    except FileNotFoundError:
        return jsonify({"error": "Book not found."}), 404

    payload = request.get_json(silent=True) or {}
    try:
        chapter_index = int(payload.get("chapter", 0))
    except (TypeError, ValueError):
        chapter_index = 0
    if chapter_index < 0 or chapter_index >= len(book["chapters"]):
        return jsonify({"error": "Chapter does not exist."}), 400
    if book["chapters"][chapter_index].get("audio"):
        return jsonify({"status": "already_generated", "book": book})

    job_id = uuid.uuid4().hex[:12]
    update_job(job_id, status="queued", message="Queued…", progress=0, book_id=book_id, chapter=chapter_index)
    Thread(target=generate_chapter_worker, args=(book_id, chapter_index, job_id), daemon=True).start()
    return jsonify({"job_id": job_id, "status": "queued", "message": "Generation started."}), 202


@app.get("/api/jobs/<job_id>")
def job_status(job_id):
    job = get_job(job_id)
    if job.get("status") == "missing":
        return jsonify({"error": "Job not found."}), 404
    return jsonify(job)


@app.get("/api/books/<book_id>/audio/<int:chapter_index>")
def audio(book_id, chapter_index):
    row = get_audio(book_id, chapter_index)
    if row is None or row["audio_data"] is None:
        return jsonify({"error": "Chapter audio is not generated yet."}), 404
    return send_file(io.BytesIO(row["audio_data"]), mimetype="audio/wav", download_name=f"chapter-{chapter_index + 1}.wav")


FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND, path)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT",10000
    app.run(host=host,port=port)
