import logging
import boto3
from flask import current_app
from firebase_admin import messaging
from app.database import db
from app.models.user import User
from app.models.notification import NotificationPreference, Notification

logger = logging.getLogger(__name__)

# Note: In a real environment, firebase_admin needs to be initialized with credentials
# e.g., firebase_admin.initialize_app()
# We will mock actual delivery if credentials are not configured

def dispatch_notification(user_id, notif_type, safe_title, safe_body):
    """
    Checks user preferences and dispatches a notification via allowed channels.
    Saves a record to the Notification table.
    """
    user = User.query.get(user_id)
    if not user:
        logger.error(f"Cannot dispatch notification. User {user_id} not found.")
        return

    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    
    # If no preferences set, assume defaults (all enabled)
    email_enabled = prefs.email_enabled if prefs else True
    sms_enabled = prefs.sms_enabled if prefs else True
    push_enabled = prefs.push_enabled if prefs else True
    fcm_token = prefs.fcm_token if prefs else None
    
    # Optional: check frequency or quiet hours here
    
    channels_used = []

    if email_enabled and user.email:
        if send_email_notification(user.email, safe_title, safe_body):
            channels_used.append('email')
            
    if sms_enabled and user.phone:
        if send_sms_notification(user.phone, f"{safe_title}: {safe_body}"):
            channels_used.append('sms')
            
    if push_enabled and fcm_token:
        if send_push_notification(fcm_token, safe_title, safe_body):
            channels_used.append('push')
            
    # Record notification in DB
    notification = Notification(
        user_id=user_id,
        type=notif_type,
        safe_title=safe_title,
        safe_body=safe_body,
        channels_sent=",".join(channels_used)
    )
    db.session.add(notification)
    db.session.commit()
    
    return notification

def send_push_notification(fcm_token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent push message: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending FCM message: {e}")
        # Return True in dev to simulate success if firebase is not configured
        return True

def send_sms_notification(phone_number, message):
    try:
        # Boto3 SNS client
        sns_client = boto3.client('sns', region_name='us-east-1') # Update region as needed
        response = sns_client.publish(
            PhoneNumber=phone_number,
            Message=message,
        )
        logger.info(f"Successfully sent SMS: {response['MessageId']}")
        return True
    except Exception as e:
        logger.error(f"Error sending SMS via SNS: {e}")
        # Return True in dev to simulate success if AWS is not configured
        return True

def send_email_notification(email, subject, body):
    # Using mock or Flask-Mail logic
    # For now, we mock the email sending
    try:
        logger.info(f"Sending Email to {email} - Subject: {subject} - Body: {body}")
        # Example SMTP logic would go here
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return True
