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

# ---------------------------------------
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

    # --- OPEN commands ---
    if "open" in t:
        if "notepad" in t: return "open_app", "notepad"
        if "calculator" in t or "calc" in t: return "open_app", "calc"
        if "browser" in t or "chrome" in t or "edge" in t: return "open_app", "browser"
        if "vs code" in t or "visual studio code" in t: return "open_app", "vscode"
        if "file explorer" in t or "explorer" in t: return "open_app", "explorer"
        if "youtube" in t: return "open_app", "youtube"
        if "downloads" in t: return "open_app", "downloads"
        if "documents" in t: return "open_app", "documents"
        if "whatsapp" in t: return "open_app", "whatsapp"
        if "word" in t: return "open_app", "word"
        if "excel" in t: return "open_app", "excel"
        if "powerpoint" in t or "power point" in t: return "open_app", "powerpoint"

    # --- CLOSE commands ---
    if "close" in t:
        if "notepad" in t: return "close_app", "notepad"
        if "calculator" in t or "calc" in t: return "close_app", "calc"
        if "browser" in t or "chrome" in t or "edge" in t: return "close_app", "browser"
        if "vs code" in t or "visual studio code" in t: return "close_app", "vscode"
        if "file explorer" in t or "explorer" in t: return "close_app", "explorer"
        if "whatsapp" in t: return "close_app", "whatsapp"
        if "word" in t: return "close_app", "word"
        if "excel" in t: return "close_app", "excel"
        if "powerpoint" in t or "power point" in t: return "close_app", "powerpoint"

    # --- Jokes ---
    if any(x in t for x in ["joke", "funny", "make me laugh", "say something funny"]):
        return "tell_joke", None

    # --- Time ---
    if "time" in t:
        return "tell_time", None

    # --- Date ---
    if "date" in t:
        return "tell_date", None

    # --- Battery ---
    if "battery" in t:
        return "battery_status", None

    # --- Wi-Fi ---
    if "wi-fi" in t or "wifi" in t:
        return "wifi_name", None

    # --- System info ---
    if any(x in t for x in ["system specification", "system info", "specs"]):
        return "system_specs", None
    
    # --- Screenshot ---
    if any(x in t for x in ["screenshot", "take screenshot", "capture screen", "take a picture of screen"]):
        return "take_screenshot", None


    # --- Internet speed ---
    if any(x in t for x in [
        "internet speed", "check my internet", "speed test", "check speed",
        "how fast is my internet", "test connection speed"
    ]):
        return "check_speed", None

    return None, None

# ---------------- ACTION HANDLERS ----------------
def perform_action(intent, param):
    try:
        if intent == "open_app":
            if param == "notepad":
                subprocess.Popen(["notepad.exe"])
                return "Opened Notepad."
            elif param == "calc":
                subprocess.Popen(["calc.exe"])
                return "Opened Calculator."
            elif param == "browser":
                webbrowser.open("https://www.google.com")
                return "Opened your browser."
            elif param == "vscode":
                subprocess.Popen(["cmd", "/c", "start code"])
                return "Opened Visual Studio Code."
            elif param == "explorer":
                subprocess.Popen(["explorer"])
                return "Opened File Explorer."
            elif param == "youtube":
                webbrowser.open("https://www.youtube.com")
                return "Opened YouTube."
            elif param == "downloads":
                path = os.path.join(os.path.expanduser("~"), "Downloads")
                subprocess.Popen(["explorer", path])
                return "Opened Downloads folder."
            elif param == "documents":
                path = os.path.join(os.path.expanduser("~"), "Documents")
                subprocess.Popen(["explorer", path])
                return "Opened Documents folder."
            elif param == "whatsapp":
                subprocess.Popen(["cmd", "/c", "start whatsapp:"])
                return "Opened WhatsApp."
            elif param == "word":
                subprocess.Popen(["cmd", "/c", "start winword"])
                return "Opened Microsoft Word."
            elif param == "excel":
                subprocess.Popen(["cmd", "/c", "start excel"])
                return "Opened Microsoft Excel."
            elif param == "powerpoint":
                subprocess.Popen(["cmd", "/c", "start powerpnt"])
                return "Opened Microsoft PowerPoint."

        elif intent == "close_app":
            closed = close_application(param)
            if closed:
                return f"Closed {param.title()}."
            else:
                return f"{param.title()} was not running."

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

# ---------------- JOKE FETCHING ----------------
def get_joke():
    url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,sexist,racist"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("type") == "single":
            return data.get("joke")
        elif data.get("type") == "twopart":
            return f"{data.get('setup')} ... {data.get('delivery')}"
    except:
        pass
    fallback_jokes = [
        "Why don’t skeletons fight each other? Because they don’t have the guts!",
        "Parallel lines have so much in common. It’s a shame they’ll never meet.",
        "Why did the math book look sad? Because it had too many problems.",
        "I told my computer I needed a break, and it said: 'You seem stressed. Would you like to open Chrome?'",
        "Why do Java developers wear glasses? Because they don’t see sharp.",
    ]
    return random.choice(fallback_jokes)

def take_screenshot():
    try:
        import pyautogui
        from datetime import datetime

        # Path to your original Screenshots folder
        save_dir = r"C:\Users\kolli\OneDrive\Pictures\Screenshots"

        # Ensure folder exists
        os.makedirs(save_dir, exist_ok=True)

        # Create filename with timestamp
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = os.path.join(save_dir, f"screenshot_{now}.png")

        # Capture and save screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)

        return f"✅ Screenshot saved to {save_path}"
    except Exception as e:
        return f"Error taking screenshot: {e}"


# ---------------- INTERNET SPEED TEST ----------------
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

# ---------------- CLOSE APP HELPER ----------------
def close_application(app_name):
    process_map = {
        "notepad": ["notepad.exe", "notepad"],
        "calc": ["calculatorapp.exe", "calculator.exe", "applicationframehost.exe"],
        "browser": ["chrome.exe", "msedge.exe"],
        "vscode": ["code.exe", "Code.exe"],
        "explorer": ["explorer.exe"],
        "whatsapp": ["whatsapp.exe", "WhatsApp.exe"],
        "word": ["winword.exe", "WINWORD.EXE"],
        "excel": ["excel.exe", "EXCEL.EXE"],
        "powerpoint": ["powerpnt.exe", "POWERPNT.EXE"],
    }

    targets = process_map.get(app_name)
    if not targets:
        return False

    closed_any = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pname = proc.info['name']
            if pname and any(pname.lower() == t.lower() for t in targets):
                proc.terminate()
                closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not closed_any:
        for target in targets:
            try:
                subprocess.run(["taskkill", "/F", "/IM", target],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                closed_any = True
            except Exception:
                pass

    return closed_any

# ---------------- FastAPI SERVER ----------------
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

if __name__ == "__main__":
    print("🎙️  Starting backend on ws://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
