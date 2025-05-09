# models/document_model.py - Model pro dokumenty

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class Document:
    """Model reprezentující dokument v MCP architektuře."""
    id: Optional[int] = None
    name: str = ""
    file_path: str = ""
    file_type: str = ""
    size: int = 0
    uploaded_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_processed: bool = False
    processing_result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Převede model na slovník pro uložení nebo serializaci."""
        result = {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "size": self.size,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
            "tags": self.tags,
            "is_processed": self.is_processed,
            "processing_result": self.processing_result
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Vytvoří model z dodaného slovníku."""
        # Převod stringových datumů na datetime objekty
        for date_field in ['created_at', 'updated_at']:
            if data.get(date_field) and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        return cls(**data)