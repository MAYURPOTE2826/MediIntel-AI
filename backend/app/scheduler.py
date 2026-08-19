import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from app.database import db
from app.models.appointment import Appointment
from app.models.notification import Reminder
from app.notifications.services import dispatch_notification
from flask import current_app

def send_24h_reminders(app):
    """
    Task to find appointments starting in ~24 hours and send reminders.
    Requires the Flask app context.
    """
    with app.app_context():
        # Look for appointments between 23.5 and 24.5 hours from now
        now = datetime.utcnow()
        start_range = now + timedelta(hours=23, minutes=30)
        end_range = now + timedelta(hours=24, minutes=30)
        
        try:
            appointments = Appointment.query.filter(
                Appointment.status == 'booked',
                Appointment.sms_reminder_sent == False,
                Appointment.appointment_date >= start_range,
                Appointment.appointment_date <= end_range
            ).all()
            
            for appt in appointments:
                safe_title = "Appointment Reminder"
                safe_body = f"Reminder: You have an upcoming appointment on {appt.appointment_date.strftime('%Y-%m-%d %H:%M')}."
                
                # Dispatch notification securely and multi-channel
                dispatch_notification(
                    user_id=appt.user_id,
                    notif_type='appointment',
                    safe_title=safe_title,
                    safe_body=safe_body
                )
                
                # Mark as sent
                appt.sms_reminder_sent = True
                
            if appointments:
                db.session.commit()
                logging.info(f"Sent {len(appointments)} appointment reminders.")
                
        except Exception as e:
            logging.error(f"Error in send_24h_reminders: {e}")
            db.session.rollback()

def process_dynamic_reminders(app):
    """
    Check the Reminder table for due follow-ups and medications.
    """
    with app.app_context():
        now = datetime.utcnow()
        try:
            # Find active reminders that are due
            due_reminders = Reminder.query.filter(
                Reminder.status == 'active',
                Reminder.next_due_date <= now
            ).all()
            
            for reminder in due_reminders:
                safe_body = f"It is time for your {reminder.reminder_type} reminder."
                dispatch_notification(
                    user_id=reminder.user_id,
                    notif_type=reminder.reminder_type,
                    safe_title=reminder.safe_title,
                    safe_body=safe_body
                )
                
                # Update next_due_date based on frequency_rule
                if reminder.frequency_rule == 'daily':
                    reminder.next_due_date = now + timedelta(days=1)
                elif reminder.frequency_rule == 'weekly':
                    reminder.next_due_date = now + timedelta(days=7)
                else:
                    reminder.status = 'completed'
                    
            if due_reminders:
                db.session.commit()
                logging.info(f"Processed {len(due_reminders)} dynamic reminders.")
                
        except Exception as e:
            logging.error(f"Error in process_dynamic_reminders: {e}")
            db.session.rollback()

def send_health_tips(app):
    """
    Send periodic health tips to users.
    """
    with app.app_context():
        try:
            # Here we might fetch opted-in users and send general tips
            # For brevity, this is a placeholder
            logging.info("Sending weekly health tips (placeholder).")
        except Exception as e:
            logging.error(f"Error in send_health_tips: {e}")

def init_scheduler(app):
    """
    Initializes and starts the APScheduler.
    """
    scheduler = BackgroundScheduler()
    
    # Run the job every hour
    scheduler.add_job(
        func=send_24h_reminders,
        trigger=IntervalTrigger(hours=1),
        args=[app],
        id='send_24h_reminders_job',
        name='Send 24h SMS Reminders',
        replace_existing=True
    )
    
    # Process dynamic reminders every 15 minutes
    scheduler.add_job(
        func=process_dynamic_reminders,
        trigger=IntervalTrigger(minutes=15),
        args=[app],
        id='process_dynamic_reminders_job',
        name='Process Dynamic Reminders',
        replace_existing=True
    )
    
    # Send health tips weekly
    scheduler.add_job(
        func=send_health_tips,
        trigger=IntervalTrigger(weeks=1),
        args=[app],
        id='send_health_tips_job',
        name='Send Weekly Health Tips',
        replace_existing=True
    )
    
    scheduler.start()
    logging.info("APScheduler started successfully.")
    
    # Optional: shut down the scheduler when exiting the app
    import atexit
    atexit.register(lambda: scheduler.shutdown(wait=False))
