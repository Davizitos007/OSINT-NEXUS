"""
Document Metadata Search Module
Searches for publicly indexed documents and extracts metadata.
"""

import asyncio
import aiohttp
from typing import List, Optional, Callable, Tuple, Set
from urllib.parse import quote, urlparse, urljoin
from bs4 import BeautifulSoup
import re

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity


class DocMetadataSearch(BaseOSINTModule):
    """
    Document metadata search module.
    Searches for indexed documents (PDF, DOCX, etc.) on a domain.
    """
    
    # File types to search for
    FILE_TYPES = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv"]
    
    # Search engine queries
    SEARCH_QUERIES = {
        "google": "site:{domain} filetype:{filetype}",
        "bing": "site:{domain} filetype:{filetype}",
        "duckduckgo": "site:{domain} filetype:{filetype}",
    }
    
    @property
    def name(self) -> str:
        return "Document Metadata Search"
    
    @property
    def description(self) -> str:
        return "Searches for indexed documents and extracts metadata"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "file"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute document metadata search."""
        
        # Check input type
        # Ideally ScanInput should have a 'type' field, or we infer.
        # If the input value is a local path, loop to local analysis.
        import os
        if os.path.isfile(scan_input.value) or (scan_input.platform and scan_input.platform.lower() == "file"):
             return await self.analyze_local_file(scan_input.value, progress_callback)

        domain = scan_input.domain.strip().lower()
        if domain.startswith(("http://", "https://")):
            domain = urlparse(domain).netloc
        
        entities: List[Entity] = []
        connections: List[tuple] = []
        discovered_docs: Set[str] = set()
        
        # Create domain entity
        domain_entity = Entity(
            entity_type="domain",
            value=domain,
            label=domain,
            attributes={"source": "input"}
        )
        entities.append(domain_entity)
        
        total_steps = len(self.FILE_TYPES) + 1
        current_step = 0
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        ) as session:
            
            # Method 1: Direct crawl of common document directories
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps)
            
            common_paths = [
                "/documents", "/docs", "/files", "/downloads", "/assets",
                "/uploads", "/media", "/resources", "/attachments",
                "/wp-content/uploads", "/public", "/static"
            ]
            
            for path in common_paths:
                try:
                    url = f"https://{domain}{path}/"
                    async with session.get(url, ssl=False) as response:
                        if response.status == 200:
                            html = await response.text()
                            self._extract_document_links(html, domain, discovered_docs)
                except Exception:
                    pass
                await asyncio.sleep(0.3)
            
            # Method 2: Search for each file type using search-like patterns
            for filetype in self.FILE_TYPES:
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps)
                
                # Check robots.txt for hints
                try:
                    url = f"https://{domain}/robots.txt"
                    async with session.get(url, ssl=False) as response:
                        if response.status == 200:
                            robots = await response.text()
                            # Look for allowed/disallowed directories
                            for line in robots.split("\n"):
                                if "Disallow:" in line or "Allow:" in line:
                                    path = line.split(":")[-1].strip()
                                    if path and not path.startswith("#"):
                                        # Check these paths for documents
                                        try:
                                            check_url = f"https://{domain}{path}"
                                            async with session.get(check_url, ssl=False) as r:
                                                if r.status == 200:
                                                    html = await r.text()
                                                    self._extract_document_links(html, domain, discovered_docs)
                                        except Exception:
                                            pass
                except Exception:
                    pass
                
                await asyncio.sleep(0.5)
            
            # Method 3: Check sitemap for document links
            try:
                sitemap_urls = [
                    f"https://{domain}/sitemap.xml",
                    f"https://{domain}/sitemap_index.xml",
                    f"https://{domain}/sitemap.txt",
                ]
                for sitemap_url in sitemap_urls:
                    async with session.get(sitemap_url, ssl=False) as response:
                        if response.status == 200:
                            content = await response.text()
                            # Extract URLs from sitemap
                            url_pattern = re.compile(r'<loc>(.*?)</loc>')
                            urls = url_pattern.findall(content)
                            for url in urls:
                                if any(url.lower().endswith(f".{ft}") for ft in self.FILE_TYPES):
                                    discovered_docs.add(url)
            except Exception:
                pass
        
        # Create entities for discovered documents
        for doc_url in discovered_docs:
            # Extract filename
            parsed = urlparse(doc_url)
            filename = parsed.path.split("/")[-1] if "/" in parsed.path else parsed.path
            
            # Determine file type
            ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
            
            doc_entity = Entity(
                entity_type="document",
                value=doc_url,
                label=filename,
                attributes={
                    "url": doc_url,
                    "filename": filename,
                    "filetype": ext,
                    "domain": domain,
                    "source": "crawled"
                }
            )
            entities.append(doc_entity)
            connections.append((doc_entity, domain_entity, "hosted_on"))
        
        return entities, connections

    async def analyze_local_file(self, file_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[List[Entity], List[tuple]]:
        """Analyze a local file for metadata."""
        import os
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        filename = os.path.basename(file_path)
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        source_entity = Entity(
            entity_type="document",
            value=file_path,
            label=filename,
            attributes={"path": file_path, "type": ext, "source": "local_upload"}
        )
        entities.append(source_entity)
        
        meta = {}
        
        if ext == "pdf":
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    info = reader.metadata
                    if info:
                        for k, v in info.items():
                            key = k.lstrip('/').replace(" ", "_").lower()
                            if v: meta[key] = str(v)
            except ImportError:
                print("PyPDF2 not installed.")
                meta["error"] = "Install PyPDF2 for PDF analysis"
            except Exception as e:
                meta["error"] = str(e)
                
        elif ext in ["jpg", "jpeg", "png", "tiff"]:
            try:
                from PIL import Image, ExifTags
                img = Image.open(file_path)
                exif = img._getexif()
                if exif:
                    # Helper for decoding rational tuples
                    def get_decimal(coords, ref):
                        d = coords[0]
                        m = coords[1]
                        s = coords[2]
                        decimal = float(d) + float(m)/60 + float(s)/3600
                        if ref == "S" or ref == "W":
                            decimal = -decimal
                        return decimal

                    gps_info = {}
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        # Filter long binary data
                        if isinstance(value, bytes) and len(value) > 100:
                            v_str = "<binary_data>"
                        else:
                            v_str = str(value)
                        
                        meta[str(tag)] = v_str
                        
                        # Collect GPS data separately
                        if tag == "GPSInfo":
                            gps_info = value

                    # Process GPS if available
                    if gps_info:
                        try:
                            # GPS tags: 1:LatRef, 2:Lat, 3:LonRef, 4:Lon
                            lat_ref = gps_info.get(1, "N")
                            lat_coords = gps_info.get(2)
                            lon_ref = gps_info.get(3, "E")
                            lon_coords = gps_info.get(4)
                            
                            if lat_coords and lon_coords:
                                lat = get_decimal(lat_coords, lat_ref)
                                lon = get_decimal(lon_coords, lon_ref)
                                
                                meta["GPS_Latitude"] = str(lat)
                                meta["GPS_Longitude"] = str(lon)
                                meta["GPS_Map_Link"] = f"https://www.google.com/maps?q={lat},{lon}"
                        except Exception as e:
                            print(f"GPS Decode Error: {e}")
                            
            except ImportError:
                print("Pillow not installed.")
                meta["error"] = "Install Pillow (PIL) for image analysis"
            except Exception as e:
                meta["error"] = str(e)
        
        # Create metadata entities
        for k, v in meta.items():
            # Skip empty or trivial
            if not v or len(str(v)) < 2: continue
            
            # Identify interesting keys
            label = f"{k}: {v}"
            if len(label) > 50: label = label[:47] + "..."
            
            ent_type = "metadata"
            if "author" in k.lower() or "creator" in k.lower(): ent_type = "person"
            if "date" in k.lower(): ent_type = "date"
            if "software" in k.lower() or "producer" in k.lower() or "model" in k.lower(): ent_type = "software"
            if "gps" in k.lower(): ent_type = "location"
            
            # Special handling for Map Link
            if k == "GPS_Map_Link":
                ent_type = "location"
                label = "Open in Maps"
            
            meta_ent = Entity(
                entity_type=ent_type,
                value=str(v)[:300], # Limit value size
                label=label,
                attributes={"key": k, "full_value": str(v)}
            )
            entities.append(meta_ent)
            connections.append((source_entity, meta_ent, "has_metadata"))
            
        return entities, connections

    def run_sync(self, scan_input: ScanInput) -> Tuple[List[Entity], List[tuple]]:
        """Wrapper for simpler execution if needed."""
        # Not used by main async engine, typical entry is 'run'
        pass
        """Extract document links from HTML content."""
        try:
            soup = BeautifulSoup(html, "lxml")
            
            # Find all links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                
                # Check if it's a document
                if any(href.lower().endswith(f".{ft}") for ft in self.FILE_TYPES):
                    # Make absolute URL
                    if href.startswith("/"):
                        href = f"https://{domain}{href}"
                    elif not href.startswith(("http://", "https://")):
                        href = f"https://{domain}/{href}"
                    
                    if domain in href:
                        docs.add(href)
        
        except Exception:
            pass
