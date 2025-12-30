"""
Domain Infrastructure Scan Module
Gathers WHOIS, DNS, and infrastructure information for domains and IPs.
"""

import asyncio
import socket
from typing import List, Optional, Callable, Tuple, Dict, Any
import dns.resolver
import dns.exception
import whois

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity
from ..config import config
import shodan


class DomainInfraScan(BaseOSINTModule):
    """
    Domain infrastructure scanning module.
    Gathers WHOIS, DNS records, and basic connectivity info.
    """
    
    # Common DNS record types to query
    DNS_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]
    
    # Common ports to check
    COMMON_PORTS = [21, 22, 25, 80, 443, 3306, 3389, 5432, 8080, 8443]
    
    @property
    def name(self) -> str:
        return "Domain Infrastructure Scan"
    
    @property
    def description(self) -> str:
        return "Gathers WHOIS, DNS records, and infrastructure information"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "ip"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute domain infrastructure scan."""
        domain = scan_input.domain.strip().lower()
        ip_address = scan_input.ip_address.strip()
        
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        total_steps = 4  # WHOIS, DNS, resolve IP, port scan
        current_step = 0
        
        # Process domain
        if domain:
            if domain.startswith(("http://", "https://")):
                from urllib.parse import urlparse
                domain = urlparse(domain).netloc
            
            # Create domain entity
            domain_entity = Entity(
                entity_type="domain",
                value=domain,
                label=domain,
                attributes={"source": "input"}
            )
            entities.append(domain_entity)
            
            # 1. WHOIS lookup
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps)
            
            whois_data = await self._get_whois(domain)
            if whois_data:
                domain_entity.attributes.update(whois_data)
                
                # Create registrar entity
                if whois_data.get("registrar"):
                    registrar_entity = Entity(
                        entity_type="company",
                        value=whois_data["registrar"],
                        label=whois_data["registrar"],
                        attributes={"type": "registrar"}
                    )
                    entities.append(registrar_entity)
                    connections.append((domain_entity, registrar_entity, "registered_with"))
                
                # Create registrant entity if available
                if whois_data.get("registrant_name"):
                    registrant_entity = Entity(
                        entity_type="person",
                        value=whois_data["registrant_name"],
                        label=whois_data["registrant_name"],
                        attributes={
                            "email": whois_data.get("registrant_email", ""),
                            "organization": whois_data.get("registrant_org", "")
                        }
                    )
                    entities.append(registrant_entity)
                    connections.append((domain_entity, registrant_entity, "registered_by"))
            
            # 2. DNS records
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps)
            
            dns_records = await self._get_dns_records(domain)
            domain_entity.attributes["dns_records"] = dns_records
            
            # Create entities for IPs, nameservers, mail servers
            for record in dns_records.get("A", []):
                ip_entity = Entity(
                    entity_type="ip",
                    value=record,
                    label=record,
                    attributes={"record_type": "A", "source": "dns"}
                )
                entities.append(ip_entity)
                connections.append((domain_entity, ip_entity, "resolves_to"))
            
            for record in dns_records.get("AAAA", []):
                ip_entity = Entity(
                    entity_type="ip",
                    value=record,
                    label=record,
                    attributes={"record_type": "AAAA", "source": "dns"}
                )
                entities.append(ip_entity)
                connections.append((domain_entity, ip_entity, "resolves_to"))
            
            for record in dns_records.get("NS", []):
                ns_entity = Entity(
                    entity_type="hostname",
                    value=record,
                    label=record,
                    attributes={"type": "nameserver", "source": "dns"}
                )
                entities.append(ns_entity)
                connections.append((domain_entity, ns_entity, "served_by"))
            
            for record in dns_records.get("MX", []):
                # MX records include priority, just take the hostname
                mx_host = record.split()[-1] if " " in record else record
                mx_entity = Entity(
                    entity_type="hostname",
                    value=mx_host,
                    label=mx_host,
                    attributes={"type": "mail_server", "source": "dns"}
                )
                entities.append(mx_entity)
                connections.append((domain_entity, mx_entity, "mail_handled_by"))
            
            # Resolve domain to IP for port scan
            if dns_records.get("A"):
                ip_address = dns_records["A"][0]
        
        # Process IP address
        if ip_address:
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps)
            
            # Check if we already have this IP
            ip_exists = any(e.value == ip_address and e.entity_type == "ip" for e in entities)
            
            if not ip_exists:
                ip_entity = Entity(
                    entity_type="ip",
                    value=ip_address,
                    label=ip_address,
                    attributes={"source": "input"}
                )
                entities.append(ip_entity)
            else:
                ip_entity = next(e for e in entities if e.value == ip_address and e.entity_type == "ip")
            
            # 3. Port scan
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps)
            
            open_ports = await self._scan_ports(ip_address)
            ip_entity.attributes["open_ports"] = open_ports
            
            # Shodan Lookup
            shodan_key = config.get("api_keys", "shodan")
            if shodan_key:
                try:
                    if progress_callback:
                        progress_callback(current_step, total_steps) # Update progress status
                        
                    api = shodan.Shodan(shodan_key)
                    host = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: api.host(ip_address)
                    )
                    
                    if host:
                        ip_entity.attributes["shodan_data"] = True
                        ip_entity.attributes["ports"] = host.get("ports", [])
                        ip_entity.attributes["org"] = host.get("org", "n/a")
                        ip_entity.attributes["os"] = host.get("os", "n/a")
                        if "vulns" in host:
                            ip_entity.attributes["vulnerabilities"] = list(host["vulns"])
                            
                        # Add ports as entities? Maybe too much noise.
                        # Just attributes is fine for now.
                except Exception as e:
                    # Silently fail for API errors (invalid key, etc)
                    pass
            
            # Reverse DNS
            try:
                hostnames = socket.gethostbyaddr(ip_address)
                if hostnames and hostnames[0]:
                    ip_entity.attributes["reverse_dns"] = hostnames[0]
            except socket.herror:
                pass
        
        return entities, connections
    
    async def _get_whois(self, domain: str) -> Dict[str, Any]:
        """Get WHOIS information for a domain."""
        try:
            loop = asyncio.get_event_loop()
            w = await loop.run_in_executor(None, lambda: whois.whois(domain))
            
            if w is None:
                return {}
            
            return {
                "registrar": w.get("registrar", ""),
                "creation_date": str(w.get("creation_date", "")),
                "expiration_date": str(w.get("expiration_date", "")),
                "updated_date": str(w.get("updated_date", "")),
                "name_servers": list(w.get("name_servers", [])) if w.get("name_servers") else [],
                "registrant_name": w.get("name", ""),
                "registrant_org": w.get("org", ""),
                "registrant_email": w.get("emails", [""])[0] if isinstance(w.get("emails"), list) and w.get("emails") else "",
                "registrant_country": w.get("country", ""),
                "status": list(w.get("status", [])) if w.get("status") else [],
                "dnssec": str(w.get("dnssec", "")),
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_dns_records(self, domain: str) -> Dict[str, List[str]]:
        """Get DNS records for a domain."""
        records: Dict[str, List[str]] = {}
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 10
        
        for record_type in self.DNS_RECORD_TYPES:
            try:
                answers = resolver.resolve(domain, record_type)
                records[record_type] = [str(rdata) for rdata in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException):
                pass
            except Exception:
                pass
        
        return records
    
    async def _scan_ports(self, ip: str, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """Perform basic port scan on common ports."""
        open_ports = []
        
        async def check_port(port: int) -> Optional[Dict[str, Any]]:
            try:
                conn = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(conn, timeout=timeout)
                writer.close()
                await writer.wait_closed()
                
                service_names = {
                    21: "FTP", 22: "SSH", 25: "SMTP", 80: "HTTP",
                    443: "HTTPS", 3306: "MySQL", 3389: "RDP",
                    5432: "PostgreSQL", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt"
                }
                return {
                    "port": port,
                    "state": "open",
                    "service": service_names.get(port, "unknown")
                }
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return None
        
        tasks = [check_port(port) for port in self.COMMON_PORTS]
        results = await asyncio.gather(*tasks)
        
        open_ports = [r for r in results if r is not None]
        return open_ports
