import os
import sys
import json
import subprocess
import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket
import uvicorn
from vosk import Model, KaldiRecognizer
import webbrowser

# ---------------- CONFIG ----------------
MODEL_PATH = "vosk-model-en-us-0.22"
SAMPLE_RATE = 16000
# ---------------------------------------

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Vosk model not found at {MODEL_PATH}")
    sys.exit(1)

# Initialize Vosk
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)
recognizer.SetWords(False)

# ---------------- Helper Functions ----------------
def get_time():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    ampm = "AM"
    h12 = hour
    if hour == 0:
        h12 = 12
    elif hour == 12:
        ampm = "PM"
        h12 = 12
    elif hour > 12:
        h12 = hour - 12
        ampm = "PM"
    return f"It is {h12}:{minute:02d} {ampm} on {now.day}/{now.month}/{now.year}."

def parse_intent(text):
    t = text.lower().strip()
    if "open notepad" in t: return "open_app", "notepad"
    if "open calculator" in t or "open calc" in t: return "open_app", "calc"
    if "open browser" in t or "open chrome" in t or "open edge" in t: return "open_app", "browser"
    if "time" in t: return "tell_time", None
    return None, None

def perform_action(intent, param):
    try:
        if intent == "open_app":
            if param == "notepad":
                subprocess.Popen(["notepad.exe"])
                return "Opened Notepad."
            if param == "calc":
                subprocess.Popen(["calc.exe"])
                return "Opened Calculator."
            if param == "browser":
                webbrowser.open("https://www.google.com")
                return "Opened your default browser."
        elif intent == "tell_time":
            return get_time()
    except Exception as e:
        return f"Error performing action: {e}"
    return "Command not recognized."

# ---------------- FastAPI ----------------
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_bytes()

            if recognizer.AcceptWaveform(data):
                res = json.loads(recognizer.Result())
                text = res.get("text", "")
                if text:
                    intent, param = parse_intent(text)
                    if intent:
                        response = perform_action(intent, param)
                    else:
                        response = "No intent found."

                    # Send recognized text and response to frontend
                    await ws.send_json({"text": text, "response": response})
                else:
                    await ws.send_json({"text": "", "response": ""})
            else:
                partial = json.loads(recognizer.PartialResult()).get("partial", "")
                if partial:
                    await ws.send_json({"partial": partial})
    except:
        try:
            ws.close()
        except:
            pass

# ---------------- Run Uvicorn ----------------
if __name__ == "__main__":
    print("Starting backend on ws://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
