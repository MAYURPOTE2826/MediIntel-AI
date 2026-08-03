import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.database import db

class AuditLog(db.Model):
    """
    Records security-sensitive and data-modifying events.
    Does NOT log routine reads to conserve storage.
    """
    __tablename__ = 'audit_logs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), nullable=True, index=True) # Can be null if failed login with unknown user
    action = db.Column(db.String(100), nullable=False) # e.g., 'LOGIN', 'FAILED_LOGIN', 'CREATE', 'UPDATE', 'DELETE', 'DOWNLOAD'
    resource_type = db.Column(db.String(100), nullable=True) # e.g., 'medical_report', 'health_record', 'user'
    resource_id = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True) # Optional JSON string or extra details
