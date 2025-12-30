"""
OSINT-Nexus Core Engine
Asynchronous execution framework using QThreadPool for parallel module execution.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import traceback

from PyQt6.QtCore import (
    QObject, QRunnable, QThreadPool, 
    pyqtSignal, pyqtSlot, QMutex, QMutexLocker
)

from .database import Entity, Connection, Database


class ScanStatus(Enum):
    """Scan execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScanInput:
    """Input data for a scan operation."""
    target_type: str = ""  # person, company, domain, ip, username
    username: str = ""
    email: str = ""
    phone: str = ""
    domain: str = ""
    ip_address: str = ""
    platform: str = ""
    sources: List[str] = field(default_factory=list)
    limit: int = 50
    depth: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_type": self.target_type,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "domain": self.domain,
            "ip_address": self.ip_address,
            "sources": self.sources,
            "limit": self.limit,
            "depth": self.depth,
        }


@dataclass
class ScanResult:
    """Result from an OSINT module."""
    module_name: str
    status: ScanStatus
    entities: List[Entity] = field(default_factory=list)
    connections: List[tuple] = field(default_factory=list)  # (source_entity, target_entity, relationship)
    error_message: str = ""
    execution_time: float = 0.0


class ModuleSignals(QObject):
    """Signals for module execution."""
    started = pyqtSignal(str)  # module_name
    progress = pyqtSignal(str, int, int)  # module_name, current, total
    result = pyqtSignal(object)  # ScanResult
    error = pyqtSignal(str, str)  # module_name, error_message
    finished = pyqtSignal(str)  # module_name


class ModuleRunner(QRunnable):
    """
    Runnable wrapper for executing OSINT modules in the thread pool.
    Bridges async module execution with Qt's threading model.
    """
    
    def __init__(self, module: 'BaseOSINTModule', scan_input: ScanInput):
        super().__init__()
        self.module = module
        self.scan_input = scan_input
        self.signals = ModuleSignals()
        self._is_cancelled = False
    
    def cancel(self):
        """Cancel the module execution."""
        self._is_cancelled = True
    
    @pyqtSlot()
    def run(self):
        """Execute the module."""
        start_time = datetime.now()
        
        try:
            self.signals.started.emit(self.module.name)
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the async module
                entities, connections = loop.run_until_complete(
                    self.module.run(self.scan_input, self._progress_callback)
                )
                
                if self._is_cancelled:
                    result = ScanResult(
                        module_name=self.module.name,
                        status=ScanStatus.CANCELLED,
                        execution_time=(datetime.now() - start_time).total_seconds()
                    )
                else:
                    result = ScanResult(
                        module_name=self.module.name,
                        status=ScanStatus.COMPLETED,
                        entities=entities,
                        connections=connections,
                        execution_time=(datetime.now() - start_time).total_seconds()
                    )
                
                try:
                    self.signals.result.emit(result)
                except RuntimeError:
                    pass
                
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            result = ScanResult(
                module_name=self.module.name,
                status=ScanStatus.FAILED,
                error_message=error_msg,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            try:
                self.signals.result.emit(result)
                self.signals.error.emit(self.module.name, str(e))
            except RuntimeError:
                pass
        
        finally:
            try:
                self.signals.finished.emit(self.module.name)
            except RuntimeError:
                pass
    
    def _progress_callback(self, current: int, total: int):
        """Callback for module progress updates."""
        try:
            self.signals.progress.emit(self.module.name, current, total)
        except RuntimeError:
            pass


class EngineSignals(QObject):
    """Signals for the OSINT engine."""
    scan_started = pyqtSignal()
    scan_progress = pyqtSignal(int, int, str)  # completed, total, current_module
    module_started = pyqtSignal(str)
    module_completed = pyqtSignal(str, object)  # module_name, ScanResult
    module_error = pyqtSignal(str, str)
    scan_completed = pyqtSignal(list)  # List[ScanResult]
    entity_discovered = pyqtSignal(object)  # Entity
    connection_discovered = pyqtSignal(object, object, str)  # source, target, relationship


class OSINTEngine(QObject):
    """
    Core OSINT scanning engine that manages module execution.
    Uses QThreadPool for parallel execution of OSINT modules.
    """
    
    def __init__(self, database: Optional[Database] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self.database = database or Database()
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(8)  # Limit concurrent modules
        
        self.signals = EngineSignals()
        self._modules: Dict[str, 'BaseOSINTModule'] = {}
        self._active_runners: List[ModuleRunner] = []
        self._results: List[ScanResult] = []
        self._mutex = QMutex()
        self._is_scanning = False
        self._current_project_id: Optional[int] = None
        
        # Load available modules
        self._load_modules()
    
    def _load_modules(self):
        """Load all available OSINT modules."""
        # Import modules here to avoid circular imports
        from .modules import (
            EmailHarvester,
            SocialLookupModule, 
            PhoneRecon,
            GoogleSearchModule,
            DomainInfraScan,
            DocMetadataSearch,
            GitHubReconModule,
            SteamReconModule,
            HarvesterReconModule,
            BreachCheckModule,
            IPReconModule,
            BreachIntelModule,
            ImageForensicsModule,
            WaybackMachineTransform,
            ShodanTransform,
            ReverseDNSTransform,
            GeoIPTransform,
            SubdomainEnumTransform,
        )
        
        # Register modules
        modules = [
            EmailHarvester(),
            SocialLookupModule(),
            PhoneRecon(),
            GoogleSearchModule(),
            DomainInfraScan(),
            DocMetadataSearch(),
            GitHubReconModule(),
            SteamReconModule(),
            HarvesterReconModule(),
            BreachCheckModule(),
            IPReconModule(),
            BreachIntelModule(),
            ImageForensicsModule(),
            WaybackMachineTransform(),
            ShodanTransform(),
            ReverseDNSTransform(),
            GeoIPTransform(),
            SubdomainEnumTransform(),
        ]
        
        for module in modules:
            self._modules[module.name] = module
    
    @property
    def available_modules(self) -> Dict[str, 'BaseOSINTModule']:
        """Get all available modules."""
        return self._modules
    
    @property
    def is_scanning(self) -> bool:
        """Check if a scan is currently running."""
        return self._is_scanning
    
    def get_applicable_modules(self, scan_input: ScanInput) -> List[str]:
        """Get list of modules applicable to the given input."""
        applicable = []
        for name, module in self._modules.items():
            if module.can_process(scan_input):
                applicable.append(name)
        return applicable
    
    def start_scan(self, scan_input: ScanInput, 
                   selected_modules: Optional[List[str]] = None,
                   project_id: Optional[int] = None):
        """
        Start an OSINT scan with the given input.
        
        Args:
            scan_input: The scan input data
            selected_modules: List of module names to run, or None for all applicable
            project_id: Project ID for database storage
        """
        if self._is_scanning:
            return
        
        self._is_scanning = True
        self._current_project_id = project_id
        self._results = []
        self._active_runners = []
        
        # Determine which modules to run
        if selected_modules:
            modules_to_run = [self._modules[m] for m in selected_modules if m in self._modules]
        else:
            modules_to_run = [
                m for m in self._modules.values() 
                if m.can_process(scan_input)
            ]
        
        if not modules_to_run:
            self._is_scanning = False
            self.signals.scan_completed.emit([])
            return
        
        self.signals.scan_started.emit()
        
        # Create and start runners for each module
        for module in modules_to_run:
            runner = ModuleRunner(module, scan_input)
            
            # Connect signals
            runner.signals.started.connect(self._on_module_started)
            runner.signals.progress.connect(self._on_module_progress)
            runner.signals.result.connect(self._on_module_result)
            runner.signals.error.connect(self._on_module_error)
            runner.signals.finished.connect(self._on_module_finished)
            
            self._active_runners.append(runner)
            self.thread_pool.start(runner)
    
    def cancel_scan(self):
        """Cancel the current scan."""
        with QMutexLocker(self._mutex):
            for runner in self._active_runners:
                runner.cancel()
    
    def _on_module_started(self, module_name: str):
        """Handle module started signal."""
        self.signals.module_started.emit(module_name)
        self._update_progress()
    
    def _on_module_progress(self, module_name: str, current: int, total: int):
        """Handle module progress signal."""
        pass  # Can be used for detailed progress tracking
    
    def _on_module_result(self, result: ScanResult):
        """Handle module result signal."""
        with QMutexLocker(self._mutex):
            self._results.append(result)
            
            # Store entities in database
            if self._current_project_id and result.status == ScanStatus.COMPLETED:
                for entity in result.entities:
                    entity.project_id = self._current_project_id
                    entity_id = self.database.add_entity(entity)
                    entity.id = entity_id
                    self.signals.entity_discovered.emit(entity)
                
                # Store connections
                for source, target, relationship in result.connections:
                    if source.id and target.id:
                        conn = Connection(
                            project_id=self._current_project_id,
                            source_id=source.id,
                            target_id=target.id,
                            relationship=relationship
                        )
                        self.database.add_connection(conn)
                        self.signals.connection_discovered.emit(source, target, relationship)
        
        self.signals.module_completed.emit(result.module_name, result)
        self._update_progress()
    
    def _on_module_error(self, module_name: str, error: str):
        """Handle module error signal."""
        self.signals.module_error.emit(module_name, error)
    
    def _on_module_finished(self, module_name: str):
        """Handle module finished signal."""
        with QMutexLocker(self._mutex):
            # Check if all modules are finished
            if len(self._results) >= len(self._active_runners):
                self._is_scanning = False
                self.signals.scan_completed.emit(self._results)
    
    def _update_progress(self):
        """Update overall scan progress."""
        completed = len(self._results)
        total = len(self._active_runners)
        current = ""
        
        # Find currently running module
        for runner in self._active_runners:
            if runner.module.name not in [r.module_name for r in self._results]:
                current = runner.module.name
                break
        
        self.signals.scan_progress.emit(completed, total, current)


# Base module interface (abstract)
from abc import ABC, abstractmethod

class BaseOSINTModule(ABC):
    """Abstract base class for all OSINT modules."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Module name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Module description."""
        pass
    
    @property
    @abstractmethod
    def input_types(self) -> List[str]:
        """List of input types this module can process."""
        pass
    
    @abstractmethod
    async def run(self, scan_input: ScanInput, 
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> tuple[List[Entity], List[tuple]]:
        """
        Execute the module.
        
        Returns:
            Tuple of (entities, connections) where connections are 
            (source_entity, target_entity, relationship) tuples.
        """
        pass
    
    def can_process(self, scan_input: ScanInput) -> bool:
        """Check if this module can process the given input."""
        if "domain" in self.input_types and scan_input.domain:
            return True
        if "email" in self.input_types and scan_input.email:
            return True
        if "username" in self.input_types and scan_input.username:
            return True
        if "phone" in self.input_types and scan_input.phone:
            return True
        if "ip" in self.input_types and scan_input.ip_address:
            return True
        return False
