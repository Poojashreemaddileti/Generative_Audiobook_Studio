# Free deployment guide

## Option A — Hugging Face Spaces (Docker)

1. Create a new **Space** at Hugging Face.
2. Choose **Docker** as the Space SDK.
3. Upload the project files from this folder.
4. The included `Dockerfile` starts Flask on port 7860.
5. Open the Space URL and upload a PDF.

The first neural generation downloads `facebook/mms-tts-eng`, so allow time for the initial model load. The browser preview works immediately without waiting for the model.

## Option B — Render-style host

Use:

- Build: `pip install -r backend/requirements.txt`
- Start: `python backend/app.py`

The app reads `PORT` and binds to `0.0.0.0` automatically.

Free instances can sleep and may have temporary filesystems. Generated WAV files should therefore be treated as temporary unless a persistent disk is enabled.

## Free/no-paid-API behavior

No OpenAI/ElevenLabs paid API is required. Neural narration uses the free/open Hugging Face model included in the application. The **Preview in browser** button uses the browser's own speech engine and is the fastest way to verify the complete PDF → NLP → listening flow before neural generation.
