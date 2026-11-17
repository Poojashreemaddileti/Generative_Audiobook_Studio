from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "audiobooks.db"
MODEL_NAME = "onecxi/mms-english-female-indic"
MAX_UPLOAD_MB = 50
MAX_CHAPTER_CHARS = 5500

for folder in (DATA_DIR, UPLOAD_DIR):
    folder.mkdir(parents=True, exist_ok=True)
