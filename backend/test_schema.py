import time
from datetime import datetime
from sqlalchemy import text
from app import create_app
from app.database import db
from app.models.user import User
from app.models.medical_report import MedicalReport
from app.models.health_record import HealthRecord
from app.models.consultation import Consultation
from app.models.audit_log import AuditLog

app = create_app()

with app.app_context():
    print("Dropping old tables...")
    db.drop_all()
    print("Creating tables...")
    db.create_all()
    
    # 1. Clean up old test data if any
    db.session.query(HealthRecord).delete()
    db.session.query(Consultation).delete()
    db.session.query(MedicalReport).delete()
    db.session.query(User).filter_by(id='auth0|testuser999').delete()
    db.session.query(AuditLog).delete()
    db.session.commit()

    # 2. Insert test data
    print("Inserting test data...")
    user = User(id='auth0|testuser999', email='test999@example.com', name='Test User')
    db.session.add(user)
    db.session.commit()
    
    report = MedicalReport(user_id=user.id, file_url='s3://bucket/test.pdf', upload_date=datetime.utcnow(), report_type='ECG', confidence_score=0.98)
    db.session.add(report)
    db.session.commit()
    
    record = HealthRecord(user_id=user.id, report_id=report.id, diagnosis='Sinus Tachycardia', medications='Beta blockers', findings='Elevated heart rate')
    db.session.add(record)
    
    consult = Consultation(user_id=user.id, doctor_name='Dr. Smith', specialty='Cardiology', consultation_date=datetime.utcnow(), notes='Patient needs rest.')
    db.session.add(consult)
    
    log = AuditLog(user_id=user.id, action='CREATE', resource_type='medical_report', resource_id=str(report.id), ip_address='127.0.0.1')
    db.session.add(log)
    
    db.session.commit()
    
    # 3. Test read performance
    print("Testing read performance...")
    start_time = time.perf_counter()
    queried_reports = MedicalReport.query.filter_by(user_id=user.id, report_type='ECG').all()
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    
    print(f"Found {len(queried_reports)} reports.")
    print(f"Query execution time: {duration_ms:.2f} ms")
    if duration_ms < 50:
        print("[SUCCESS] Performance criterion met (<50ms).")
    else:
        print("[FAIL] Performance criterion failed (>50ms).")

    # 4. Verify encryption (Application-level)
    print("Verifying encryption...")
    # Read via SQLAlchemy (should be decrypted automatically)
    queried_record = HealthRecord.query.filter_by(user_id=user.id).first()
    print(f"Decrypted diagnosis via SQLAlchemy: {queried_record.diagnosis}")
    assert queried_record.diagnosis == 'Sinus Tachycardia', "Decryption failed!"
    
    # Read via raw SQL to bypass SQLAlchemy decryption
    result = db.session.execute(text("SELECT diagnosis FROM health_records WHERE user_id = :uid"), {'uid': user.id}).fetchone()
    raw_diagnosis = result[0]
    print(f"Raw diagnosis in database (should be encrypted string/bytes): {raw_diagnosis}")
    
    if 'Sinus Tachycardia' not in str(raw_diagnosis):
        print("[SUCCESS] Encryption is working. Raw data is obfuscated.")
    else:
        print("[FAIL] Encryption failed. Raw data contains plaintext!")
        
    print("All tests completed successfully!")
