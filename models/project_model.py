# models/project_model.py - Model pro projekty

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class Project:
    """Model reprezentující projekt v MCP architektuře."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    icon: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Vztahové pole
    tasks: List[int] = field(default_factory=list)  # ID úkolů v projektu
    documents: List[int] = field(default_factory=list)  # ID dokumentů v projektu
    context_id: Optional[str] = None  # ID kontextového souboru
    
    def to_dict(self) -> Dict[str, Any]:
        """Převede model na slovník pro uložení nebo serializaci."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "icon": self.icon,
            "tags": self.tags,
            "metadata": self.metadata,
            "tasks": self.tasks,
            "documents": self.documents,
            "context_id": self.context_id
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Vytvoří model z dodaného slovníku."""
        # Převod stringových datumů na datetime objekty
        for date_field in ['created_at', 'updated_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        return cls(**data)