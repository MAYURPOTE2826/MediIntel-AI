import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.database import db
from app.models.mixins import TimestampMixin, SoftDeleteMixin

class NotificationPreference(TimestampMixin, db.Model):
    __tablename__ = 'notification_preferences'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Opt-in settings
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=True)
    
    # Notification frequency
    frequency = db.Column(db.String(50), default='immediate') # e.g. immediate, daily_digest, none
    quiet_hours_start = db.Column(db.Time, nullable=True)
    quiet_hours_end = db.Column(db.Time, nullable=True)
    
    # Tokens
    fcm_token = db.Column(db.String(512), nullable=True)

    user = db.relationship('User', backref=db.backref('notification_preference', uselist=False, lazy=True))

    def to_dict(self):
        return {
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "push_enabled": self.push_enabled,
            "frequency": self.frequency,
            "quiet_hours_start": self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            "quiet_hours_end": self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            "fcm_token": self.fcm_token
        }

class Notification(TimestampMixin, db.Model):
    __tablename__ = 'notifications'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Type of notification: 'appointment', 'follow_up', 'medication', 'lab_report', 'health_tip'
    type = db.Column(db.String(50), nullable=False, index=True)
    
    # Content must NOT contain sensitive PII
    safe_title = db.Column(db.String(255), nullable=False)
    safe_body = db.Column(db.Text, nullable=False)
    
    # Channels used (e.g. 'sms,push')
    channels_sent = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def to_dict(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "safe_title": self.safe_title,
            "safe_body": self.safe_body,
            "channels_sent": self.channels_sent,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Reminder(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'reminders'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Type: 'medication', 'follow_up'
    reminder_type = db.Column(db.String(50), nullable=False)
    
    safe_title = db.Column(db.String(255), nullable=False)
    
    # For medication, frequency might be 'daily', 'weekly'. For follow_up, it might be 'once'.
    frequency_rule = db.Column(db.String(100), default='once')
    
    # Next time to trigger
    next_due_date = db.Column(db.DateTime, nullable=False, index=True)
    
    # active, paused, completed
    status = db.Column(db.String(50), default='active')
    
    user = db.relationship('User', backref=db.backref('reminders', lazy=True))

    def to_dict(self):
        return {
            "id": str(self.id),
            "reminder_type": self.reminder_type,
            "safe_title": self.safe_title,
            "frequency_rule": self.frequency_rule,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
