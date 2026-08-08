import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.database import db
from app.models.mixins import TimestampMixin

class DoctorProfile(TimestampMixin, db.Model):
    __tablename__ = 'doctor_profiles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(100), nullable=False, index=True)
    license_number = db.Column(db.String(100), nullable=False, unique=True)
    medical_board_verified = db.Column(db.Boolean, default=False)
    clinic_address = db.Column(db.String(512), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(100), nullable=True, index=True)
    rating = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "specialty": self.specialty,
            "license_number": self.license_number,
            "medical_board_verified": self.medical_board_verified,
            "clinic_address": self.clinic_address,
            "phone": self.phone,
            "city": self.city,
            "rating": self.rating
        }
