---
title: Generative Audiobook Studio
description: Convert PDF books into chapter-wise audiobooks with a female neural voice.
sdk: docker
app_port: 7860
---

# Generative Audiobook Studio

This is the original Flask application, packaged for Hugging Face Spaces with Docker. The original HTML/CSS/JavaScript interface and Flask API are retained.

## Features
- Original editorial interface with Studio, How it works, and Library navigation.
- PDF upload and text extraction using PDFMiner.
- NLTK-based chapter organization.
- SQLite storage for uploaded PDFs, book metadata, chapters, and generated audio.
- Chapter-by-chapter female neural voice generation using `onecxi/mms-english-female-indic`.
- Chapter playback and WAV downloads.

## Hugging Face Spaces
Create a new Space and select **Docker** as the SDK. Upload the contents of this repository (including this README and Dockerfile). The container listens on port **7860**.

The first audio generation downloads the neural voice model and can take several minutes. CPU inference can also be slow for long chapters.

## Storage note
The Space uses `/data` for its Hugging Face model cache. The SQLite database is created under the application `data/` directory. On free Spaces, local filesystem data may be lost when the Space restarts or is rebuilt. Enable persistent storage in Space settings if you need uploaded books and generated audio to remain available.

## Voice model license
The configured model is `onecxi/mms-english-female-indic`. Review its model-card license and usage restrictions before public or commercial use.
