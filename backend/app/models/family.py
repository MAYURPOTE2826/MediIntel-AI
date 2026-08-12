import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.database import db
from app.models.mixins import TimestampMixin

class FamilyMember(TimestampMixin, db.Model):
    __tablename__ = 'family_members'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inviter_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, index=True)
    invitee_email = db.Column(db.String(255), nullable=False)
    invitee_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=True, index=True)
    
    status = db.Column(db.String(50), default='pending') # 'pending', 'accepted'
    share_mode = db.Column(db.String(50), default='FULL') # 'FULL', 'ANONYMOUS'
    is_emergency_contact = db.Column(db.Boolean, default=False)
    emergency_access_active = db.Column(db.Boolean, default=False)

    inviter = db.relationship('User', foreign_keys=[inviter_id], backref=db.backref('family_invitations_sent', lazy=True))
    invitee = db.relationship('User', foreign_keys=[invitee_id], backref=db.backref('family_invitations_received', lazy=True))

    def to_dict(self):
        return {
            "id": str(self.id),
            "inviter_id": self.inviter_id,
            "invitee_email": self.invitee_email,
            "invitee_id": self.invitee_id,
            "status": self.status,
            "share_mode": self.share_mode,
            "is_emergency_contact": self.is_emergency_contact,
            "emergency_access_active": self.emergency_access_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
