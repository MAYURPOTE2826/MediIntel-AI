from flask import request, jsonify, g
from app.auth.security import require_auth
from app.finder import finder_bp
from app.finder.services import search_doctors
import logging

@finder_bp.route('/search', methods=['POST'])
@require_auth
def search():
    """
    Endpoint to search for doctors/hospitals based on location and specialty.
    Expects JSON: {"location": "Mumbai", "specialty": "Cardiologists"}
    """
    data = request.get_json()
    if not data or 'location' not in data or 'specialty' not in data:
        return jsonify({"error": "Missing 'location' or 'specialty' in request body"}), 400
        
    location = data['location']
    specialty = data['specialty']
    
    try:
        results = search_doctors(location, specialty)
        return jsonify({
            "message": "Search completed successfully",
            "data": results
        }), 200
    except Exception as e:
        logging.error(f"Error searching doctors: {e}")
        return jsonify({"error": str(e)}), 500
