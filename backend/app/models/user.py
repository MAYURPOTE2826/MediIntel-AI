from datetime import datetime
from app.database import db
from app.models.mixins import TimestampMixin, SoftDeleteMixin

class User(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(255), primary_key=True) # Auth0 'sub' (e.g., auth0|123456789)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True) # For future local auth
    name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
