# contexts/project_context.py - Kontext pro projekty (implementace MCP)

from typing import List, Dict, Any, Optional
from models.project_model import Project
import sqlite3
import json
import os
from datetime import datetime


class ProjectContext:
    """Kontext pro práci s projekty v MCP architektuře."""
    
    def __init__(self, db_path: str = "office_automation.db"):
        # Ověření, zda jde o SQLAlchemy URI
        if db_path.startswith('sqlite:///'):
            # Extrakce cesty k souboru z URI
            self.db_path = db_path.replace('sqlite:///', '')
        else:
            self.db_path = db_path
        
        # Převeďte relativní cestu na absolutní - zajistí, že SQLite bude mít přístup k souboru
        if not os.path.isabs(self.db_path):
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.db_path)
        
        # Zajistěte, že adresář pro databázi existuje
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self._create_tables_if_not_exist()

    
    def _create_tables_if_not_exist(self):
        """Vytvoří potřebné tabulky v databázi, pokud neexistují."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT,
            updated_at TEXT,
            created_by INTEGER,
            icon TEXT,
            tags TEXT,
            metadata TEXT,
            tasks TEXT,
            documents TEXT,
            context_id TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_all_projects(self) -> List[Project]:
        """Získá všechny projekty z databáze."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            project_dict = dict(row)
            # Deserializace JSON sloupců
            for json_field in ['tags', 'metadata', 'tasks', 'documents']:
                if project_dict.get(json_field):
                    try:
                        project_dict[json_field] = json.loads(project_dict[json_field])
                    except (json.JSONDecodeError, TypeError):
                        project_dict[json_field] = [] if json_field in ['tags', 'tasks', 'documents'] else {}
                else:
                    project_dict[json_field] = [] if json_field in ['tags', 'tasks', 'documents'] else {}
            
            projects.append(Project.from_dict(project_dict))
        
        conn.close()
        return projects
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Získá projekt podle ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        project_dict = dict(row)
        # Deserializace JSON sloupců
        for json_field in ['tags', 'metadata', 'tasks', 'documents']:
            if project_dict.get(json_field):
                try:
                    project_dict[json_field] = json.loads(project_dict[json_field])
                except (json.JSONDecodeError, TypeError):
                    project_dict[json_field] = [] if json_field in ['tags', 'tasks', 'documents'] else {}
            else:
                project_dict[json_field] = [] if json_field in ['tags', 'tasks', 'documents'] else {}
        
        conn.close()
        return Project.from_dict(project_dict)
    
    def create_project(self, project: Project) -> Project:
        """Vytvoří nový projekt v databázi."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serializace JSON sloupců
        project_dict = project.to_dict()
        for json_field in ['tags', 'metadata', 'tasks', 'documents']:
            if project_dict.get(json_field):
                project_dict[json_field] = json.dumps(project_dict[json_field])
            else:
                project_dict[json_field] = json.dumps([]) if json_field in ['tags', 'tasks', 'documents'] else json.dumps({})
        
        cursor.execute('''
            INSERT INTO projects (
                name, description, created_at, updated_at, created_by,
                icon, tags, metadata, tasks, documents, context_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_dict['name'], project_dict['description'],
            project_dict['created_at'], project_dict['updated_at'],
            project_dict['created_by'], project_dict['icon'],
            project_dict['tags'], project_dict['metadata'],
            project_dict['tasks'], project_dict['documents'],
            project_dict['context_id']
        ))
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Načtení vytvořeného projektu s přiděleným ID
        created_project = self.get_project_by_id(project_id)
        return created_project
    
    def update_project(self, project: Project) -> Project:
        """Aktualizuje existující projekt v databázi."""
        if not project.id:
            raise ValueError("Project ID is required for update operation")
        
        project.updated_at = datetime.now()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serializace JSON sloupců
        project_dict = project.to_dict()
        for json_field in ['tags', 'metadata', 'tasks', 'documents']:
            if project_dict.get(json_field):
                project_dict[json_field] = json.dumps(project_dict[json_field])
            else:
                project_dict[json_field] = json.dumps([]) if json_field in ['tags', 'tasks', 'documents'] else json.dumps({})
        
        cursor.execute('''
            UPDATE projects SET
                name = ?, description = ?, updated_at = ?, created_by = ?,
                icon = ?, tags = ?, metadata = ?, tasks = ?, documents = ?,
                context_id = ?
            WHERE id = ?
        ''', (
            project_dict['name'], project_dict['description'],
            project_dict['updated_at'], project_dict['created_by'],
            project_dict['icon'], project_dict['tags'],
            project_dict['metadata'], project_dict['tasks'],
            project_dict['documents'], project_dict['context_id'],
            project_dict['id']
        ))
        
        conn.commit()
        conn.close()
        
        # Načtení aktualizovaného projektu
        updated_project = self.get_project_by_id(project.id)
        return updated_project
    
    def delete_project(self, project_id: int) -> bool:
        """Odstraní projekt z databáze."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def add_task_to_project(self, project_id: int, task_id: int) -> bool:
        """Přidá úkol do projektu."""
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        
        if task_id not in project.tasks:
            project.tasks.append(task_id)
            self.update_project(project)
            return True
        
        return False
    
    def remove_task_from_project(self, project_id: int, task_id: int) -> bool:
        """Odebere úkol z projektu."""
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        
        if task_id in project.tasks:
            project.tasks.remove(task_id)
            self.update_project(project)
            return True
        
        return False
    
    def add_document_to_project(self, project_id: int, document_id: int) -> bool:
        """Přidá dokument do projektu."""
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        
        if document_id not in project.documents:
            project.documents.append(document_id)
            self.update_project(project)
            return True
        
        return False
    
    def remove_document_from_project(self, project_id: int, document_id: int) -> bool:
        """Odebere dokument z projektu."""
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        
        if document_id in project.documents:
            project.documents.remove(document_id)
            self.update_project(project)
            return True
        
        return False
    
    def get_project_tasks(self, project_id: int) -> List[int]:
        """Získá ID úkolů patřících k projektu."""
        project = self.get_project_by_id(project_id)
        if not project:
            return []
        
        return project.tasks
    
    def get_project_documents(self, project_id: int) -> List[int]:
        """Získá ID dokumentů patřících k projektu."""
        project = self.get_project_by_id(project_id)
        if not project:
            return []
        
        return project.documents