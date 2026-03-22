# REELPILOT 🌑🌑
### Premium Monochrome Instagram Reels Automation

REELPILOT is a minimalist desktop application designed for serious content creators. It automates the process of uploading Instagram Reels with a focus on speed, reliability, and set-and-forget background execution.

---

## 🚀 DOWNLOAD
**[Download ReelPilot.exe (Windows Standard)](file:///c:/code%20playground/ReelPilot/dist/ReelPilot.exe)**
*No Python installation required. Just download and execute.*

---

## 🌟 KEY FEATURES
- **🌑 Minimalist Monochrome UI**: A high-contrast Black & White command center designed for precision and focus.
- **⚙️ Windows Task Scheduler Integration**: "Sync" your scenarios with Windows to "wake up" and upload even when the application is closed.
- **⏰ Smart Dual Scheduling**: Set up to **2 execution times per day** for each Instagram scenario.
- **🕵️ Silent Background Execution**: Runs as a native background process with live Windows Desktop notifications.
- **🛡️ "Industrial" File Management**: Innovative **Move-before-Delete** strategy to overcome Windows file-locks and ensure clean folder maintenance.
- **🔒 Secure Session Handling**: Passwords are only used once; subsequent logins use encrypted local session files.

---

## 🛠️ HOW TO USE
1.  **Launch**: Open `ReelPilot.exe`.
2.  **Add Scenario**: 
    -   Enter your **Instagram Username** and **Password** (initial login only).
    -   Select a **Local Folder** where your `.mp4` reels are stored.
    -   Type your **Captions**.
3.  **Set Times**: Pick your times (e.g., `09:30 AM`, `05:00 PM`).
4.  **Sync**: Click **"Sync Windows Scheduler"**. 
5.  **Go Live**: Close the app. ReelPilot will now "wake up" at those exact times, upload one video from your folder, and notify you instantly.

---

## 📘 TECHNICAL DETAILS
- **Engine**: Built with `PyQt6` and powered by the `instagrapi` private API mimicry.
- **Background Mode**: Registers a recurring task in `schtasks` (Windows Task Scheduler) that fires every minute to check your local `scenarios.json` logic.
- **Notifications**: Uses `plyer` for native OS system tray messages.

---

## ⚠️ RECOMMENDATIONS
- **Video Format**: Use **MP4** (H.264/AAC) at **1080x1920** for the best result.
- **Stability**: For maximum reliability, run the application as **Administrator** once to ensure it has permission to register background tasks in Windows.
- **Responsible Use**: We recommend no more than 2 uploads per day per account to maintain a high trust score with Instagram's protective systems.

---

Built by **Vinayak Shukla** 🌿
*A focused tool for focused creators.*
