import logging
import urllib.parse
from app.models.doctor_profile import DoctorProfile

def generate_booking_url(specialty: str, city: str = None, doctor_name: str = None, platform: str = 'practo'):
    """
    Generates a mock redirect URL for the booking platform.
    """
    base_url = "https://www.practo.com/search/doctors"
    if platform == 'zocdoc':
        base_url = "https://www.zocdoc.com/search"
        
    query_params = {}
    if specialty:
        query_params['specialty'] = specialty
    if city:
        query_params['city'] = city
    if doctor_name:
        query_params['q'] = doctor_name
        
    encoded_params = urllib.parse.urlencode(query_params)
    return f"{base_url}?{encoded_params}"

def send_sms_reminder(appointment_id: str, phone_number: str, message: str):
    """
    Mock implementation of an SMS sender (e.g., using Twilio).
    In a real scenario, this would call Twilio SDK.
    """
    # TODO: Integrate real Twilio Client here
    # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    # message = client.messages.create(body=message, from_=TWILIO_PHONE_NUMBER, to=phone_number)
    
    logging.info(f"========== MOCK SMS SENT ==========")
    logging.info(f"To: {phone_number}")
    logging.info(f"Message: {message}")
    logging.info(f"Appointment ID: {appointment_id}")
    logging.info(f"===================================")
    return True
