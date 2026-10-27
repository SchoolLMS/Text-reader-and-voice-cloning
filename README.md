# Text Reader & Voice Cloner

Local, consent-based text-to-speech and voice cloning with Coqui XTTS-v2 and FastAPI.

## Setup

Install Python 3.10/3.11 and FFmpeg. A GPU is recommended; CPU inference may be slow. First generation downloads a large model and may prompt for acceptance of its license.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Windows environment activation: `.venv\Scripts\activate`.

## Tests

`pip install pytest httpx` then `pytest -q`.

## Privacy and restrictions

Use only your own voice or one for which you have explicit permission. Reference samples are deleted after each generation. Generated WAV files remain locally in `generated/` until manually deleted. No authentication is built in: **do not expose this server to the internet** without authentication, rate limiting, retention controls and a security review. XTTS-v2 supports Arabic and 16 other languages, but Urdu is not officially supported. Review the model license before commercial deployment.
