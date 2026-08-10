from flask import Blueprint

appointments_bp = Blueprint('appointments', __name__)

from app.appointments import routes
