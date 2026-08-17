from flask import Blueprint

chatbot_bp = Blueprint('chatbot_bp', __name__)

from app.chatbot import routes
