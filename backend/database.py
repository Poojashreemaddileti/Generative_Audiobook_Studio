import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from config import DB_PATH


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            title TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            pdf_data BLOB NOT NULL,
            word_count INTEGER NOT NULL DEFAULT 0,
            character_count INTEGER NOT NULL DEFAULT 0,
            summary TEXT,
            status TEXT NOT NULL DEFAULT 'ready',
            tts_model TEXT,
            tts_device TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL,
            chapter_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            characters INTEGER NOT NULL DEFAULT 0,
            preview TEXT,
            status TEXT NOT NULL DEFAULT 'ready',
            duration REAL,
            audio_data BLOB,
            sample_rate INTEGER,
            UNIQUE(book_id, chapter_index),
            FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_books_created_at ON books(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id, chapter_index);
        """
    )
    conn.commit()
    conn.close()


def insert_book(book, pdf_data, chapters):
    conn = connect()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO books
           (id, filename, title, mime_type, pdf_data, word_count, character_count, summary, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (book["id"], book["filename"], book["title"], "application/pdf", pdf_data,
         book["word_count"], book["character_count"], book["summary"], "ready", now),
    )
    conn.executemany(
        """INSERT INTO chapters
           (book_id, chapter_index, title, text, characters, preview, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            (book["id"], i, c["title"], c["text"], len(c["text"]), c.get("preview", ""), "ready")
            for i, c in enumerate(chapters)
        ],
    )
    conn.commit()
    conn.close()


def get_book(book_id):
    conn = connect()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    chapters = conn.execute(
        "SELECT * FROM chapters WHERE book_id = ? ORDER BY chapter_index", (book_id,)
    ).fetchall()
    conn.close()
    return row, chapters


def list_books():
    conn = connect()
    rows = conn.execute(
        """SELECT id, filename, title, word_count, character_count, status, created_at,
                  (SELECT COUNT(*) FROM chapters c WHERE c.book_id=b.id) AS chapter_count
           FROM books b ORDER BY created_at DESC"""
    ).fetchall()
    conn.close()
    return rows


def get_pdf(book_id):
    conn = connect()
    row = conn.execute("SELECT filename, mime_type, pdf_data FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return row


def update_chapter_status(book_id, chapter_index, status):
    conn = connect()
    conn.execute(
        "UPDATE chapters SET status = ? WHERE book_id = ? AND chapter_index = ?",
        (status, book_id, chapter_index),
    )
    conn.commit()
    conn.close()


def save_audio(book_id, chapter_index, audio_data, duration, sample_rate, model, device):
    conn = connect()
    conn.execute(
        """UPDATE chapters
           SET audio_data = ?, duration = ?, sample_rate = ?, status = 'generated'
           WHERE book_id = ? AND chapter_index = ?""",
        (audio_data, duration, sample_rate, book_id, chapter_index),
    )
    conn.execute(
        "UPDATE books SET status='generated', tts_model=?, tts_device=? WHERE id=?",
        (model, device, book_id),
    )
    conn.commit()
    conn.close()


def get_audio(book_id, chapter_index):
    conn = connect()
    row = conn.execute(
        "SELECT audio_data, sample_rate, title FROM chapters WHERE book_id=? AND chapter_index=?",
        (book_id, chapter_index),
    ).fetchone()
    conn.close()
    return row
