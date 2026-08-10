import pytest
from app import create_app
from app.database import db
from app.models.doctor_profile import DoctorProfile
from app.models.appointment import Appointment
import os
import uuid

@pytest.fixture
def app():
    os.environ["TESTING"] = "1"
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def setup_db(app):
    with app.app_context():
        doc = DoctorProfile(
            name="Dr. Test",
            specialty="Dentist",
            license_number="LIC-12345",
            accepts_online_booking=True,
            booking_url="https://practo.com/test",
            phone="1234567890"
        )
        db.session.add(doc)
        db.session.commit()
        return doc.id

# Mock require_auth to not check tokens
def test_book_appointment(client, setup_db, monkeypatch):
    # Bypass auth
    def mock_require_auth(f):
        return f
    # Wait, patching the decorator after it's applied is hard, so we mock g instead inside a request
    
    with client.application.test_request_context():
        from flask import g
        g.current_user = {"sub": "auth0|12345"}

    # However test_client requests create their own context. A better way:
    # Just patch the endpoint directly if needed, or mock get_token_auth_header if it calls out.
    # We will monkeypatch get_token_auth_header to not throw and jwt.decode to return mock payload.
    
    import app.auth.security as sec
    monkeypatch.setattr(sec, 'get_token_auth_header', lambda: "dummy_token")
    monkeypatch.setattr('requests.get', lambda url: type('obj', (object,), {'json': lambda: {'keys': [{'kid': '1', 'kty': 'RSA', 'use': 'sig', 'n': '', 'e': ''}]}})())
    monkeypatch.setattr('jwt.get_unverified_header', lambda token: {"alg": "RS256", "kid": "1"})
    monkeypatch.setattr('jwt.decode', lambda *args, **kwargs: {"sub": "test_user_id"})

    response = client.post('/api/appointments/book', json={
        "doctor_id": str(setup_db),
        "doctor_name": "Dr. Test",
        "specialty": "Dentist",
        "appointment_date": "2026-08-20T10:00:00",
        "city": "Mumbai"
    })
    
    assert response.status_code == 200
    data = response.json
    assert data["can_book_online"] is True
    assert data["redirect_url"] == "https://practo.com/test"
    assert "appointment_id" in data

def test_book_appointment_fallback(client, monkeypatch):
    import app.auth.security as sec
    monkeypatch.setattr(sec, 'get_token_auth_header', lambda: "dummy_token")
    monkeypatch.setattr('requests.get', lambda url: type('obj', (object,), {'json': lambda: {'keys': [{'kid': '1', 'kty': 'RSA', 'use': 'sig', 'n': '', 'e': ''}]}})())
    monkeypatch.setattr('jwt.get_unverified_header', lambda token: {"alg": "RS256", "kid": "1"})
    monkeypatch.setattr('jwt.decode', lambda *args, **kwargs: {"sub": "test_user_id"})

    response = client.post('/api/appointments/book', json={
        "doctor_name": "Dr. No DB",
        "specialty": "Cardiologist",
        "appointment_date": "2026-08-21T10:00:00",
        "city": "Delhi"
    })
    
    assert response.status_code == 200
    data = response.json
    assert data["can_book_online"] is True
    # It should generate a search URL since there's no doctor in DB
    assert "practo.com/search/doctors" in data["redirect_url"]
