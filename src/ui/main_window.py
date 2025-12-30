"""
OSINT-Nexus Main Window
Primary application window with tabbed interface.
"""

from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QMenuBar, QMenu, QStatusBar, QToolBar,
    QLabel, QProgressBar, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QFont, QIcon

from .styles import DARK_STYLE, COLORS
from .target_scan_tab import TargetScanTab
from .graph_view_tab import GraphViewTab
from .settings_dialog import SettingsDialog
from .settings_dialog import SettingsDialog
from ..machines import MachineManager, MachineRunner
from ..database import Database, Entity, Connection, Project
from ..osint_core import OSINTEngine, ScanInput, ScanResult, ScanStatus


class NewProjectDialog(QDialog):
    """Dialog for creating a new project."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("My OSINT Investigation")
        form.addRow("Project Name:", self.name_input)
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Optional description...")
        form.addRow("Description:", self.desc_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_project_data(self):
        return {
            "name": self.name_input.text() or "Untitled Project",
            "description": self.desc_input.text()
        }


class MainWindow(QMainWindow):
    """Main application window for OSINT-Nexus."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OSINT-Nexus")
        self.setMinimumSize(1200, 800)
        
        # Initialize database and engine
        self.database = Database()
        self.engine = OSINTEngine(self.database)
        self.machine_manager = MachineManager(self.engine)
        
        # Current project
        self.current_project: Optional[Project] = None
        self._entity_id_counter = 0
        
        # Set up UI
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_connections()
        
        # Pass manager to graph tab
        self.graph_tab.set_machine_manager(self.machine_manager)
        
        # Apply dark theme
        self.setStyleSheet(DARK_STYLE)
        
        # Create default project
        self._create_default_project()
    
    def _setup_ui(self):
        """Set up the main UI components."""
        # Central widget with tabs
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Target Scan tab
        self.scan_tab = TargetScanTab()
        self.tabs.addTab(self.scan_tab, "🎯 Target Scan")
        
        # Graph View tab
        self.graph_tab = GraphViewTab()
        self.tabs.addTab(self.graph_tab, "🔗 Graph View")
        
        layout.addWidget(self.tabs)
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Project", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Project", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_menu = file_menu.addMenu("Export")
        
        export_json = QAction("Export as JSON", self)
        export_json.triggered.connect(self._export_json)
        export_menu.addAction(export_json)
        
        export_csv = QAction("Export as CSV", self)
        export_csv.triggered.connect(self._export_csv)
        export_menu.addAction(export_csv)
        
        export_menu.addSeparator()
        
        export_html = QAction("📊 Export HTML Report", self)
        export_html.triggered.connect(self._export_html_report)
        export_menu.addAction(export_html)
        
        export_pdf = QAction("📄 Export PDF Report", self)
        export_pdf.triggered.connect(self._export_pdf_report)
        export_menu.addAction(export_pdf)
        
        export_stix = QAction("🔐 Export STIX 2.1 (CTI)", self)
        export_stix.triggered.connect(self._export_stix)
        export_menu.addAction(export_stix)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        clear_action = QAction("Clear Graph", self)
        clear_action.triggered.connect(self.graph_tab.clear_graph)
        edit_menu.addAction(clear_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        zoom_in = QAction("Zoom In", self)
        zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in.triggered.connect(self.graph_tab._zoom_in)
        view_menu.addAction(zoom_in)
        
        zoom_out = QAction("Zoom Out", self)
        zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out.triggered.connect(self.graph_tab._zoom_out)
        view_menu.addAction(zoom_out)
        
        fit_view = QAction("Fit to View", self)
        fit_view.setShortcut("Ctrl+0")
        fit_view.triggered.connect(self.graph_tab._fit_to_view)
        view_menu.addAction(fit_view)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = QAction("⚙ Settings", self)
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)
        tools_menu.addSeparator()
        
        relayout = QAction("Relayout Graph", self)
        relayout.setShortcut("Ctrl+L")
        relayout.triggered.connect(self.graph_tab._restart_layout)
        tools_menu.addAction(relayout)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About OSINT-Nexus", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Project info
        self.project_label = QLabel("📁 No Project")
        self.project_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 0 16px;")
        toolbar.addWidget(self.project_label)
        
        toolbar.addSeparator()
        
        # Quick scan button
        quick_scan_action = QAction("🚀 Quick Scan", self)
        quick_scan_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        toolbar.addAction(quick_scan_action)
        
        # View graph button
        view_graph_action = QAction("🔗 View Graph", self)
        view_graph_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        toolbar.addAction(view_graph_action)
    
    def _setup_statusbar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message
        self.status_message = QLabel("Ready")
        self.status_bar.addWidget(self.status_message, 1)
        
        # Module status
        self.module_status = QLabel("")
        self.status_bar.addPermanentWidget(self.module_status)
        
        # Progress bar (hidden by default)
        self.status_progress = QProgressBar()
        self.status_progress.setMaximumWidth(200)
        self.status_progress.hide()
        self.status_bar.addPermanentWidget(self.status_progress)
    
    def _setup_connections(self):
        """Connect signals to slots."""
        # Scan tab signals
        self.scan_tab.scan_requested.connect(self._on_scan_requested)
        self.scan_tab.cancel_requested.connect(self._on_cancel_requested)
        
        # Engine signals
        self.engine.signals.scan_started.connect(self._on_scan_started)
        self.engine.signals.scan_progress.connect(self._on_scan_progress)
        self.engine.signals.module_started.connect(self._on_module_started)
        self.engine.signals.module_completed.connect(self._on_module_completed)
        self.engine.signals.module_error.connect(self._on_module_error)
        self.engine.signals.scan_completed.connect(self._on_scan_completed)
        self.engine.signals.entity_discovered.connect(self._on_entity_discovered)
        self.engine.signals.connection_discovered.connect(self._on_connection_discovered)
        
        # Graph signals
        # Graph signals
        self.graph_tab.transform_requested.connect(self._on_transform_requested)
        self.graph_tab.machine_requested.connect(self._on_machine_requested)
    
    def _create_default_project(self):
        """Create a default project on startup."""
        project_id = self.database.create_project(
            name=f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description="Auto-created session"
        )
        self.current_project = self.database.get_project(project_id)
        self._update_project_label()
    
    def _update_project_label(self):
        """Update the project label in toolbar."""
        if self.current_project:
            self.project_label.setText(f"📁 {self.current_project.name}")
        else:
            self.project_label.setText("📁 No Project")
    
    # === Slot handlers ===
    
    @pyqtSlot(dict)
    def _on_scan_requested(self, scan_data: dict):
        """Handle scan request from scan tab."""
        if not self.current_project:
            self._create_default_project()
        
        # Create ScanInput from dict
        from ..osint_core import ScanInput as CoreScanInput
        scan_input = CoreScanInput(
            target_type=scan_data.get("target_type", ""),
            username=scan_data.get("username", ""),
            email=scan_data.get("email", ""),
            phone=scan_data.get("phone", ""),
            domain=scan_data.get("domain", ""),
            ip_address=scan_data.get("ip_address", ""),
            sources=scan_data.get("sources", []),
            limit=scan_data.get("limit", 50),
            depth=scan_data.get("depth", 2),
        )
        
        # Start scan
        self.engine.start_scan(scan_input, project_id=self.current_project.id)
    
    @pyqtSlot()
    def _on_cancel_requested(self):
        """Handle scan cancellation."""
        self.engine.cancel_scan()
        self.scan_tab.set_scanning(False)
        self.scan_tab.log_message("⏹ Scan cancelled", "warning")
        self.status_message.setText("Scan cancelled")
    
    @pyqtSlot()
    def _on_scan_started(self):
        """Handle scan started."""
        self.scan_tab.set_scanning(True)
        self.scan_tab.log_message("🚀 Scan started...", "info")
        self.status_message.setText("Scanning...")
        self.status_progress.setValue(0)
        self.status_progress.show()
        # Ensure status bar is visible
        self.statusBar().show()
    
    @pyqtSlot(int, int, str)
    def _on_scan_progress(self, completed: int, total: int, current_module: str):
        """Handle scan progress update."""
        self.scan_tab.update_progress(completed, total, current_module)
        if total > 0:
            self.status_progress.setMaximum(total)
            self.status_progress.setValue(completed)
    
    @pyqtSlot(str)
    def _on_module_started(self, module_name: str):
        """Handle module started."""
        self.scan_tab.log_message(f"▶ Running: {module_name}", "info")
        self.graph_tab.log_message(f"▶ Scanning: {module_name}...", "info")
        self.module_status.setText(f"Running: {module_name}")
    
    @pyqtSlot(str, object)
    def _on_module_completed(self, module_name: str, result: ScanResult):
        """Handle module completion."""
        if result.status == ScanStatus.COMPLETED:
            entity_count = len(result.entities)
            msg = f"✓ {module_name}: Found {entity_count} entities"
            self.scan_tab.log_message(msg, "success")
            self.graph_tab.log_message(msg, "success")
        elif result.status == ScanStatus.FAILED:
            msg = f"✗ {module_name}: {result.error_message[:50]}"
            self.scan_tab.log_message(msg, "error")
            self.graph_tab.log_message(msg, "error")
    
    @pyqtSlot(str, str)
    def _on_module_error(self, module_name: str, error: str):
        """Handle module error."""
        msg = f"⚠ {module_name}: Error - {error}"
        self.scan_tab.log_message(msg, "error")
        self.graph_tab.log_message(msg, "error")
    
    @pyqtSlot(list)
    def _on_scan_completed(self, results: list):
        """Handle scan completion."""
        self.scan_tab.set_scanning(False)
        self.status_progress.hide()
        self.module_status.setText("")
        
        total_entities = sum(len(r.entities) for r in results if r.status == ScanStatus.COMPLETED)
        self.scan_tab.log_message(f"✓ Scan completed! Total entities: {total_entities}", "success")
        self.status_message.setText(f"Scan completed - {total_entities} entities discovered")
        
        # Start graph layout animation (without clearing)
        self.graph_tab.start_layout_animation()
        
        # Switch to graph tab if not already there
        if self.tabs.currentIndex() != 1:
             self.tabs.setCurrentIndex(1)
    
    @pyqtSlot(object)
    def _on_entity_discovered(self, entity: Entity):
        """Handle entity discovery."""
        self.graph_tab.add_entity(entity)
    
    @pyqtSlot(object, object, str)
    def _on_connection_discovered(self, source: Entity, target: Entity, relationship: str):
        """Handle connection discovery."""
        self.graph_tab.add_connection(source, target, relationship)
    
    @pyqtSlot(object, str)
    def _on_transform_requested(self, node_data: object, transform_name: str):
        """Handle transform request from graph view."""
        if not self.current_project:
            self._create_default_project()
            
        # Create ScanInput from node data
        from ..osint_core import ScanInput as CoreScanInput
        scan_input = CoreScanInput()
        
        # Map entity value to appropriate input field based on type
        # Note: This mapping should match module can_process logic
        if node_data.entity_type == "domain":
            scan_input.domain = node_data.value
        elif node_data.entity_type in ("ip", "netblock"):
            scan_input.ip_address = node_data.value
        elif node_data.entity_type == "email":
            scan_input.email = node_data.value
        elif node_data.entity_type in ("username", "person"):
            scan_input.username = node_data.value
        elif node_data.entity_type == "phone":
            scan_input.phone = node_data.value
        elif node_data.entity_type == "url":
            scan_input.target_type = "url"
            scan_input.domain = node_data.value  # Some transforms treat URL as domain input
        
        # Set limits/depth
        scan_input.limit = 20
        scan_input.depth = 1
        
        # Log action
        self.scan_tab.log_message(f"⚡ Running transform: {transform_name} on {node_data.value}", "info")
        self.status_message.setText(f"Running transform: {transform_name}...")
        
        # Start scan with specific module
        # Start scan with specific module
        self.engine.start_scan(scan_input, selected_modules=[transform_name], project_id=self.current_project.id)

    @pyqtSlot(object, str)
    def _on_machine_requested(self, node_data: object, machine_name: str):
        """Handle context menu machine request."""
        machine = self.machine_manager.machines.get(machine_name)
        if not machine:
            return
            
        self.status_message.setText(f"Running Machine: {machine_name} on {node_data.value}...")
        
        # Create and start runner
        self._current_machine_runner = MachineRunner(machine, self.engine)
        self._current_machine_runner.step_started.connect(
            lambda desc, i, n: self.status_message.setText(f"Machine Step {i}/{n}: {desc}")
        )
        self._current_machine_runner.finished.connect(
            lambda name, success: self.status_message.setText(f"Machine {name} completed!")
        )
        # Pass node_data as initial entity (needs conversion or duck typing)
        # Convert node_data (NodeData) back to Entity object for processing
        from ..database import Entity
        initial_entity = Entity(
            id=node_data.id,
            entity_type=node_data.entity_type, 
            value=node_data.value,
            label=node_data.label,
            attributes=node_data.attributes
        )
        self._current_machine_runner.start([initial_entity])
    
    # === Menu actions ===
    
    def _new_project(self):
        """Create a new project."""
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_project_data()
            
            # Clear current graph
            self.graph_tab.clear_graph()
            
            # Create new project
            project_id = self.database.create_project(data["name"], data["description"])
            self.current_project = self.database.get_project(project_id)
            self._update_project_label()
            
            self.status_message.setText(f"Created project: {data['name']}")
    
    def _open_project(self):
        """Open an existing project."""
        projects = self.database.get_all_projects()
        if not projects:
            QMessageBox.information(self, "Open Project", "No projects found.")
            return

        # Simple list selection
        items = [f"{p.name} (ID: {p.id})" for p in projects]
        item, ok = QInputDialog.getItem(self, "Open Project", "Select Project:", items, 0, False)
        
        if ok and item:
            # Extract ID
            project_id = int(item.split("ID: ")[1].strip(")"))
            project = self.database.get_project(project_id)
            
            if project:
                self.current_project = project
                self._update_project_label()  # Update window title
                
                 # Load entities and connections
                self.graph_tab.clear_graph()
                
                entities = self.database.get_project_entities(project_id)
                connections = self.database.get_project_connections(project.id)
                
                self.status_message.setText(f"Loading {len(entities)} entities...")
                
                for entity in entities:
                    self.graph_tab.add_entity(entity)
                    
                for conn in connections:
                    # Creating dummy entities to satisfy signature
                    s_ent = Entity(id=conn.source_id)
                    t_ent = Entity(id=conn.target_id)
                    self.graph_tab.add_connection(s_ent, t_ent, conn.relationship)
                
                self.status_message.setText(f"Project '{project.name}' loaded.")
                self.graph_tab._fit_to_view()
    
    def _save_project(self):
        """Save current project."""
        if self.current_project:
            self.status_message.setText(f"Project saved: {self.current_project.name}")
        else:
            QMessageBox.warning(self, "No Project", "No active project to save.")
    
    def _export_json(self):
        """Export project as JSON."""
        if not self.current_project:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", 
            f"{self.current_project.name}.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            import json
            data = self.database.export_project_json(self.current_project.id)
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            self.status_message.setText(f"Exported to {filename}")
    
    def _export_csv(self):
        """Export project as CSV."""
        if not self.current_project:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export CSV",
            f"{self.current_project.name}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            import csv
            entities = self.database.get_project_entities(self.current_project.id)
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "Value", "Label", "Attributes"])
                for e in entities:
                    writer.writerow([e.entity_type, e.value, e.label, str(e.attributes)])
            self.status_message.setText(f"Exported to {filename}")
    
    def _export_html_report(self):
        """Export project as HTML intelligence report."""
        if not self.current_project:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export HTML Report",
            f"{self.current_project.name}_report.html",
            "HTML Files (*.html)"
        )
        
        if filename:
            from ..reports import report_generator
            
            entities = self.database.get_project_entities(self.current_project.id)
            connections = self.database.get_project_connections(self.current_project.id)
            
            # Convert to dicts
            entity_dicts = [e.to_dict() for e in entities]
            conn_tuples = [(c.source_id, c.target_id, c.relationship) for c in connections]
            
            # Generate HTML
            html = report_generator.generate_html_report(
                project_name=self.current_project.name,
                entities=entity_dicts,
                connections=conn_tuples,
                ai_summary=""
            )
            
            # Save
            if report_generator.save_html_report(html, filename):
                self.status_message.setText(f"HTML report exported to {filename}")
                QMessageBox.information(self, "Export Complete", 
                    f"HTML report saved to:\n{filename}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to save HTML report.")
    
    def _export_pdf_report(self):
        """Export project as PDF intelligence report."""
        if not self.current_project:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export PDF Report",
            f"{self.current_project.name}_report.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            from ..reports import report_generator
            
            entities = self.database.get_project_entities(self.current_project.id)
            connections = self.database.get_project_connections(self.current_project.id)
            
            # Convert to dicts
            entity_dicts = [e.to_dict() for e in entities]
            conn_tuples = [(c.source_id, c.target_id, c.relationship) for c in connections]
            
            # Generate PDF
            success = report_generator.generate_pdf_report(
                project_name=self.current_project.name,
                entities=entity_dicts,
                connections=conn_tuples,
                output_path=filename
            )
            
            if success:
                self.status_message.setText(f"PDF report exported to {filename}")
                QMessageBox.information(self, "Export Complete", 
                    f"PDF report saved to:\n{filename}")
            else:
                QMessageBox.warning(self, "Export Failed", 
                    "Failed to generate PDF report.\n\n"
                    "PDF export requires 'reportlab' package.\n"
                    "Install with: pip install reportlab")
    
    def _export_stix(self):
        """Export project as STIX 2.1 bundle for CTI sharing."""
        if not self.current_project:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export STIX 2.1",
            f"{self.current_project.name}_stix.json",
            "STIX JSON Files (*.json)"
        )
        
        if filename:
            from ..reports import report_generator
            
            entities = self.database.get_project_entities(self.current_project.id)
            connections = self.database.get_project_connections(self.current_project.id)
            
            # Convert to dicts
            entity_dicts = [e.to_dict() for e in entities]
            conn_tuples = [(c.source_id, c.target_id, c.relationship) for c in connections]
            
            # Generate STIX
            stix_json = report_generator.export_stix(
                project_name=self.current_project.name,
                entities=entity_dicts,
                connections=conn_tuples
            )
            
            with open(filename, 'w') as f:
                f.write(stix_json)
            
            self.status_message.setText(f"STIX bundle exported to {filename}")
            QMessageBox.information(self, "Export Complete", 
                f"STIX 2.1 bundle saved to:\n{filename}\n\n"
                "This file can be imported into threat intelligence platforms.")
    
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About OSINT-Nexus",
            """<h2>OSINT-Nexus</h2>
            <p>Version 1.0.0</p>
            <p>Cross-platform Open-Source Intelligence (OSINT) 
            gathering and visualization application.</p>
            <p>Combining passive reconnaissance capabilities with 
            powerful visual link analysis.</p>
            <hr>
            <p><small>Built with PyQt6 and Python</small></p>"""
        )
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def closeEvent(self, event):
        """Handle window close."""
        # Clean up
        self.database.close()
        super().closeEvent(event)
