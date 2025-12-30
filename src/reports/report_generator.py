"""
OSINT-Nexus Report Generator
Generate professional PDF reports from OSINT investigations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import io


@dataclass
class ReportSection:
    """A section of the report."""
    title: str
    content: str
    level: int = 1  # Heading level


class ReportGenerator:
    """
    Generate professional intelligence reports.
    
    Supports:
    - HTML reports (always available)
    - PDF reports (requires reportlab)
    - STIX 2.1 export for CTI sharing
    """
    
    def __init__(self):
        self._pdf_available = False
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            self._pdf_available = True
        except ImportError:
            pass
    
    def generate_html_report(
        self,
        project_name: str,
        entities: List[Dict[str, Any]],
        connections: List[Tuple[int, int, str]],
        analytics: Optional[Dict[str, Any]] = None,
        ai_summary: str = ""
    ) -> str:
        """Generate an HTML intelligence report."""
        
        # Count entity types
        entity_types: Dict[str, int] = {}
        for e in entities:
            etype = e.get('entity_type', 'unknown')
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Report - {project_name}</title>
    <style>
        :root {{
            --bg-dark: #0d1117;
            --bg-medium: #161b22;
            --bg-light: #21262d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --border: #30363d;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 40px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid var(--accent-blue);
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1em;
        }}
        
        .header .meta {{
            margin-top: 20px;
            font-size: 0.9em;
            color: var(--text-secondary);
        }}
        
        .section {{
            background: var(--bg-medium);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        
        .section h2 {{
            color: var(--accent-blue);
            font-size: 1.4em;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }}
        
        .section h3 {{
            color: var(--text-primary);
            font-size: 1.1em;
            margin: 16px 0 8px 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: var(--bg-light);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: var(--accent-blue);
        }}
        
        .stat-card .label {{
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        th {{
            background: var(--bg-light);
            color: var(--text-secondary);
            font-weight: 500;
        }}
        
        tr:hover {{
            background: var(--bg-light);
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .badge-email {{ background: #1f6feb20; color: #58a6ff; }}
        .badge-domain {{ background: #23863620; color: #3fb950; }}
        .badge-ip {{ background: #f0883e20; color: #f0883e; }}
        .badge-phone {{ background: #a371f720; color: #a371f7; }}
        .badge-username {{ background: #db61a220; color: #db61a2; }}
        .badge-breach {{ background: #f8514920; color: #f85149; }}
        
        .risk-low {{ color: var(--accent-green); }}
        .risk-medium {{ color: var(--accent-yellow); }}
        .risk-high {{ color: var(--accent-red); }}
        
        .ai-summary {{
            background: linear-gradient(135deg, var(--bg-light), var(--bg-medium));
            border-left: 4px solid var(--accent-blue);
            padding: 20px;
            margin: 20px 0;
            font-style: italic;
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 0;
            color: var(--text-secondary);
            font-size: 0.9em;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }}
        
        @media print {{
            body {{
                background: white;
                color: black;
            }}
            .section {{
                background: #f5f5f5;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OSINT Intelligence Report</h1>
            <div class="subtitle">{project_name}</div>
            <div class="meta">
                Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")} |
                Classification: UNCLASSIFIED
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Executive Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{len(entities)}</div>
                    <div class="label">Entities Discovered</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(connections)}</div>
                    <div class="label">Relationships</div>
                </div>
                <div class="stat-card">
                    <div class="value">{len(entity_types)}</div>
                    <div class="label">Entity Types</div>
                </div>
                <div class="stat-card">
                    <div class="value">{entity_types.get('breach', 0)}</div>
                    <div class="label">Breaches Found</div>
                </div>
            </div>
            
            {"<div class='ai-summary'>" + ai_summary + "</div>" if ai_summary else ""}
        </div>
        
        <div class="section">
            <h2>📈 Entity Breakdown</h2>
            <table>
                <tr>
                    <th>Entity Type</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
"""
        
        total = len(entities) if entities else 1
        for etype, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            badge_class = f"badge-{etype}" if etype in ['email', 'domain', 'ip', 'phone', 'username', 'breach'] else ''
            html += f"""
                <tr>
                    <td><span class="badge {badge_class}">{etype.title()}</span></td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""
        
        html += """
            </table>
        </div>
        
        <div class="section">
            <h2>🔗 Entity Details</h2>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Value</th>
                    <th>Details</th>
                </tr>
"""
        
        for entity in entities[:50]:  # Limit to 50 for readability
            etype = entity.get('entity_type', 'unknown')
            value = entity.get('value', '')
            attrs = entity.get('attributes', {})
            details = ", ".join([f"{k}: {v}" for k, v in list(attrs.items())[:3]])
            badge_class = f"badge-{etype}" if etype in ['email', 'domain', 'ip', 'phone', 'username', 'breach'] else ''
            html += f"""
                <tr>
                    <td><span class="badge {badge_class}">{etype.title()}</span></td>
                    <td>{value}</td>
                    <td>{details}</td>
                </tr>
"""
        
        if len(entities) > 50:
            html += f"""
                <tr>
                    <td colspan="3" style="text-align: center; color: var(--text-secondary);">
                        ... and {len(entities) - 50} more entities
                    </td>
                </tr>
"""
        
        # Add analytics section if available
        if analytics:
            html += f"""
            </table>
        </div>
        
        <div class="section">
            <h2>📊 Graph Analytics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="value">{analytics.get('connected_components', 0)}</div>
                    <div class="label">Connected Components</div>
                </div>
                <div class="stat-card">
                    <div class="value">{analytics.get('density', 0):.3f}</div>
                    <div class="label">Graph Density</div>
                </div>
                <div class="stat-card">
                    <div class="value">{analytics.get('avg_clustering', 0):.3f}</div>
                    <div class="label">Clustering Coefficient</div>
                </div>
            </div>
"""
            
            # Add top entities by PageRank
            if 'top_entities' in analytics:
                html += """
            <h3>🏆 Key Entities (by PageRank)</h3>
            <table>
                <tr>
                    <th>Entity</th>
                    <th>Score</th>
                </tr>
"""
                for entity_id, score in analytics['top_entities'][:10]:
                    # Find entity by ID
                    entity = next((e for e in entities if e.get('id') == entity_id), None)
                    if entity:
                        html += f"""
                <tr>
                    <td>{entity.get('value', 'Unknown')}</td>
                    <td>{score:.4f}</td>
                </tr>
"""
                html += """
            </table>
"""
        
        html += f"""
        </div>
        
        <div class="footer">
            <p>Generated by <strong>OSINT-Nexus</strong> - Cross-Platform Intelligence Gathering Tool</p>
            <p>Report ID: {datetime.now().strftime('%Y%m%d%H%M%S')} | For authorized use only</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_pdf_report(
        self,
        project_name: str,
        entities: List[Dict[str, Any]],
        connections: List[Tuple[int, int, str]],
        output_path: str,
        analytics: Optional[Dict[str, Any]] = None,
        ai_summary: str = ""
    ) -> bool:
        """Generate a PDF report. Returns True on success."""
        if not self._pdf_available:
            print("PDF generation requires reportlab. Install with: pip install reportlab")
            return False
        
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak
            )
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#1f6feb')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10,
                textColor=colors.HexColor('#58a6ff')
            )
            
            # Build content
            story = []
            
            # Title
            story.append(Paragraph(f"OSINT Intelligence Report", title_style))
            story.append(Paragraph(f"Project: {project_name}", styles['Heading2']))
            story.append(Paragraph(
                f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
                styles['Normal']
            ))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))
            summary_data = [
                ['Metric', 'Value'],
                ['Total Entities', str(len(entities))],
                ['Total Connections', str(len(connections))],
                ['Entity Types', str(len(set(e.get('entity_type', '') for e in entities)))],
            ]
            
            t = Table(summary_data, colWidths=[3*inch, 2*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#21262d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#30363d')),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))
            
            # AI Summary if available
            if ai_summary:
                story.append(Paragraph("AI Analysis", heading_style))
                story.append(Paragraph(ai_summary, styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Entity list
            story.append(Paragraph("Discovered Entities", heading_style))
            
            entity_data = [['Type', 'Value']]
            for e in entities[:30]:
                entity_data.append([
                    e.get('entity_type', 'unknown').title(),
                    e.get('value', '')[:50]
                ])
            
            if len(entities) > 30:
                entity_data.append(['...', f'+ {len(entities) - 30} more entities'])
            
            t = Table(entity_data, colWidths=[1.5*inch, 4*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#21262d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#30363d')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(t)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            return False
    
    def export_stix(
        self,
        project_name: str,
        entities: List[Dict[str, Any]],
        connections: List[Tuple[int, int, str]]
    ) -> str:
        """
        Export data in STIX 2.1 format.
        STIX (Structured Threat Information Expression) is a standard for CTI sharing.
        """
        import uuid
        
        stix_bundle = {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": []
        }
        
        # Create identity for the report creator
        identity_id = f"identity--{uuid.uuid4()}"
        stix_bundle["objects"].append({
            "type": "identity",
            "id": identity_id,
            "created": datetime.now().isoformat() + "Z",
            "modified": datetime.now().isoformat() + "Z",
            "name": "OSINT-Nexus",
            "identity_class": "tool",
            "description": "Automated OSINT gathering tool"
        })
        
        # Create report object
        report_id = f"report--{uuid.uuid4()}"
        object_refs = [identity_id]
        
        # Map entities to STIX observables
        entity_id_map = {}
        
        for entity in entities:
            stix_type = self._map_entity_to_stix_type(entity.get('entity_type', ''))
            if not stix_type:
                continue
            
            stix_id = f"{stix_type}--{uuid.uuid4()}"
            entity_id_map[entity.get('id', 0)] = stix_id
            object_refs.append(stix_id)
            
            stix_obj = {
                "type": stix_type,
                "id": stix_id,
                "created": datetime.now().isoformat() + "Z",
                "modified": datetime.now().isoformat() + "Z",
            }
            
            # Add type-specific fields
            etype = entity.get('entity_type', '')
            value = entity.get('value', '')
            
            if etype == 'email':
                stix_obj["value"] = value
            elif etype == 'domain':
                stix_obj["value"] = value
            elif etype == 'ip':
                stix_obj["value"] = value
            elif etype == 'url':
                stix_obj["value"] = value
            else:
                stix_obj["name"] = value
                stix_obj["description"] = json.dumps(entity.get('attributes', {}))
            
            stix_bundle["objects"].append(stix_obj)
        
        # Add relationships
        for src_id, tgt_id, relationship in connections:
            src_stix = entity_id_map.get(src_id)
            tgt_stix = entity_id_map.get(tgt_id)
            
            if src_stix and tgt_stix:
                rel_id = f"relationship--{uuid.uuid4()}"
                stix_bundle["objects"].append({
                    "type": "relationship",
                    "id": rel_id,
                    "created": datetime.now().isoformat() + "Z",
                    "modified": datetime.now().isoformat() + "Z",
                    "relationship_type": relationship.replace("_", "-"),
                    "source_ref": src_stix,
                    "target_ref": tgt_stix
                })
                object_refs.append(rel_id)
        
        # Add report
        stix_bundle["objects"].insert(1, {
            "type": "report",
            "id": report_id,
            "created": datetime.now().isoformat() + "Z",
            "modified": datetime.now().isoformat() + "Z",
            "name": f"OSINT Report: {project_name}",
            "description": f"Automated OSINT investigation report generated by OSINT-Nexus",
            "report_types": ["threat-report"],
            "published": datetime.now().isoformat() + "Z",
            "object_refs": object_refs
        })
        
        return json.dumps(stix_bundle, indent=2)
    
    def _map_entity_to_stix_type(self, entity_type: str) -> Optional[str]:
        """Map OSINT entity type to STIX observable type."""
        mapping = {
            'email': 'email-addr',
            'domain': 'domain-name',
            'ip': 'ipv4-addr',
            'url': 'url',
            'username': 'user-account',
            'phone': 'x-osint-phone',  # Custom extension
            'breach': 'x-osint-breach',  # Custom extension
        }
        return mapping.get(entity_type.lower())
    
    def save_html_report(
        self,
        html_content: str,
        output_path: str
    ) -> bool:
        """Save HTML report to file."""
        try:
            Path(output_path).write_text(html_content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error saving HTML report: {e}")
            return False


# Global instance
report_generator = ReportGenerator()
