from flask import Blueprint, jsonify, request, g
from app.database import db
from app.models.medical_report import MedicalReport
from app.models.health_record import HealthRecord
from app.models.consultation import Consultation
from app.auth.security import require_auth
from datetime import datetime

timeline_bp = Blueprint('timeline_bp', __name__)

@timeline_bp.route('/', methods=['GET'])
@require_auth
def get_timeline():
    """
    Get the patient's health timeline.
    Retrieves reports sorted by date and extracts key points.
    Filters: start_date, end_date, report_type
    """
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    report_type_filter = request.args.get('report_type')
    
    query = MedicalReport.query.filter_by(user_id=auth0_id)
    
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            query = query.filter(MedicalReport.upload_date >= start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            query = query.filter(MedicalReport.upload_date <= end_date)
        except ValueError:
            pass
            
    if report_type_filter:
        query = query.filter(MedicalReport.report_type == report_type_filter)
        
    reports = query.order_by(MedicalReport.upload_date.desc()).all()
    
    timeline_data = []
    
    for i, report in enumerate(reports):
        # Extract key findings
        key_findings = "No key findings available."
        if report.explanation_text:
            key_findings = report.explanation_text[:200] + ("..." if len(report.explanation_text) > 200 else "")
        elif report.extracted_data and isinstance(report.extracted_data, dict):
            key_findings = report.extracted_data.get('summary', str(report.extracted_data)[:200])
            
        # Determine status (mocked or inferred based on classification)
        status = "Reviewed"
        if report.requires_manual_review:
            status = "Pending Review"
            
        # Specialist seen
        specialist = "General Physician"
        if report.document_type:
            # simple mock logic for specialist based on document
            doc_type_lower = report.document_type.lower()
            if "ecg" in doc_type_lower or "cardio" in doc_type_lower:
                specialist = "Cardiologist"
            elif "x-ray" in doc_type_lower or "ct" in doc_type_lower or "mri" in doc_type_lower:
                specialist = "Radiologist"
            elif "blood" in doc_type_lower:
                specialist = "Pathologist"
                
        # Calculate trend based on some data or randomly assign for demo purposes if no clear data
        # In a real app we'd compare consecutive reports. Here we assume improving/worsening 
        # based on a simple confidence metric or just constant if we don't have enough data
        trend = "Stable"
        if len(reports) > 1 and i < len(reports) - 1:
            prev_report = reports[i+1]
            if report.composite_confidence_score and prev_report.composite_confidence_score:
                if report.composite_confidence_score > prev_report.composite_confidence_score:
                    trend = "Improving"
                elif report.composite_confidence_score < prev_report.composite_confidence_score:
                    trend = "Worsening"
                    
        timeline_data.append({
            "id": str(report.id),
            "date": report.upload_date.isoformat() if report.upload_date else None,
            "report_type": report.report_type,
            "document_type": report.document_type,
            "key_findings": key_findings,
            "specialist_seen": specialist,
            "status": status,
            "trend": trend
        })
        
    return jsonify({
        "timeline": timeline_data,
        "total_count": len(timeline_data)
    }), 200
