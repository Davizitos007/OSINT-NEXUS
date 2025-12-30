"""
OSINT-Nexus - Main Entry Point
Cross-platform OSINT gathering and visualization application.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main entry point for OSINT-Nexus application."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QPalette, QColor
    
    # Enable high DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("OSINT-Nexus")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("OSINT-Nexus")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Set dark palette as base
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#58a6ff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1f6feb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    
    # Import and create main window
    from src.ui.main_window import MainWindow
    
    # Show disclaimer
    from PyQt6.QtWidgets import QMessageBox
    disclaimer = QMessageBox()
    disclaimer.setWindowTitle("OSINT-Nexus - Legal Disclaimer")
    disclaimer.setIcon(QMessageBox.Icon.Information)
    disclaimer.setText(
        "<h3>⚠️ Legal Disclaimer</h3>"
        "<p>OSINT-Nexus is designed for <b>legitimate security research</b> "
        "and <b>authorized penetration testing</b> only.</p>"
        "<p>By using this application, you agree to:</p>"
        "<ul>"
        "<li>Only gather information you are authorized to access</li>"
        "<li>Comply with all applicable laws and regulations</li>"
        "<li>Use gathered information responsibly and ethically</li>"
        "</ul>"
        "<p>The developers are not responsible for any misuse of this tool.</p>"
    )
    disclaimer.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    disclaimer.setDefaultButton(QMessageBox.StandardButton.Ok)
    
    # Apply dark style to disclaimer
    disclaimer.setStyleSheet("""
        QMessageBox {
            background-color: #0d1117;
            color: #e6edf3;
        }
        QMessageBox QLabel {
            color: #e6edf3;
        }
        QPushButton {
            background-color: #21262d;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 24px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #30363d;
        }
        QPushButton:default {
            background-color: #238636;
            border-color: #2ea043;
        }
    """)
    
    result = disclaimer.exec()
    if result != QMessageBox.StandardButton.Ok:
        sys.exit(0)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
