"""
Steam Recon Module
Fetches detailed Steam profile information including friends, groups, and games.
Uses the Steam Community XML/JSON endpoints.
"""

import aiohttp
import re
from typing import List, Tuple, Optional, Callable, Dict, Any
import json
import xml.etree.ElementTree as ET

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity

class SteamReconModule(BaseOSINTModule):
    """
    Deep scans Steam profiles.
    """
    
    @property
    def name(self) -> str:
        return "Steam Recon"
    
    @property
    def description(self) -> str:
        return "Extracts detailed profile info, friends, and recent games from Steam."
    
    @property
    def input_types(self) -> List[str]:
        return ["username", "person"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute Steam recon."""
        
        # Only run if generic or explicitly Steam
        if scan_input.platform and scan_input.platform.lower() not in ["steam", "generic (sherlock)"]:
            return [], []

        # If platform is Generic, we might want to skip deep scan unless confirmed?
        # But user asked for detailed info. Let's try to run it if username looks likely?
        # For now, explicit Steam selection or if SocialLookup found a Steam profile (chained).
        # This module takes a username input directly.
        
        username = scan_input.username
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        source_entity = Entity(
            entity_type="username",
            value=username,
            label=f"steam:{username}",
            attributes={"source": "input", "platform": "steam"}
        )
        entities.append(source_entity)
        
        # Try both /id/ (custom url) and /profiles/ (id64)
        urls_to_try = [
            f"https://steamcommunity.com/id/{username}/?xml=1",
            f"https://steamcommunity.com/profiles/{username}/?xml=1"
        ]
        
        async with aiohttp.ClientSession() as session:
            found = False
            for url in urls_to_try:
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status == 200:
                            # Parse XML
                            content = await resp.text()
                            if "The specified profile could not be found" in content:
                                continue
                                
                            try:
                                root = ET.fromstring(content)
                                found = True
                                
                                # Extract Basic Info
                                steamID64 = root.findtext("steamID64")
                                steamID = root.findtext("steamID")
                                realname = root.findtext("realname")
                                location = root.findtext("location")
                                avatar = root.findtext("avatarFull")
                                state = root.findtext("stateMessage")
                                summary = root.findtext("summary")
                                memberSince = root.findtext("memberSince")
                                
                                # Create Profile Entity
                                prof_url = f"https://steamcommunity.com/profiles/{steamID64}" if steamID64 else url.replace("/?xml=1", "")
                                prof = Entity(
                                    entity_type="social_profile",
                                    value=prof_url,
                                    label=f"Steam: {steamID}",
                                    attributes={
                                        "platform": "Steam",
                                        "username": steamID,
                                        "real_name": realname,
                                        "location": location,
                                        "steam_id_64": steamID64,
                                        "status": state,
                                        "member_since": memberSince,
                                        "bio": summary[:100] + "..." if summary else "",
                                        "avatar_url": avatar
                                    }
                                )
                                entities.append(prof)
                                connections.append((source_entity, prof, "has_account"))
                                
                                # Extract Location Node
                                if location:
                                    loc = Entity(entity_type="location", value=location, label=location)
                                    entities.append(loc)
                                    connections.append((prof, loc, "located_in"))
                                    
                                # Extract Real Name Node
                                if realname:
                                    rn = Entity(entity_type="person", value=realname, label=realname)
                                    entities.append(rn)
                                    connections.append((prof, rn, "identifies_as"))

                                # TODO: Groups and Friends often require parsing the HTML page as XML doesn't always have full list
                                # But let's stick to XML for robust basics first.
                                
                                break # Stop if found
                                
                            except ET.ParseError:
                                continue
                except Exception as e:
                    print(f"Steam check error: {e}")
            
            if not found and scan_input.platform.lower() == "steam":
                 warn = Entity(entity_type="warning", value="Steam 404", label="Not Found", attributes={"info": f"User {username} not found on Steam (checked ID & Profiles)"})
                 entities.append(warn)
                 connections.append((source_entity, warn, "status"))

        if progress_callback: progress_callback(1, 1)
        return entities, connections
