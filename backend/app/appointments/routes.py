from flask import request, jsonify, g
from app.auth.security import require_auth
from app.appointments import appointments_bp
from app.appointments.services import generate_booking_url
from app.models.appointment import Appointment
from app.models.doctor_profile import DoctorProfile
from app.database import db
from datetime import datetime
import logging

@appointments_bp.route('/book', methods=['POST'])
@require_auth
def book_appointment():
    """
    Initiates an appointment booking.
    Expected JSON: {
        "doctor_id": "optional_uuid",
        "doctor_name": "Dr. Smith",
        "specialty": "Cardiologist",
        "appointment_date": "2026-08-20T10:00:00",
        "city": "Mumbai"
    }
    """
    data = request.get_json()
    if not data or 'doctor_name' not in data or 'appointment_date' not in data:
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        appointment_date = datetime.fromisoformat(data['appointment_date'])
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format."}), 400
        
    user_id = g.current_user.get("sub") if hasattr(g, 'current_user') and g.current_user else "test_user_id"
    doctor_id = data.get('doctor_id')
    doctor_name = data['doctor_name']
    specialty = data.get('specialty', '')
    city = data.get('city', '')
    
    doctor = None
    if doctor_id:
        doctor = DoctorProfile.query.get(doctor_id)
        
    # Create the pending appointment
    appointment = Appointment(
        user_id=user_id,
        doctor_id=doctor_id if doctor else None,
        doctor_name=doctor_name,
        specialty=specialty,
        appointment_date=appointment_date,
        status='pending'
    )
    db.session.add(appointment)
    db.session.commit()
    
    # Check if doctor supports online booking
    if doctor and doctor.accepts_online_booking and doctor.booking_url:
        redirect_url = doctor.booking_url
        can_book_online = True
    elif doctor and not doctor.accepts_online_booking:
        redirect_url = None
        can_book_online = False
    else:
        # Fallback for external doctors or if no specific URL is provided
        # We redirect to a search page with prefilled specialty
        redirect_url = generate_booking_url(specialty=specialty, city=city, doctor_name=doctor_name)
        can_book_online = True

    response_data = {
        "message": "Booking initiated",
        "appointment_id": str(appointment.id),
        "can_book_online": can_book_online
    }
    
    if can_book_online:
        response_data["redirect_url"] = redirect_url
    else:
        response_data["fallback_contact"] = {
            "phone": doctor.phone if doctor else "Not available",
            "email": doctor.email if doctor else "Not available"
        }
        
    return jsonify(response_data), 200

@appointments_bp.route('/confirm', methods=['POST'])
@require_auth
def confirm_appointment():
    """
    Webhook/callback to confirm booking.
    Expected JSON: { "appointment_id": "uuid", "booking_reference": "REF123" }
    """
    data = request.get_json()
    appointment_id = data.get('appointment_id')
    
    if not appointment_id:
        return jsonify({"error": "Missing appointment_id"}), 400
        
    user_id = g.current_user.get("sub") if hasattr(g, 'current_user') and g.current_user else "test_user_id"
    appointment = Appointment.query.filter_by(id=appointment_id, user_id=user_id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
        
    appointment.status = 'booked'
    appointment.booking_reference = data.get('booking_reference')
    db.session.commit()
    
    return jsonify({
        "message": "Appointment confirmed successfully",
        "appointment": appointment.to_dict()
    }), 200
