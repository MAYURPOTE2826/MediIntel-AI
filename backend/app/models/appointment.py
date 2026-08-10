import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.database import db
from app.models.mixins import TimestampMixin

class Appointment(TimestampMixin, db.Model):
    __tablename__ = 'appointments'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, index=True)
    doctor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('doctor_profiles.id'), nullable=True)
    doctor_name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(255), nullable=True)
    appointment_date = db.Column(db.DateTime, nullable=False, index=True)
    
    # 'pending', 'booked', 'cancelled'
    status = db.Column(db.String(50), default='pending')
    
    booking_reference = db.Column(db.String(255), nullable=True)
    sms_reminder_sent = db.Column(db.Boolean, default=False, index=True)

    user = db.relationship('User', backref=db.backref('appointments', lazy=True))
    doctor = db.relationship('DoctorProfile', backref=db.backref('appointments', lazy=True))

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "doctor_id": str(self.doctor_id) if self.doctor_id else None,
            "doctor_name": self.doctor_name,
            "specialty": self.specialty,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "status": self.status,
            "booking_reference": self.booking_reference,
            "sms_reminder_sent": self.sms_reminder_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
