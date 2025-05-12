# controllers/project_controller.py - Kontroler pro projekty

from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for
from models.project_model import Project
from contexts.project_context import ProjectContext
from datetime import datetime
import os
import json

project_bp = Blueprint('project', __name__)

# Inicializace projektu
project_context = None

@project_bp.before_request
def before_request():
    global project_context
    if project_context is None:
        project_context = ProjectContext(current_app.config.get('DATABASE_URI', 'office_automation.db'))

@project_bp.route('/', methods=['GET'])
def list_projects():
    """Zobrazí seznam všech projektů."""
    projects = project_context.get_all_projects()
    return render_template('projects.html', projects=projects)

@project_bp.route('/create', methods=['GET', 'POST'])
def create_project():
    """Formulář pro vytvoření nového projektu a zpracování odeslaných dat."""
    if request.method == 'POST':
        # Získání dat z formuláře
        name = request.form.get('name', '')
        description = request.form.get('description', '')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
        tags = [tag.strip() for tag in tags if tag.strip()]
        icon = request.form.get('icon', 'bi-folder')
        
        # Vytvoření nového projektu
        project = Project(
            name=name,
            description=description,
            created_at=datetime.now(),
            created_by=1,  # Předpokládáme přihlášeného uživatele
            icon=icon,
            tags=tags
        )
        
        # Uložení projektu
        created_project = project_context.create_project(project)
        
        # Přesměrování na detail projektu
        return redirect(url_for('project.view_project', project_id=created_project.id))
    
    # Zobrazení formuláře pro vytvoření projektu
    return render_template('create_project.html')

@project_bp.route('/<int:project_id>', methods=['GET'])
def view_project(project_id):
    """Zobrazí detail projektu."""
    project = project_context.get_project_by_id(project_id)
    if not project:
        return render_template('error.html', message='Projekt nebyl nalezen'), 404
    
    # Získání úkolů a dokumentů projektu pro zobrazení
    # V reálné aplikaci bychom zde načetli skutečné objekty úkolů a dokumentů
    tasks = []  # Zde by byl kód pro načtení úkolů
    documents = []  # Zde by byl kód pro načtení dokumentů
    
    return render_template('project_detail.html', project=project, tasks=tasks, documents=documents)

@project_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    """Formulář pro úpravu projektu a zpracování odeslaných dat."""
    project = project_context.get_project_by_id(project_id)
    if not project:
        return render_template('error.html', message='Projekt nebyl nalezen'), 404
    
    if request.method == 'POST':
        # Aktualizace dat projektu
        project.name = request.form.get('name', project.name)
        project.description = request.form.get('description', project.description)
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
        project.tags = [tag.strip() for tag in tags if tag.strip()]
        project.icon = request.form.get('icon', project.icon)
        project.updated_at = datetime.now()
        
        # Uložení aktualizovaného projektu
        project_context.update_project(project)
        
        # Přesměrování na detail projektu
        return redirect(url_for('project.view_project', project_id=project.id))
    
    # Zobrazení formuláře pro úpravu projektu
    return render_template('edit_project.html', project=project)

@project_bp.route('/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    """Smaže projekt."""
    success = project_context.delete_project(project_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX požadavek
        if success:
            return jsonify({'status': 'success', 'message': 'Projekt byl úspěšně smazán'})
        else:
            return jsonify({'status': 'error', 'message': 'Projekt nebyl nalezen'}), 404
    else:
        # Běžný požadavek
        if success:
            return redirect(url_for('project.list_projects'))
        else:
            return render_template('error.html', message='Projekt nebyl nalezen'), 404

@project_bp.route('/<int:project_id>/add-task/<int:task_id>', methods=['POST'])
def add_task_to_project(project_id, task_id):
    """Přidá úkol do projektu."""
    success = project_context.add_task_to_project(project_id, task_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX požadavek
        if success:
            return jsonify({'status': 'success', 'message': 'Úkol byl přidán do projektu'})
        else:
            return jsonify({'status': 'error', 'message': 'Projekt nebo úkol nebyl nalezen'}), 404
    else:
        # Běžný požadavek
        if success:
            return redirect(url_for('project.view_project', project_id=project_id))
        else:
            return render_template('error.html', message='Projekt nebo úkol nebyl nalezen'), 404

@project_bp.route('/<int:project_id>/remove-task/<int:task_id>', methods=['POST'])
def remove_task_from_project(project_id, task_id):
    """Odebere úkol z projektu."""
    success = project_context.remove_task_from_project(project_id, task_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX požadavek
        if success:
            return jsonify({'status': 'success', 'message': 'Úkol byl odebrán z projektu'})
        else:
            return jsonify({'status': 'error', 'message': 'Projekt nebo úkol nebyl nalezen'}), 404
    else:
        # Běžný požadavek
        if success:
            return redirect(url_for('project.view_project', project_id=project_id))
        else:
            return render_template('error.html', message='Projekt nebo úkol nebyl nalezen'), 404

@project_bp.route('/<int:project_id>/add-document/<int:document_id>', methods=['POST'])
def add_document_to_project(project_id, document_id):
    """Přidá dokument do projektu."""
    success = project_context.add_document_to_project(project_id, document_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX požadavek
        if success:
            return jsonify({'status': 'success', 'message': 'Dokument byl přidán do projektu'})
        else:
            return jsonify({'status': 'error', 'message': 'Projekt nebo dokument nebyl nalezen'}), 404
    else:
        # Běžný požadavek
        if success:
            return redirect(url_for('project.view_project', project_id=project_id))
        else:
            return render_template('error.html', message='Projekt nebo dokument nebyl nalezen'), 404

@project_bp.route('/<int:project_id>/remove-document/<int:document_id>', methods=['POST'])
def remove_document_from_project(project_id, document_id):
    """Odebere dokument z projektu."""
    success = project_context.remove_document_from_project(project_id, document_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX požadavek
        if success:
            return jsonify({'status': 'success', 'message': 'Dokument byl odebrán z projektu'})
        else:
            return jsonify({'status': 'error', 'message': 'Projekt nebo dokument nebyl nalezen'}), 404
    else:
        # Běžný požadavek
        if success:
            return redirect(url_for('project.view_project', project_id=project_id))
        else:
            return render_template('error.html', message='Projekt nebo dokument nebyl nalezen'), 404

@project_bp.route('/api/list', methods=['GET'])
def api_list_projects():
    """API endpoint pro seznam projektů."""
    projects = project_context.get_all_projects()
    return jsonify({
        'status': 'success',
        'count': len(projects),
        'projects': [project.to_dict() for project in projects]
    })

@project_bp.route('/api/<int:project_id>', methods=['GET'])
def api_get_project(project_id):
    """API endpoint pro získání projektu."""
    project = project_context.get_project_by_id(project_id)
    if not project:
        return jsonify({'status': 'error', 'message': 'Projekt nebyl nalezen'}), 404
    
    return jsonify({
        'status': 'success',
        'project': project.to_dict()
    })