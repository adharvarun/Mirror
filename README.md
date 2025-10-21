# 😀 Mirror

Mirror is a desktop + web hybrid that detects facial emotion with OpenCV and serves a local Flask chat UI powered by Google Gemini. Conversations persist to SQLite, and a dashboard shows recent activity and trends.

## Features
- Real‑time emotion detection (OpenCV + Haar cascade)
- Flask + Socket.IO chat UI
- Gemini (gemini‑2.5‑flash) responses
- SQLite conversation history (per Socket.IO session)
- Recent session history included in prompts for better context
- Dashboard at `/dashboard`

## Video Demo
[https://youtu.be/VSHev87VBLk](https://youtu.be/VSHev87VBLk)

## Requirements
- Python 3.10+
- Webcam
- Google Generative AI API key

## Setup
1) Create a virtual environment and install dependencies
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip
pip install opencv-python customtkinter flask flask-socketio python-dotenv google-genai pillow
```

2) Create a `.env` file in the project root
```env
FLASK_KEY=replace-with-a-random-secret
GOOGLE_API_KEY=your-google-genai-api-key
```

3) Run the app
```bash
python app.py
```
- A Tkinter window opens for emotion reading; click "Done" when ready.
- Chat UI: `http://127.0.0.1:5000`
- Dashboard: `http://127.0.0.1:5000/dashboard`

## Files
- `app.py` – camera + Tk flow, launches Flask
- `flask_app.py` – Flask/Socket.IO, Gemini, SQLite
- `templates/index.html` – chat UI
- `templates/dashboard.html` – dashboard UI
- `haarcascade.xml` – face detection model
- `mirror.db` – auto‑created SQLite database (next to `flask_app.py`)

## Troubleshooting
- Camera black/not found: close other camera apps; ensure `haarcascade.xml` exists in the project root.
- Server not reachable: check console/firewall; runs on 127.0.0.1:5000.
- Gemini errors: verify `GOOGLE_API_KEY` and network access.

## Notes
- History window is the most recent 8 messages; adjust in `flask_app.py` if needed.
- For cross‑session continuity, add a stable user identifier and merge histories.
