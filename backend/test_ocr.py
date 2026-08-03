
import os
import uuid
import json
from unittest.mock import patch
from app import create_app
from app.database import db
from app.models.user import User
from app.models.medical_report import MedicalReport

# Create an app configured for testing
app = create_app()
app.config['TESTING'] = True

def test_ocr_processing():
    with app.app_context():
        # Clean up database state and recreate schema
        db.drop_all()
        db.create_all()
        
        # Setup: Create a test user and a mock report
        user = User.query.filter_by(id='auth0|testuser999').first()
        if not user:
            user = User(id='auth0|testuser999', email='testupload@example.com', name='Test Uploader')
            db.session.add(user)
            db.session.commit()
            
        from datetime import datetime
        report = MedicalReport(
            user_id=user.id,
            file_url='s3://mediintel-clean-reports/mock_report.jpg',
            report_type='Image Document',
            upload_date=datetime.utcnow()
        )
        db.session.add(report)
        db.session.commit()
        
        report_id = str(report.id)
        print(f"Created mock report with ID: {report_id}")
        
        from app.ocr.services import process_ocr_task
        
        # We need to mock download_from_s3 so it doesn't actually hit AWS
        # And we need to mock ocr_engine.ocr to return sample data
        sample_ocr_result = [[
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("Name: John Doe", 0.98)],
            [[[10, 40], [100, 40], [100, 60], [10, 60]], ("Age: 45", 0.95)],
            [[[10, 70], [100, 70], [100, 90], [10, 90]], ("Date: 12/05/2023", 0.99)],
            [[[10, 100], [100, 100], [100, 120], [10, 120]], ("Hemoglobin 13.5", 0.92)],
            [[[10, 130], [100, 130], [100, 150], [10, 150]], ("Low confidence text", 0.65)]
        ]]
        
        with patch('app.ocr.services.download_from_s3') as mock_download:
            # Create a fake file so PaddleOCR doesn't crash if it tries to read it
            # (Though we're mocking the ocr call itself, so we don't even need a file)
            def side_effect_download(s3_url, local_path):
                with open(local_path, "w") as f:
                    f.write("fake image data")
            mock_download.side_effect = side_effect_download
            
            with patch('app.ocr.services.ocr_engine.ocr', return_value=sample_ocr_result) as mock_ocr:
                print("Running OCR processing task...")
                result = process_ocr_task(report.id)
                
                print("\n=== OCR Results ===")
                print(json.dumps(result, indent=2))
                
                # Assertions
                assert result['requires_manual_review'] is True # Because of the 0.65 confidence
                assert result['extracted_data']['patient_name'] == "John Doe"
                assert result['extracted_data']['age'] == 45
                assert result['extracted_data']['test_date'] == "12/05/2023"
                assert result['extracted_data']['lab_values']['hemoglobin'] == "13.5"
                
                # New assertions for confidence scores and filtering
                assert 'raw_confidence_scores' in result
                assert len(result['raw_confidence_scores']) == 5
                assert 'average_confidence' in result
                assert 0.89 < result['average_confidence'] < 0.90  # Average of 0.98, 0.95, 0.99, 0.92, 0.65 is 0.898
                
                # Verify that low confidence text was filtered from raw_text
                assert "Low confidence text" not in result['raw_text']
                assert "Name: John Doe" in result['raw_text']
                
                print("\n[SUCCESS] OCR processing test passed successfully!")

if __name__ == '__main__':
    test_ocr_processing()
