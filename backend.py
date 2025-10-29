import os
import sys
import json
import subprocess
import re
from datetime import datetime
from fastapi import FastAPI, WebSocket
import uvicorn
from vosk import Model, KaldiRecognizer
import webbrowser
import psutil
import requests
import random
import speedtest
import platform

# ---------------- CONFIG ----------------
MODEL_PATH = "vosk-model-en-us-0.22"
SAMPLE_RATE = 16000

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Vosk model not found at {MODEL_PATH}")
    sys.exit(1)

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

def get_date():
    today = datetime.now().date()
    return f"Today is {today.strftime('%A, %d %B %Y')}."

def get_battery_percentage():
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "Battery information is not available on this device."
        percent = battery.percent
        plugged = battery.power_plugged
        status = "charging" if plugged else "not charging"
        return f"Your battery is at {percent}% and currently {status}."
    except Exception as e:
        return f"Error checking battery: {e}"

def get_wifi_name():
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True
        )
        output = result.stdout
        match = re.search(r"SSID\s*:\s*(.+)", output)
        if match:
            ssid = match.group(1).strip()
            return f"You are connected to Wi-Fi network '{ssid}'."
        else:
            return "Wi-Fi network name could not be detected."
    except Exception as e:
        return f"Error getting Wi-Fi name: {e}"

def get_system_specs():
    try:
        uname = platform.uname()
        cpu = platform.processor()
        memory = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        return (
            f"System: {uname.system} {uname.release}\n"
            f"Machine: {uname.machine}\n"
            f"Processor: {cpu}\n"
            f"RAM: {memory} GB"
        )
    except Exception as e:
        return f"Error fetching system specs: {e}"

# ---------------- INTENT PARSING ----------------
def parse_intent(text):
    t = text.lower().strip()
    apps = {
            "notepad": "notepad",
            "calculator": "calc",
            "calc": "calc",
            "browser": "browser",
            "chrome": "browser",
            "edge": "browser",
            "vs code": "vscode",
            "visual studio code": "vscode",
            "file explorer": "explorer",
            "explorer": "explorer",
            "youtube": "youtube",
            "downloads": "downloads",
            "documents": "documents",
            "whatsapp": "whatsapp",
            "word": "word",
            "excel": "excel",
            "powerpoint": "powerpoint",
            "power point": "powerpoint",
        }
    
    # --- OPEN commands ---
    if "open" in t:
        for key, val in apps.items():
            if key in t:
                return "open_app", val

    # --- CLOSE commands ---
    if "close" in t:
        for key, val in apps.items():
            if key in t:
                return "close_app", val

    # --- Other intents ---
    if any(x in t for x in ["joke", "funny", "make me laugh"]):
        return "tell_joke", None
    if "time" in t:
        return "tell_time", None
    if "date" in t:
        return "tell_date", None
    if "battery" in t:
        return "battery_status", None
    if "wifi" in t or "wi-fi" in t:
        return "wifi_name", None
    if any(x in t for x in ["system info", "specs", "specification"]):
        return "system_specs", None
    if "screenshot" in t:
        return "take_screenshot", None
    if "speed" in t:
        return "check_speed", None

    return None, None

# ---------------- ACTION HANDLERS ----------------
def perform_action(intent, param):
    try:
        if intent == "open_app":
            open_map = {
                "notepad": ["notepad.exe"],
                "calc": ["calc.exe"],
                "browser": ["cmd", "/c", "start", "https://www.google.com"],
                "vscode": ["cmd", "/c", "start", "code"],
                "explorer": ["explorer"],
                "youtube": ["cmd", "/c", "start", "https://www.youtube.com"],
                "downloads": ["explorer", os.path.join(os.path.expanduser("~"), "Downloads")],
                "documents": ["explorer", os.path.join(os.path.expanduser("~"), "Documents")],
                "whatsapp": ["cmd", "/c", "start", "whatsapp:"],
                "word": ["cmd", "/c", "start", "winword"],
                "excel": ["cmd", "/c", "start", "excel"],
                "powerpoint": ["cmd", "/c", "start", "powerpnt"],
            }
            if param in open_map:
                subprocess.Popen(open_map[param])
                return f"Opened {param.title()}."
        elif intent == "close_app":
            closed = close_application(param)
            return f"Closed {param.title()}." if closed else f"{param.title()} was not running."
        elif intent == "tell_time":
            return get_time()
        elif intent == "tell_date":
            return get_date()
        elif intent == "tell_joke":
            return get_joke()
        elif intent == "check_speed":
            return check_internet_speed()
        elif intent == "battery_status":
            return get_battery_percentage()
        elif intent == "wifi_name":
            return get_wifi_name()
        elif intent == "system_specs":
            return get_system_specs()
        elif intent == "take_screenshot":
            return take_screenshot()
    except Exception as e:
        return f"Error performing action: {e}"

    return "Command not recognized."

# ---------------- Helper Tasks ----------------
def get_joke():
    try:
        r = requests.get(
            "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,sexist,racist", timeout=5)
        data = r.json()
        if data.get("type") == "single":
            return data.get("joke")
        elif data.get("type") == "twopart":
            return f"{data.get('setup')} ... {data.get('delivery')}"
    except:
        pass
    return random.choice([
        "Why don’t skeletons fight each other? Because they don’t have the guts!",
        "Parallel lines have so much in common. It’s a shame they’ll never meet.",
        "Why did the math book look sad? Because it had too many problems.",
        "I told my computer I needed a break, and it said: 'You seem stressed. Would you like to open Chrome?'",
        "Why do Java developers wear glasses? Because they don’t see sharp.",
    ])

def take_screenshot():
    try:
        import pyautogui
        save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        os.makedirs(save_dir, exist_ok=True)
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = os.path.join(save_dir, f"screenshot_{now}.png")
        pyautogui.screenshot(save_path)
        return f"✅ Screenshot saved to {save_path}"
    except Exception as e:
        return f"Error taking screenshot: {e}"

def check_internet_speed():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
        ping = st.results.ping
        return f"Your download speed is {download:.2f} Mbps, upload speed is {upload:.2f} Mbps, and ping is {ping:.0f} ms."
    except Exception as e:
        return f"Error checking internet speed: {e}"

def close_application(app_name):
    targets = {
        "notepad": ["notepad.exe"],
        "calc": ["calculator.exe", "calculatorapp.exe"],
        "browser": ["chrome.exe", "msedge.exe"],
        "vscode": ["code.exe"],
        "explorer": ["explorer.exe"],
        "whatsapp": ["whatsapp.exe"],
        "word": ["winword.exe"],
        "excel": ["excel.exe"],
        "powerpoint": ["powerpnt.exe"],
    }.get(app_name)
    if not targets:
        return False
    closed_any = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() in targets:
                proc.terminate()
                closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return closed_any

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
        print("WebSocket closed:", e)

if __name__ == "__main__":
    print("🎙️  Starting backend on ws://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
