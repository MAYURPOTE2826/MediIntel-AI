import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from app.database import db

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Configure Database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure Upload limits
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50MB
    
    # Initialize plugins
    db.init_app(app)
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.uploads.routes import uploads_bp
    from app.ocr.routes import ocr_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(ocr_bp, url_prefix='/api/ocr')
    
    # Basic health check route
    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "message": "MediIntel Auth API is running!"}), 200

    return app
