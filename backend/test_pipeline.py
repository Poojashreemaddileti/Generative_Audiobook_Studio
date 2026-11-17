import tempfile
from pathlib import Path

from database import init_db, insert_book, get_book, get_pdf


def test_database_roundtrip():
    # Uses the application's SQLite schema; normal app initialization creates the DB.
    init_db()
    book_id = "test-book-db"
    # Avoid duplicate failure if this test is run repeatedly by using a unique-ish filename.
    book = {
        "id": book_id,
        "filename": "test.pdf",
        "title": "Test Book",
        "word_count": 4,
        "character_count": 20,
        "summary": "A test.",
    }
    try:
        insert_book(book, b"%PDF-test", [{"title":"Chapter 1","text":"Hello world.","preview":"Hello world."}])
        row, chapters = get_book(book_id)
        assert row["title"] == "Test Book"
        assert row["pdf_data"] == b"%PDF-test"
        assert chapters[0]["title"] == "Chapter 1"
        assert get_pdf(book_id)["pdf_data"] == b"%PDF-test"
    finally:
        import sqlite3
        from config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        conn.close()


if __name__ == "__main__":
    test_database_roundtrip()
    print("database test passed")
