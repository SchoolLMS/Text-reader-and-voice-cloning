"""Consent-based local voice synthesis API."""
import os
import tempfile
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.getenv("VOICE_OUTPUT_DIR", ROOT / "generated"))
OUTPUT.mkdir(parents=True, exist_ok=True)
LANGUAGES = {"en", "ar", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "zh-cn", "ja", "ko", "hu", "hi"}
MAX_SAMPLE = 15 * 1024 * 1024
_tts = None
_load_lock = threading.Lock()
_inference_lock = threading.Lock()

app = FastAPI(title="Text Reader & Voice Cloner")
app.mount("/static", StaticFiles(directory=ROOT), name="static")


def model():
    global _tts
    if _tts is None:
        with _load_lock:
            if _tts is None:
                from TTS.api import TTS
                import torch
                _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda" if torch.cuda.is_available() else "cpu")
    return _tts


@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _tts is not None}


@app.post("/api/generate")
async def generate(text: str = Form(...), language: str = Form("en"), consent: bool = Form(False), speaker: UploadFile = File(...)):
    if not text.strip() or len(text) > 2000:
        raise HTTPException(422, "Text must contain between 1 and 2000 characters")
    if language not in LANGUAGES:
        raise HTTPException(422, "Unsupported language")
    if not consent:
        raise HTTPException(422, "Confirm permission to use the reference voice")
    suffix = Path(speaker.filename or "").suffix.lower()
    if suffix not in {".wav", ".mp3", ".flac"}:
        raise HTTPException(422, "Upload a WAV, MP3 or FLAC sample")

    with tempfile.TemporaryDirectory(prefix="voice_ref_") as folder:
        sample = Path(folder) / ("sample" + suffix)
        size = 0
        with sample.open("wb") as destination:
            while chunk := await speaker.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_SAMPLE:
                    raise HTTPException(413, "Voice sample exceeds 15 MB")
                destination.write(chunk)
        if not size:
            raise HTTPException(422, "Empty voice sample")
        name = uuid.uuid4().hex + ".wav"
        output = OUTPUT / name
        try:
            with _inference_lock:
                model().tts_to_file(text=text.strip(), language=language, speaker_wav=str(sample), file_path=str(output))
        except Exception as error:
            output.unlink(missing_ok=True)
            raise HTTPException(500, "Generation failed; inspect server logs and model setup") from error
    return {"audio_url": "/api/audio/" + name}


@app.get("/api/audio/{filename}")
def audio(filename: str):
    if len(filename) != 36 or not filename.endswith(".wav") or any(c not in "0123456789abcdef" for c in filename[:-4]):
        raise HTTPException(404, "Audio not found")
    path = OUTPUT / filename
    if not path.is_file():
        raise HTTPException(404, "Audio not found")
    return FileResponse(path, media_type="audio/wav", filename="generated-voice.wav")
