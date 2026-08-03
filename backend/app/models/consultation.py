import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from app.database import db
from app.models.mixins import TimestampMixin, SoftDeleteMixin
from app.models.encryption import ENCRYPTION_KEY

class Consultation(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'consultations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, index=True)
    doctor_name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(255), nullable=True)
    consultation_date = db.Column(db.DateTime, nullable=False)
    
    # Encrypted notes
    notes = db.Column(EncryptedType(db.Text, ENCRYPTION_KEY, FernetEngine), nullable=True)

    user = db.relationship('User', backref=db.backref('consultations', lazy=True))
