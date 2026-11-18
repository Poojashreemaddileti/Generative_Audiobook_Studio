import sqlite3
from datetime import datetime, timezone
from config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ready',
            word_count INTEGER NOT NULL DEFAULT 0,
            character_count INTEGER NOT NULL DEFAULT 0,
            summary TEXT DEFAULT '',
            pdf_data BLOB NOT NULL,
            mime_type TEXT NOT NULL DEFAULT 'application/pdf',
            tts_model TEXT,
            tts_device TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            chapter_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            characters INTEGER NOT NULL DEFAULT 0,
            preview TEXT DEFAULT '',
            audio_data BLOB,
            duration REAL,
            status TEXT NOT NULL DEFAULT 'ready',
            UNIQUE(book_id, chapter_index)
        );
        CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id, chapter_index);
        """)


def insert_book(book, pdf_data, chapters):
    with _connect() as conn:
        conn.execute("""INSERT INTO books
            (id, filename, title, status, word_count, character_count, summary, pdf_data, mime_type, created_at)
            VALUES (?, ?, ?, 'ready', ?, ?, ?, ?, 'application/pdf', ?)""",
            (book['id'], book['filename'], book['title'], book['word_count'],
             book['character_count'], book.get('summary', ''), sqlite3.Binary(pdf_data),
             datetime.now(timezone.utc).isoformat()))
        for index, chapter in enumerate(chapters):
            title = chapter.get('title') or f'Chapter {index + 1}'
            text = chapter.get('text', '')
            conn.execute("""INSERT INTO chapters
                (book_id, chapter_index, title, text, characters, preview, status)
                VALUES (?, ?, ?, ?, ?, ?, 'ready')""",
                (book['id'], index, title, text, len(text), text[:420]))


def get_book(book_id):
    with _connect() as conn:
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if book is None:
            return None, []
        chapters = conn.execute("""SELECT chapter_index, title, text, characters, preview,
            audio_data, duration, status FROM chapters WHERE book_id = ? ORDER BY chapter_index""",
            (book_id,)).fetchall()
        return book, chapters


def list_books():
    with _connect() as conn:
        return conn.execute("""SELECT b.id, b.filename, b.title, b.word_count, b.status, b.created_at,
            COUNT(c.id) AS chapter_count FROM books b LEFT JOIN chapters c ON c.book_id=b.id
            GROUP BY b.id ORDER BY b.created_at DESC""").fetchall()


def get_pdf(book_id):
    with _connect() as conn:
        return conn.execute("SELECT pdf_data, filename, mime_type FROM books WHERE id = ?", (book_id,)).fetchone()


def update_chapter_status(book_id, chapter_index, status):
    with _connect() as conn:
        conn.execute("UPDATE chapters SET status=? WHERE book_id=? AND chapter_index=?",
                     (status, book_id, chapter_index))
        if status == 'generating':
            conn.execute("UPDATE books SET status='generating' WHERE id=?", (book_id,))
        elif status == 'error':
            conn.execute("UPDATE books SET status='ready' WHERE id=?", (book_id,))


def save_audio(book_id, chapter_index, audio_bytes, seconds, sample_rate, model, device):
    with _connect() as conn:
        conn.execute("UPDATE chapters SET audio_data=?, duration=?, status='generated' WHERE book_id=? AND chapter_index=?",
                     (sqlite3.Binary(audio_bytes), seconds, book_id, chapter_index))
        conn.execute("UPDATE books SET status='generated', tts_model=?, tts_device=? WHERE id=?",
                     (model, device, book_id))


def get_audio(book_id, chapter_index):
    with _connect() as conn:
        return conn.execute("SELECT audio_data FROM chapters WHERE book_id=? AND chapter_index=?",
                            (book_id, chapter_index)).fetchone()
