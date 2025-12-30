"""
IP Recon Module
Performs geolocation and RIR lookups for IP addresses and Domains (resolves them).
Uses ip-api.com (free).
"""

import aiohttp
import socket
from typing import List, Tuple, Optional, Callable
from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity

class IPReconModule(BaseOSINTModule):
    @property
    def name(self) -> str:
        return "IP/Geo Recon"
    
    @property
    def description(self) -> str:
        return "Resolves domain to IP and fetches Geolocation/ISP info."
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "ip_address", "host"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        
        target = scan_input.value
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        # Determine if IP or Domain
        is_ip = False
        try:
            socket.inet_aton(target)
            is_ip = True
        except socket.error:
            is_ip = False
            
        ip_addr = target
        
        source_entity = Entity(
            entity_type="ip_address" if is_ip else "domain",
            value=target,
            label=target,
            attributes={"source": "input"}
        )
        entities.append(source_entity)
        
        if not is_ip:
            try:
                # Resolve
                ip_addr = socket.gethostbyname(target)
                ip_entity = Entity(
                    entity_type="ip_address",
                    value=ip_addr,
                    label=ip_addr,
                    attributes={"resolved_from": target}
                )
                entities.append(ip_entity)
                connections.append((source_entity, ip_entity, "resolves_to"))
                source_for_geo = ip_entity
            except Exception:
                # Failed resolve
                return entities, connections
        else:
            source_for_geo = source_entity

        # Geo Lookup
        url = f"http://ip-api.com/json/{ip_addr}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "success":
                            country = data.get("country")
                            city = data.get("city")
                            isp = data.get("isp")
                            lat = data.get("lat")
                            lon = data.get("lon")
                            
                            # Location Node
                            loc_str = f"{city}, {country}"
                            loc_ent = Entity(
                                entity_type="location",
                                value=loc_str,
                                label=loc_str,
                                attributes={"lat": lat, "lon": lon, "country": country}
                            )
                            entities.append(loc_ent)
                            connections.append((source_for_geo, loc_ent, "located_in"))
                            
                            # ISP Node
                            isp_ent = Entity(
                                entity_type="organization",
                                value=isp,
                                label=isp,
                                attributes={"type": "ISP"}
                            )
                            entities.append(isp_ent)
                            connections.append((source_for_geo, isp_ent, "hosted_by"))
                            
            except Exception as e:
                print(f"IP Recon error: {e}")

        # --- RDAP / WHOIS Lookup ---
        # Query rdap.org for domain/IP registration data
        rdap_url = f"https://rdap.org/domain/{target}" if not is_ip else f"https://rdap.org/ip/{target}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(rdap_url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        handle = data.get("handle")
                        name = data.get("name") # Network name or Domain name
                        
                        whois_info = []
                        if handle: whois_info.append(f"Handle: {handle}")
                        if name: whois_info.append(f"Name: {name}")
                        
                        # Entities (entities field in RDAP contains contact info)
                        rdap_entities = data.get("entities", [])
                        emails = set()
                        for ent in rdap_entities:
                            # Recursive search for vcardArray
                            # Simplified: just look for 'registrar'
                            roles = ent.get("roles", [])
                            if "registrar" in roles:
                                registrar_name = ent.get("handle")
                                # Extract vcard fn if possible (complex structure)
                                whois_info.append(f"Registrar: {registrar_name}")
                            
                            # Try to find abuse emails in remarks or standard fields
                            # RDAP JSON is deep.
                        
                        summary = ", ".join(whois_info)
                        whois_node = Entity(
                            entity_type="whois_record",
                            value=rdap_url,
                            label="Whois/RDAP Info",
                            attributes={"info": summary, "raw_rdap": str(data)[:200]+"..."}
                        )
                        entities.append(whois_node)
                        connections.append((source_entity, whois_node, "registered_info"))
                        
            except Exception as e:
                print(f"RDAP error: {e}")
        
        if progress_callback: progress_callback(1, 1)
        return entities, connections
