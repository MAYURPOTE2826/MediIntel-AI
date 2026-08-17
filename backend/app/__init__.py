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
    
    # Initialize Scheduler
    from app.scheduler import init_scheduler
    if not os.environ.get('TESTING'):
        init_scheduler(app)
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.uploads.routes import uploads_bp
    from app.ocr.routes import ocr_bp
    from app.explanation.routes import explanation_bp
    from app.recommendation.routes import recommendation_bp
    from app.questions.routes import questions_bp
    from app.finder.routes import finder_bp
    from app.appointments.routes import appointments_bp
    from app.timeline.routes import timeline_bp
    from app.family.routes import family_bp
    from app.trends.routes import trends_bp
    from app.chatbot.routes import chatbot_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(ocr_bp, url_prefix='/api/ocr')
    app.register_blueprint(explanation_bp, url_prefix='/api/explanation')
    app.register_blueprint(recommendation_bp, url_prefix='/api/recommendation')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(finder_bp, url_prefix='/api/finder')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(timeline_bp, url_prefix='/api/timeline')
    app.register_blueprint(family_bp, url_prefix='/api/family')
    app.register_blueprint(trends_bp, url_prefix='/api/trends')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    
    # Basic health check route
    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "message": "MediIntel Auth API is running!"}), 200

    @app.route('/')
    def index():
        return jsonify({"message": "Welcome to the MediIntel API! Try /health to check status."}), 200

    return app
