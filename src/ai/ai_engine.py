"""
OSINT-Nexus AI Engine
AI-powered analysis using Google Gemini for intelligent entity correlation,
threat assessment, and natural language querying.
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..config import config
from ..database import Entity


@dataclass
class ThreatReport:
    """AI-generated threat assessment report."""
    entity_id: int
    risk_score: float  # 0.0 to 10.0
    risk_level: str  # low, medium, high, critical
    summary: str
    findings: List[str]
    recommendations: List[str]
    generated_at: datetime


@dataclass 
class CorrelationResult:
    """Result of AI correlation analysis."""
    correlations: List[Dict[str, Any]]
    hidden_patterns: List[str]
    key_entities: List[int]
    summary: str


class AIEngine:
    """AI-powered analysis engine using Google Gemini."""
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or config.get("api_keys", "gemini")
        self.model = config.get("ai", "model") or "gemini-1.5-flash"
        self.enabled = config.get("ai", "enabled") if config.get("ai") else True
        
    def is_available(self) -> bool:
        """Check if AI engine is available (has API key)."""
        return bool(self.api_key) and self.enabled
    
    async def _call_gemini(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Make a call to Gemini API."""
        if not self.api_key:
            return None
            
        url = f"{self.GEMINI_API_URL}/{self.model}:generateContent?key={self.api_key}"
        
        # Build the request payload
        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System Context: {system_prompt}"}]
            })
            contents.append({
                "role": "model", 
                "parts": [{"text": "I understand. I'll act accordingly."}]
            })
        
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "candidates" in data and data["candidates"]:
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        error = await response.text()
                        print(f"Gemini API error: {response.status} - {error}")
                        return None
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return None
    
    async def analyze_entity_relationships(
        self, 
        entities: List[Entity], 
        connections: List[Tuple[int, int, str]]
    ) -> Optional[CorrelationResult]:
        """Use AI to identify hidden patterns and correlations between entities."""
        if not self.is_available() or not entities:
            return None
            
        # Build entity summary
        entity_summary = []
        for e in entities[:50]:  # Limit to avoid token overflow
            entity_summary.append(f"- {e.entity_type}: {e.value} (attrs: {json.dumps(e.attributes)})")
        
        connection_summary = []
        for src, tgt, rel in connections[:50]:
            connection_summary.append(f"- Entity {src} --[{rel}]--> Entity {tgt}")
        
        prompt = f"""Analyze the following OSINT (Open Source Intelligence) data and identify patterns:

ENTITIES:
{chr(10).join(entity_summary)}

CONNECTIONS:
{chr(10).join(connection_summary)}

Provide a JSON response with:
1. "correlations": List of discovered correlations between entities
2. "hidden_patterns": List of suspicious or notable patterns
3. "key_entities": List of entity IDs that appear most significant
4. "summary": Brief summary of findings

Focus on security-relevant patterns like:
- Connected infrastructure (shared IPs, domains, hosts)
- Identity correlations (same person across platforms)
- Suspicious timing or clustering
- Potential threat indicators
"""
        
        system = "You are a cybersecurity OSINT analyst. Analyze data and find hidden connections. Always respond with valid JSON."
        
        response = await self._call_gemini(prompt, system)
        if not response:
            return None
            
        try:
            # Parse JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                return CorrelationResult(
                    correlations=data.get("correlations", []),
                    hidden_patterns=data.get("hidden_patterns", []),
                    key_entities=data.get("key_entities", []),
                    summary=data.get("summary", "")
                )
        except json.JSONDecodeError:
            # Return raw summary if JSON parsing fails
            return CorrelationResult(
                correlations=[],
                hidden_patterns=[],
                key_entities=[],
                summary=response
            )
        
        return None
    
    async def generate_threat_assessment(self, entity: Entity) -> Optional[ThreatReport]:
        """Generate a risk score and threat narrative for an entity."""
        if not self.is_available():
            return None
            
        prompt = f"""Perform a threat assessment for this OSINT entity:

Type: {entity.entity_type}
Value: {entity.value}
Attributes: {json.dumps(entity.attributes, indent=2)}

Provide a JSON response with:
1. "risk_score": Float 0.0-10.0 based on threat potential
2. "risk_level": "low" / "medium" / "high" / "critical"
3. "summary": Brief threat summary (2-3 sentences)
4. "findings": List of specific security findings
5. "recommendations": List of recommended actions

Risk scoring guide:
- 0-2: Benign, legitimate entity
- 3-4: Low risk, worth monitoring
- 5-6: Medium risk, investigate further
- 7-8: High risk, potential threat
- 9-10: Critical, immediate action needed
"""
        
        system = "You are a cyber threat analyst. Assess OSINT data for security risks. Always respond with valid JSON."
        
        response = await self._call_gemini(prompt, system)
        if not response:
            return None
            
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                return ThreatReport(
                    entity_id=entity.id or 0,
                    risk_score=float(data.get("risk_score", 0)),
                    risk_level=data.get("risk_level", "low"),
                    summary=data.get("summary", ""),
                    findings=data.get("findings", []),
                    recommendations=data.get("recommendations", []),
                    generated_at=datetime.now()
                )
        except (json.JSONDecodeError, ValueError):
            pass
            
        return None
    
    async def natural_language_query(
        self, 
        query: str, 
        entities: List[Entity],
        connections: List[Tuple[int, int, str]]
    ) -> Dict[str, Any]:
        """Query the OSINT graph using natural language."""
        if not self.is_available():
            return {"error": "AI engine not available", "results": []}
            
        # Build entity summary
        entity_list = []
        for e in entities[:100]:
            entity_list.append({
                "id": e.id,
                "type": e.entity_type,
                "value": e.value,
                "attributes": e.attributes
            })
        
        prompt = f"""Given this OSINT database, answer the following query:

QUERY: "{query}"

ENTITIES (JSON):
{json.dumps(entity_list, indent=2)}

CONNECTIONS: {len(connections)} relationships exist between entities.

Provide a JSON response with:
1. "answer": Natural language answer to the query
2. "matching_entity_ids": List of entity IDs that match the query
3. "explanation": Why these entities match
4. "follow_up_suggestions": Related queries the user might want to try
"""
        
        system = "You are an OSINT database query assistant. Help users find information in their intelligence data."
        
        response = await self._call_gemini(prompt, system)
        if not response:
            return {"error": "Failed to get AI response", "results": []}
            
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            return {"answer": response, "matching_entity_ids": [], "explanation": ""}
            
        return {"error": "Failed to parse response", "results": []}
    
    async def generate_executive_summary(
        self,
        project_name: str,
        entities: List[Entity],
        connections: List[Tuple[int, int, str]]
    ) -> str:
        """Generate an executive summary for a project."""
        if not self.is_available():
            return "AI analysis unavailable. Configure Gemini API key in settings."
            
        # Aggregate stats
        entity_types = {}
        for e in entities:
            entity_types[e.entity_type] = entity_types.get(e.entity_type, 0) + 1
        
        prompt = f"""Generate an executive summary for this OSINT investigation:

PROJECT: {project_name}

STATISTICS:
- Total Entities: {len(entities)}
- Entity Types: {json.dumps(entity_types)}
- Total Connections: {len(connections)}

SAMPLE ENTITIES (first 20):
{json.dumps([{"type": e.entity_type, "value": e.value} for e in entities[:20]], indent=2)}

Write a professional executive summary (3-4 paragraphs) covering:
1. Investigation scope and key findings
2. Notable patterns or concerns
3. Risk assessment
4. Recommended next steps

Write in formal, professional language suitable for a security report.
"""
        
        system = "You are a senior security analyst writing an executive briefing."
        
        response = await self._call_gemini(prompt, system)
        return response or "Failed to generate executive summary."


# Global instance
ai_engine = AIEngine()
