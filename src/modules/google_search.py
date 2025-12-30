from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity
from ..config import config
from typing import List, Optional, Callable, Tuple
import asyncio
import aiohttp
import urllib.parse

class GoogleSearchModule(BaseOSINTModule):
    """
    Google Custom Search Module.
    Uses Google API to search for entities.
    """
    
    @property
    def name(self) -> str:
        return "Google Search"
    
    @property
    def description(self) -> str:
        return "Searches Google for username or domain using Custom Search API."
    
    @property
    def input_types(self) -> List[str]:
        return ["username", "person", "domain", "company"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute Google search."""
        query_val = ""
        if scan_input.username:
            query_val = scan_input.username
        elif scan_input.domain:
            query_val = scan_input.domain
        
        if not query_val:
            return [], []

        entities: List[Entity] = []
        connections: List[tuple] = []
        
        source_entity = Entity(
            entity_type="username" if scan_input.username else "domain",
            value=query_val,
            label=query_val,
            attributes={"source": "input"}
        )
        entities.append(source_entity)
        
        # Check API Key
        api_key = config.get("api_keys", "google_api")
        cx = config.get("api_keys", "google_cse_id")
        
        if not api_key:
            # Return a warning entity so the user sees it in the graph
            warning = Entity(
                entity_type="warning",
                value="Missing Google API Key",
                label="Setup Google API Key",
                attributes={"error": "Check Settings > API Keys"}
            )
            entities.append(warning)
            return entities, connections
            
        if not cx:
             # Return a warning entity
             warning = Entity(
                entity_type="warning",
                value="Missing Google CX ID",
                label="Setup Google CX ID",
                attributes={"error": "Check Settings > API Keys. See Walkthrough."}
             )
             entities.append(warning)
             return entities, connections
             
        async with aiohttp.ClientSession() as session:
            # Google Custom Search API
            
            # Construct Query: 
            # If username, search social sites
            q = query_val
            if scan_input.username:
                q = f'"{query_val}" (site:instagram.com OR site:twitter.com OR site:linkedin.com OR site:facebook.com)'
            
            params = {
                'key': api_key,
                'cx': cx,
                'q': q
            }
            
            url = "https://www.googleapis.com/customsearch/v1"
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        
                        if not items:
                            # Explicitly show no results were found
                            no_res = Entity(
                                entity_type="warning",
                                value=f"No Results: {query_val[:20]}...",
                                label="No Search Results",
                                attributes={"query": query_val, "info": "Google returned 0 results."}
                            )
                            entities.append(no_res)
                            connections.append((source_entity, no_res, "no_match"))
                            
                        for item in items:
                            link = item.get("link")
                            title = item.get("title")
                            snippet = item.get("snippet")
                            
                            if link:
                                # Create URL entity
                                url_entity = Entity(
                                    entity_type="url",
                                    value=link,
                                    label=title[:30] + "..." if title else link[:30],
                                    attributes={
                                        "title": title,
                                        "snippet": snippet,
                                        "url": link
                                    }
                                )
                                entities.append(url_entity)
                                connections.append((source_entity, url_entity, "found_on_google"))
            except Exception as e:
                # Return error entity
                err_ent = Entity(
                    entity_type="error",
                    value=f"Google API Error: {str(e)}",
                    label="Google Search Failed"
                )
                entities.append(err_ent)
                connections.append((source_entity, err_ent, "error"))
                
        if progress_callback:
            progress_callback(1, 1)
            
        return entities, connections
