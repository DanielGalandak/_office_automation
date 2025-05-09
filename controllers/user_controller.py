# controllers/user_controller.py

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from models.user_model import User
from datetime import datetime

user_bp = Blueprint('user', __name__)

# Simulovaná databáze uživatelů (v reálné aplikaci bychom použili kontext podobně jako u úloh)
users = [
    User(
        id=1,
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="Administrátorský",
        created_at=datetime.now(),
        is_admin=True
    ),
    User(
        id=2,
        username="user",
        email="user@example.com",
        first_name="Běžný",
        last_name="Uživatel",
        created_at=datetime.now()
    )
]

@user_bp.route('/', methods=['GET'])
def list_users():
    """Zobrazí seznam všech uživatelů."""
    return render_template('users.html', users=users)

@user_bp.route('/<int:user_id>', methods=['GET'])
def view_user(user_id):
    """Zobrazí detail uživatele."""
    user = next((u for u in users if u.id == user_id), None)
    if not user:
        return render_template('error.html', message='Uživatel nebyl nalezen'), 404
    
    return render_template('user_detail.html', user=user)

@user_bp.route('/api/list', methods=['GET'])
def api_list_users():
    """API endpoint pro seznam uživatelů."""
    return jsonify({
        'status': 'success',
        'count': len(users),
        'users': [user.to_dict() for user in users]
    })

@user_bp.route('/api/user/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    """API endpoint pro získání detailu uživatele."""
    user = next((u for u in users if u.id == user_id), None)
    if not user:
        return jsonify({'status': 'error', 'message': 'Uživatel nebyl nalezen'}), 404
    
    return jsonify({
        'status': 'success',
        'user': user.to_dict()
    })

@user_bp.route('/api/user', methods=['POST'])
def api_create_user():
    """API endpoint pro vytvoření uživatele."""
    try:
        data = request.json
        
        # Generování ID pro nového uživatele
        new_id = max(u.id for u in users) + 1 if users else 1
        
        # Vytvoření nového uživatele
        user = User(
            id=new_id,
            username=data.get('username', ''),
            email=data.get('email', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            created_at=datetime.now(),
            is_admin=data.get('is_admin', False),
            preferences=data.get('preferences', {})
        )
        
        # Přidání uživatele do simulované databáze
        users.append(user)
        
        return jsonify({
            'status': 'success',
            'message': 'Uživatel byl vytvořen',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400