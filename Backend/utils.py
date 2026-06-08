
import psutil
import subprocess
import re
import platform
import requests
import random
import speedtest
from datetime import datetime

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