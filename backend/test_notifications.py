import pytest
from app.models.notification import NotificationPreference, Notification, Reminder
from app.notifications.services import dispatch_notification

def test_get_preferences_default(client, app, init_db, auth_headers):
    response = client.get('/api/notifications/preferences', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    # Default should be returned if none exists
    assert data['email_enabled'] is True
    assert data['sms_enabled'] is True

def test_update_preferences(client, app, init_db, auth_headers):
    payload = {
        "email_enabled": False,
        "push_enabled": True,
        "frequency": "daily_digest"
    }
    response = client.put('/api/notifications/preferences', json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['preferences']['email_enabled'] is False
    assert data['preferences']['push_enabled'] is True
    assert data['preferences']['frequency'] == 'daily_digest'

def test_register_fcm_token(client, app, init_db, auth_headers):
    payload = {"fcm_token": "test_token_123"}
    response = client.post('/api/notifications/fcm-token', json=payload, headers=auth_headers)
    assert response.status_code == 200
    
    with app.app_context():
        # user_id is from auth_headers (auth0|123456789)
        prefs = NotificationPreference.query.filter_by(user_id='auth0|123456789').first()
        assert prefs.fcm_token == "test_token_123"

def test_dispatch_notification(app, init_db):
    with app.app_context():
        # Setup preferences for mock user
        user_id = 'auth0|123456789'
        prefs = NotificationPreference(
            user_id=user_id,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            fcm_token="dummy_token"
        )
        app.db.session.add(prefs)
        app.db.session.commit()
        
        # Dispatch notification
        notification = dispatch_notification(
            user_id=user_id,
            notif_type='health_tip',
            safe_title='Stay Hydrated',
            safe_body='Drink 8 glasses of water today.'
        )
        
        assert notification is not None
        assert notification.safe_title == 'Stay Hydrated'
        # sms is false, so channels_sent should be 'email,push'
        assert 'email' in notification.channels_sent
        assert 'sms' not in notification.channels_sent
        assert 'push' in notification.channels_sent

def test_get_notifications(client, app, init_db, auth_headers):
    response = client.get('/api/notifications', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
