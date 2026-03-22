import os
import sys
import json
import datetime
import time
import gc
from instagram_manager import InstagramManager
import config

# We need a cross-platform way to notify that doesn't require a constant UI event loop
try:
    from plyer import notification
    HAS_NOTIFICATION = True
except ImportError:
    HAS_NOTIFICATION = False

def send_notification(title, message):
    if HAS_NOTIFICATION:
        notification.notify(
            title=title,
            message=message,
            app_name='ReelPilot',
            timeout=10
        )
    else:
        print(f"[{title}] {message}")

def run_scheduler():
    now = datetime.datetime.now()
    current_time_str = now.strftime("%I:%M %p") # e.g., "09:30 PM"
    # Normalize to match the hh:mm AP format (09:30 PM)
    # Actually QTime uses "hh:mm AP" which is 09:30 PM
    
    today_str = now.strftime("%Y-%m-%d")
    
    # Load scenarios
    scenarios = config.load_scenarios()
    
    # We need a way to track "already executed today" without a running app.
    # We need a way to track "already executed today" without a running app.
    log_file = os.path.join(config.DATA_DIR, "executed_log.json")
    executed_data = {}
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            executed_data = json.load(f)

    for s in scenarios:
        # ... rest remains logic ...
        username = s["username"]
        schedules = s.get("schedule", [])
        
        if username not in executed_data or executed_data[username].get("date") != today_str:
            executed_data[username] = {"date": today_str, "times": []}

        for sched_time in schedules:
            if sched_time.lstrip('0') == current_time_str.lstrip('0'):
                if sched_time not in executed_data[username]["times"]:
                    def safe_log(msg):
                        try:
                            # Log to terminal if possible, otherwise write to a background log file
                            with open(os.path.join(config.DATA_DIR, "background_runner.log"), "a", encoding="utf-8") as lf:
                                lf.write(f"[{datetime.datetime.now()}] {msg}\n")
                        except:
                            pass
                    
                    safe_log(f"Triggering scheduled upload for @{username} at {sched_time}...")
                    
                    mgr = InstagramManager(username)
                    try:
                        if mgr.login():
                            success = mgr.upload_one_video(
                                s["folder_path"], 
                                s["captions"], 
                                log_callback=safe_log
                            )
                            if success:
                                executed_data[username]["times"].append(sched_time)
                                send_notification("ReelPilot: Auto-Upload Success", f"Successfully posted to @{username}")
                            else:
                                send_notification("ReelPilot: Auto-Upload Failed", f"Check logs for @{username}")
                        else:
                            send_notification("ReelPilot: Login Required", f"Account @{username} needs re-authentication.")
                    except Exception as e:
                        send_notification("ReelPilot: Error", str(e))
                    
                    del mgr
                    gc.collect()

    # Save execution log
    with open(log_file, "w") as f:
        json.dump(executed_data, f, indent=4)


if __name__ == "__main__":
    run_scheduler()
