from flask import request, jsonify, g
from app.ocr import ocr_bp
from app.auth.security import require_auth
from app.ocr.services import process_ocr_task
from app.models.medical_report import MedicalReport
from app.database import db

@ocr_bp.route('/process', methods=['POST'])
@require_auth
def process_ocr():
    """
    Endpoint to trigger OCR processing for a given medical report.
    Expects JSON: {"report_id": "uuid"}
    """
    data = request.get_json()
    if not data or 'report_id' not in data:
        return jsonify({"error": "Missing report_id"}), 400
        
    report_id = data['report_id']
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    # Check if report exists and belongs to user
    report = MedicalReport.query.filter_by(id=report_id, user_id=auth0_id).first()
    if not report:
        return jsonify({"error": "Report not found or unauthorized"}), 404
        
    try:
        # In the future, this can easily be replaced by:
        # celery_app.send_task('process_ocr_task', args=[report.id])
        # return jsonify({"message": "OCR task queued"}), 202
        
        # Currently running synchronously
        result = process_ocr_task(report.id)
        return jsonify({
            "message": "OCR processing completed",
            "extracted_data": result.get("extracted_data"),
            "requires_manual_review": result.get("requires_manual_review")
        }), 200
    except Exception as e:
        return jsonify({"error": f"OCR processing failed: {str(e)}"}), 500
