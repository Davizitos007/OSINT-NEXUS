"""
OSINT Automation Machines.
Defines automated workflows (Machines) that chain multiple transforms together.
"""

from typing import List, Dict, Type
from dataclasses import dataclass
import asyncio

from .osint_core import OSINTEngine, ScanInput

@dataclass
class MachineStep:
    """A single step in a machine."""
    description: str
    transforms: List[str]  # List of transform names to run parallelly
    entity_filter: List[str] = None  # Only run on these entity types

class BaseMachine:
    """Base class for all automation machines."""
    
    def __init__(self):
        # List of steps to execute
        self.steps: List[MachineStep] = []
        
    @property
    def name(self) -> str:
        """Name of the machine."""
        raise NotImplementedError
        
    @property
    def description(self) -> str:
        """Description of what the machine does."""
        raise NotImplementedError

class DomainFootprintMachine(BaseMachine):
    """Machine to perform full reconnaissance on a domain."""
    
    @property
    def name(self) -> str:
        return "Footprint Domain L1"
        
    @property
    def description(self) -> str:
        return "Passive reconnaissance on a domain (Whois, DNS, Email)."
        
    def __init__(self):
        super().__init__()
        self.steps = [
            MachineStep(
                description="Infrastructure Scan",
                transforms=["Domain Infrastructure", "Subdomain Enum"],
                entity_filter=["domain"]
            ),
            MachineStep(
                description="Domain Intelligence",
                transforms=["Email Harvester", "Domain Infra Scan", "TheHarvester Recon", "IP/Geo Recon"],
                entity_filter=["domain"]
            ),
            MachineStep(
                description="IP Analysis",
                transforms=["GeoIP Lookup", "Shodan Lookup"],
                entity_filter=["ip", "netblock"]
            )
        ]

class UserInvestigatorMachine(BaseMachine):
    """Machine to investigate a username or person."""
    
    @property
    def name(self) -> str:
        return "Investigate Persona"
        
    @property
    def description(self) -> str:
        return "Find social profiles and related info for a username."
        
    def __init__(self):
        super().__init__()
        self.steps = [
            MachineStep(
                description="Social Profile Search",
                transforms=["Social Profile Lookup", "GitHub Recon", "Steam Recon"],
                entity_filter=["username", "person"]
            )
        ]

class MachineManager:
    """Manages available machines and their execution."""
    
    def __init__(self, engine: OSINTEngine):
        self.engine = engine
        self.machines: Dict[str, BaseMachine] = {}
        self._register_defaults()
        
    def _register_defaults(self):
        """Register default machines."""
        self.register_machine(DomainFootprintMachine())
        self.register_machine(UserInvestigatorMachine())
        
    def register_machine(self, machine: BaseMachine):
        """Register a new machine."""
        self.machines[machine.name] = machine
        
    def get_machines_for_type(self, entity_type: str) -> List[BaseMachine]:
        """Return machines applicable to an entity type (based on 1st step)."""
        applicable = []
        for machine in self.machines.values():
            if not machine.steps:
                continue
            first_step = machine.steps[0]
            if not first_step.entity_filter or entity_type in first_step.entity_filter:
                applicable.append(machine)
        return applicable

    # Note: Actual execution logic will need to handle sequential steps
    # and chaining results from step N to step N+1.
    # This might require enhancing OSINTEngine or handling it here via signals.

from PyQt6.QtCore import QObject, pyqtSignal

class MachineRunner(QObject):
    """Executes a machine's steps sequentially."""
    
    finished = pyqtSignal(str, bool)  # machine_name, success
    step_started = pyqtSignal(str, int, int)  # step_desc, current_step, total_steps
    progress = pyqtSignal(str, int, int) # message, done, total
    
    def __init__(self, machine: BaseMachine, engine: OSINTEngine):
        super().__init__()
        self.machine = machine
        self.engine = engine
        self.current_step_idx = -1
        self.current_entities = []
        self.active_scans = 0
        self.collected_results = []
        
        # Connect to engine signals
        self.engine.signals.module_completed.connect(self._on_module_completed)
        self.engine.signals.module_error.connect(self._on_module_error)
        
    def start(self, initial_entities: List[object]):
        """Start the machine execution."""
        self.current_entities = initial_entities
        self.collected_results = []
        self._next_step()
        
    def _next_step(self):
        """Execute the next step."""
        self.current_step_idx += 1
        
        if self.current_step_idx >= len(self.machine.steps):
            self.finished.emit(self.machine.name, True)
            return
            
        step = self.machine.steps[self.current_step_idx]
        self.step_started.emit(step.description, self.current_step_idx + 1, len(self.machine.steps))
        
        # Filter entities
        targets = []
        for entity in self.current_entities:
            if not step.entity_filter or entity.entity_type in step.entity_filter:
                targets.append(entity)
                
        if not targets:
            # No targets for this step, skip to next
            self._next_step()
            return
            
        # Launch scans
        self.active_scans = 0
        self.step_results = [] # Reset for this step
        
        for entity in targets:
            # Create input from entity
            # Assuming entity has data needed
            # Create input from entity
            scan_args = {
                "target_type": entity.entity_type, 
                "depth": 1,
                "sources": []
            }
            
            # Map value to specific field
            if entity.entity_type == "domain":
                scan_args["domain"] = entity.value
            elif entity.entity_type == "ip":
                scan_args["ip_address"] = entity.value
            elif entity.entity_type == "email":
                scan_args["email"] = entity.value
            elif entity.entity_type == "phone":
                scan_args["phone"] = entity.value
            elif entity.entity_type in ["username", "person"]:
                scan_args["username"] = entity.value
            else:
                # Fallback for generic types if any module supports them
                scan_args["username"] = entity.value 

            scan_input = ScanInput(**scan_args)
            
            # Start scan for each transform
            for transform_name in step.transforms:
                self.active_scans += 1
                self.engine.start_scan(scan_input, selected_modules=[transform_name])
        
        if self.active_scans == 0:
             self._next_step()

    def _on_module_completed(self, module_name: str, result: object):
        """Handle individual module completion."""
        if self.active_scans > 0:
            self.active_scans -= 1
            if result and result.entities:
                self.collected_results.extend(result.entities)
                self.step_results.extend(result.entities)
            
            self.progress.emit(f"Module {module_name} finished", 0, 0)
            
            if self.active_scans == 0:
                # Step finished
                # Update current entities with NEW results for next step
                # (Machines usually feed output of Step N to Step N+1)
                self.current_entities = list(set(self.step_results)) # Unique entities
                self._next_step()

    def _on_module_error(self, module_name: str, error: str):
        """Handle errors."""
        self._on_module_completed(module_name, None)

