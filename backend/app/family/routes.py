import io
from flask import Blueprint, jsonify, request, g, send_file
from app.database import db
from app.models.family import FamilyMember
from app.models.user import User
from app.models.medical_report import MedicalReport
from app.models.audit_log import AuditLog
from app.auth.security import require_auth
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import logging

family_bp = Blueprint('family_bp', __name__)
logger = logging.getLogger(__name__)

@family_bp.route('/invite', methods=['POST'])
@require_auth
def invite_member():
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    data = request.get_json()
    
    email = data.get('email')
    share_mode = data.get('share_mode', 'FULL')
    is_emergency_contact = data.get('is_emergency_contact', False)
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    # Check if already invited
    existing = FamilyMember.query.filter_by(inviter_id=auth0_id, invitee_email=email).first()
    if existing:
        return jsonify({"error": "Invitation already sent to this email"}), 400
        
    new_member = FamilyMember(
        inviter_id=auth0_id,
        invitee_email=email,
        share_mode=share_mode,
        is_emergency_contact=is_emergency_contact,
        status='pending'
    )
    
    db.session.add(new_member)
    db.session.commit()
    
    # Mock sending email
    print(f"MOCK EMAIL SENT: To {email}. User {auth0_id} invited you to share health records.")
    
    return jsonify(new_member.to_dict()), 201

@family_bp.route('/accept', methods=['POST'])
@require_auth
def accept_invite():
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    # We assume the user's email is in the payload or we query their User record
    user = User.query.get(auth0_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    invitation = FamilyMember.query.filter_by(invitee_email=user.email, status='pending').first()
    if not invitation:
        return jsonify({"error": "No pending invitation found"}), 404
        
    invitation.status = 'accepted'
    invitation.invitee_id = auth0_id
    db.session.commit()
    
    return jsonify({"message": "Invitation accepted", "family_member": invitation.to_dict()}), 200

@family_bp.route('/dashboard', methods=['GET'])
@require_auth
def get_dashboard():
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    # Get all users who have shared with this user (where user is the invitee and status is accepted)
    # OR where user is the inviter and the invitee accepted.
    # For this feature, "View family health overview": usually implies two-way or one-way sharing.
    # We will fetch records where the current user is the inviter and the invitee accepted.
    shared_members = FamilyMember.query.filter_by(inviter_id=auth0_id, status='accepted').all()
    
    family_data = []
    
    for member in shared_members:
        member_user = User.query.get(member.invitee_id)
        if not member_user:
            continue
            
        # Get reports
        reports = MedicalReport.query.filter_by(user_id=member_user.id).order_by(MedicalReport.upload_date.desc()).limit(5).all()
        
        report_data = []
        for r in reports:
            # Check share_mode
            if member.share_mode == 'ANONYMOUS':
                key_findings = "Private finding (Anonymous)"
                # Generalized trend
                if r.composite_confidence_score and r.composite_confidence_score > 0.8:
                    key_findings = "Stable/Improving indicator"
            else:
                key_findings = r.explanation_text[:200] if r.explanation_text else "No details"
                
            report_data.append({
                "date": r.upload_date.isoformat() if r.upload_date else None,
                "type": r.report_type,
                "findings": key_findings
            })
            
        name = "Family Member" if member.share_mode == 'ANONYMOUS' else (member_user.name or member_user.email)
        
        family_data.append({
            "member_id": member_user.id,
            "name": name,
            "share_mode": member.share_mode,
            "recent_reports": report_data
        })
        
    return jsonify({"family": family_data}), 200

@family_bp.route('/emergency', methods=['POST'])
@require_auth
def trigger_emergency_access():
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    data = request.get_json()
    target_user_id = data.get('target_user_id')
    
    if not target_user_id:
        return jsonify({"error": "Target user ID required"}), 400
        
    # Check if this user is designated as an emergency contact for the target user
    # Meaning: target_user_id invited auth0_id as emergency contact
    relation = FamilyMember.query.filter_by(
        inviter_id=target_user_id, 
        invitee_id=auth0_id, 
        is_emergency_contact=True, 
        status='accepted'
    ).first()
    
    if not relation:
        return jsonify({"error": "You are not an authorized emergency contact for this user"}), 403
        
    relation.emergency_access_active = True
    
    # Audit log
    audit = AuditLog(
        user_id=auth0_id,
        action='EMERGENCY_ACCESS',
        resource_type='medical_report',
        resource_id=target_user_id,
        details='Emergency access activated by trusted contact'
    )
    
    db.session.add(audit)
    db.session.commit()
    
    return jsonify({"message": "Emergency access granted. Action logged."}), 200

@family_bp.route('/export', methods=['GET'])
@require_auth
def export_pdf():
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    # Generate simple PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)
    
    p.drawString(100, 750, "Family Medical History Export")
    p.drawString(100, 730, "============================")
    
    y = 700
    
    shared_members = FamilyMember.query.filter_by(inviter_id=auth0_id, status='accepted').all()
    for member in shared_members:
        member_user = User.query.get(member.invitee_id)
        if member_user:
            name = "Anonymous" if member.share_mode == 'ANONYMOUS' else (member_user.name or member_user.email)
            p.drawString(100, y, f"Member: {name} (Mode: {member.share_mode})")
            y -= 20
            
            reports = MedicalReport.query.filter_by(user_id=member_user.id).limit(3).all()
            for r in reports:
                date_str = r.upload_date.strftime("%Y-%m-%d") if r.upload_date else "Unknown Date"
                p.drawString(120, y, f"- {date_str} : {r.report_type}")
                y -= 20
                if y < 100:
                    p.showPage()
                    y = 750
            
            y -= 10
            
    p.save()
    buffer.seek(0)
    
    return send_file(
        buffer, 
        as_attachment=True, 
        download_name='family_history.pdf', 
        mimetype='application/pdf'
    )
