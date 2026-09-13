# Anime Info Bot

A full-featured Telegram Anime Info Bot built with PyroFork, MongoDB (3 split clusters), FastAPI Mini App backend, and ffmpeg media tools.

## Setup

1. Copy `.env.example` to `.env` and fill in API credentials and MongoDB URIs.
2. Install dependencies: `pip install -r requirements.txt`
3. Run bot: `python -m bot.main`
4. Run Mini App backend: `uvicorn webapp.backend.main:app --port 8000`
5. Run tests: `pytest`

