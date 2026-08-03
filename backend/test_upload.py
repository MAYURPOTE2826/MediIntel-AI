import os
import io
from app import create_app
from app.database import db
from app.models.user import User
from app.models.medical_report import MedicalReport
from unittest.mock import patch, MagicMock

# Create an app configured for testing
app = create_app()
app.config['TESTING'] = True
client = app.test_client()

def test_chunked_upload():
    with app.app_context():
        # Clean up database state
        db.drop_all()
        db.create_all()
        
        # Insert a test user
        user = User(id='auth0|testuser999', email='testupload@example.com', name='Test Uploader')
        db.session.add(user)
        db.session.commit()

        # Generate a dummy PDF content that satisfies magic bytes
        # A valid PDF starts with %PDF-1.
        pdf_content = b"%PDF-1.4\n%This is a fake PDF for testing file validation.\nEOF\n"
        
        # Patch the security require_auth to simulate an authenticated request
        with patch('app.auth.security.require_auth') as mock_require_auth:
            # We need to monkeypatch the route because require_auth is applied at import time.
            # Instead, let's just patch the `g` object context in a before_request.
            pass

    # Actually, a simpler way is to patch `g` inside the route, but since require_auth decorators 
    # run before the route, we should patch get_token_auth_header and jwt decoding or just 
    # directly call the process_completed_upload function to test the core logic.

    with app.app_context():
        from app.uploads.routes import process_completed_upload
        
        test_filepath = "test_doc.pdf"
        with open(test_filepath, "wb") as f:
            f.write(b"%PDF-1.4\n%This is a fake PDF for testing file validation.\nEOF\n")
            
        # Mock VirusTotal (return 'clean') and S3 upload
        with patch('app.uploads.routes.scan_with_virustotal', return_value='clean') as mock_vt:
            with patch('app.uploads.routes.upload_to_s3', return_value=('fake_key', 's3://fake-bucket/fake_key')) as mock_s3:
                # To avoid g.current_user issues, we will just call process_completed_upload
                response, status_code = process_completed_upload(test_filepath, "my_report.pdf", 'auth0|testuser999')
                
                print("Response:", response.get_json())
                print("Status Code:", status_code)
                
                assert status_code == 201
                assert response.get_json()['status'] == 'UPLOAD_CLEAN'
                assert mock_vt.called
                assert mock_s3.called
                
        # Verify db insertion
        report = MedicalReport.query.filter_by(user_id='auth0|testuser999').first()
        assert report is not None
        assert report.report_type == 'PDF Document'
        assert report.file_url == 's3://fake-bucket/fake_key'
        print("✅ DB record successfully created!")
        
        # Cleanup
        if os.path.exists(test_filepath):
            os.remove(test_filepath)
            
if __name__ == '__main__':
    test_chunked_upload()
    print("✅ All upload tests passed!")
