import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from app import create_app
from app.database import db
from app.models.medical_report import MedicalReport
from app.models.user import User
from app.explanation.services import generate_explanation

def run_test():
    app = create_app()
    with app.app_context():
        # Create tables if not exist (since we modified the schema)
        # Note: In a real app we'd use migrations, but for testing we can just call create_all. 
        # However, create_all might not alter existing tables. So let's drop and recreate for testing if needed.
        # But wait, MedIntel might already have tables. 
        # Let's just create a new DB for testing or hope SQLAlchemy alters. Actually SQLAlchemy create_all does not alter.
        # Let's do a raw SQL alter if column missing:
        
        from sqlalchemy import text
        try:
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN explanation_text TEXT;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN explanation_citations JSON;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN explanation_manual_qa_required BOOLEAN DEFAULT FALSE;"))
            # Add missing classification columns as well
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN document_type VARCHAR(100);"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN classification_confidence FLOAT;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN classification_results JSON;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN classification_model_version VARCHAR(50);"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN classified_at TIMESTAMP;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN explanation_confidence FLOAT;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN specialist_recommendation_confidence FLOAT;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN key_findings_confidence FLOAT;"))
            db.session.execute(text("ALTER TABLE medical_reports ADD COLUMN composite_confidence_score FLOAT;"))
            db.session.commit()
            print("Added explanation columns to DB.")
        except Exception as e:
            db.session.rollback()
            print("Columns might already exist or error:", e)

        # Setup mock user and report
        user = User.query.first()
        if not user:
            user = User(id="test_user_auth0", email="test@example.com", name="Test User")
            db.session.add(user)
            db.session.commit()
            
        report_id = uuid.uuid4()
        mock_ocr_text = "Patient John Doe. Age 45. Hemoglobin 11.2 g/dL. WBC 12,000. Assessment: High WBC and low hemoglobin. Needs review."
        report = MedicalReport(
            id=report_id,
            user_id=user.id,
            file_url="s3://mock-bucket/mock.pdf",
            upload_date=datetime.utcnow(),
            report_type="CBC Blood Test",
            raw_ocr_output=mock_ocr_text
        )
        db.session.add(report)
        db.session.commit()
        
        print(f"Created mock report: {report_id}")
        
        print("Running explanation generation...")
        try:
            result = generate_explanation(report_id)
            print("\n--- TEST SUCCESS ---")
            print(json.dumps(result, indent=2))
            
            # Verify disclaimer
            if "Consult a qualified healthcare professional" in result["explanation"]:
                print("[PASS] Disclaimer found.")
            else:
                print("[FAIL] Disclaimer missing.")
                
            # Verify DB changes
            updated_report = MedicalReport.query.get(report_id)
            if updated_report.explanation_text == result["explanation"]:
                print("[PASS] Explanation saved to DB.")
            else:
                print("[FAIL] Explanation not saved to DB.")
                
        except Exception as e:
            print(f"\n--- TEST FAILED ---")
            print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
