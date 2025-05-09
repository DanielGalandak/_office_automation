# controllers/task_controller.py - Kontroler pro úlohy

from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for
from models.task_model import Task
from contexts.task_context import TaskContext
from services.email_service import EmailService
from services.file_service import FileService
from services.pdf_service import PdfService
from datetime import datetime
import json

task_bp = Blueprint('task', __name__)

# Inicializace potřebných služeb a kontextů
task_context = None
email_service = None
file_service = None
pdf_service = None

@task_bp.before_request
def before_request():
    global task_context, email_service, file_service, pdf_service
    if task_context is None:
        task_context = TaskContext(current_app.config.get('DATABASE_URI', 'office_automation.db'))
    if email_service is None:
        email_service = EmailService(current_app.config)
    if file_service is None:
        file_service = FileService(current_app.config)
    if pdf_service is None:
        pdf_service = PdfService(current_app.config)

@task_bp.route('/', methods=['GET'])
def list_tasks():
    """Zobrazí seznam všech úloh."""
    tasks = task_context.get_all_tasks()
    return render_template('tasks.html', tasks=tasks)

@task_bp.route('/create', methods=['GET', 'POST'])
def create_task():
    """Formulář pro vytvoření nové úlohy a zpracování odeslaných dat."""
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Zpracování parametrů úlohy z formuláře
        parameters = {}
        for key in request.form:
            if key.startswith('param_'):
                param_name = key.replace('param_', '')
                parameters[param_name] = request.form[key]
        
        # Vytvoření nové úlohy
        task = Task(
            name=data.get('name', ''),
            type=data.get('type', ''),
            category=data.get('category', ''),
            status='pending',
            priority=int(data.get('priority', 1)),
            description=data.get('description', ''),
            scheduled_for=datetime.fromisoformat(data.get('scheduled_for')) if data.get('scheduled_for') else None,
            created_by=1,  # Předpokládáme přihlášeného uživatele (v reálné aplikaci by se načetl z session)
            parameters=parameters,
            is_recurring=data.get('is_recurring', '0') == '1',
            recurrence_pattern=data.get('recurrence_pattern', ''),
            tags=data.get('tags', '').split(',') if data.get('tags') else []
        )
        
        # Uložení úlohy do databáze
        created_task = task_context.create_task(task)
        
        # Přesměrování zpět na seznam úloh
        return redirect(url_for('task.list_tasks'))
    
    # Zobrazení formuláře pro vytvoření úlohy
    return render_template('create_task.html')

@task_bp.route('/<int:task_id>', methods=['GET'])
def view_task(task_id):
    """Zobrazí detail úlohy."""
    task = task_context.get_task_by_id(task_id)
    if not task:
        return render_template('error.html', message='Úloha nebyla nalezena'), 404
    
    return render_template('task_detail.html', task=task)

@task_bp.route('/<int:task_id>/run', methods=['POST'])
def run_task(task_id):
    """Spustí úlohu."""
    task = task_context.get_task_by_id(task_id)
    if not task:
        return jsonify({'status': 'error', 'message': 'Úloha nebyla nalezena'}), 404
    
    # Nastavení stavu úlohy na "běží"
    task.status = 'running'
    task_context.update_task(task)
    
    try:
        result = None
        
        # Spuštění odpovídající akce podle kategorie a typu úlohy
        if task.category == 'email':
            if task.type == 'send_email':
                result = email_service.send_email(
                    recipient=task.parameters.get('recipient', ''),
                    subject=task.parameters.get('subject', ''),
                    body=task.parameters.get('body', ''),
                    html_body=task.parameters.get('html_body'),
                    attachments=task.parameters.get('attachments', [])
                )
            elif task.type == 'check_inbox':
                result = email_service.check_inbox(
                    limit=int(task.parameters.get('limit', 10)),
                    folder=task.parameters.get('folder', 'INBOX'),
                    unread_only=task.parameters.get('unread_only', 'false').lower() == 'true'
                )
        
        elif task.category == 'file':
            if task.type == 'convert_excel_to_csv':
                result = file_service.convert_excel_to_csv(
                    file_path=task.parameters.get('file_path', ''),
                    output_path=task.parameters.get('output_path')
                )
            elif task.type == 'rename_files':
                result = file_service.rename_files(
                    directory=task.parameters.get('directory', ''),
                    pattern=task.parameters.get('pattern', ''),
                    replacement=task.parameters.get('replacement', ''),
                    recursive=task.parameters.get('recursive', 'false').lower() == 'true'
                )
            elif task.type == 'organize_files':
                result = file_service.organize_files(
                    directory=task.parameters.get('directory', ''),
                    target_directory=task.parameters.get('target_directory')
                )
        
        elif task.category == 'pdf':
            if task.type == 'merge_pdfs':
                result = pdf_service.merge_pdfs(
                    pdf_files=task.parameters.get('pdf_files', []),
                    output_path=task.parameters.get('output_path', '')
                )
            elif task.type == 'extract_text':
                result = pdf_service.extract_text(
                    pdf_file=task.parameters.get('pdf_file', ''),
                    output_path=task.parameters.get('output_path')
                )
            elif task.type == 'create_pdf':
                result = pdf_service.create_pdf(
                    title=task.parameters.get('title', ''),
                    content=task.parameters.get('content', ''),
                    output_path=task.parameters.get('output_path', '')
                )
        
        # Uložení výsledku a aktualizace stavu úlohy
        task.status = 'completed' if result.get('status') == 'success' else 'failed'
        task.result = result
        task.completed_at = datetime.now()
        task.error = result.get('message') if result.get('status') == 'error' else None
        
        # Aktualizace úlohy v databázi
        updated_task = task_context.update_task(task)
        
        return jsonify({'status': 'success', 'task': updated_task.to_dict()})
        
    except Exception as e:
        # V případě chyby nastavíme stav úlohy na "chyba"
        task.status = 'failed'
        task.error = str(e)
        task.completed_at = datetime.now()
        task_context.update_task(task)
        
        return jsonify({'status': 'error', 'message': str(e)}), 500

@task_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Smaže úlohu."""
    success = task_context.delete_task(task_id)
    if not success:
        return jsonify({'status': 'error', 'message': 'Úloha nebyla nalezena'}), 404
    
    return jsonify({'status': 'success', 'message': 'Úloha byla smazána'})

@task_bp.route('/api/list', methods=['GET'])
def api_list_tasks():
    """API endpoint pro seznam úloh."""
    status = request.args.get('status')
    category = request.args.get('category')
    
    if status:
        tasks = task_context.get_tasks_by_status(status)
    elif category:
        tasks = task_context.get_tasks_by_category(category)
    else:
        tasks = task_context.get_all_tasks()
    
    return jsonify({
        'status': 'success',
        'count': len(tasks),
        'tasks': [task.to_dict() for task in tasks]
    })

@task_bp.route('/api/create', methods=['POST'])
def api_create_task():
    """API endpoint pro vytvoření úlohy."""
    try:
        data = request.json
        
        # Vytvoření nové úlohy
        task = Task(
            name=data.get('name', ''),
            type=data.get('type', ''),
            category=data.get('category', ''),
            status='pending',
            priority=int(data.get('priority', 1)),
            description=data.get('description', ''),
            scheduled_for=datetime.fromisoformat(data.get('scheduled_for')) if data.get('scheduled_for') else None,
            created_by=data.get('created_by', 1),
            parameters=data.get('parameters', {}),
            is_recurring=data.get('is_recurring', False),
            recurrence_pattern=data.get('recurrence_pattern', ''),
            tags=data.get('tags', [])
        )
        
        # Uložení úlohy do databáze
        created_task = task_context.create_task(task)
        
        return jsonify({
            'status': 'success',
            'message': 'Úloha byla vytvořena',
            'task': created_task.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400