# contexts/task_context.py - Kontext pro úlohy (implementace MCP)

from typing import List, Dict, Any, Optional
from models.task_model import Task
import sqlite3
import json
import os
from datetime import datetime


class TaskContext:
    """Kontext pro práci s úlohami v MCP architektuře."""
    
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
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            description TEXT,
            created_at TEXT,
            updated_at TEXT,
            scheduled_for TEXT,
            completed_at TEXT,
            created_by INTEGER,
            parameters TEXT,
            result TEXT,
            error TEXT,
            is_recurring INTEGER DEFAULT 0,
            recurrence_pattern TEXT,
            tags TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_all_tasks(self) -> List[Task]:
        """Získá všechny úlohy z databáze."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            task_dict = dict(row)
            # Deserializace JSON sloupců
            for json_field in ['parameters', 'result', 'tags']:
                if task_dict.get(json_field):
                    try:
                        task_dict[json_field] = json.loads(task_dict[json_field])
                    except (json.JSONDecodeError, TypeError):
                        task_dict[json_field] = {} if json_field in ['parameters', 'result'] else []
                else:
                    task_dict[json_field] = {} if json_field in ['parameters', 'result'] else []
            
            tasks.append(Task.from_dict(task_dict))
        
        conn.close()
        return tasks
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Získá úlohu podle ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        task_dict = dict(row)
        # Deserializace JSON sloupců
        for json_field in ['parameters', 'result', 'tags']:
            if task_dict.get(json_field):
                try:
                    task_dict[json_field] = json.loads(task_dict[json_field])
                except (json.JSONDecodeError, TypeError):
                    task_dict[json_field] = {} if json_field in ['parameters', 'result'] else []
            else:
                task_dict[json_field] = {} if json_field in ['parameters', 'result'] else []
        
        conn.close()
        return Task.from_dict(task_dict)
    
    def create_task(self, task: Task) -> Task:
        """Vytvoří novou úlohu v databázi."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serializace JSON sloupců
        task_dict = task.to_dict()
        for json_field in ['parameters', 'result', 'tags']:
            if task_dict.get(json_field):
                task_dict[json_field] = json.dumps(task_dict[json_field])
            else:
                task_dict[json_field] = json.dumps({}) if json_field in ['parameters', 'result'] else json.dumps([])
        
        cursor.execute('''
            INSERT INTO tasks (
                name, type, category, status, priority, description,
                created_at, updated_at, scheduled_for, completed_at, created_by,
                parameters, result, error, is_recurring, recurrence_pattern, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_dict['name'], task_dict['type'], task_dict['category'],
            task_dict['status'], task_dict['priority'], task_dict['description'],
            task_dict['created_at'], task_dict['updated_at'], task_dict['scheduled_for'],
            task_dict['completed_at'], task_dict['created_by'],
            task_dict['parameters'], task_dict['result'], task_dict['error'],
            1 if task_dict['is_recurring'] else 0, task_dict['recurrence_pattern'], task_dict['tags']
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Načtení vytvořené úlohy s přiděleným ID
        created_task = self.get_task_by_id(task_id)
        return created_task
    
    def update_task(self, task: Task) -> Task:
        """Aktualizuje existující úlohu v databázi."""
        if not task.id:
            raise ValueError("Task ID is required for update operation")
        
        task.updated_at = datetime.now()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Serializace JSON sloupců
        task_dict = task.to_dict()
        for json_field in ['parameters', 'result', 'tags']:
            if task_dict.get(json_field):
                task_dict[json_field] = json.dumps(task_dict[json_field])
            else:
                task_dict[json_field] = json.dumps({}) if json_field in ['parameters', 'result'] else json.dumps([])
        
        cursor.execute('''
            UPDATE tasks SET
                name = ?, type = ?, category = ?, status = ?, priority = ?,
                description = ?, updated_at = ?, scheduled_for = ?, completed_at = ?,
                parameters = ?, result = ?, error = ?, is_recurring = ?,
                recurrence_pattern = ?, tags = ?
            WHERE id = ?
        ''', (
            task_dict['name'], task_dict['type'], task_dict['category'],
            task_dict['status'], task_dict['priority'], task_dict['description'],
            task_dict['updated_at'], task_dict['scheduled_for'], task_dict['completed_at'],
            task_dict['parameters'], task_dict['result'], task_dict['error'],
            1 if task_dict['is_recurring'] else 0, task_dict['recurrence_pattern'], 
            task_dict['tags'], task_dict['id']
        ))
        
        conn.commit()
        conn.close()
        
        # Načtení aktualizované úlohy
        updated_task = self.get_task_by_id(task.id)
        return updated_task
    
    def delete_task(self, task_id: int) -> bool:
        """Odstraní úlohu z databáze."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Získá úlohy podle jejich stavu."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC', (status,))
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            task_dict = dict(row)
            # Deserializace JSON sloupců
            for json_field in ['parameters', 'result', 'tags']:
                if task_dict.get(json_field):
                    task_dict[json_field] = json.loads(task_dict[json_field])
                else:
                    task_dict[json_field] = {} if json_field in ['parameters', 'result'] else []
            
            tasks.append(Task.from_dict(task_dict))
        
        conn.close()
        return tasks

    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Získá úlohy podle kategorie."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE category = ? ORDER BY created_at DESC', (category,))
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            task_dict = dict(row)
            # Deserializace JSON sloupců
            for json_field in ['parameters', 'result', 'tags']:
                if task_dict.get(json_field):
                    task_dict[json_field] = json.loads(task_dict[json_field])
                else:
                    task_dict[json_field] = {} if json_field in ['parameters', 'result'] else []
            
            tasks.append(Task.from_dict(task_dict))
        
        conn.close()
        return tasks