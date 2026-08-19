from flask import Blueprint, request, jsonify, g
from app.auth.security import require_auth
from app.explanation.services import generate_explanation
from app.models.medical_report import MedicalReport

explanation_bp = Blueprint('explanation_bp', __name__)

@explanation_bp.route('/explain', methods=['POST'])
@require_auth
def explain_report():
    """
    Endpoint to generate an explanation for a processed medical report.
    Expects JSON: {"report_id": "uuid"}
    """
    data = request.get_json()
    if not data or 'report_id' not in data:
        return jsonify({"error": "Missing report_id"}), 400
        
    report_id = data['report_id']
    target_language = data.get('lang', 'en')
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    # Verify ownership
    report = MedicalReport.query.filter_by(id=report_id, user_id=auth0_id).first()
    if not report:
        return jsonify({"error": "Report not found or unauthorized"}), 404
        
    try:
        result = generate_explanation(report_id, target_language)
        return jsonify({
            "message": "Explanation generated successfully",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
