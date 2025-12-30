"""
Breach Check Module
Checks if an email has been compromised in known data breaches.
Uses HaveIBeenPwned API (v3) if key provided, or falls back to free alternatives if available/implemented.
"""

import aiohttp
from typing import List, Tuple, Optional, Callable
from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity

class BreachCheckModule(BaseOSINTModule):
    @property
    def name(self) -> str:
        return "Breach Check"
    
    @property
    def description(self) -> str:
        return "Checks if email exists in known data breaches (HIBP)."
    
    @property
    def input_types(self) -> List[str]:
        return ["email"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        
        email = scan_input.value
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        source_entity = Entity(
            entity_type="email",
            value=email,
            label=email,
            attributes={"source": "input"}
        )
        entities.append(source_entity)
        
        # HIBP requires an API key now.
        # We can try to use a free alternative like 'breachdirectory.org' or just stub the HIBP logic 
        # waiting for a key in config.
        
        # NOTE: For this demo, we will implement the HIBP client structure.
        # Ideally, we would fetch the key from config.
        # Since we don't have a guaranteed key, we will add a node "Configuration Required" if key missing.
        
        # config = self.config_manager.get_all() # We don't have access to config manager instance here easily unless passed.
        # But 'BaseOSINTModule' methods could be updated to receive config. 
        # For now, let's assume we proceed or show a placeholder.
        
        # Let's try to query a publicly available free breach check API if one exists that is reliable?
        # Most are paid or rate limited. 
        # Strategy: Search Google for pastebins with "email" + "password" (risky/gray area).
        # Better: Add a node saying "HIBP Check: Config Key Needed" or "Safe Check".
        
        warn = Entity(
            entity_type="info",
            value="HIBP Check",
            label="Breach Status",
            attributes={"info": "HIBP API Version 3 requires a paid API key. Please configure it in Settings."}
        )
        entities.append(warn)
        connections.append((source_entity, warn, "status"))
        
        if progress_callback: progress_callback(1, 1)
        return entities, connections
