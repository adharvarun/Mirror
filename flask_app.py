import re
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sqlite3
from datetime import datetime, timedelta

load_dotenv()

def run_flask_app(emotion):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_KEY")
    socketio = SocketIO(app)

    client = genai.Client()

    # --- SQLite setup ---
    DB_PATH = os.path.join(os.path.dirname(__file__), "mirror.db")

    def get_db_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        conn = get_db_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT CHECK(role IN ('user','assistant')) NOT NULL,
                    text TEXT NOT NULL,
                    emotion TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    init_db()

    def save_message(session_id, role, text, detected_emotion):
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO messages (session_id, role, text, emotion) VALUES (?, ?, ?, ?)",
                (session_id, role, text, detected_emotion),
            )
            conn.commit()
        finally:
            conn.close()

    def fetch_recent_history(session_id, limit=8):
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT role, text FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
            # Reverse to chronological order
            return list(reversed([(row["role"], row["text"]) for row in rows]))
        finally:
            conn.close()

    def remove_repeated_text(response):
        response = re.sub(r'\s+', ' ', response).strip()
        seen = set()
        filtered_words = []
        for word in response.split():
            if word not in seen:
                seen.add(word)
                filtered_words.append(word)
        return " ".join(filtered_words)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        conn = get_db_connection()
        try:
            total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

            # messages per emotion (top 10)
            emotion_counts = conn.execute(
                "SELECT IFNULL(emotion,'unknown') as emotion, COUNT(*) as count FROM messages GROUP BY emotion ORDER BY count DESC LIMIT 10"
            ).fetchall()

            # recent sessions (last 10 by last message time)
            recent_sessions = conn.execute(
                """
                SELECT session_id, MAX(created_at) AS last_time, COUNT(*) AS msg_count
                FROM messages
                GROUP BY session_id
                ORDER BY last_time DESC
                LIMIT 10
                """
            ).fetchall()

            # last 100 messages
            recent_messages = conn.execute(
                "SELECT session_id, role, text, emotion, created_at FROM messages ORDER BY id DESC LIMIT 100"
            ).fetchall()

            return render_template(
                "dashboard.html",
                total_messages=total_messages,
                emotion_counts=emotion_counts,
                recent_sessions=recent_sessions,
                recent_messages=recent_messages,
            )
        finally:
            conn.close()

    @socketio.on("message")
    def handle_message(msg):
        try:
            session_id = request.sid

            # Persist the user's message
            save_message(session_id, "user", msg, emotion)

            # Fetch short recent history for better context
            history = fetch_recent_history(session_id)
            history_text = "\n".join([f"{role.upper()}: {text}" for role, text in history])

            prompt = (
                "You are Mirror, a friendly, empathetic mood-mirror assistant.\n"
                f"Detected emotion: {emotion}.\n"
                "Adapt your tone and guidance to the user's mood. Support students with study strategies and stress relief;"
                " professionals with productivity and work-life balance; offer compassionate, practical advice for sadness;"
                " celebrate wins when happy. Keep responses concise, actionable, and caring.\n\n"
                f"Recent conversation (most recent last):\n{history_text}\n\n"
                f"USER: {msg}\nASSISTANT:"
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                ),
            )

            response_text = response.candidates[0].content.parts[0].text

            # Persist assistant response
            save_message(session_id, "assistant", response_text, emotion)

            emit("response", response_text)

        except Exception as e:
            print(f"Gemini error: {e}")
            emit("response", "Oops, I had trouble thinking that through. Mind trying again?")

    socketio.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)