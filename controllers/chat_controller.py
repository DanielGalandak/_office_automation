# controllers/chat_controller.py - Kontroler pro chat

from flask import Blueprint, request, jsonify, render_template, current_app, session
from services.llm_service import LLMService
from contexts.project_context import ProjectContext
from datetime import datetime
import os

chat_bp = Blueprint('chat', __name__)

# Inicializace služeb
llm_service = None
project_context = None

@chat_bp.before_request
def before_request():
    global llm_service, project_context
    if llm_service is None:
        llm_service = LLMService(current_app.config)
    if project_context is None:
        project_context = ProjectContext(current_app.config.get('DATABASE_URI', 'office_automation.db'))

@chat_bp.route('/', methods=['GET'])
def general_chat_page():
    """Zobrazí stránku s obecným chatem."""
    # Získání seznamu projektů pro sidebar
    projects = project_context.get_all_projects()
    return render_template('chat.html', projects=projects, project=None, project_id=None)

@chat_bp.route('/project/<int:project_id>', methods=['GET'])
def project_chat_page(project_id):
    """Zobrazí stránku s chatem pro konkrétní projekt."""
    # Získání projektu a seznamu všech projektů pro sidebar
    project = project_context.get_project_by_id(project_id)
    projects = project_context.get_all_projects()
    
    if not project:
        return render_template('error.html', message='Projekt nebyl nalezen'), 404
    
    return render_template('chat.html', projects=projects, project=project, project_id=project_id)

@chat_bp.route('/project/<int:project_id>', methods=['POST'])
def project_chat(project_id):
    """API endpoint pro chat s projektem."""
    # Kontrola, zda je message v požadavku
    if not request.json or 'message' not in request.json:
        return jsonify({
            'status': 'error', 
            'message': 'Chybí pole "message" v požadavku'
        }), 400
    
    message = request.json['message']
    
    # Kontrola, zda projekt existuje
    project = project_context.get_project_by_id(project_id)
    if not project:
        return jsonify({
            'status': 'error',
            'message': 'Projekt nebyl nalezen'
        }), 404
    
    try:
        # Volání LLM služby pro získání odpovědi
        result = llm_service.chat_with_project(project_id, message)
        
        # Přidání časové značky pro front-end
        if 'timestamp' not in result:
            result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
    except Exception as e:
        # Logování chyby
        current_app.logger.error(f"Chyba při komunikaci s LLM: {str(e)}")
        
        # Pokud LLM není nakonfigurováno nebo došlo k chybě, použijeme fallback
        return jsonify({
            'status': 'error',
            'message': f"Chyba při generování odpovědi: {str(e)}",
            'response': "Omlouvám se, ale došlo k chybě při generování odpovědi. Zkontrolujte, zda jsou správně nastaveny API klíče pro LLM v proměnných prostředí.",
            'timestamp': datetime.now().isoformat()
        })

@chat_bp.route('/general', methods=['POST'])
def general_chat():
    """API endpoint pro obecný chat bez kontextu projektu."""
    # Kontrola, zda je message v požadavku
    if not request.json or 'message' not in request.json:
        return jsonify({
            'status': 'error', 
            'message': 'Chybí pole "message" v požadavku'
        }), 400
    
    message = request.json['message']
    
    try:
        # Kontrola, zda je LLM nakonfigurováno
        if not os.environ.get('OPENAI_API_KEY') and not os.environ.get('ANTHROPIC_API_KEY'):
            return jsonify({
                'status': 'warning',
                'message': 'LLM není nakonfigurováno',
                'response': "Pro chat s AI je potřeba nakonfigurovat API klíče pro OpenAI nebo Anthropic. Nastavte proměnné prostředí OPENAI_API_KEY nebo ANTHROPIC_API_KEY.",
                'timestamp': datetime.now().isoformat()
            })
        
        # Volání LLM služby pro obecný chat bez kontextu
        response = llm_service.general_chat(message)
        
        return jsonify({
            'status': 'success',
            'message': 'Odpověď byla vygenerována',
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        # Logování chyby
        current_app.logger.error(f"Chyba při komunikaci s LLM: {str(e)}")
        
        # Pokud LLM není nakonfigurováno nebo došlo k chybě, použijeme fallback
        return jsonify({
            'status': 'error',
            'message': f"Chyba při generování odpovědi: {str(e)}",
            'response': "Omlouvám se, ale došlo k chybě při generování odpovědi. Zkontrolujte, zda jsou správně nastaveny API klíče pro LLM v proměnných prostředí.",
            'timestamp': datetime.now().isoformat()
        })

# Historie chatu - jednoduchá implementace pro ukládání historie konverzace v session
@chat_bp.route('/history', methods=['GET'])
def get_chat_history():
    """Získá historii chatu pro aktuální relaci."""
    history = session.get('chat_history', {})
    return jsonify({
        'status': 'success',
        'history': history
    })