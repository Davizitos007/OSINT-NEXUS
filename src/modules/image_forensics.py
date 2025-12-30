"""
Image Forensics Module
Extract metadata and perform analysis on images.
"""

import asyncio
import aiohttp
import re
from typing import List, Optional, Callable, Tuple, Dict, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime

from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity


class ImageForensicsModule(BaseOSINTModule):
    """
    Image Forensics Module.
    Extracts EXIF metadata, GPS coordinates, and other hidden information from images.
    """
    
    # Common image extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    def __init__(self):
        self._exif_available = False
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            self._exif_available = True
        except ImportError:
            pass
    
    @property
    def name(self) -> str:
        return "Image Forensics"
    
    @property
    def description(self) -> str:
        return "Extract EXIF metadata, GPS coordinates, and analyze images from domains"
    
    @property
    def input_types(self) -> List[str]:
        return ["domain", "url"]
    
    async def run(
        self, 
        scan_input: ScanInput,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[List[Entity], List[tuple]]:
        """Execute image forensics analysis."""
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        domain = getattr(scan_input, 'domain', '')
        
        if not domain:
            return entities, connections
        
        if progress_callback:
            progress_callback(0, 3)
        
        # First, find images on the domain
        image_urls = await self._find_images_on_domain(domain)
        
        if progress_callback:
            progress_callback(1, 3)
        
        # Create domain entity
        domain_entity = Entity(
            entity_type="domain",
            value=domain,
            label=domain,
            attributes={
                "images_found": len(image_urls),
                "analyzed_at": datetime.now().isoformat()
            }
        )
        entities.append(domain_entity)
        
        # Analyze each image (limit to first 10)
        for i, img_url in enumerate(image_urls[:10]):
            try:
                metadata = await self._analyze_image(img_url)
                
                if metadata:
                    # Create image entity
                    img_entity = Entity(
                        entity_type="image",
                        value=img_url,
                        label=f"📷 {img_url.split('/')[-1][:30]}",
                        attributes=metadata
                    )
                    entities.append(img_entity)
                    connections.append((domain_entity, img_entity, "contains_image"))
                    
                    # If GPS coordinates found, create location entity
                    if metadata.get('gps_latitude') and metadata.get('gps_longitude'):
                        loc_entity = Entity(
                            entity_type="location",
                            value=f"{metadata['gps_latitude']}, {metadata['gps_longitude']}",
                            label=f"📍 GPS Location",
                            attributes={
                                "latitude": metadata['gps_latitude'],
                                "longitude": metadata['gps_longitude'],
                                "source": img_url
                            }
                        )
                        entities.append(loc_entity)
                        connections.append((img_entity, loc_entity, "geolocated_at"))
                    
                    # If camera info found, create device entity
                    if metadata.get('camera_make') or metadata.get('camera_model'):
                        device_name = f"{metadata.get('camera_make', '')} {metadata.get('camera_model', '')}".strip()
                        device_entity = Entity(
                            entity_type="device",
                            value=device_name,
                            label=f"📱 {device_name}",
                            attributes={
                                "make": metadata.get('camera_make', ''),
                                "model": metadata.get('camera_model', ''),
                                "software": metadata.get('software', '')
                            }
                        )
                        entities.append(device_entity)
                        connections.append((img_entity, device_entity, "captured_with"))
                        
            except Exception as e:
                print(f"Error analyzing image {img_url}: {e}")
        
        if progress_callback:
            progress_callback(3, 3)
        
        return entities, connections
    
    async def _find_images_on_domain(self, domain: str) -> List[str]:
        """Find image URLs on a domain."""
        image_urls = []
        
        try:
            url = f"https://{domain}" if not domain.startswith('http') else domain
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={'User-Agent': 'Mozilla/5.0 (OSINT-Nexus)'}
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Find image tags
                        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
                        matches = re.findall(img_pattern, html, re.IGNORECASE)
                        
                        for match in matches:
                            # Convert relative URLs to absolute
                            if match.startswith('//'):
                                match = 'https:' + match
                            elif match.startswith('/'):
                                match = f"https://{domain}{match}"
                            elif not match.startswith('http'):
                                match = f"https://{domain}/{match}"
                            
                            # Check if it's an image
                            ext = '.' + match.split('.')[-1].lower().split('?')[0]
                            if ext in self.IMAGE_EXTENSIONS:
                                image_urls.append(match)
                                
        except Exception as e:
            print(f"Error finding images: {e}")
        
        return list(set(image_urls))[:20]  # Dedupe and limit
    
    async def _analyze_image(self, url: str) -> Optional[Dict[str, Any]]:
        """Download and analyze an image for metadata."""
        if not self._exif_available:
            # Return basic info without EXIF
            return {
                "url": url,
                "note": "EXIF analysis requires PIL/Pillow"
            }
        
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            import io
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers={'User-Agent': 'Mozilla/5.0 (OSINT-Nexus)'}
                ) as response:
                    if response.status != 200:
                        return None
                    
                    content = await response.read()
                    
                    # Open image from bytes
                    img = Image.open(io.BytesIO(content))
                    
                    metadata = {
                        "url": url,
                        "format": img.format,
                        "mode": img.mode,
                        "width": img.width,
                        "height": img.height,
                        "size_bytes": len(content)
                    }
                    
                    # Try to get EXIF data
                    try:
                        exif_data = img._getexif()
                        if exif_data:
                            for tag_id, value in exif_data.items():
                                tag = TAGS.get(tag_id, tag_id)
                                
                                # Handle specific useful tags
                                if tag == 'Make':
                                    metadata['camera_make'] = str(value)
                                elif tag == 'Model':
                                    metadata['camera_model'] = str(value)
                                elif tag == 'DateTime':
                                    metadata['datetime'] = str(value)
                                elif tag == 'Software':
                                    metadata['software'] = str(value)
                                elif tag == 'Artist':
                                    metadata['artist'] = str(value)
                                elif tag == 'Copyright':
                                    metadata['copyright'] = str(value)
                                elif tag == 'GPSInfo':
                                    gps = self._parse_gps_info(value, GPSTAGS)
                                    if gps:
                                        metadata.update(gps)
                    except Exception as e:
                        pass  # No EXIF data available
                    
                    return metadata
                    
        except Exception as e:
            print(f"Image analysis error: {e}")
            return None
    
    def _parse_gps_info(self, gps_info: dict, gpstags: dict) -> Optional[Dict[str, float]]:
        """Parse GPS information from EXIF data."""
        try:
            gps_data = {}
            for key, val in gps_info.items():
                tag = gpstags.get(key, key)
                gps_data[tag] = val
            
            lat = gps_data.get('GPSLatitude')
            lat_ref = gps_data.get('GPSLatitudeRef', 'N')
            lon = gps_data.get('GPSLongitude')
            lon_ref = gps_data.get('GPSLongitudeRef', 'E')
            
            if lat and lon:
                # Convert to decimal degrees
                lat_deg = float(lat[0]) + float(lat[1])/60 + float(lat[2])/3600
                lon_deg = float(lon[0]) + float(lon[1])/60 + float(lon[2])/3600
                
                if lat_ref == 'S':
                    lat_deg = -lat_deg
                if lon_ref == 'W':
                    lon_deg = -lon_deg
                
                return {
                    'gps_latitude': lat_deg,
                    'gps_longitude': lon_deg
                }
        except Exception as e:
            pass
        
        return None


# Entity type colors for new types
ENTITY_COLORS_UPDATE = {
    "entity_image": "#79c0ff",    # Light blue for images
    "entity_location": "#f0883e", # Orange for locations
    "entity_device": "#a371f7",   # Purple for devices
}
