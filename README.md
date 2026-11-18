# Generative Audiobook Studio

A local Flask application that turns text-based PDF files into chapter-wise WAV audiobooks using PDFMiner and the female-speaker VITS model configured in `backend/config.py`.

## Features

- Upload a text-based PDF (maximum 50 MB).
- Extract PDF text and create chapters while keeping paragraphs together.
- Store uploaded PDFs, chapter text and generated WAV audio in a local SQLite database.
- Generate audio one chapter at a time using `onecxi/mms-english-female-indic`.
- See progress updates while each text segment is synthesized.
- Play generated audio in the browser and download chapter WAV files.
- Reopen books from the local library after restarting the app.
- Responsive interface with the Deep Teal, Champagne Gold, Soft Ivory and Light Blue theme.
- Browser speech preview is available separately from neural audio generation.

## Windows setup

**Recommended:** Windows 10/11, Python 3.11 (64-bit), at least 8 GB RAM, and an internet connection for the first installation/model download. A GPU is optional; CPU inference is supported but can be slower.

1. Extract the ZIP file to a normal writable folder, for example `C:\Users\YourName\Documents\Generative Audiobook Studio`.
2. Install Python 3.11 (64-bit) if it is not already installed. During installation, enable **Add Python to PATH**.
3. Double-click `setup.bat` and wait for dependency installation to finish.
4. Double-click `run.bat`.
5. Keep the black command window open and visit **http://127.0.0.1:5000** in Chrome or Edge.

The first audio-generation request downloads and initializes the Hugging Face voice model. This can take several minutes and requires internet access and free disk space. Later generations reuse the downloaded model.

## Manual setup

From the project folder in Command Prompt:

```bat
py -3.11 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r backend\requirements.txt
python backend\app.py
```

## Project structure

```text
Generative_Audiobook_Studio/
├── backend/
│   ├── app.py              # Flask API and local web server
│   ├── config.py           # Paths, model name and upload limits
│   ├── database.py         # SQLite storage and retrieval
│   ├── nlp_pipeline.py     # Chapter splitting and short summary
│   ├── pdf_pipeline.py     # PDF text extraction and cleanup
│   ├── tts_engine.py       # Female VITS speech synthesis
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── assets/hero-audio.svg
├── data/                   # Local database and uploads are stored here
├── setup.bat
├── run.bat
└── README.md
```

## Notes and troubleshooting

- Use a **text-based PDF**. Image-only/scanned PDFs need OCR, which is not included in this version.
- The first neural audio generation can be slow on CPU. The progress bar now reports completed audio segments instead of staying at one fixed percentage.
- Keep the terminal window open while using the app. Closing it stops the local server.
- Your books and generated audio are stored in `data/audiobooks.db`. Back up this file if you want to preserve your library when moving the project.
- To reset the library, stop the server and remove `data/audiobooks.db`. This permanently removes the locally stored books and generated audio.
- If port 5000 is already in use, close the other app using it or set a different `PORT` environment variable before starting the server.
- The browser's **Preview voice** uses speech synthesis supplied by the browser/operating system. It is not the same voice as the neural VITS model.
- The demo button demonstrates the interface and browser preview only. Upload a real PDF to generate and save neural audio.

## API health check

With the app running, open `http://127.0.0.1:5000/api/health`. A healthy response includes `"ok": true`.

## Privacy

The Flask application stores PDFs, extracted text and generated audio locally in the project's `data` folder. The voice model is downloaded from Hugging Face on first use. No hosted account or cloud database is required for local use.
