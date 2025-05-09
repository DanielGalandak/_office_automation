# models/user_model.py - Model pro uživatele

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class User:
    """Model reprezentující uživatele v MCP architektuře."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    is_admin: bool = False
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Převede model na slovník pro uložení nebo serializaci."""
        result = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "preferences": self.preferences
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Vytvoří model z dodaného slovníku."""
        # Převod stringových datumů na datetime objekty
        for date_field in ['created_at', 'last_login']:
            if data.get(date_field) and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        return cls(**data)