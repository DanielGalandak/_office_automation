# controllers/document_controller.py - Kontroler pro dokumenty

from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for, send_file
from models.document_model import Document
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import mimetypes
import uuid

document_bp = Blueprint('document', __name__)

# Simulovaná databáze dokumentů (v reálné aplikaci bychom použili kontext podobně jako u úloh)
documents = []

@document_bp.route('/', methods=['GET'])
def list_documents():
    """Zobrazí seznam všech dokumentů."""
    return render_template('documents.html', documents=documents)

@document_bp.route('/upload', methods=['GET', 'POST'])
def upload_document():
    """Formulář pro nahrání nového dokumentu a zpracování odeslaných dat."""
    if request.method == 'POST':
        # Kontrola, zda byl soubor nahrán
        if 'file' not in request.files:
            return render_template('error.html', message='Nebyl vybrán žádný soubor'), 400
        
        file = request.files['file']
        
        # Kontrola, zda byl vybrán soubor
        if file.filename == '':
            return render_template('error.html', message='Nebyl vybrán žádný soubor'), 400
        
        # Kontrola, zda je přípona souboru povolena
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
            # Zabezpečení názvu souboru
            filename = secure_filename(file.filename)
            
            # Generování jedinečného názvu souboru
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Cesta pro uložení souboru
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Uložení souboru
            file.save(file_path)
            
            # Získání velikosti souboru
            file_size = os.path.getsize(file_path)
            
            # Získání typu souboru
            file_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # Vytvoření nového dokumentu
            new_id = max(d.id for d in documents) + 1 if documents else 1
            document = Document(
                id=new_id,
                name=filename,
                file_path=file_path,
                file_type=file_type,
                size=file_size,
                uploaded_by=1,  # Předpokládáme přihlášeného uživatele (v reálné aplikaci by se načetl z session)
                created_at=datetime.now(),
                metadata={
                    'original_filename': filename,
                    'content_type': file_type
                },
                tags=request.form.get('tags', '').split(',') if request.form.get('tags') else []
            )
            
            # Přidání dokumentu do simulované databáze
            documents.append(document)
            
            # Přesměrování zpět na seznam dokumentů
            return redirect(url_for('document.list_documents'))
        
        # Pokud přípona souboru není povolena
        return render_template('error.html', message='Tento typ souboru není povolen'), 400
    
    # Zobrazení formuláře pro nahrání dokumentu
    return render_template('upload_document.html')

@document_bp.route('/<int:document_id>', methods=['GET'])
def view_document(document_id):
    """Zobrazí detail dokumentu."""
    document = next((d for d in documents if d.id == document_id), None)
    if not document:
        return render_template('error.html', message='Dokument nebyl nalezen'), 404
    
    return render_template('document_detail.html', document=document)

@document_bp.route('/<int:document_id>/download', methods=['GET'])
def download_document(document_id):
    """Stáhne dokument."""
    document = next((d for d in documents if d.id == document_id), None)
    if not document:
        return render_template('error.html', message='Dokument nebyl nalezen'), 404
    
    # Kontrola, zda soubor existuje
    if not os.path.exists(document.file_path):
        return render_template('error.html', message='Soubor neexistuje nebo byl smazán'), 404
    
    # Odeslání souboru klientovi
    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.name,
        mimetype=document.file_type
    )

@document_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Smaže dokument."""
    document = next((d for d in documents if d.id == document_id), None)
    if not document:
        return jsonify({'status': 'error', 'message': 'Dokument nebyl nalezen'}), 404
    
    # Smazání souboru z disku
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Odebrání dokumentu ze simulované databáze
    documents.remove(document)
    
    return jsonify({'status': 'success', 'message': 'Dokument byl smazán'})

@document_bp.route('/api/list', methods=['GET'])
def api_list_documents():
    """API endpoint pro seznam dokumentů."""
    return jsonify({
        'status': 'success',
        'count': len(documents),
        'documents': [document.to_dict() for document in documents]
    })

@document_bp.route('/api/document/<int:document_id>', methods=['GET'])
def api_get_document(document_id):
    """API endpoint pro získání detailu dokumentu."""
    document = next((d for d in documents if d.id == document_id), None)
    if not document:
        return jsonify({'status': 'error', 'message': 'Dokument nebyl nalezen'}), 404
    
    return jsonify({
        'status': 'success',
        'document': document.to_dict()
    })