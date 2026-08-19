from flask import request, jsonify, g
from app.auth.security import require_auth
from app.chatbot import chatbot_bp
from app.chatbot.services import process_chat_message
from app.models.medical_report import MedicalReport
import logging

@chatbot_bp.route('/chat', methods=['POST'])
# @require_auth  # Temporarily disabled for MVP testing
def chat_route():
    """
    Endpoint for the conversational AI chatbot.
    Expects JSON: 
    {
      "report_id": "uuid",
      "message": "User's message",
      "history": [{"role": "user", "content": "..."}]
    }
    """
    data = request.get_json()
    if not data or 'report_id' not in data or 'message' not in data:
        return jsonify({"error": "Missing report_id or message"}), 400
        
    report_id = data['report_id']
    message = data['message']
    history = data.get('history', [])
    target_language = data.get('lang', 'en')
    
    # Temporarily bypass user verification for MVP testing
    # user_payload = g.current_user
    # auth0_id = user_payload.get("sub")
    
    # Try to find report, or use a mock one for testing
    report = MedicalReport.query.filter_by(id=report_id).first()
    if not report:
        # Create a mock report object in memory for MVP
        report = MedicalReport(
            id=report_id,
            extracted_data={"mock": "True", "details": "This is a mock report for testing since the real report wasn't found in the DB."}
        )
        
    try:
        response_content = process_chat_message(report, message, history, target_language)
        return jsonify({
            "message": "Chat response generated successfully",
            "reply": response_content
        }), 200
    except Exception as e:
        logging.error(f"Error generating chat response: {e}")
        return jsonify({"error": str(e)}), 500
