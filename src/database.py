"""
OSINT-Nexus Database Layer
SQLite3 database for local persistence of projects, entities, and connections.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Entity:
    """Represents an OSINT entity (node in the graph)."""
    id: Optional[int] = None
    entity_type: str = ""  # email, domain, ip, phone, username, person, company
    value: str = ""
    label: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    project_id: Optional[int] = None
    
    def __hash__(self):
        # Hash based on unique properties: type, value, and project_id
        # attributes aren't used for identity
        return hash((self.entity_type, self.value, self.project_id))
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return (self.entity_type == other.entity_type and 
                self.value == other.value and 
                self.project_id == other.project_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "value": self.value,
            "label": self.label,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "project_id": self.project_id
        }


@dataclass
class Connection:
    """Represents a connection (edge) between two entities."""
    id: Optional[int] = None
    source_id: int = 0
    target_id: int = 0
    relationship: str = ""  # "registered_on", "owns", "linked_to", etc.
    weight: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    project_id: Optional[int] = None


@dataclass
class Project:
    """Represents an OSINT project/investigation."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Database:
    """SQLite database manager for OSINT-Nexus."""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".osint-nexus" / "osint_nexus.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database with schema."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                value TEXT NOT NULL,
                label TEXT DEFAULT '',
                attributes TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE(project_id, entity_type, value)
            )
        """)
        
        # Connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relationship TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                attributes TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
            )
        """)
        
        # Scan results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                input_data TEXT NOT NULL,
                output_data TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_project ON entities(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_project ON connections(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_source ON connections(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_target ON connections(target_id)")
        
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # ==================== Project Operations ====================
    
    def create_project(self, name: str, description: str = "") -> int:
        """Create a new project and return its ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if row:
            return Project(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            )
        return None
    
    def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
        projects = []
        for row in cursor.fetchall():
            projects.append(Project(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ))
        return projects
    
    def delete_project(self, project_id: int):
        """Delete a project and all associated data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()
    
    # ==================== Entity Operations ====================
    
    def add_entity(self, entity: Entity) -> int:
        """Add an entity and return its ID."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO entities (project_id, entity_type, value, label, attributes)
                   VALUES (?, ?, ?, ?, ?)""",
                (entity.project_id, entity.entity_type, entity.value, 
                 entity.label, json.dumps(entity.attributes))
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Entity already exists, get its ID
            cursor.execute(
                "SELECT id FROM entities WHERE project_id = ? AND entity_type = ? AND value = ?",
                (entity.project_id, entity.entity_type, entity.value)
            )
            row = cursor.fetchone()
            return row["id"] if row else -1
    
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Get an entity by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        if row:
            return Entity(
                id=row["id"],
                entity_type=row["entity_type"],
                value=row["value"],
                label=row["label"],
                attributes=json.loads(row["attributes"]) if row["attributes"] else {},
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                project_id=row["project_id"]
            )
        return None
    
    def get_project_entities(self, project_id: int) -> List[Entity]:
        """Get all entities for a project."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE project_id = ?", (project_id,))
        entities = []
        for row in cursor.fetchall():
            entities.append(Entity(
                id=row["id"],
                entity_type=row["entity_type"],
                value=row["value"],
                label=row["label"],
                attributes=json.loads(row["attributes"]) if row["attributes"] else {},
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                project_id=row["project_id"]
            ))
        return entities
    
    def update_entity_attributes(self, entity_id: int, attributes: Dict[str, Any]):
        """Update entity attributes."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE entities SET attributes = ? WHERE id = ?",
            (json.dumps(attributes), entity_id)
        )
        self.conn.commit()
    
    # ==================== Connection Operations ====================
    
    def add_connection(self, connection: Connection) -> int:
        """Add a connection between entities."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO connections (project_id, source_id, target_id, relationship, weight, attributes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (connection.project_id, connection.source_id, connection.target_id,
             connection.relationship, connection.weight, json.dumps(connection.attributes))
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_project_connections(self, project_id: int) -> List[Connection]:
        """Get all connections for a project."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM connections WHERE project_id = ?", (project_id,))
        connections = []
        for row in cursor.fetchall():
            connections.append(Connection(
                id=row["id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relationship=row["relationship"],
                weight=row["weight"],
                attributes=json.loads(row["attributes"]) if row["attributes"] else {},
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                project_id=row["project_id"]
            ))
        return connections
    
    def get_entity_connections(self, entity_id: int) -> List[Connection]:
        """Get all connections for an entity (both incoming and outgoing)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM connections WHERE source_id = ? OR target_id = ?",
            (entity_id, entity_id)
        )
        connections = []
        for row in cursor.fetchall():
            connections.append(Connection(
                id=row["id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relationship=row["relationship"],
                weight=row["weight"],
                attributes=json.loads(row["attributes"]) if row["attributes"] else {},
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                project_id=row["project_id"]
            ))
        return connections
    
    # ==================== Scan Results ====================
    
    def save_scan_result(self, project_id: int, module_name: str, 
                         input_data: Dict, output_data: Dict, status: str = "completed") -> int:
        """Save a scan result."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO scan_results (project_id, module_name, input_data, output_data, status)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, module_name, json.dumps(input_data), json.dumps(output_data), status)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    # ==================== Export Functions ====================
    
    def export_project_json(self, project_id: int) -> Dict[str, Any]:
        """Export project data as JSON."""
        project = self.get_project(project_id)
        if not project:
            return {}
        
        entities = self.get_project_entities(project_id)
        connections = self.get_project_connections(project_id)
        
        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat() if project.created_at else None
            },
            "entities": [e.to_dict() for e in entities],
            "connections": [
                {
                    "id": c.id,
                    "source_id": c.source_id,
                    "target_id": c.target_id,
                    "relationship": c.relationship,
                    "weight": c.weight,
                    "attributes": c.attributes
                }
                for c in connections
            ]
        }
