"""
Harvester Recon Module
Implements functionality similar to 'TheHarvester' tool.
Aggregates subdomains, emails, and hosts from public sources like CRT.sh, HackerTarget, and Search Engines.
"""

import aiohttp
import re
import asyncio
from typing import List, Tuple, Optional, Callable, Dict, Set
from urllib.parse import urlparse

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity

class HarvesterReconModule(BaseOSINTModule):
    """
    Advanced Domain & Email Reconnaissance (TheHarvester style).
    """
    
    @property
    def name(self) -> str:
        return "TheHarvester Recon"
    
    @property
    def description(self) -> str:
        return "Aggregates subdomains, emails, and hosts from public sources (CRT.sh, HackerTarget, etc)."
    
    @property
    def input_types(self) -> List[str]:
        return ["domain"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute Harvester recon."""
        
        domain = scan_input.value
        # Basic validation
        if not domain or "." not in domain:
            return [], []

        entities: List[Entity] = []
        connections: List[tuple] = []
        
        source_entity = Entity(
            entity_type="domain",
            value=domain,
            label=domain,
            attributes={"source": "input"}
        )
        entities.append(source_entity)
        
        subdomains: Set[str] = set()
        emails: Set[str] = set()
        
        # Parallel Execution
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._query_crtsh(session, domain),
                self._query_hackertarget_hostsearch(session, domain),
                self._query_hackertarget_dnsdumpster(session, domain) # Placeholder conceptual
            ]
            
            # Update progress
            if progress_callback: progress_callback(1, 4)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            if progress_callback: progress_callback(3, 4)
            
            # Process Results
            for res in results:
                if isinstance(res, tuple):
                    subs, mails = res
                    subdomains.update(subs)
                    emails.update(mails)
                elif isinstance(res, list) or isinstance(res, set):
                    subdomains.update(res)

        # Create Entities
        for sub in subdomains:
            # Clean subdomain
            sub = sub.lower().strip()
            if sub.startswith("*."): sub = sub[2:]
            if not sub or sub == domain: continue
            
            sub_entity = Entity(
                entity_type="domain", # or 'subdomain'
                value=sub,
                label=sub,
                attributes={"parent_domain": domain, "source": "TheHarvester"}
            )
            entities.append(sub_entity)
            connections.append((source_entity, sub_entity, "has_subdomain"))
            
        for mail in emails:
            mail_entity = Entity(
                entity_type="email",
                value=mail,
                label=mail,
                attributes={"domain": domain}
            )
            entities.append(mail_entity)
            connections.append((source_entity, mail_entity, "has_email_record"))

        # Feedback
        if not subdomains and not emails:
             warn = Entity(entity_type="warning", value="No Recon Data", label="No Data Found", attributes={"info": "CRT.sh and HackerTarget returned no results."})
             entities.append(warn)
             connections.append((source_entity, warn, "status"))
        
        if progress_callback: progress_callback(4, 4)
        return entities, connections

    async def _query_crtsh(self, session, domain: str) -> Tuple[Set[str], Set[str]]:
        """Query CRT.sh for subdomains."""
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        subs = set()
        try:
            async with session.get(url, timeout=20) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json()
                        for entry in data:
                            name_value = entry.get("name_value", "")
                            # Split multiple domains in one cert
                            for part in name_value.split("\n"):
                                if domain in part:
                                    subs.add(part.strip())
                    except Exception:
                        # Fallback to text parsing if JSON fails (sometimes crt.sh behaves oddly)
                        text = await resp.text()
                        found = re.findall(r'<TD>([^<]+' + re.escape(domain) + r')</TD>', text)
                        subs.update(found)
        except Exception as e:
            print(f"CRT.sh error: {e}")
        return subs, set()

    async def _query_hackertarget_hostsearch(self, session, domain: str) -> Tuple[Set[str], Set[str]]:
        """Query HackerTarget Host Search."""
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        subs = set()
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Format: hostname,ip
                    for line in text.splitlines():
                        if "," in line:
                            host, ip = line.split(",")
                            if domain in host:
                                subs.add(host)
        except Exception as e:
            print(f"HackerTarget error: {e}")
        return subs, set()

    async def _query_hackertarget_dnsdumpster(self, session, domain: str) -> Tuple[Set[str], Set[str]]:
        """Placeholder for future DNS dumpster integration."""
        return set(), set()
