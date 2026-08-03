import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from app.database import db
from app.models.mixins import TimestampMixin, SoftDeleteMixin
from app.models.encryption import ENCRYPTION_KEY

class HealthRecord(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'health_records'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, index=True)
    report_id = db.Column(UUID(as_uuid=True), db.ForeignKey('medical_reports.id'), nullable=True)
    
    # Encrypted fields for highly sensitive data
    diagnosis = db.Column(EncryptedType(db.Text, ENCRYPTION_KEY, FernetEngine), nullable=True)
    medications = db.Column(EncryptedType(db.Text, ENCRYPTION_KEY, FernetEngine), nullable=True)
    findings = db.Column(EncryptedType(db.Text, ENCRYPTION_KEY, FernetEngine), nullable=True)

    user = db.relationship('User', backref=db.backref('health_records', lazy=True))
    report = db.relationship('MedicalReport', backref=db.backref('health_records', lazy=True))
