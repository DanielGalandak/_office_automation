# models/task_model.py - Model pro úlohy (implementace MCP)

from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class Task:
    """Model reprezentující úlohu v MCP architektuře."""
    id: Optional[int] = None
    name: str = ""
    type: str = ""
    category: str = ""
    status: str = "pending"
    priority: int = 1  # 1=nízká, 2=střední, 3=vysoká
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Převede model na slovník pro uložení nebo serializaci."""
        result = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "status": self.status,
            "priority": self.priority,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "tags": self.tags
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Vytvoří model z dodaného slovníku."""
        # Převod stringových datumů na datetime objekty
        for date_field in ['created_at', 'updated_at', 'scheduled_for', 'completed_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        return cls(**data)