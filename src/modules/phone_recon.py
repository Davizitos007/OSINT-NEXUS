"""
Phone Number Reconnaissance Module
Gathers information about phone numbers including carrier, location, and social footprint.
"""

import asyncio
import aiohttp
from typing import List, Optional, Callable, Tuple
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from ..config import config
from .base_module import BaseOSINTModule, ScanInput
from ..database import Entity


class PhoneRecon(BaseOSINTModule):
    """
    Phone number reconnaissance module.
    Uses phonenumbers library for validation and carrier lookup.
    Also uses Google Dorks to find social footprint if API key is present.
    """
    
    @property
    def name(self) -> str:
        return "Phone Number Recon"
    
    @property
    def description(self) -> str:
        return "Gathers carrier, location, and social footprint for phone numbers"
    
    @property
    def input_types(self) -> List[str]:
        return ["phone"]
    
    async def run(self, scan_input: ScanInput,
                  progress_callback: Optional[Callable[[int, int], None]] = None
                  ) -> Tuple[List[Entity], List[tuple]]:
        """Execute phone number reconnaissance."""
        phone = scan_input.phone.strip()
        if not phone:
            return [], []
        
        entities: List[Entity] = []
        connections: List[tuple] = []
        
        if progress_callback:
            progress_callback(0, 3)
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone, None)
            
            # Validate
            is_valid = phonenumbers.is_valid_number(parsed)
            is_possible = phonenumbers.is_possible_number(parsed)
            
            if progress_callback:
                progress_callback(1, 3)
            
            # Get carrier info
            carrier_name = carrier.name_for_number(parsed, "en")
            
            # Get location
            location = geocoder.description_for_number(parsed, "en")
            
            # Get timezone
            timezones = timezone.time_zones_for_number(parsed)
            
            if progress_callback:
                progress_callback(2, 3)
            
            # Format number
            formatted_international = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            formatted_national = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.NATIONAL
            )
            formatted_e164 = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
            
            # Get number type
            number_type = phonenumbers.number_type(parsed)
            type_names = {
                0: "Fixed Line",
                1: "Mobile",
                2: "Fixed Line or Mobile",
                3: "Toll Free",
                4: "Premium Rate",
                5: "Shared Cost",
                6: "VoIP",
                7: "Personal Number",
                8: "Pager",
                9: "UAN",
                10: "Voicemail",
                -1: "Unknown"
            }
            type_name = type_names.get(number_type, "Unknown")
            
            # Country code
            country_code = phonenumbers.region_code_for_number(parsed)
            
            # Create phone entity
            phone_entity = Entity(
                entity_type="phone",
                value=formatted_e164,
                label=formatted_international,
                attributes={
                    "original": phone,
                    "international": formatted_international,
                    "national": formatted_national,
                    "e164": formatted_e164,
                    "is_valid": is_valid,
                    "is_possible": is_possible,
                    "carrier": carrier_name or "Unknown",
                    "location": location or "Unknown",
                    "country_code": country_code or "Unknown",
                    "number_type": type_name,
                    "timezones": list(timezones) if timezones else [],
                    "source": "analysis"
                }
            )
            entities.append(phone_entity)
            
            # Create location entity if available
            if location:
                location_entity = Entity(
                    entity_type="location",
                    value=location,
                    label=location,
                    attributes={
                        "country_code": country_code,
                        "source": "phone_lookup"
                    }
                )
                entities.append(location_entity)
                connections.append((phone_entity, location_entity, "located_in"))
            
            # Create carrier entity if available
            if carrier_name:
                carrier_entity = Entity(
                    entity_type="company",
                    value=carrier_name,
                    label=carrier_name,
                    attributes={
                        "type": "carrier",
                        "source": "phone_lookup"
                    }
                )
                entities.append(carrier_entity)
                connections.append((phone_entity, carrier_entity, "provided_by"))

            # --- WhatsApp Check ---
            # Heuristic: wa.me/<number> redirects or shows page.
            # We can just add the link as "Potential WhatsApp" because we can't easily verify existence without full browser/API.
            # But the user asked for "Legal Contact Syncing" simulation. 
            # We will add a node for it.
            wa_url = f"https://wa.me/{phone.lstrip('+')}"
            wa_ent = Entity(
                entity_type="social_profile",
                value=wa_url,
                label=f"WhatsApp: {formatted_e164}",
                attributes={"platform": "WhatsApp", "url": wa_url, "info": "Click to verify in WhatsApp"}
            )
            entities.append(wa_ent)
            connections.append((phone_entity, wa_ent, "has_account_check"))

            # --- Deep Identity Recon: Social Footprint (Google Dorks) ---
            api_key = config.get("api_keys", "google_api")
            cx = config.get("api_keys", "google_cse_id")
            
            if api_key and cx:
                # Targeted "Dorks" for improved visibility
                variants = [formatted_e164, formatted_international, formatted_national, phone]
                variants = list(set([v for v in variants if v])) 
                
                targets = [
                    ("Google/Gmail", f'"{formatted_e164}" OR "{formatted_international}" OR "{phone}" site:google.com'),
                    ("Facebook", f'"{formatted_e164}" OR "{formatted_international}" OR "{phone}" site:facebook.com'),
                    ("Instagram", f'"{formatted_e164}" OR "{formatted_international}" OR "{phone}" site:instagram.com'),
                    ("LinkedIn", f'"{formatted_e164}" OR "{formatted_international}" OR "{phone}" site:linkedin.com'),
                    ("Twitter/X", f'"{formatted_e164}" OR "{formatted_international}" OR "{phone}" site:twitter.com OR site:x.com'),
                    ("Truecaller", f'"{formatted_e164}" OR "{formatted_international}" site:truecaller.com'),
                    ("Documents", f'"{formatted_e164}" OR "{formatted_international}" filetype:pdf OR filetype:doc OR filetype:xls OR filetype:csv')
                ]
                
                async with aiohttp.ClientSession() as session:
                    url = "https://www.googleapis.com/customsearch/v1"
                    found_any_social = False
                    
                    for platform_name, q in targets:
                        params = {'key': api_key, 'cx': cx, 'q': q}
                        try:
                            async with session.get(url, params=params) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    items = data.get("items", [])
                                    
                                    for item in items:
                                        link = item.get("link")
                                        title = item.get("title")
                                        snippet = item.get("snippet")
                                        
                                        if link:
                                            found_any_social = True
                                            ent_type = "social_profile" if "filetype" not in q else "document"
                                            lbl = f"{platform_name}: {title}"
                                            if len(lbl) > 40: lbl = lbl[:37] + "..."
                                            
                                            # Extract Handle Logic (Maltego-style)
                                            handle = ""
                                            if "facebook.com" in link:
                                                match = re.search(r'facebook\.com/([a-zA-Z0-9\.]+)', link)
                                                if match: handle = match.group(1)
                                            elif "instagram.com" in link:
                                                match = re.search(r'instagram\.com/([a-zA-Z0-9_\.]+)', link)
                                                if match: handle = match.group(1)
                                            elif "twitter.com" in link or "x.com" in link:
                                                match = re.search(r'(?:twitter|x)\.com/([a-zA-Z0-9_]+)', link)
                                                if match: handle = match.group(1)
                                            elif "linkedin.com/in" in link:
                                                match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', link)
                                                if match: handle = match.group(1)
                                            
                                            # Create Handle Entity
                                            if handle:
                                                h_ent = Entity(
                                                    entity_type="social_profile", # Could be distinct 'username'
                                                    value=handle,
                                                    label=f"@{handle}",
                                                    attributes={"platform": platform_name, "url": link}
                                                )
                                                entities.append(h_ent)
                                                connections.append((phone_entity, h_ent, "likely_username"))
                                            
                                            url_ent = Entity(
                                                entity_type=ent_type, 
                                                value=link, 
                                                label=lbl, 
                                                attributes={
                                                    "platform": platform_name,
                                                    "title": title, 
                                                    "snippet": snippet, 
                                                    "source": "phone_google_dork"
                                                }
                                            )
                                            entities.append(url_ent)
                                            if handle:
                                                connections.append((h_ent, url_ent, "profile_page"))
                                            else:
                                                connections.append((phone_entity, url_ent, "likely_linked_to"))
                                            
                        except Exception as e:
                            print(f"Google Dork Error ({platform_name}): {e}")
            else:
                 # Warn about missing keys for social footprint
                 warn_ent = Entity(
                    entity_type="warning",
                    value="Missing Google Keys",
                    label="Social Search Skipping",
                    attributes={"info": "Add Google API/CX keys to search for social profiles linked to this number."}
                 )
                 entities.append(warn_ent)
                 connections.append((phone_entity, warn_ent, "warning"))
            
            if progress_callback:
                progress_callback(3, 3)
                
        except phonenumbers.NumberParseException as e:
            # Invalid phone number
            phone_entity = Entity(
                entity_type="phone",
                value=phone,
                label=phone,
                attributes={
                    "original": phone,
                    "is_valid": False,
                    "error": str(e),
                    "source": "input"
                }
            )
            entities.append(phone_entity)
        
        return entities, connections
