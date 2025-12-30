"""
OSINT-Nexus Dark Mode Styling
Modern dark theme with blue accents for PyQt6 application.
"""

# Dark Mode Color Palette
COLORS = {
    # Base colors
    "background_dark": "#0d1117",
    "background_medium": "#161b22",
    "background_light": "#21262d",
    "background_hover": "#30363d",
    
    # Text colors
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    
    # Accent colors
    "accent_primary": "#58a6ff",
    "accent_secondary": "#1f6feb",
    "accent_success": "#3fb950",
    "accent_warning": "#d29922",
    "accent_danger": "#f85149",
    
    # Border colors
    "border_default": "#30363d",
    "border_muted": "#21262d",
    
    # Entity type colors (for graph nodes)
    "entity_email": "#58a6ff",
    "entity_domain": "#3fb950",
    "entity_ip": "#f0883e",
    "entity_phone": "#a371f7",
    "entity_username": "#db61a2",
    "entity_person": "#79c0ff",
    "entity_company": "#56d364",
    "entity_subdomain": "#7ee787",
    "entity_hostname": "#ffa657",
    # New entity types for advanced features
    "entity_breach": "#f85149",
    "entity_leak": "#d29922",
    "entity_image": "#79c0ff",
    "entity_location": "#f0883e",
    "entity_device": "#a371f7",
    "entity_wallet": "#ffd700",
    "entity_transaction": "#56d364",
    "entity_social": "#db61a2",
}

# Main Application Stylesheet
DARK_STYLE = """
/* ==================== Global Styles ==================== */
QMainWindow, QDialog {
    background-color: #0d1117;
    color: #e6edf3;
}

QWidget {
    background-color: transparent;
    color: #e6edf3;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
    font-size: 13px;
}

/* ==================== Menu Bar ==================== */
QMenuBar {
    background-color: #161b22;
    color: #e6edf3;
    border-bottom: 1px solid #30363d;
    padding: 4px 0;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 2px;
}

QMenuBar::item:selected {
    background-color: #30363d;
}

QMenu {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
    margin: 2px;
}

QMenu::item:selected {
    background-color: #58a6ff;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #30363d;
    margin: 4px 8px;
}

/* ==================== Tab Widget ==================== */
QTabWidget::pane {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px;
}

QTabBar::tab {
    background-color: #21262d;
    color: #8b949e;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #30363d;
    border-bottom: none;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #0d1117;
    color: #e6edf3;
    border-bottom: 2px solid #58a6ff;
}

QTabBar::tab:hover:!selected {
    background-color: #30363d;
    color: #e6edf3;
}

/* ==================== Buttons ==================== */
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}

QPushButton:pressed {
    background-color: #161b22;
}

QPushButton:disabled {
    background-color: #161b22;
    color: #6e7681;
    border-color: #21262d;
}

/* Primary Action Button */
QPushButton#primaryButton, QPushButton[primary="true"] {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
}

QPushButton#primaryButton:hover, QPushButton[primary="true"]:hover {
    background-color: #2ea043;
    border-color: #3fb950;
}

/* Danger Button */
QPushButton#dangerButton, QPushButton[danger="true"] {
    background-color: #21262d;
    color: #f85149;
    border: 1px solid #f85149;
}

QPushButton#dangerButton:hover, QPushButton[danger="true"]:hover {
    background-color: #f85149;
    color: #ffffff;
}

/* Scan Button - Large primary action */
QPushButton#scanButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1f6feb, stop:1 #58a6ff);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 14px 32px;
    font-size: 14px;
    font-weight: 600;
    min-width: 160px;
}

QPushButton#scanButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #388bfd, stop:1 #79c0ff);
}

QPushButton#scanButton:disabled {
    background: #21262d;
    color: #6e7681;
}

/* ==================== Input Fields ==================== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #1f6feb;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #58a6ff;
    outline: none;
}

QLineEdit:disabled {
    background-color: #161b22;
    color: #6e7681;
}

QLineEdit::placeholder {
    color: #6e7681;
}

/* ==================== Combo Box ==================== */
QComboBox {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #8b949e;
}

QComboBox:focus {
    border-color: #58a6ff;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    padding-right: 8px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8b949e;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    selection-background-color: #58a6ff;
    outline: none;
}

/* ==================== Check Box ==================== */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #30363d;
    border-radius: 4px;
    background-color: #0d1117;
}

QCheckBox::indicator:hover {
    border-color: #58a6ff;
}

QCheckBox::indicator:checked {
    background-color: #58a6ff;
    border-color: #58a6ff;
}

QCheckBox::indicator:checked:hover {
    background-color: #79c0ff;
    border-color: #79c0ff;
}

/* ==================== Slider ==================== */
QSlider::groove:horizontal {
    background-color: #21262d;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #58a6ff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background-color: #79c0ff;
}

QSlider::sub-page:horizontal {
    background-color: #1f6feb;
    border-radius: 3px;
}

/* ==================== Scroll Bars ==================== */
QScrollBar:vertical {
    background-color: #0d1117;
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #30363d;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #0d1117;
    height: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #30363d;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #484f58;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ==================== Group Box ==================== */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
    font-weight: 500;
}

QGroupBox::title {
    color: #e6edf3;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    background-color: #161b22;
    border-radius: 4px;
    left: 12px;
}

/* ==================== Labels ==================== */
QLabel {
    color: #e6edf3;
}

QLabel#headingLabel {
    font-size: 18px;
    font-weight: 600;
    color: #e6edf3;
}

QLabel#subheadingLabel {
    font-size: 14px;
    color: #8b949e;
}

QLabel#mutedLabel {
    color: #6e7681;
    font-size: 12px;
}

/* ==================== Status Bar ==================== */
QStatusBar {
    background-color: #161b22;
    color: #8b949e;
    border-top: 1px solid #30363d;
    padding: 4px;
}

QStatusBar::item {
    border: none;
}

/* ==================== Progress Bar ==================== */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1f6feb, stop:1 #58a6ff);
    border-radius: 4px;
}

/* ==================== Tool Bar ==================== */
QToolBar {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 4px;
    spacing: 4px;
}

QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px;
    color: #8b949e;
}

QToolButton:hover {
    background-color: #30363d;
    color: #e6edf3;
}

QToolButton:pressed {
    background-color: #21262d;
}

/* ==================== Splitter ==================== */
QSplitter::handle {
    background-color: #30363d;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #58a6ff;
}

/* ==================== Tree Widget ==================== */
QTreeWidget, QListWidget, QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    outline: none;
}

QTreeWidget::item, QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}

QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #21262d;
}

QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 8px;
    font-weight: 500;
}

/* ==================== Dock Widget ==================== */
QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}

QDockWidget::title {
    background-color: #161b22;
    color: #e6edf3;
    padding: 8px;
    border-bottom: 1px solid #30363d;
}

QDockWidget::close-button, QDockWidget::float-button {
    background-color: transparent;
    border: none;
    padding: 4px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background-color: #30363d;
    border-radius: 4px;
}

/* ==================== Tooltips ==================== */
QToolTip {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 6px 10px;
}

/* ==================== Frame ==================== */
QFrame#cardFrame {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
}

QFrame#separatorFrame {
    background-color: #30363d;
    max-height: 1px;
}
"""

# Entity type icons (SVG paths for drawing)
ENTITY_ICONS = {
    "email": "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
    "domain": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z",
    "ip": "M15 7v4h-1v-1H9v1H8V7h7zm1-2v8h-2v1h-2v-1H8v1H6v-1H4V5h12zm-5 3v1h2V8h-2z",
    "phone": "M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z",
    "username": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
    "person": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
    "company": "M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z",
    "subdomain": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-4h2v2h-2v-2zm0-8h2v6h-2V8z",
    "hostname": "M21 3H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H3V5h18v14zM9 10h6v6H9v-6z",
    "document": "M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z",
    "network": "M17 16l-4-4V8.82C14.16 8.4 15 7.3 15 6c0-1.66-1.34-3-3-3S9 4.34 9 6c0 1.3.84 2.4 2 2.82V12l-4 4H3v5h5v-3.05l4-4.2 4 4.2V21h5v-5h-4z",
}


def get_entity_color(entity_type: str) -> str:
    """Get the color for an entity type."""
    color_key = f"entity_{entity_type.lower()}"
    return COLORS.get(color_key, COLORS["accent_primary"])
