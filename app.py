import cv2
import customtkinter as ctk
from deepface import DeepFace
import threading
import flask_app
import webbrowser
import os
import sys
import tkinter as tk
from PIL import Image

result_data = {"emotion": None, "running": True}

def camera_loop():
    while result_data["running"]:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        faces = cascade.detectMultiScale(rgb, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_roi = rgb[y:y + h, x:x + w]
            analysis = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
            emotion = analysis[0]['dominant_emotion']
            result_data["emotion"] = emotion
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imshow("Mirror Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            result_data["running"] = False
            break

    cap.release()
    cv2.destroyAllWindows()

cascade = cv2.CascadeClassifier("haarcascade.xml")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    exit()

def resolve_first_existing(paths):
	for p in paths:
		if os.path.exists(p):
			return p
	return None

ICON_PATH = resolve_first_existing(["favicon.ico", os.path.join("static", "favicon.ico")])
LOGO_PATH = resolve_first_existing([os.path.join("static", "Logo.png"), os.path.join("static", "logo.png")])

reading_win = ctk.CTk()
reading_win.geometry("300x300")
reading_win.title("Mirror")

try:
	if sys.platform == "win32" and ICON_PATH:
		reading_win.iconbitmap(ICON_PATH)
except Exception:
	pass

try:
	if LOGO_PATH:
		reading_win.iconphoto(True, tk.PhotoImage(file=LOGO_PATH))
except Exception:
	pass

if LOGO_PATH:
	try:
		_logo_img = ctk.CTkImage(light_image=Image.open(LOGO_PATH), dark_image=Image.open(LOGO_PATH), size=(56, 56))
		logo_label = ctk.CTkLabel(reading_win, image=_logo_img, text="")
		logo_label.pack(pady=6)
	except Exception:
		pass

title = ctk.CTkLabel(reading_win, text="Mirror - Reading Emotion", font=ctk.CTkFont(size=20, weight="bold"))
title.pack(pady=10)

instruction = ctk.CTkLabel(reading_win, text="Press 'Done' to finish reading your emotion.", font=ctk.CTkFont(size=14))
instruction.pack(pady=10)

def on_done():
    result_data["running"] = False
    reading_win.quit()

quit_button = ctk.CTkButton(reading_win, text="Done", command=on_done)
quit_button.pack(pady=20)

camera_thread = threading.Thread(target=camera_loop, daemon=True)
camera_thread.start()

reading_win.mainloop()
camera_thread.join()

flask_thread = threading.Thread(
    target=flask_app.run_flask_app,
    args=(result_data["emotion"] if result_data["emotion"] else "neutral",),
    daemon=True
)
flask_thread.start()

flask_win = ctk.CTk()
flask_win.geometry("300x300")
flask_win.title("Mirror")

try:
	if sys.platform == "win32" and ICON_PATH:
		flask_win.iconbitmap(ICON_PATH)
except Exception:
	pass

try:
	if LOGO_PATH:
		flask_win.iconphoto(True, tk.PhotoImage(file=LOGO_PATH))
except Exception:
	pass

if LOGO_PATH:
	try:
		_flask_logo_img = ctk.CTkImage(light_image=Image.open(LOGO_PATH), dark_image=Image.open(LOGO_PATH), size=(56, 56))
		flask_logo_label = ctk.CTkLabel(flask_win, image=_flask_logo_img, text="")
		flask_logo_label.pack(pady=6)
	except Exception:
		pass

flask_title = ctk.CTkLabel(flask_win, text="Mirror", font=ctk.CTkFont(size=20, weight="bold"))
flask_title.pack(pady=10)

if result_data["emotion"]:
    emotion_label = ctk.CTkLabel(flask_win, text=f"Emotion Detected: {result_data['emotion']}", font=ctk.CTkFont(size=14))
else:
    emotion_label = ctk.CTkLabel(flask_win, text="No emotion detected.", font=ctk.CTkFont(size=14))

emotion_label.pack(pady=10)

running_label = ctk.CTkLabel(flask_win, text="Flask GUI running at 127.0.0.1:5000", font=ctk.CTkFont(size=14))
running_label.pack(pady=10)
open_button = ctk.CTkButton(flask_win, text="Open in Browser", command=lambda: webbrowser.open('http://127.0.0.1:5000'))
open_button.pack(pady=10)

playlists = {
    "sad": "https://open.spotify.com/playlist/37i9dQZF1DWYoYGBbGKurt",
    "happy": "https://open.spotify.com/playlist/37i9dQZF1EIgG2NEOhqsD7",
    "surprised": "https://open.spotify.com/playlist/4k7AJ58rAxkxxdCuJ2jZOV",
    "fear": "https://open.spotify.com/playlist/37i9dQZF1EIfTmpqlGn32s"
}
playlist_link = playlists.get(result_data["emotion"].lower(), "")
playlist_button = ctk.CTkButton(flask_win, text="Open Suggested Playlist", command=lambda: webbrowser.open(playlist_link) if playlist_link else None)
playlist_button.pack(pady=10)

quit_button = ctk.CTkButton(flask_win, text="Quit", command=flask_win.quit)
quit_button.pack(pady=10)

flask_win.mainloop()