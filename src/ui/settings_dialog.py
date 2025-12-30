from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QLineEdit, QFormLayout, QPushButton, QSpinBox, 
    QCheckBox
)
from PyQt6.QtCore import Qt

from ..config import config

class SettingsDialog(QDialog):
    """Dialog for application settings and API keys."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._init_ui()
        self._load_settings()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_api_tab(), "API Keys")
        self.tabs.addTab(self._create_scan_tab(), "Scan Settings")
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #2d2d2d; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QLineEdit { background-color: #3d3d3d; color: #ffffff; border: 1px solid #555; padding: 5px; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: #aaa; padding: 8px 12px; }
            QTabBar::tab:selected { background: #444; color: #fff; }
            QPushButton { background-color: #0d6efd; color: white; border: none; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #0b5ed7; }
        """)

    def _create_api_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)
        
        self.api_inputs = {}
        
        # Add API fields
        keys = [
            ("🤖 Gemini API Key", "gemini"),
            ("🔓 HaveIBeenPwned API Key", "haveibeenpwned"),
            ("Shodan API Key", "shodan"),
            ("VirusTotal API Key", "virustotal"),
            ("Hunter.io API Key", "hunter_io"),
            ("OpenCage API Key", "opencage"),
            ("NumVerify API Key", "numverify"),
            ("Google API Key", "google_api"),
            ("Google CSE ID", "google_cse_id")
        ]
        
        for label, key in keys:
            inp = QLineEdit()
            inp.setEchoMode(QLineEdit.EchoMode.Password)
            inp.setPlaceholderText(f"Enter {label}")
            layout.addRow(label, inp)
            self.api_inputs[key] = inp
            
        return widget
        
    def _create_scan_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.scan_inputs = {}
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setSuffix(" sec")
        layout.addRow("Request Timeout:", self.timeout_spin)
        self.scan_inputs["timeout"] = self.timeout_spin
        
        # Max Threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 50)
        layout.addRow("Max Threads:", self.threads_spin)
        self.scan_inputs["max_threads"] = self.threads_spin
        
        return widget
        
    def _load_settings(self):
        """Load current settings into UI."""
        # API Keys
        api_keys = config.get("api_keys")
        for key, inp in self.api_inputs.items():
            inp.setText(api_keys.get(key, ""))
            
        # Scan Settings
        scan_settings = config.get("scan")
        self.scan_inputs["timeout"].setValue(scan_settings.get("timeout", 30))
        self.scan_inputs["max_threads"].setValue(scan_settings.get("max_threads", 10))
        
    def _save_settings(self):
        """Save UI values to config."""
        # API Keys
        for key, inp in self.api_inputs.items():
            config.set("api_keys", key, inp.text().strip())
            
        # Scan Settings
        config.set("scan", "timeout", self.scan_inputs["timeout"].value())
        config.set("scan", "max_threads", self.scan_inputs["max_threads"].value())
        
        config.save()
        self.accept()
