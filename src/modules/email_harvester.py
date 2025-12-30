"""
Email Harvester Module
Discovers emails, names, and subdomains from a target domain.
Also performs deep identity reconnaissance on specific email inputs.
"""

import re
import asyncio
import aiohttp
import hashlib
from typing import List, Optional, Callable, Tuple, Set
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity
from ..config import config


class EmailHarvester(BaseOSINTModule):
    """
    Email harvesting module that discovers emails and related information from domains.
    Also performs identity checks (Gravatar, Google Dorks) on single email inputs.
    """
    
    # Common email patterns
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )
    
    # Search engines to query
    SEARCH_ENGINES = {
        "google": "https://www.google.com/search?q=site:{domain}+email&num=100",
        "bing": "https://www.bing.com/search?q=site:{domain}+email&count=50",
        "duckduckgo": "https://duckduckgo.com/html/?q=site:{domain}+email",
    }
    
    # Common pages to check for emails
    COMMON_PAGES = [
        "/contact", "/contact-us", "/about", "/about-us",
        "/team", "/people", "/staff", "/leadership",
        "/careers", "/jobs", "/support", "/help",
    ]
    
    @property
    def name(self) -> str:
        return "Email Harvester"
    
    @property
    def description(self) -> str:
        return "Discovers emails from domains and performs identity checks on emails (Gravatar, Dorks)"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "email"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute email reconnaissance."""
        
        # Branch logic: Domain Harvesting vs Single Email Recon
        if scan_input.email:
            return await self._analyze_email(scan_input.email, progress_callback)
        elif scan_input.domain:
            return await self._harvest_domain(scan_input, progress_callback)
        else:
            return [], []

    async def _analyze_email(self, email: str, progress_callback) -> Tuple[List[Entity], List[tuple]]:
        """Perform deep analysis on a single email."""
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        source_entity = Entity(entity_type="email", value=email, label=email, attributes={"source": "input"})
        entities.append(source_entity)
        
        # 1. Identity Check: Gravatar (MD5 hash)
        email_hash = hashlib.md5(email.lower().encode()).hexdigest()
        profile_url = f"https://www.gravatar.com/{email_hash}.json"
        
        async with aiohttp.ClientSession() as session:
            # Check for Profile
            try:
                async with session.get(profile_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        entry = data.get("entry", [])[0]
                        
                        # Extract Name/Username
                        if "preferredUsername" in entry:
                            username = entry["preferredUsername"]
                            user_ent = Entity(entity_type="username", value=username, label=username, attributes={"source": "gravatar"})
                            entities.append(user_ent)
                            connections.append((source_entity, user_ent, "uses_username"))
                            
                        if "displayName" in entry:
                            name = entry["displayName"]
                            name_ent = Entity(entity_type="person", value=name, label=name, attributes={"source": "gravatar"})
                            entities.append(name_ent)
                            connections.append((source_entity, name_ent, "real_name"))
                            
                        # Extract Photos
                        if "thumbnailUrl" in entry:
                            img_url = entry["thumbnailUrl"]
                            img_ent = Entity(entity_type="image", value=img_url, label="Profile Photo", attributes={"url": img_url})
                            entities.append(img_ent)
                            connections.append((source_entity, img_ent, "profile_photo"))
                            
                        # Extract Location
                        if "currentLocation" in entry:
                            loc = entry["currentLocation"]
                            loc_ent = Entity(entity_type="location", value=loc, label=loc)
                            entities.append(loc_ent)
                            connections.append((source_entity, loc_ent, "located_in"))
                            
                        # Extract About Me / Urls
                        if "aboutMe" in entry:
                            source_entity.attributes["about"] = entry["aboutMe"]

            except Exception as e:
                print(f"Gravatar error: {e}")
                
            # 2. Google Dorks for Email (Footprint)
            api_key = config.get("api_keys", "google_api")
            cx = config.get("api_keys", "google_cse_id")
            
            if api_key and cx:
                dorks = [
                    f'"{email}"', 
                    f'"{email}" site:linkedin.com',
                    f'"{email}" site:facebook.com',
                    f'"{email}" site:twitter.com',
                    f'"{email}" filetype:pdf OR filetype:doc OR filetype:xls'
                ]
                
                url = "https://www.googleapis.com/customsearch/v1"
                for dork in dorks:
                    params = {'key': api_key, 'cx': cx, 'q': dork}
                    try:
                        async with session.get(url, params=params) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if "items" in data:
                                    for item in data["items"]:
                                        link = item.get("link")
                                        title = item.get("title")
                                        if link:
                                            url_ent = Entity(
                                                entity_type="url", 
                                                value=link, 
                                                label=title[:30] + "..." if title else link[:30], 
                                                attributes={"title": title, "snippet": item.get("snippet")}
                                            )
                                            entities.append(url_ent)
                                            connections.append((source_entity, url_ent, "found_publicly_on"))
                    except Exception as e:
                         print(f"Google Dork error: {e}")
        if len(entities) == 1: # Only source email
             # No identity info found
             warning = Entity(
                entity_type="warning",
                value="No Identity Info",
                label="No Public Identity",
                attributes={"info": "Checked Gravatar and Google Dorks. No public profile found for this email."}
             )
             entities.append(warning)
             connections.append((source_entity, warning, "no_results"))

        if progress_callback: progress_callback(1, 1)
        return entities, connections

    async def _harvest_domain(self, scan_input: ScanInput, progress_callback) -> Tuple[List[Entity], List[tuple]]:
        """Execute domain harvesting."""
        domain = scan_input.domain.lower().strip()
        if domain.startswith(("http://", "https://")):
            domain = urlparse(domain).netloc
        
        entities: List[Entity] = []
        connections: List[tuple] = []
        discovered_emails: Set[str] = set()
        discovered_subdomains: Set[str] = set()
        
        # Create domain entity
        domain_entity = Entity(
            entity_type="domain",
            value=domain,
            label=domain,
            attributes={"source": "input"}
        )
        entities.append(domain_entity)
        
        total_steps = len(self.COMMON_PAGES) + len(scan_input.sources)
        current_step = 0
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ) as session:
            
            # 1. Check common pages on the domain
            for page in self.COMMON_PAGES:
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps)
                
                try:
                    url = f"https://{domain}{page}"
                    async with session.get(url, ssl=False) as response:
                        if response.status == 200:
                            html = await response.text()
                            self._extract_emails(html, domain, discovered_emails)
                            self._extract_subdomains(html, domain, discovered_subdomains)
                except Exception:
                    pass
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            # 2. Check main page
            try:
                url = f"https://{domain}"
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        html = await response.text()
                        self._extract_emails(html, domain, discovered_emails)
                        self._extract_subdomains(html, domain, discovered_subdomains)
            except Exception:
                pass
            
            # 3. Search engines (if selected)
            for source in scan_input.sources:
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps)
                
                if source.lower() in self.SEARCH_ENGINES:
                    try:
                        search_url = self.SEARCH_ENGINES[source.lower()].format(domain=domain)
                        async with session.get(search_url, ssl=False) as response:
                            if response.status == 200:
                                html = await response.text()
                                self._extract_emails(html, domain, discovered_emails)
                    except Exception:
                        pass
                    
                    await asyncio.sleep(1)  # Longer delay for search engines
        
        # Create entities for discovered emails
        if not discovered_emails:
            warning = Entity(
                entity_type="warning",
                value=f"No Emails: {domain}",
                label="No Emails Found",
                attributes={"info": f"Scanned {current_step} pages on {domain}. No emails found in public HTML."}
            )
            entities.append(warning)
            connections.append((domain_entity, warning, "no_results"))
            
        for email in discovered_emails:
            email_entity = Entity(
                entity_type="email",
                value=email,
                label=email,
                attributes={
                    "domain": domain,
                    "source": "harvested"
                }
            )
            entities.append(email_entity)
            connections.append((email_entity, domain_entity, "found_on"))
            
            # Try to extract name from email
            local_part = email.split("@")[0]
            if "." in local_part or "_" in local_part:
                parts = re.split(r'[._]', local_part)
                if len(parts) >= 2:
                    name = " ".join(p.capitalize() for p in parts if len(p) > 1)
                    if name and len(name) > 3:
                        person_entity = Entity(
                            entity_type="person",
                            value=name,
                            label=name,
                            attributes={
                                "email": email,
                                "source": "inferred"
                            }
                        )
                        entities.append(person_entity)
                        connections.append((person_entity, email_entity, "owns"))
        
        # Create entities for subdomains
        for subdomain in discovered_subdomains:
            if subdomain != domain:
                subdomain_entity = Entity(
                    entity_type="subdomain",
                    value=subdomain,
                    label=subdomain,
                    attributes={
                        "parent_domain": domain,
                        "source": "harvested"
                    }
                )
                entities.append(subdomain_entity)
                connections.append((subdomain_entity, domain_entity, "subdomain_of"))
        
        return entities, connections
    
    def _extract_emails(self, html: str, domain: str, emails: Set[str]):
        """Extract emails from HTML content."""
        found = self.EMAIL_PATTERN.findall(html)
        for email in found:
            email = email.lower()
            # Filter out common false positives
            if not any(fp in email for fp in ['example.com', 'domain.com', '@2x', '@3x', '.png', '.jpg']):
                # Optional: only include emails from target domain
                if domain in email or "@" in email:
                    emails.add(email)
    
    def _extract_subdomains(self, html: str, domain: str, subdomains: Set[str]):
        """Extract subdomains from HTML content."""
        pattern = re.compile(rf'([a-zA-Z0-9][-a-zA-Z0-9]*\.)*{re.escape(domain)}')
        found = pattern.findall(html)
        
        # Also look for full URLs
        url_pattern = re.compile(rf'https?://([a-zA-Z0-9][-a-zA-Z0-9.]*\.{re.escape(domain)})')
        url_matches = url_pattern.findall(html)
        
        for match in url_matches:
            if match and match != domain:
                subdomains.add(match.lower())
