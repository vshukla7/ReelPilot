import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QFileDialog, QDialog, QScrollArea, QFrame, 
    QTextEdit, QProgressBar, QMessageBox, QSpacerItem, QSizePolicy,
    QTimeEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTime
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

# Stylesheet for a "premium" Monochrome (Black & White) look
DARK_STYLESHEET = """
QWidget {
    background-color: #000000;
    color: #FFFFFF;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

QFrame#ScenarioCard {
    background-color: #0A0A0A;
    border-radius: 12px;
    border: 1px solid #222222;
    padding: 12px;
    margin-bottom: 12px;
}

QFrame#ScenarioCard:hover {
    border: 1px solid #FFFFFF;
    background-color: #111111;
}

QPushButton {
    background-color: #222222;
    color: #FFFFFF;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: bold;
    border: 1px solid #333333;
}

QPushButton:hover {
    background-color: #333333;
    border: 1px solid #444444;
}

QPushButton#ActionButton {
    background-color: #FFFFFF;
    color: #000000;
    border: none;
}

QPushButton#ActionButton:hover {
    background-color: #E0E0E0;
}

QPushButton#DeleteButton {
    background-color: #000000;
    color: #FF5252;
    border: 1px solid #330000;
}

QPushButton#DeleteButton:hover {
    background-color: #FF5252;
    color: #000000;
}

QLineEdit, QTextEdit, QTimeEdit {
    background-color: #111111;
    border: 1px solid #222222;
    border-radius: 8px;
    padding: 8px;
    color: #FFFFFF;
}

QLineEdit:focus, QTextEdit:focus, QTimeEdit:focus {
    border: 1px solid #FFFFFF;
}

QLabel#Title {
    font-size: 28px;
    font-weight: 900;
    letter-spacing: -1px;
    color: #FFFFFF;
}

QLabel#SubText {
    color: #888888;
    font-size: 13px;
}

QProgressBar {
    border: 1px solid #222222;
    border-radius: 6px;
    text-align: center;
    background-color: #0A0A0A;
    height: 12px;
}

QProgressBar::chunk {
    background-color: #FFFFFF;
    border-radius: 5px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}
"""

class ScenarioCard(QFrame):
    execute_signal = pyqtSignal(str) # username
    edit_signal = pyqtSignal(dict)   # scenario dict
    delete_signal = pyqtSignal(str) # username

    def __init__(self, scenario_dict, history=None):
        super().__init__()
        self.setObjectName("ScenarioCard")
        self.scenario = scenario_dict
        self.history = history
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Info side
        info_layout = QVBoxLayout()
        self.username_label = QLabel(f"@{self.scenario['username']}")
        self.username_label.setStyleSheet("font-weight: 800; font-size: 18px; color: #FFFFFF;")
        
        path_label = QLabel(f"📁 {os.path.basename(self.scenario['folder_path'])}")
        path_label.setObjectName("SubText")
        
        # Schedule info
        sched = self.scenario.get("schedule", [])
        sched_text = "⏰ Not Scheduled"
        if sched:
            sched_text = f"⏰ {', '.join(sched)}"
        sched_label = QLabel(sched_text)
        sched_label.setStyleSheet("font-size: 12px; color: #AAAAAA; font-weight: 500;")
        
        # History info
        hist_text = "⚪ No recent background activity"
        if self.history and self.history.get("times"):
            last_time = self.history["times"][-1]
            hist_text = f"⚫ Last Background Upload: {last_time} ({self.history['date']})"
        
        hist_label = QLabel(hist_text)
        hist_label.setStyleSheet("font-size: 11px; color: #666666; font-style: italic;")
        
        info_layout.addWidget(self.username_label)
        info_layout.addWidget(path_label)
        info_layout.addWidget(sched_label)
        info_layout.addWidget(hist_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()


        # Action buttons
        self.exec_btn = QPushButton("Execute Now")
        self.exec_btn.setObjectName("ActionButton")
        self.exec_btn.clicked.connect(lambda: self.execute_signal.emit(self.scenario["username"]))
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(lambda: self.edit_signal.emit(self.scenario))
        
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("DeleteButton")
        self.del_btn.clicked.connect(lambda: self.delete_signal.emit(self.scenario["username"]))
        
        layout.addWidget(self.exec_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.del_btn)

class AddScenarioDialog(QDialog):
    def __init__(self, parent=None, editing_data=None):
        super().__init__(parent)
        self.editing_data = editing_data
        self.setWindowTitle("Add Instagram Scenario" if not editing_data else "Edit Scenario")
        self.setMinimumWidth(450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Username
        layout.addWidget(QLabel("Instagram Username:"))
        self.username_input = QLineEdit()
        if self.editing_data:
            self.username_input.setText(self.editing_data["username"])
            self.username_input.setEnabled(False)
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Password (only for initial login):"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        # Folder Selection
        layout.addWidget(QLabel("Videos Folder:"))
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        if self.editing_data:
            self.folder_input.setText(self.editing_data["folder_path"])
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.browse_btn)
        layout.addLayout(folder_layout)
        
        # Captions
        layout.addWidget(QLabel("Captions (one per line):"))
        self.caption_input = QTextEdit()
        if self.editing_data:
            captions = self.editing_data["captions"]
            self.caption_input.setPlainText("\n".join(captions) if isinstance(captions, list) else captions)
        layout.addWidget(self.caption_input)
        
        # Scheduling
        layout.addWidget(QLabel("📅 Schedule Auto-Execution (Max 2/day):"))
        sched_layout = QHBoxLayout()
        
        self.time1 = QTimeEdit()
        self.time1.setDisplayFormat("hh:mm AP")
        self.time2 = QTimeEdit()
        self.time2.setDisplayFormat("hh:mm AP")
        
        self.use_time1 = QCheckBox("Time 1")
        self.use_time2 = QCheckBox("Time 2")
        
        if self.editing_data and "schedule" in self.editing_data:
            times = self.editing_data["schedule"]
            if len(times) > 0:
                self.use_time1.setChecked(True)
                self.time1.setTime(QTime.fromString(times[0], "hh:mm AP"))
            if len(times) > 1:
                self.use_time2.setChecked(True)
                self.time2.setTime(QTime.fromString(times[1], "hh:mm AP"))

        sched_layout.addWidget(self.use_time1)
        sched_layout.addWidget(self.time1)
        sched_layout.addWidget(self.use_time2)
        sched_layout.addWidget(self.time2)
        layout.addLayout(sched_layout)
        
        # Save Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Scenario")
        self.save_btn.setObjectName("ActionButton")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DeleteButton")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_input.setText(folder)

    def get_data(self):
        captions = self.caption_input.toPlainText().split("\n")
        captions = [c.strip() for c in captions if c.strip()]
        
        schedule = []
        if self.use_time1.isChecked():
            schedule.append(self.time1.time().toString("hh:mm AP"))
        if self.use_time2.isChecked():
            schedule.append(self.time2.time().toString("hh:mm AP"))
        
        return {
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "folder_path": self.folder_input.text(),
            "captions": captions if len(captions) > 1 else (captions[0] if captions else ""),
            "schedule": schedule
        }

