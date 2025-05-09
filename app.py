from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

# Načtení proměnných prostředí z .env souboru
load_dotenv()

# Import kontrolerů
from controllers.task_controller import task_bp
from controllers.user_controller import user_bp
from controllers.document_controller import document_bp

# Vytvoření Flask aplikace
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Registrace blueprintů
app.register_blueprint(task_bp, url_prefix='/tasks')
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(document_bp, url_prefix='/documents')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "version": "1.0.0"}), 200

if __name__ == '__main__':
    # Vytvoření potřebných složek, pokud neexistují
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)