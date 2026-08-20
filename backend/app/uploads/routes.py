import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from app.database import db
from app.models.medical_report import MedicalReport
from app.models.audit_log import AuditLog
from app.auth.security import require_auth
from app.uploads.services import validate_file_type, scan_with_virustotal, upload_to_s3, FileValidationError
from app.monitoring import upload_volume_counter

uploads_bp = Blueprint('uploads_bp', __name__)

# Temporary directory for chunked uploads
TEMP_UPLOAD_DIR = os.path.join(os.getcwd(), 'tmp_uploads')
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

@uploads_bp.route('/chunked', methods=['POST'])
@require_auth
def upload_chunk():
    """
    Endpoint for resumable chunked uploads.
    Headers required: 
    - X-Upload-ID: Unique ID for the upload session (client generated UUID)
    - X-Filename: Original filename
    - Content-Range: bytes START-END/TOTAL
    """
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    upload_id = request.headers.get('X-Upload-ID')
    filename = request.headers.get('X-Filename')
    content_range = request.headers.get('Content-Range')
    
    if not upload_id or not filename or not content_range:
        return jsonify({"error": "Missing required upload headers"}), 400
        
    filename = secure_filename(filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
        
    # Parse Content-Range (e.g. "bytes 0-1023/1048576")
    try:
        range_info, total_size = content_range.replace('bytes ', '').split('/')
        start_byte, end_byte = map(int, range_info.split('-'))
        total_size = int(total_size)
    except ValueError:
        return jsonify({"error": "Invalid Content-Range header format"}), 400

    # Write chunk to temp file
    temp_filepath = os.path.join(TEMP_UPLOAD_DIR, f"{upload_id}_{filename}")
    
    try:
        with open(temp_filepath, 'ab') as f:
            f.seek(start_byte)
            f.write(request.data)
    except Exception as e:
        return jsonify({"error": f"Failed to write chunk: {str(e)}"}), 500

    # If this is the final chunk, process the file
    if end_byte + 1 >= total_size:
        return process_completed_upload(temp_filepath, filename, auth0_id)
        
    return jsonify({"status": "chunk received"}), 200

def process_completed_upload(filepath, original_filename, user_id):
    """Processes the fully assembled file."""
    try:
        # 1. Validate magic bytes
        mime_type = validate_file_type(filepath)
        
        # Determine report_type based on mime (simplified logic)
        report_type = 'PDF Document' if mime_type == 'application/pdf' else 'Image Document'
        
        # Record upload metric
        file_size = os.path.getsize(filepath)
        upload_volume_counter.labels(file_type=mime_type).inc(file_size)
        
        # 2. Scan with VirusTotal
        scan_status = scan_with_virustotal(filepath)
        
        if scan_status == 'malicious':
            os.remove(filepath)
            # Log the security event
            log = AuditLog(user_id=user_id, action='MALWARE_BLOCKED', resource_type='file_upload', details=original_filename)
            db.session.add(log)
            db.session.commit()
            return jsonify({"error": "Malware detected. File rejected."}), 403
            
        # 3. Upload to S3
        is_quarantined = (scan_status == 'unknown')
        object_key, s3_url = upload_to_s3(filepath, original_filename, is_quarantined=is_quarantined)
        
        # 4. Save to database
        # Even if quarantined, we create the record, but maybe mark it as pending
        # For now, we store it. In a real app, a background job would check VT later and move the S3 object.
        report = MedicalReport(
            user_id=user_id,
            file_url=s3_url,
            upload_date=datetime.utcnow(),
            report_type=report_type,
            confidence_score=0.0 # Pending AI analysis
        )
        db.session.add(report)
        
        # Audit Log
        action = 'UPLOAD_QUARANTINED' if is_quarantined else 'UPLOAD_CLEAN'
        log = AuditLog(user_id=user_id, action=action, resource_type='medical_report', resource_id=str(report.id))
        db.session.add(log)
        
        db.session.commit()
        
        # Clean up local temp file
        os.remove(filepath)
        
        response_data = {
            "message": "File uploaded successfully" if not is_quarantined else "File uploaded and quarantined pending virus scan",
            "file_id": report.id,
            "status": action
        }
        return jsonify(response_data), 201
        
    except FileValidationError as e:
        os.remove(filepath)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
