# nlp.py
from utils import (
    get_time, get_date, get_joke, check_internet_speed, 
    get_battery_percentage, get_wifi_name, get_system_specs
)
from system_controls import open_application, close_application, take_screenshot

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
        "spotify": "spotify",
        "microsoft store": "store",
        "store": "store"
    }
    
    if "open" in t:
        for key, val in apps.items():
            if key in t:
                return "open_app", val

    if "close" in t:
        for key, val in apps.items():
            if key in t:
                return "close_app", val

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

def perform_action(intent, param):
    try:
        if intent == "open_app":
            opened = open_application(param)
            return f"Opened {param.title()}." if opened else f"Could not open {param}."
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