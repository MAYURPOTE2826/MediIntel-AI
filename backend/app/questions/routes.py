from flask import request, jsonify, g
from app.auth.security import require_auth
from app.questions import questions_bp
from app.questions.services import generate_questions
from app.models.medical_report import MedicalReport
import logging

@questions_bp.route('/generate', methods=['POST'])
@require_auth
def generate_questions_route():
    """
    Endpoint to generate questions a patient can ask their doctor based on a medical report.
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
        questions = generate_questions(report_id, target_language)
        return jsonify({
            "message": "Questions generated successfully",
            "data": questions
        }), 200
    except Exception as e:
        logging.error(f"Error generating questions: {e}")
        return jsonify({"error": str(e)}), 500
