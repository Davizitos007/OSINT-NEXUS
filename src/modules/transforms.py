"""
OSINT-Nexus Transform Modules
Advanced transforms for Maltego-like entity expansion.
"""

import asyncio
import aiohttp
import socket
from typing import List, Optional, Callable, Tuple, Dict, Any
from urllib.parse import urlparse, quote
from datetime import datetime

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity


class WaybackMachineTransform(BaseOSINTModule):
    """
    Wayback Machine transform to find archived versions of websites.
    Uses the free Wayback Machine API.
    """
    
    @property
    def name(self) -> str:
        return "Wayback Machine"
    
    @property
    def description(self) -> str:
        return "Finds archived versions of websites from the Internet Archive"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "url"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Query Wayback Machine for archived URLs."""
        domain = scan_input.domain.strip().lower()
        if domain.startswith(("http://", "https://")):
            domain = urlparse(domain).netloc
        
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        if progress_callback:
            progress_callback(0, 2)
        
        # Create domain entity
        domain_entity = Entity(
            entity_type="domain",
            value=domain,
            label=domain,
            attributes={"source": "input"}
        )
        entities.append(domain_entity)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Query CDX API for archived snapshots
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&limit=50&fl=timestamp,original,statuscode,mimetype"
            
            try:
                async with session.get(cdx_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if progress_callback:
                            progress_callback(1, 2)
                        
                        if len(data) > 1:  # First row is header
                            for row in data[1:]:  # Skip header
                                timestamp, original_url, status, mimetype = row[:4]
                                
                                # Create snapshot entity
                                wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                                
                                # Parse date
                                try:
                                    date_str = datetime.strptime(timestamp[:8], "%Y%m%d").strftime("%Y-%m-%d")
                                except:
                                    date_str = timestamp
                                
                                snapshot_entity = Entity(
                                    entity_type="url",
                                    value=wayback_url,
                                    label=f"Archive: {date_str}",
                                    attributes={
                                        "original_url": original_url,
                                        "timestamp": timestamp,
                                        "date": date_str,
                                        "status_code": status,
                                        "mime_type": mimetype,
                                        "source": "wayback_machine"
                                    }
                                )
                                entities.append(snapshot_entity)
                                connections.append((snapshot_entity, domain_entity, "archived_version_of"))
                
            except Exception as e:
                pass
        
        if progress_callback:
            progress_callback(2, 2)
        
        return entities, connections


class ShodanTransform(BaseOSINTModule):
    """
    Shodan transform for IP/domain reconnaissance.
    Requires free Shodan API key for full functionality.
    """
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "Shodan Lookup"
    
    @property
    def description(self) -> str:
        return "Searches Shodan for host information, open ports, and vulnerabilities"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "ip"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Query Shodan for IP/domain information."""
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        target = scan_input.ip_address or scan_input.domain
        if not target:
            return entities, connections
        
        # Resolve domain to IP if needed
        ip_address = scan_input.ip_address
        domain = scan_input.domain
        
        if domain and not ip_address:
            try:
                ip_address = socket.gethostbyname(domain)
            except socket.gaierror:
                pass
        
        if progress_callback:
            progress_callback(0, 2)
        
        # Create base entity
        if domain:
            domain_entity = Entity(
                entity_type="domain",
                value=domain,
                label=domain,
                attributes={"source": "input"}
            )
            entities.append(domain_entity)
        
        if ip_address:
            ip_entity = Entity(
                entity_type="ip",
                value=ip_address,
                label=ip_address,
                attributes={"source": "resolved" if domain else "input"}
            )
            entities.append(ip_entity)
            
            if domain:
                connections.append((domain_entity, ip_entity, "resolves_to"))
            
            # Query Shodan InternetDB (free, no API key required)
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:
                try:
                    url = f"https://internetdb.shodan.io/{ip_address}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if progress_callback:
                                progress_callback(1, 2)
                            
                            # Update IP entity with Shodan data
                            ip_entity.attributes.update({
                                "ports": data.get("ports", []),
                                "hostnames": data.get("hostnames", []),
                                "cpes": data.get("cpes", []),
                                "vulns": data.get("vulns", []),
                                "tags": data.get("tags", []),
                                "source": "shodan_internetdb"
                            })
                            
                            # Create port entities
                            for port in data.get("ports", [])[:10]:  # Limit to 10
                                port_entity = Entity(
                                    entity_type="port",
                                    value=f"{ip_address}:{port}",
                                    label=f"Port {port}",
                                    attributes={
                                        "port": port,
                                        "ip": ip_address,
                                        "source": "shodan"
                                    }
                                )
                                entities.append(port_entity)
                                connections.append((ip_entity, port_entity, "has_open_port"))
                            
                            # Create hostname entities
                            for hostname in data.get("hostnames", []):
                                hostname_entity = Entity(
                                    entity_type="hostname",
                                    value=hostname,
                                    label=hostname,
                                    attributes={"source": "shodan"}
                                )
                                entities.append(hostname_entity)
                                connections.append((ip_entity, hostname_entity, "has_hostname"))
                            
                            # Create vulnerability entities
                            for vuln in data.get("vulns", [])[:10]:  # Limit
                                vuln_entity = Entity(
                                    entity_type="vulnerability",
                                    value=vuln,
                                    label=vuln,
                                    attributes={"cve": vuln, "source": "shodan"}
                                )
                                entities.append(vuln_entity)
                                connections.append((ip_entity, vuln_entity, "has_vulnerability"))
                
                except Exception as e:
                    pass
        
        if progress_callback:
            progress_callback(2, 2)
        
        return entities, connections


class VirusTotalTransform(BaseOSINTModule):
    """
    VirusTotal transform for threat intelligence.
    Uses free API (limited to 4 requests/minute).
    """
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "VirusTotal Lookup"
    
    @property
    def description(self) -> str:
        return "Checks domains/IPs against VirusTotal threat database"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "ip"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Query VirusTotal for threat information."""
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        # VirusTotal requires API key for proper functionality
        # For demo, we'll create placeholder entities
        
        domain = scan_input.domain
        ip = scan_input.ip_address
        
        if progress_callback:
            progress_callback(0, 1)
        
        if domain:
            domain_entity = Entity(
                entity_type="domain",
                value=domain,
                label=domain,
                attributes={
                    "source": "input",
                    "virustotal_note": "Full VT integration requires API key"
                }
            )
            entities.append(domain_entity)
        
        if ip:
            ip_entity = Entity(
                entity_type="ip",
                value=ip,
                label=ip,
                attributes={
                    "source": "input",
                    "virustotal_note": "Full VT integration requires API key"
                }
            )
            entities.append(ip_entity)
        
        if progress_callback:
            progress_callback(1, 1)
        
        return entities, connections


class ReverseDNSTransform(BaseOSINTModule):
    """
    Reverse DNS lookup transform.
    Finds hostnames associated with an IP address.
    """
    
    @property
    def name(self) -> str:
        return "Reverse DNS"
    
    @property
    def description(self) -> str:
        return "Performs reverse DNS lookup to find hostnames for an IP"
    
    @property
    def input_types(self) -> List[str]:
        return ["ip"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Perform reverse DNS lookup."""
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        ip = scan_input.ip_address
        if not ip:
            return entities, connections
        
        if progress_callback:
            progress_callback(0, 1)
        
        ip_entity = Entity(
            entity_type="ip",
            value=ip,
            label=ip,
            attributes={"source": "input"}
        )
        entities.append(ip_entity)
        
        try:
            # Reverse DNS lookup
            hostname, aliases, _ = socket.gethostbyaddr(ip)
            
            # Primary hostname
            if hostname:
                hostname_entity = Entity(
                    entity_type="hostname",
                    value=hostname,
                    label=hostname,
                    attributes={"source": "reverse_dns", "primary": True}
                )
                entities.append(hostname_entity)
                connections.append((ip_entity, hostname_entity, "resolves_to"))
            
            # Aliases
            for alias in aliases:
                alias_entity = Entity(
                    entity_type="hostname",
                    value=alias,
                    label=alias,
                    attributes={"source": "reverse_dns", "primary": False}
                )
                entities.append(alias_entity)
                connections.append((ip_entity, alias_entity, "also_known_as"))
        
        except socket.herror:
            ip_entity.attributes["reverse_dns_error"] = "No PTR record found"
        
        if progress_callback:
            progress_callback(1, 1)
        
        return entities, connections


class GeoIPTransform(BaseOSINTModule):
    """
    GeoIP lookup transform.
    Finds geographic location of an IP address using free API.
    """
    
    @property
    def name(self) -> str:
        return "GeoIP Lookup"
    
    @property
    def description(self) -> str:
        return "Finds geographic location of an IP address"
    
    @property
    def input_types(self) -> List[str]:
        return ["ip"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Perform GeoIP lookup."""
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        ip = scan_input.ip_address
        if not ip:
            return entities, connections
        
        if progress_callback:
            progress_callback(0, 1)
        
        ip_entity = Entity(
            entity_type="ip",
            value=ip,
            label=ip,
            attributes={"source": "input"}
        )
        entities.append(ip_entity)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            try:
                # Use ip-api.com (free, no key required, 45 req/min)
                url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "success":
                            # Update IP entity
                            ip_entity.attributes.update({
                                "country": data.get("country", ""),
                                "country_code": data.get("countryCode", ""),
                                "region": data.get("regionName", ""),
                                "city": data.get("city", ""),
                                "zip": data.get("zip", ""),
                                "latitude": data.get("lat", 0),
                                "longitude": data.get("lon", 0),
                                "timezone": data.get("timezone", ""),
                                "isp": data.get("isp", ""),
                                "org": data.get("org", ""),
                                "asn": data.get("as", ""),
                            })
                            
                            # Create location entity
                            city = data.get("city", "Unknown")
                            country = data.get("country", "Unknown")
                            location_str = f"{city}, {country}"
                            
                            location_entity = Entity(
                                entity_type="location",
                                value=location_str,
                                label=location_str,
                                attributes={
                                    "city": city,
                                    "region": data.get("regionName", ""),
                                    "country": country,
                                    "country_code": data.get("countryCode", ""),
                                    "latitude": data.get("lat", 0),
                                    "longitude": data.get("lon", 0),
                                    "source": "geoip"
                                }
                            )
                            entities.append(location_entity)
                            connections.append((ip_entity, location_entity, "located_in"))
                            
                            # Create ISP entity
                            isp = data.get("isp")
                            if isp:
                                isp_entity = Entity(
                                    entity_type="company",
                                    value=isp,
                                    label=isp,
                                    attributes={
                                        "type": "isp",
                                        "asn": data.get("as", ""),
                                        "source": "geoip"
                                    }
                                )
                                entities.append(isp_entity)
                                connections.append((ip_entity, isp_entity, "provided_by"))
            
            except Exception as e:
                pass
        
        if progress_callback:
            progress_callback(1, 1)
        
        return entities, connections


class SubdomainEnumTransform(BaseOSINTModule):
    """
    Subdomain enumeration transform.
    Finds subdomains using certificate transparency logs.
    """
    
    @property
    def name(self) -> str:
        return "Subdomain Enum"
    
    @property
    def description(self) -> str:
        return "Enumerates subdomains using certificate transparency logs"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Enumerate subdomains."""
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        domain = scan_input.domain.strip().lower()
        if domain.startswith(("http://", "https://")):
            domain = urlparse(domain).netloc
        
        if progress_callback:
            progress_callback(0, 2)
        
        domain_entity = Entity(
            entity_type="domain",
            value=domain,
            label=domain,
            attributes={"source": "input"}
        )
        entities.append(domain_entity)
        
        subdomains = set()
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Use crt.sh (certificate transparency)
            try:
                url = f"https://crt.sh/?q=%.{domain}&output=json"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if progress_callback:
                            progress_callback(1, 2)
                        
                        for entry in data:
                            name = entry.get("name_value", "")
                            # Handle multiple names separated by newline
                            for subdomain in name.split("\n"):
                                subdomain = subdomain.strip().lower()
                                if subdomain and subdomain.endswith(domain):
                                    subdomains.add(subdomain)
            
            except Exception as e:
                pass
        
        # Create subdomain entities
        for subdomain in list(subdomains)[:50]:  # Limit to 50
            if subdomain != domain:
                subdomain_entity = Entity(
                    entity_type="subdomain",
                    value=subdomain,
                    label=subdomain,
                    attributes={"source": "crt.sh"}
                )
                entities.append(subdomain_entity)
                connections.append((subdomain_entity, domain_entity, "subdomain_of"))
        
        if progress_callback:
            progress_callback(2, 2)
        
        return entities, connections
