"""
GitHub Recon Module
Fetches public activity from GitHub API to extract emails and repo info.
"""

import aiohttp
import re
from typing import List, Tuple, Optional, Callable
from datetime import datetime

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity

class GitHubReconModule(BaseOSINTModule):
    """
    Scans GitHub public event stream for emails and activity.
    """
    
    API_URL = "https://api.github.com/users/{}/events/public"
    PROFILE_URL = "https://api.github.com/users/{}"
    
    @property
    def name(self) -> str:
        return "GitHub Recon"
    
    @property
    def description(self) -> str:
        return "Extracts emails and activity from GitHub public events."
    
    @property
    def input_types(self) -> List[str]:
        return ["username", "person"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute GitHub recon."""
        
        # Check if platform matches (if specified)
        if scan_input.platform and scan_input.platform.lower() != "github" and scan_input.platform.lower() != "generic (sherlock)":
            return [], []

        username = scan_input.username
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        source_entity = Entity(
            entity_type="username",
            value=username,
            label=f"gh:{username}",
            attributes={"source": "input", "platform": "github"}
        )
        entities.append(source_entity)
        
        async with aiohttp.ClientSession() as session:
            # 1. Check Profile
            profile_Link = f"https://github.com/{username}"
            async with session.get(self.PROFILE_URL.format(username)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Profile Node
                    prof = Entity(
                        entity_type="social_profile",
                        value=profile_Link,
                        label=f"GitHub: {data.get('name', username)}",
                        attributes={
                            "name": data.get("name"),
                            "bio": data.get("bio"),
                            "company": data.get("company"),
                            "location": data.get("location"),
                            "followers": data.get("followers"),
                            "public_repos": data.get("public_repos"),
                            "avatar_url": data.get("avatar_url")
                        }
                    )
                    entities.append(prof)
                    connections.append((source_entity, prof, "has_account"))
                    
                    # Extract location/company nodes
                    if data.get("location"):
                        loc = Entity(entity_type="location", value=data["location"], label=data["location"])
                        entities.append(loc)
                        connections.append((prof, loc, "located_in"))
                        
                    if data.get("company"):
                        comp = Entity(entity_type="company", value=data["company"], label=data["company"])
                        entities.append(comp)
                        connections.append((prof, comp, "works_at"))
                        
                    # 2. Check Events for Leaked Emails
                    async with session.get(self.API_URL.format(username)) as evt_resp:
                        if evt_resp.status == 200:
                            events = await evt_resp.json()
                            emails = set()
                            repos = set()
                            
                            for event in events:
                                if event["type"] == "PushEvent":
                                    repo_name = event["repo"]["name"]
                                    repos.add(repo_name)
                                    
                                    # Check commits
                                    commits = event.get("payload", {}).get("commits", [])
                                    for commit in commits:
                                        author_email = commit.get("author", {}).get("email")
                                        if author_email and "noreply" not in author_email:
                                            emails.add(author_email)
                                            
                            # Add Email Nodes
                            for email in emails:
                                email_ent = Entity(
                                    entity_type="email", 
                                    value=email, 
                                    label=email,
                                    attributes={"source": "github_commit"}
                                )
                                entities.append(email_ent)
                                connections.append((prof, email_ent, "leaked_in_commit"))
                                
                            # Add Repo Nodes (Limit 5 recent)
                            for i, repo in enumerate(list(repos)[:5]):
                                repo_ent = Entity(
                                    entity_type="url",
                                    value=f"https://github.com/{repo}",
                                    label=repo,
                                    attributes={"type": "repository"}
                                )
                                entities.append(repo_ent)
                                connections.append((prof, repo_ent, "contributed_to"))

                elif resp.status == 404:
                   # Only warn if explicitly targeting GitHub
                   if scan_input.platform.lower() == "github":
                        warn = Entity(entity_type="warning", value="GitHub 404", label="User Not Found", attributes={"info": f"User {username} not found on GitHub"})
                        entities.append(warn)
                        connections.append((source_entity, warn, "status"))

        if progress_callback: progress_callback(1, 1)
        return entities, connections
