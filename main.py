import utils.http_session
import utils.transport
import utils.session
import moviepy
try:
    import moviepy.editor as mp
    moviepy.VideoFileClip = mp.VideoFileClip
    moviepy.AudioFileClip = mp.AudioFileClip
    print("🎬 MoviePy Engine Linked Successfully")
except Exception as e:
    print(f"⚠️ MoviePy linkage warning: {e}")

import sys
import os
import time
import gc
import json
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QScrollArea, QFrame, QTextEdit, 
    QProgressBar, QMessageBox, QSpacerItem, QSizePolicy,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer, QDateTime
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction

import config
import ui_components
from instagram_manager import InstagramManager
import cli_runner

class ExecutionThread(QThread):
    progress_signal = pyqtSignal(int, int) 
    log_signal = pyqtSignal(str)           
    finished_signal = pyqtSignal()         

    def __init__(self, scenario):
        super().__init__()
        self.scenario = scenario
        self.mgr = InstagramManager(scenario["username"])

    def run(self):
        self.log_signal.emit(f"Starting execution for @{self.scenario['username']}...")
        try:
            if not self.mgr.login():
                self.log_signal.emit("CRITICAL: Login failed! Check credentials.")
                return
            self.log_signal.emit("Successfully authenticated.")
        except Exception as e:
            self.log_signal.emit(f"Login error: {str(e)}")
            return

        def progress_cb(current, total): self.progress_signal.emit(current, total)
        def log_cb(msg): self.log_signal.emit(msg)

        try:
            self.mgr.upload_one_video(
                self.scenario["folder_path"], 
                self.scenario["captions"], 
                progress_callback=progress_cb,
                log_callback=log_cb
            )
        except Exception as e:
            self.log_signal.emit(f"Upload error: {str(e)}")
        
        del self.mgr
        gc.collect()
        self.finished_signal.emit()

class LogSignaler(QObject):
    log_signal = pyqtSignal(str)

class StdoutRedirector:
    def __init__(self, signaler):
        self.signaler = signaler
    def write(self, text):
        if text.strip(): self.signaler.log_signal.emit(text.strip())
    def flush(self): pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("REELPILOT")
        self.setMinimumSize(950, 650)
        self.setStyleSheet(ui_components.DARK_STYLESHEET)
        
        self.log_signaler = LogSignaler()
        self.log_signaler.log_signal.connect(self.add_log)
        sys.stdout = StdoutRedirector(self.log_signaler)
        
        self.init_ui()
        self.init_tray()
        self.refresh_scenarios()
        
        self.scheduler_timer = QTimer()
        self.scheduler_timer.timeout.connect(self.check_schedules)
        self.scheduler_timer.start(30000)
        self.executed_today = {} 

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("REELPILOT")
        title_label.setObjectName("Title")
        
        task_btn = QPushButton("Sync Windows Scheduler")
        task_btn.setStyleSheet("background-color: #000000; border: 1px solid #333333; color: #888888; font-size: 11px;")
        task_btn.clicked.connect(self.register_windows_task)
        
        add_btn = QPushButton("+ New Scenario")
        add_btn.setObjectName("ActionButton")
        add_btn.clicked.connect(self.open_add_scenario)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(task_btn)
        header_layout.addWidget(add_btn)
        left_layout.addLayout(header_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scenario_container = QWidget()
        self.scenario_layout = QVBoxLayout(self.scenario_container)
        self.scenario_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scenario_container)
        left_layout.addWidget(self.scroll_area)
        main_layout.addLayout(left_layout, 2)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        status_label = QLabel("SYSTEM MONITOR")
        status_label.setStyleSheet("font-weight: 900; font-size: 14px; color: #FFFFFF; border-bottom: 1px solid #222222; padding-bottom: 5px;")
        right_layout.addWidget(status_label)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        right_layout.addWidget(self.log_output)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)
        main_layout.addLayout(right_layout, 1)

    def register_windows_task(self):
        exe_path = sys.executable
        task_name = "ReelPilot_AutoRun"
        # Command for the bundled EXE
        tr_command = f'\\"{exe_path}\\" --cli' if exe_path.endswith(".exe") else f'python \\"{os.path.abspath(__file__)}\\" --cli'
        command = f'schtasks /create /tn "{task_name}" /tr "{tr_command}" /sc minute /mo 1 /f'
        try:
            subprocess.run(command, shell=True, check=True)
            QMessageBox.information(self, "Success", "Synced with Windows Scheduler!")
        except Exception as e:
            QMessageBox.critical(self, "Failed", str(e))

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_ComputerIcon))
        tray_menu = QMenu()
        show_action = QAction("Show", self); show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Exit", self); quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(show_action); tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def notify(self, title, message):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

    def refresh_scenarios(self):
        for i in reversed(range(self.scenario_layout.count())):
            w = self.scenario_layout.itemAt(i).widget()
            if w: w.setParent(None)
        
        # Use absolute path from config
        history = {}
        log_file = os.path.join(config.DATA_DIR, "executed_log.json")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f: history = json.load(f)
            except: pass

        scenarios = config.load_scenarios()
        for s in scenarios:
            card = ui_components.ScenarioCard(s, history=history.get(s["username"]))
            card.execute_signal.connect(self.execute_scenario)
            card.edit_signal.connect(self.edit_scenario)
            card.delete_signal.connect(self.delete_scenario)
            self.scenario_layout.addWidget(card)

    def open_add_scenario(self):
        dialog = ui_components.AddScenarioDialog(self)
        if dialog.exec() == ui_components.QDialog.DialogCode.Accepted:
            self.handle_save_and_login(dialog.get_data())

    def handle_save_and_login(self, data):
        mgr = InstagramManager(data["username"])
        try:
            if mgr.login(data["password"]):
                config.add_scenario(data["username"], data["folder_path"], data["captions"], data.get("schedule", []))
                self.refresh_scenarios()
            else: QMessageBox.critical(self, "Failed", "Login failed.")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def edit_scenario(self, scenario_dict):
        dialog = ui_components.AddScenarioDialog(self, editing_data=scenario_dict)
        if dialog.exec() == ui_components.QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            config.add_scenario(data["username"], data["folder_path"], data["captions"], data.get("schedule", []))
            self.refresh_scenarios()

    def delete_scenario(self, username):
        if QMessageBox.question(self, "Confirm", f"Delete @{username}?") == QMessageBox.StandardButton.Yes:
            config.delete_scenario(username)
            self.refresh_scenarios()

    def add_log(self, message):
        self.log_output.append(message)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress(self, current, total):
        if current == -1: self.progress_bar.setMaximum(0); self.progress_bar.setValue(0)
        else: self.progress_bar.setMaximum(total); self.progress_bar.setValue(current)

    def check_schedules(self):
        now = QDateTime.currentDateTime()
        current_time_str = now.toString("hh:mm AP")
        today_str = now.toString("yyyy-MM-dd")
        scenarios = config.load_scenarios()
        for s in scenarios:
            un = s["username"]
            if un not in self.executed_today or self.executed_today[un].get("date") != today_str:
                self.executed_today[un] = {"date": today_str, "times": []}
            for st in s.get("schedule", []):
                if st == current_time_str and st not in self.executed_today[un]["times"]:
                    self.executed_today[un]["times"].append(st)
                    self.execute_scenario(un, is_auto=True)

    def execute_scenario(self, username, is_auto=False):
        scenarios = config.load_scenarios()
        scenario = next((s for s in scenarios if s["username"] == username), None)
        if not scenario: return
        self.update_progress(-1, 0)
        self.add_log(f"{'🤖 Auto' if is_auto else '👤 Manual'} run: @{username}")
        self.exec_thread = ExecutionThread(scenario)
        self.exec_thread.log_signal.connect(self.add_log)
        self.exec_thread.progress_signal.connect(self.update_progress)
        def fin():
            self.add_log("Done."); self.update_progress(1, 1)
            if is_auto: self.notify("ReelPilot", f"Finished: @{username}")
        self.exec_thread.finished_signal.connect(fin)
        self.exec_thread.start()

if __name__ == "__main__":
    if "--cli" in sys.argv: cli_runner.run_scheduler()
    else:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
