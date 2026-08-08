import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.database import db
from app.models.mixins import TimestampMixin, SoftDeleteMixin

class MedicalReport(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'medical_reports'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False, index=True)
    file_url = db.Column(db.String(512), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False)
    report_type = db.Column(db.String(100), nullable=False, index=True)
    confidence_score = db.Column(db.Float, nullable=True)
    
    # OCR Data
    extracted_data = db.Column(db.JSON, nullable=True)
    requires_manual_review = db.Column(db.Boolean, default=False)
    raw_ocr_output = db.Column(db.Text, nullable=True)
    
    # Classification Data
    document_type = db.Column(db.String(100), nullable=True, index=True)
    classification_confidence = db.Column(db.Float, nullable=True)
    classification_results = db.Column(db.JSON, nullable=True)
    classification_model_version = db.Column(db.String(50), nullable=True)
    classified_at = db.Column(db.DateTime, nullable=True)

    # Explanation Data
    explanation_text = db.Column(db.Text, nullable=True)
    explanation_citations = db.Column(db.JSON, nullable=True)
    explanation_manual_qa_required = db.Column(db.Boolean, default=False)
    
    # Confidence Metrics
    explanation_confidence = db.Column(db.Float, nullable=True)
    specialist_recommendation_confidence = db.Column(db.Float, nullable=True)
    key_findings_confidence = db.Column(db.Float, nullable=True)
    composite_confidence_score = db.Column(db.Float, nullable=True)
    
    # Generated Questions
    generated_questions = db.Column(db.JSON, nullable=True)

    user = db.relationship('User', backref=db.backref('medical_reports', lazy=True))
