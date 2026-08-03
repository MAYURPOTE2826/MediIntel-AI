from flask import Blueprint

ocr_bp = Blueprint('ocr_bp', __name__)

from app.ocr import routes
