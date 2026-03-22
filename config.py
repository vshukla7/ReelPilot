import json
import os
import sys

# Crucial: Determine the application's base directory (works for both script and .exe)
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle (.exe)
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Running in normal Python environment
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
CONFIG_FILE = os.path.join(DATA_DIR, "scenarios.json")

def ensure_dirs():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR, exist_ok=True)

def load_scenarios():
    ensure_dirs()
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_scenarios(scenarios):
    ensure_dirs()
    with open(CONFIG_FILE, "w") as f:
        json.dump(scenarios, f, indent=4)

def add_scenario(username, folder_path, captions, schedule=None):
    scenarios = load_scenarios()
    for s in scenarios:
        if s["username"] == username:
            s["folder_path"] = folder_path
            s["captions"] = captions
            s["schedule"] = schedule if schedule else []
            save_scenarios(scenarios)
            return
    
    scenarios.append({
        "username": username,
        "folder_path": folder_path,
        "captions": captions,
        "schedule": schedule if schedule else []
    })
    save_scenarios(scenarios)

def delete_scenario(username):
    scenarios = load_scenarios()
    scenarios = [s for s in scenarios if s["username"] != username]
    save_scenarios(scenarios)
    
    session_file = os.path.join(SESSIONS_DIR, f"{username}.json")
    if os.path.exists(session_file):
        os.remove(session_file)
