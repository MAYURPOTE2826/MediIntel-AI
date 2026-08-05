from flask import Blueprint, request, jsonify
from app.recommendation.services import recommend_specialists
import logging

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/', methods=['POST'])
def get_recommendations():
    """
    Expects JSON:
    {
        "report_type": "Blood Report",
        "confidence": 0.98
    }
    """
    data = request.get_json()
    if not data or 'report_type' not in data:
        return jsonify({"error": "Missing 'report_type' in request body"}), 400
        
    report_type = data['report_type']
    confidence = data.get('confidence', 1.0)
    
    try:
        recommendations = recommend_specialists(report_type, confidence)
        return jsonify(recommendations), 200
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        return jsonify({"error": str(e)}), 500
