import uuid
import datetime
from app import create_app
from app.database import db
from app.models.user import User
from app.models.medical_report import MedicalReport

app = create_app()

with app.app_context():
    # 1. Ensure user exists
    test_user_id = "auth0|testuser123"
    user = User.query.get(test_user_id)
    if not user:
        user = User(id=test_user_id, email="test@example.com", name="Test User")
        db.session.add(user)
        db.session.commit()
        print("Created test user.")

    # 2. Generate UUIDs for reports
    report_1_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    report_2_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    # Clear old reports if they exist
    MedicalReport.query.filter(MedicalReport.id.in_([report_1_id, report_2_id])).delete(synchronize_session=False)
    db.session.commit()

    # 3. Add baseline report (older)
    report1 = MedicalReport(
        id=report_1_id,
        user_id=test_user_id,
        file_url="http://example.com/report1.pdf",
        upload_date=datetime.datetime(2026, 3, 20),
        report_type="Blood Test",
        document_type="Comprehensive Metabolic Panel",
        raw_ocr_output="Patient Test User. Date: March 20, 2026. Fasting Glucose: 125 mg/dL (High). Total Cholesterol: 240 mg/dL (High). LDL Cholesterol: 160 mg/dL (High). HDL Cholesterol: 40 mg/dL. Triglycerides: 180 mg/dL."
    )
    
    # 4. Add follow-up report (newer)
    report2 = MedicalReport(
        id=report_2_id,
        user_id=test_user_id,
        file_url="http://example.com/report2.pdf",
        upload_date=datetime.datetime(2026, 8, 10),
        report_type="Blood Test",
        document_type="Comprehensive Metabolic Panel",
        raw_ocr_output="Patient Test User. Date: August 10, 2026. Fasting Glucose: 102 mg/dL. Total Cholesterol: 195 mg/dL. LDL Cholesterol: 120 mg/dL. HDL Cholesterol: 45 mg/dL. Triglycerides: 150 mg/dL."
    )

    db.session.add(report1)
    db.session.add(report2)
    db.session.commit()
    
    print(f"Report 1 (Baseline) UUID: {report_1_id}")
    print(f"Report 2 (Follow-up) UUID: {report_2_id}")
    print("Database successfully seeded with test reports.")
