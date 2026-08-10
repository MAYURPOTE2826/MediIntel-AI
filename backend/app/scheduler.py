import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from app.database import db
from app.models.appointment import Appointment
from app.appointments.services import send_sms_reminder
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
                # In a real app, we'd fetch the user's phone number from the user model
                # Assuming the user model has a phone number, or we just mock it
                mock_phone = "+1234567890" 
                message = f"Reminder: You have an appointment with {appt.doctor_name} on {appt.appointment_date.strftime('%Y-%m-%d %H:%M')}."
                
                send_sms_reminder(str(appt.id), mock_phone, message)
                
                # Mark as sent
                appt.sms_reminder_sent = True
                
            if appointments:
                db.session.commit()
                logging.info(f"Sent {len(appointments)} SMS reminders.")
                
        except Exception as e:
            logging.error(f"Error in send_24h_reminders: {e}")
            db.session.rollback()

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
    
    scheduler.start()
    logging.info("APScheduler started successfully.")
    
    # Optional: shut down the scheduler when exiting the app
    import atexit
    atexit.register(lambda: scheduler.shutdown(wait=False))
