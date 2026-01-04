"""
Instagram Interactions Module
Uses custom Google dorking to find Instagram interactions (likes, comments, mentions, etc.)
for a given username across the web.
"""

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity
from ..config import config
from typing import List, Optional, Callable, Tuple
import asyncio
import aiohttp
import urllib.parse


class InstagramInteractionsModule(BaseOSINTModule):
    """
    Instagram Interactions Search Module.
    Uses Google Custom Search API with specialized queries to find
    Instagram interactions like comments, likes, mentions, and shares.
    """
    
    # Define interaction search queries (Google dorks)
    INTERACTION_QUERIES = [
        # Direct profile mentions and links
        {
            "name": "Profile Mentions",
            "query": 'site:instagram.com "{username}"',
            "description": "Direct mentions on Instagram"
        },
        # Comments containing the username
        {
            "name": "Comments & Replies", 
            "query": 'site:instagram.com "{username}" ("replied" OR "commented" OR "said")',
            "description": "Comments and replies mentioning user"
        },
        # Tagged photos and posts
        {
            "name": "Tagged Posts",
            "query": 'site:instagram.com "@{username}" ("tagged" OR "with")',
            "description": "Posts where user is tagged"
        },
        # User's interactions captured by third-party sites
        {
            "name": "External Interactions",
            "query": '"{username}" instagram (comment OR like OR follow OR mention)',
            "description": "Instagram interactions on external sites"
        },
        # Screenshots and archives of Instagram content
        {
            "name": "Archived Content",
            "query": '(site:web.archive.org OR site:archive.today) instagram.com/{username}',
            "description": "Archived Instagram content"
        },
        # Instagram embeds on other websites
        {
            "name": "Embedded Posts",
            "query": 'instagram.com/p/ "{username}" -site:instagram.com',
            "description": "Instagram posts embedded on other sites"
        },
        # Social media aggregators and trackers
        {
            "name": "Social Trackers",
            "query": '(site:socialblade.com OR site:ninjalitics.com OR site:hypeauditor.com) "{username}"',
            "description": "Social analytics for the user"
        },
        # Reddit discussions about the Instagram user
        {
            "name": "Reddit Discussions",
            "query": 'site:reddit.com instagram "{username}"',
            "description": "Reddit mentions of Instagram account"
        },
        # Twitter/X discussions 
        {
            "name": "Twitter Mentions",
            "query": 'site:twitter.com OR site:x.com instagram "{username}"',
            "description": "Twitter/X discussions about the account"
        },
        # Stories and highlights (often indexed)
        {
            "name": "Stories & Highlights",
            "query": 'site:instagram.com/stories/{username} OR "{username}" instagram stories',
            "description": "Instagram stories and highlights"
        },
        # Bio links and linktree
        {
            "name": "Bio Links",
            "query": '(site:linktr.ee OR site:linkin.bio OR site:bio.link) "{username}"',
            "description": "Bio link pages associated with user"
        },
        # Third-party Instagram viewers
        {
            "name": "Third-Party Viewers",
            "query": '(site:picuki.com OR site:imginn.com OR site:dumpor.com) "{username}"',
            "description": "Third-party Instagram profile viewers"
        },
    ]
    
    @property
    def name(self) -> str:
        return "Instagram Interactions"
    
    @property
    def description(self) -> str:
        return "Finds Instagram interactions (comments, likes, mentions, shares) using advanced Google dorking."
    
    @property
    def input_types(self) -> List[str]:
        return ["username"]
    
    def can_process(self, scan_input: ScanInput) -> bool:
        """Only process if platform is Instagram or generic."""
        if not scan_input.username:
            return False
        platform = scan_input.platform.lower() if scan_input.platform else ""
        return platform in ["", "instagram", "generic (sherlock)"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute Instagram interaction search."""
        username = scan_input.username.strip()
        
        if not username:
            return [], []
        
        # Clean username (remove @ if present)
        if username.startswith("@"):
            username = username[1:]
        
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        # Create source entity
        source_entity = Entity(
            entity_type="instagram_user",
            value=f"https://instagram.com/{username}",
            label=f"@{username}",
            attributes={
                "username": username,
                "platform": "Instagram",
                "source": "input"
            }
        )
        entities.append(source_entity)
        
        # Check API keys
        api_key = config.get("api_keys", "google_api")
        cx = config.get("api_keys", "google_cse_id")
        
        if not api_key:
            warning = Entity(
                entity_type="warning",
                value="Missing Google API Key",
                label="Setup Google API Key",
                attributes={"error": "Check Settings > API Keys"}
            )
            entities.append(warning)
            connections.append((source_entity, warning, "configuration_error"))
            return entities, connections
        
        if not cx:
            warning = Entity(
                entity_type="warning",
                value="Missing Google CX ID",
                label="Setup Google CX ID",
                attributes={"error": "Check Settings > API Keys"}
            )
            entities.append(warning)
            connections.append((source_entity, warning, "configuration_error"))
            return entities, connections
        
        total_queries = len(self.INTERACTION_QUERIES)
        completed = 0
        total_results = 0
        
        async with aiohttp.ClientSession() as session:
            for query_info in self.INTERACTION_QUERIES:
                query_name = query_info["name"]
                query_template = query_info["query"]
                query_desc = query_info["description"]
                
                # Format query with username
                query = query_template.replace("{username}", username)
                
                # Create category entity for this interaction type
                category_entity = Entity(
                    entity_type="interaction_category",
                    value=f"{query_name}:{username}",
                    label=f"📊 {query_name}",
                    attributes={
                        "category": query_name,
                        "description": query_desc,
                        "query_used": query
                    }
                )
                entities.append(category_entity)
                connections.append((source_entity, category_entity, "interaction_search"))
                
                # Execute Google search
                params = {
                    'key': api_key,
                    'cx': cx,
                    'q': query,
                    'num': 10  # Max 10 results per query
                }
                
                url = "https://www.googleapis.com/customsearch/v1"
                
                try:
                    async with session.get(url, params=params, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            items = data.get("items", [])
                            
                            if items:
                                for item in items:
                                    link = item.get("link", "")
                                    title = item.get("title", "")
                                    snippet = item.get("snippet", "")
                                    
                                    if link:
                                        # Determine entity type based on URL
                                        entity_type = self._classify_url(link)
                                        
                                        result_entity = Entity(
                                            entity_type=entity_type,
                                            value=link,
                                            label=title[:50] + "..." if len(title) > 50 else title,
                                            attributes={
                                                "title": title,
                                                "snippet": snippet,
                                                "url": link,
                                                "category": query_name,
                                                "source": "google_dork"
                                            }
                                        )
                                        entities.append(result_entity)
                                        connections.append((category_entity, result_entity, "contains"))
                                        total_results += 1
                            else:
                                # No results for this query
                                no_result = Entity(
                                    entity_type="info",
                                    value=f"No results: {query_name}",
                                    label="No results found",
                                    attributes={"query": query}
                                )
                                entities.append(no_result)
                                connections.append((category_entity, no_result, "empty"))
                                
                        elif response.status == 429:
                            # Rate limited
                            error_entity = Entity(
                                entity_type="warning",
                                value="Rate Limited",
                                label="⚠️ API Rate Limited",
                                attributes={"info": "Google API quota exceeded. Try again later."}
                            )
                            entities.append(error_entity)
                            connections.append((category_entity, error_entity, "error"))
                            
                except asyncio.TimeoutError:
                    error_entity = Entity(
                        entity_type="warning",
                        value=f"Timeout: {query_name}",
                        label="⏱️ Request Timeout",
                        attributes={"info": f"Query '{query_name}' timed out"}
                    )
                    entities.append(error_entity)
                    connections.append((category_entity, error_entity, "error"))
                    
                except Exception as e:
                    error_entity = Entity(
                        entity_type="error",
                        value=f"Error: {query_name}",
                        label=f"❌ {str(e)[:30]}",
                        attributes={"error": str(e), "query": query_name}
                    )
                    entities.append(error_entity)
                    connections.append((category_entity, error_entity, "error"))
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_queries)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
        
        # Add summary entity
        summary_entity = Entity(
            entity_type="summary",
            value=f"Summary:{username}",
            label=f"📈 Found {total_results} interactions",
            attributes={
                "total_results": total_results,
                "queries_executed": total_queries,
                "username": username
            }
        )
        entities.append(summary_entity)
        connections.append((source_entity, summary_entity, "scan_summary"))
        
        return entities, connections
    
    def _classify_url(self, url: str) -> str:
        """Classify URL to determine entity type."""
        url_lower = url.lower()
        
        if "instagram.com" in url_lower:
            if "/p/" in url_lower:
                return "instagram_post"
            elif "/stories/" in url_lower:
                return "instagram_story"
            elif "/reel/" in url_lower:
                return "instagram_reel"
            else:
                return "instagram_profile"
        elif "reddit.com" in url_lower:
            return "reddit_post"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter_post"
        elif "archive.org" in url_lower or "archive.today" in url_lower:
            return "archive"
        elif any(tracker in url_lower for tracker in ["socialblade", "ninjalitics", "hypeauditor"]):
            return "analytics"
        elif any(viewer in url_lower for viewer in ["picuki", "imginn", "dumpor"]):
            return "third_party_viewer"
        elif any(bio in url_lower for bio in ["linktr.ee", "linkin.bio", "bio.link"]):
            return "bio_link"
        else:
            return "url"
