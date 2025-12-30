from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity
from typing import List, Optional, Callable, Dict, Any, Tuple
import asyncio
import aiohttp

class SocialLookupModule(BaseOSINTModule):
    """
    Social Media Lookup Module.
    Searches for usernames across multiple platforms.
    """
    
    # Supported platforms
    PLATFORMS = {
        "instagram": "https://www.instagram.com/{}",
        "facebook": "https://www.facebook.com/{}",
        "twitter": "https://twitter.com/{}",
        "github": "https://github.com/{}",
        "linkedin": "https://www.linkedin.com/in/{}",
        "pinterest": "https://www.pinterest.com/{}",
        "reddit": "https://www.reddit.com/user/{}",
        "tiktok": "https://www.tiktok.com/@{}",
        "snapchat": "https://www.snapchat.com/add/{}"
        # Add more as needed
    }
    
    @property
    def name(self) -> str:
        return "Social Media Lookup"
    
    @property
    def description(self) -> str:
        return "Finds social media profiles for a username."
    
    @property
    def input_types(self) -> List[str]:
        return ["username", "person"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute social lookup."""
        self.current_username = scan_input.username
        
        # Load Sherlock Data
        import json
        import os
        
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sherlock_data.json")
        sherlock_sites = {}
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                sherlock_sites = json.load(f)
        except Exception as e:
            print(f"Failed to load Sherlock data: {e}")
            # Fallback to internal dict if JSON fails
            sherlock_sites = {k: {"url": v, "errorType": "status_code"} for k, v in self.PLATFORMS.items()}

        # Filter platforms
        target_sites = sherlock_sites
        
        # Filter if specific platform requested
        if scan_input.platform and scan_input.platform.lower() not in ["", "generic (sherlock)"]:
            req = scan_input.platform.lower()
            # fuzzy match keys
            matches = {k: v for k, v in sherlock_sites.items() if k.lower() == req}
            if matches:
                target_sites = matches
            elif req == "github": 
                 # Handled by separate module, allowing overlap
                 target_sites = {k: v for k, v in sherlock_sites.items() if k.lower() == "github"}
            else:
                 target_sites = {}

        entities: List[Entity] = []
        connections: List[tuple] = []
        
        source_entity = Entity(
            entity_type="username",
            value=self.current_username,
            label=self.current_username,
            attributes={"source": "input"}
        )
        entities.append(source_entity)
        
        total = len(target_sites)
        completed = 0
        
        
        import re
        
        async with aiohttp.ClientSession() as session:
            for platform, site_data in target_sites.items():
                # 0. Regex Validation (Filter faulty inputs)
                regex_pattern = site_data.get("regexCheck")
                if regex_pattern:
                    try:
                        # Sherlock regexes are JS compatible, mostly work in Python but check anchors
                        if not re.search(regex_pattern, self.current_username):
                            # Username invalid for this platform
                            continue
                    except re.error:
                        pass # Ignore regex errors, proceed to check
                
                url_template = site_data.get("url")
                exists = await self._check_profile(session, url_template, platform, site_data)
                
                if exists:
                    profile_url = url_template.format(self.current_username)
                    
                    # --- Deep Extraction (Profile Scraping) ---
                    # Utilize the existing session to fetch the page content (if not already fetched in check_profile)
                    # Note: check_profile might have just overlapped. 
                    
                    attributes = {
                        "platform": platform, 
                        "url": profile_url,
                        "username": self.current_username
                    }
                    
                    # Attempt to extract Title/Bio
                    try:
                        async with session.get(profile_url, timeout=5) as p_resp:
                            if p_resp.status == 200:
                                content = await p_resp.text()
                                # Simple Regex for Title
                                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                                if title_match:
                                    attributes["page_title"] = title_match.group(1).strip()
                                
                                # Simple Regex for Description
                                desc_match = re.search(r'<meta name="description" content="(.*?)"', content, re.IGNORECASE)
                                if desc_match:
                                    attributes["bio"] = desc_match.group(1).strip()
                                    
                                # Simple Regex for Emails logic check (basic)
                                # email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                                # if email_match:
                                #     attributes["found_email"] = email_match.group(0)
                                    
                    except Exception:
                        pass

                    profile_entity = Entity(
                        entity_type="social_profile", 
                        value=profile_url,
                        label=f"{platform}: {self.current_username}",
                        attributes=attributes
                    )
                    entities.append(profile_entity)
                    connections.append((source_entity, profile_entity, "has_account"))
                    
                    # If we found an email, create a node!
                    if "found_email" in attributes:
                        email_val = attributes["found_email"]
                        e_ent = Entity(entity_type="email", value=email_val, label=email_val, attributes={"source": platform})
                        entities.append(e_ent)
                        connections.append((profile_entity, e_ent, "mentions_email"))
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                    
        if not entities or len(entities) == 1: 
             warning = Entity(
                entity_type="warning",
                value="No Social Profiles",
                label="No Profiles Found",
                attributes={"info": f"Checked {total} platforms. No public profiles found."}
             )
             entities.append(warning)
             connections.append((source_entity, warning, "no_results"))
                    
        return entities, connections

    async def _check_profile(self, session, url_template: str, platform: str, config: Dict = None) -> bool:
        """Check if profile exists using Sherlock-style logic."""
        if not config: config = {}
        
        # Format URL
        try:
            url = url_template.format(self.current_username)
        except Exception:
            return False

        error_type = config.get("errorType", "status_code")
        
        try:
            # Use common browser headers to avoid blocking
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            
            async with session.get(url, headers=headers, timeout=10, allow_redirects=True) as response:
                # 1. Status Code Check
                if error_type == "status_code":
                    return response.status == 200
                
                # 2. Message Check (if status is 200 but content says "Not Found")
                elif error_type == "message":
                    if response.status != 200: return False
                    error_msg = config.get("errorMsg", "User not found")
                    text = await response.text()
                    return error_msg not in text
                    
                # 3. Response URL Check (Redirection)
                elif error_type == "response_url":
                    # If redirected to a specific error URL
                    error_url = config.get("errorUrl", "")
                    if error_url:
                        # Check if final URL matches error URL
                        # Note: errorUrl in json might have placeholders
                        formatted_err = error_url.format(username=self.current_username)
                        if formatted_err in str(response.url):
                            return False
                    return response.status == 200
                    
        except Exception:
            return False
            
        return False
