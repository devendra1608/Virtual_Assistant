
import os
import subprocess
import psutil
from datetime import datetime

def open_application(app_name):
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
        "spotify": ["cmd", "/c", "start", "spotify:"],
        "store": ["cmd", "/c", "start", "ms-windows-store:"],
    }
    
    if app_name in open_map:
        subprocess.Popen(open_map[app_name])
        return True
    return False

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
        "spotify": ["spotify.exe"],
        "store": ["WinStore.App.exe", "WindowsStore.exe"],
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