import os
import time
from unittest import mock
import pytest
from app import create_app
from app.database import db
from app.models.medical_report import MedicalReport
from app.models.user import User

# This will only test if the logic works correctly,
# we will mock the model in CI but allow real tests if testing locally
from app.classifier.services import classify_document

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def dummy_image(tmp_path):
    from PIL import Image
    image = Image.new('RGB', (100, 100))
    path = tmp_path / "test_report.jpg"
    image.save(path)
    return str(path)

@mock.patch("app.classifier.services.classifier_pipeline")
def test_classify_document_mock(mock_pipeline, dummy_image):
    # Mock pipeline returns top 3
    mock_pipeline.return_value = [
        {"label": "Blood Report", "score": 0.95},
        {"label": "ECG", "score": 0.03},
        {"label": "Chest X-ray", "score": 0.02}
    ]
    
    result = classify_document(dummy_image)
    assert result["document_type"] == "Blood Report"
    assert result["confidence"] == 0.95
    assert len(result["top_3"]) == 3
    assert result["requires_manual_review"] is False

@mock.patch("app.classifier.services.classifier_pipeline")
def test_classify_document_low_confidence(mock_pipeline, dummy_image):
    mock_pipeline.return_value = [
        {"label": "Ultrasound", "score": 0.70},
        {"label": "MRI", "score": 0.20},
        {"label": "CT Scan", "score": 0.10}
    ]
    
    result = classify_document(dummy_image)
    assert result["document_type"] == "Ultrasound"
    assert result["confidence"] == 0.70
    assert result["requires_manual_review"] is True

def test_classifier_benchmark(dummy_image):
    # This test will run the real pipeline. It will be skipped if pipeline is not initialized
    from app.classifier.services import classifier_pipeline
    if not classifier_pipeline:
        pytest.skip("Classifier pipeline not loaded.")
        
    start_time = time.time()
    result = classify_document(dummy_image)
    duration_ms = (time.time() - start_time) * 1000
    
    print(f"\nClassification latency: {duration_ms:.2f} ms")
    print(f"Result: {result['document_type']} (confidence: {result['confidence']:.2f})")
    
    # Optional constraint check
    if duration_ms > 1000:
        print("WARNING: Inference time exceeded 1s limit.")
