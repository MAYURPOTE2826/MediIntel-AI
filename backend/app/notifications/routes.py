import logging
from flask import request, jsonify
from app.database import db
from app.auth.middleware import require_auth
from app.models.notification import NotificationPreference, Notification, Reminder
from app.notifications import bp

logger = logging.getLogger(__name__)

@bp.route('/api/notifications/preferences', methods=['GET'])
@require_auth
def get_preferences(user_id):
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if not prefs:
        # Return defaults if not set
        return jsonify({
            "email_enabled": True,
            "sms_enabled": True,
            "push_enabled": True,
            "frequency": "immediate"
        }), 200
        
    return jsonify(prefs.to_dict()), 200

@bp.route('/api/notifications/preferences', methods=['PUT'])
@require_auth
def update_preferences(user_id):
    data = request.json
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    
    if not prefs:
        prefs = NotificationPreference(user_id=user_id)
        db.session.add(prefs)
        
    if 'email_enabled' in data:
        prefs.email_enabled = data['email_enabled']
    if 'sms_enabled' in data:
        prefs.sms_enabled = data['sms_enabled']
    if 'push_enabled' in data:
        prefs.push_enabled = data['push_enabled']
    if 'frequency' in data:
        prefs.frequency = data['frequency']
        
    db.session.commit()
    return jsonify({"message": "Preferences updated successfully", "preferences": prefs.to_dict()}), 200

@bp.route('/api/notifications/fcm-token', methods=['POST'])
@require_auth
def register_fcm_token(user_id):
    data = request.json
    fcm_token = data.get('fcm_token')
    
    if not fcm_token:
        return jsonify({"error": "fcm_token is required"}), 400
        
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = NotificationPreference(user_id=user_id)
        db.session.add(prefs)
        
    prefs.fcm_token = fcm_token
    db.session.commit()
    return jsonify({"message": "FCM token registered successfully"}), 200

@bp.route('/api/notifications', methods=['GET'])
@require_auth
def get_notifications(user_id):
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notifications]), 200

@bp.route('/api/notifications/<notification_id>/read', methods=['PUT'])
@require_auth
def mark_read(user_id, notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return jsonify({"error": "Notification not found"}), 404
        
    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Notification marked as read"}), 200
