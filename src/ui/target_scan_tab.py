"""
OSINT-Nexus Target Scan Tab
Input form and scan controls for OSINT operations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QSlider, QGroupBox, QScrollArea, QFrame, QGridLayout,
    QProgressBar, QTextEdit, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .styles import COLORS


class DroppableLineEdit(QLineEdit):
    """QLineEdit that accepts file drops."""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def  dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                self.setText(path)
                self.file_dropped.emit(path)


class TargetScanTab(QWidget):
    """Target scan input form and controls."""
    
    # Signal emitted when scan is requested
    scan_requested = pyqtSignal(dict)  # scan_input dict
    cancel_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._is_scanning = False
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create splitter for form and log
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # === Top Section: Input Form ===
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("🎯 Target Configuration")
        header.setObjectName("headingLabel")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        form_layout.addWidget(header)
        
        subtitle = QLabel("Configure your OSINT scan parameters")
        subtitle.setObjectName("subheadingLabel")
        form_layout.addWidget(subtitle)
        
        # Create scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # === Smart Input Bar ===
        input_group = QGroupBox("Target Input")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(12)
        
        # Row 1: Type + Platform
        type_row = QHBoxLayout()
        
        type_label = QLabel("Type:")
        self.target_type = QComboBox()
        self.target_type.addItems([
            "Username", "Email", "Phone", "Domain", "IP Address", "File"
        ])
        self.target_type.currentTextChanged.connect(self._on_type_changed)
        
        # Platform selector (for Username)
        self.platform_label = QLabel("Platform:")
        self.platform_combo = QComboBox()
        self.platform_combo.addItems([
            "Generic (Sherlock)", 
            "GitHub", 
            "Steam",
            "Instagram", 
            "Twitter", 
            "LinkedIn",
            "Reddit"
        ])
        
        type_row.addWidget(type_label)
        type_row.addWidget(self.target_type, 1) # Stretch type
        type_row.addWidget(self.platform_label)
        type_row.addWidget(self.platform_combo, 1)
        
        input_layout.addLayout(type_row)
        
        # Row 2: Input Value
        self.value_input = DroppableLineEdit()
        self.value_input.setPlaceholderText("Enter username, domain, or drag & drop file...")
        self.value_input.setMinimumHeight(42)
        font = QFont("Segoe UI", 11)
        self.value_input.setFont(font)
        self.value_input.returnPressed.connect(self._on_scan_clicked)
        self.value_input.file_dropped.connect(self._on_file_dropped)
        
        input_layout.addWidget(self.value_input)
        
        scroll_layout.addWidget(input_group)
        
        # Store references to removed fields to avoid getattr errors if any
        # (Though we are cleaning the class, so it should be fine if we remove usage in methods too)
        
        # === Data Sources ===
        sources_group = QGroupBox("Data Sources")
        sources_layout = QGridLayout(sources_group)
        sources_layout.setSpacing(12)
        
        self.source_checkboxes = {}
        sources = [
            ("Google", True), ("Bing", True), ("DuckDuckGo", False),
            ("LinkedIn", False), ("GitHub", True), ("Twitter", False),
            ("Instagram", False), ("Reddit", True), ("YouTube", False),
            ("Shodan", False), ("VirusTotal", False), ("HaveIBeenPwned", False),
        ]
        
        for i, (source, default) in enumerate(sources):
            cb = QCheckBox(source)
            cb.setChecked(default)
            self.source_checkboxes[source.lower()] = cb
            sources_layout.addWidget(cb, i // 4, i % 4)
        
        scroll_layout.addWidget(sources_group)
        
        # === Scan Settings ===
        settings_group = QGroupBox("Scan Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Result Limit
        limit_layout = QHBoxLayout()
        limit_label = QLabel("Result Limit:")
        self.limit_slider = QSlider(Qt.Orientation.Horizontal)
        self.limit_slider.setMinimum(10)
        self.limit_slider.setMaximum(200)
        self.limit_slider.setValue(50)
        self.limit_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.limit_slider.setTickInterval(20)
        self.limit_value = QLabel("50")
        self.limit_value.setMinimumWidth(40)
        self.limit_slider.valueChanged.connect(
            lambda v: self.limit_value.setText(str(v))
        )
        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self.limit_slider, 1)
        limit_layout.addWidget(self.limit_value)
        settings_layout.addLayout(limit_layout)
        
        # Scan Depth
        depth_layout = QHBoxLayout()
        depth_label = QLabel("Scan Depth:")
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setMinimum(1)
        self.depth_slider.setMaximum(5)
        self.depth_slider.setValue(2)
        self.depth_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.depth_slider.setTickInterval(1)
        self.depth_value = QLabel("2")
        self.depth_value.setMinimumWidth(40)
        self.depth_slider.valueChanged.connect(
            lambda v: self.depth_value.setText(str(v))
        )
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.depth_slider, 1)
        depth_layout.addWidget(self.depth_value)
        settings_layout.addLayout(depth_layout)
        
        scroll_layout.addWidget(settings_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        form_layout.addWidget(scroll, 1)
        
        # === Action Buttons ===
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_inputs)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        
        self.scan_btn = QPushButton("🚀 Run Full Scan")
        self.scan_btn.setObjectName("scanButton")
        self.scan_btn.setMinimumWidth(180)
        self.scan_btn.setMinimumHeight(48)
        self.scan_btn.clicked.connect(self._on_scan_clicked)
        button_layout.addWidget(self.scan_btn)
        
        form_layout.addLayout(button_layout)
        
        splitter.addWidget(form_container)
        
        # === Bottom Section: Progress and Log ===
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress section
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m modules")
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to scan")
        self.status_label.setObjectName("subheadingLabel")
        progress_layout.addWidget(self.status_label)
        
        log_layout.addWidget(progress_group)
        
        # Log output
        log_group = QGroupBox("Scan Log")
        log_inner = QVBoxLayout(log_group)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setPlaceholderText("Scan results will appear here...")
        self.log_output.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        log_inner.addWidget(self.log_output)
        
        log_layout.addWidget(log_group)
        
        splitter.addWidget(log_container)
        splitter.setSizes([500, 200])
        
        layout.addWidget(splitter)
    
    def _on_type_changed(self, text):
        """Handle target type change."""
        # Show platform combo only for Username
        is_username = text == "Username"
        self.platform_label.setVisible(is_username)
        self.platform_combo.setVisible(is_username)
        
        # Update placeholder
        placeholders = {
            "Username": "Enter username (e.g. johndoe)",
            "Email": "Enter email (e.g. user@example.com)",
            "Phone": "Enter phone (e.g. +15550000000)",
            "Domain": "Enter domain (e.g. example.com)",
            "IP Address": "Enter IP (e.g. 192.168.1.1)"
        }
        self.value_input.setPlaceholderText(placeholders.get(text, "Enter target..."))

    def _on_file_dropped(self, path: str):
        """Handle file drop event."""
        # Auto-switch to File type
        index = self.target_type.findText("File")
        if index >= 0:
            self.target_type.setCurrentIndex(index)
            
    def _on_scan_clicked(self):
        """Handle scan button click."""
        value = self.value_input.text().strip()
        if not value:
            return
            
        target_type = self.target_type.currentText().lower()
        platform = self.platform_combo.currentText()
        
        # Construct scan input
        scan_input = {
            "type": target_type,
            "value": value,
            "platform": platform,
            "sources": []
        }
        
        # Collect selected sources
        for source, cb in self.source_checkboxes.items():
            if cb.isChecked():
                scan_input["sources"].append(source)
                
        self.scan_requested.emit(scan_input)
        
    def _clear_inputs(self):
        """Clear all input fields."""
        self.value_input.clear()
        self.target_type.setCurrentIndex(0)
        self.log_output.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to scan")
    
    def _on_scan_clicked(self):
        """Handle scan button click."""
        if self._is_scanning:
            self.cancel_requested.emit()
            return
            
        target_val = self.value_input.text().strip()
        if not target_val:
            self.log_message("Please enter a target value.", "error")
            return

        # Map smart input to ScanInput fields
        scan_input = {
            "target_type": self.target_type.currentText(),
            "username": "", "email": "", "phone": "", "domain": "", "ip_address": "",
            "platform": "",
            "sources": [
                name for name, cb in self.source_checkboxes.items()
                if cb.isChecked()
            ],
            "limit": self.limit_slider.value(),
            "depth": self.depth_slider.value(),
        }
        
        t_type = self.target_type.currentText()
        if t_type == "Username":
            scan_input["username"] = target_val
            scan_input["platform"] = self.platform_combo.currentText()
        elif t_type == "Email":
            scan_input["email"] = target_val
        elif t_type == "Phone":
            scan_input["phone"] = target_val
        elif t_type == "Domain":
            scan_input["domain"] = target_val
        elif t_type == "IP Address":
            scan_input["ip_address"] = target_val
        
        # Emit scan request
        self.scan_requested.emit(scan_input)
    
    def set_scanning(self, is_scanning: bool):
        """Update UI for scanning state."""
        self._is_scanning = is_scanning
        if is_scanning:
            self.scan_btn.setText("⏹ Cancel Scan")
            self.scan_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f85149, stop:1 #da3633);
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 14px 32px;
                    font-size: 14px;
                    font-weight: 600;
                }
            """)
        else:
            self.scan_btn.setText("🚀 Run Full Scan")
            self.scan_btn.setStyleSheet("")  # Reset to default
    
    def update_progress(self, completed: int, total: int, current_module: str):
        """Update progress bar and status."""
        if total > 0:
            percent = int((completed / total) * 100)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(completed)
            self.progress_bar.setFormat(f"%p% - {completed}/{total} modules")
        
        if current_module:
            self.status_label.setText(f"Running: {current_module}")
        elif completed >= total:
            self.status_label.setText("Scan completed!")
    
    def log_message(self, message: str, level: str = "info"):
        """Add message to log output."""
        colors = {
            "info": COLORS["text_primary"],
            "success": COLORS["accent_success"],
            "warning": COLORS["accent_warning"],
            "error": COLORS["accent_danger"],
        }
        color = colors.get(level, COLORS["text_primary"])
        
        self.log_output.append(
            f'<span style="color: {color}">{message}</span>'
        )
        # Scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
