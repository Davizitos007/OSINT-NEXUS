"""
Base OSINT Module
Abstract base class for all OSINT modules.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from ..database import Entity


@dataclass
class ScanInput:
    """Input data for a scan operation."""
    target_type: str = ""
    username: str = ""
    email: str = ""
    phone: str = ""
    domain: str = ""
    ip_address: str = ""
    platform: str = ""  # e.g. github, steam, instagram
    sources: List[str] = field(default_factory=list)
    limit: int = 50
    depth: int = 1


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
                  ) -> Tuple[List[Entity], List[tuple]]:
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
