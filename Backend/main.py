# main.py
import os
import sys
import json
import uvicorn
from fastapi import FastAPI, WebSocket
from vosk import Model, KaldiRecognizer

# Local imports
from config import MODEL_PATH, SAMPLE_RATE, HOST, PORT
from nlp import parse_intent, perform_action

# ---------------- VOSK INITIALIZATION ----------------
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Vosk model not found at {MODEL_PATH}")
    sys.exit(1)

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, SAMPLE_RATE)
recognizer.SetWords(False)

# ---------------- FASTAPI SERVER ----------------
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_json({"text": "Hello! I’m your assistant — you can speak or type."})

    try:
        while True:
            message = await ws.receive()

            # --- Voice input ---
            if "bytes" in message:
                data = message["bytes"]

                # Partial (live) transcription
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        intent, param = parse_intent(text)
                        response = perform_action(intent, param) if intent else "No intent found."
                        await ws.send_json({"text": text, "response": response})
                else:
                    partial = json.loads(recognizer.PartialResult()).get("partial", "")
                    if partial:
                        await ws.send_json({"partial": partial})

            # --- Typed input ---
            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "text":
                    text = data.get("text", "")
                    intent, param = parse_intent(text)
                    response = perform_action(intent, param) if intent else "No intent found."
                    await ws.send_json({"text": text, "response": response})

    except Exception as e:
        print(f"WebSocket closed: {e}")

if __name__ == "__main__":
    print(f"🎙️  Starting backend on ws://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)