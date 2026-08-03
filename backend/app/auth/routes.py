from flask import Blueprint, jsonify, request, g
from app.database import db
from app.models.user import User
from app.auth.security import require_auth

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get the currently authenticated user's profile.
    If the user does not exist in the local database, creates a basic record.
    """
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    # Optional: If your token includes custom claims like email, extract them.
    # Often, you might need to query the Auth0 /userinfo endpoint if not in the token.
    # For this example, we assume we sync via /sync endpoint or token has it.
    
    user = User.query.get(auth0_id)
    if not user:
        # Create a basic user record
        # In a real app, you might want to force them to call /sync to provide email
        user = User(id=auth0_id, email=f"{auth0_id}@placeholder.com")
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Failed to create user record"}), 500
            
    return jsonify(user.to_dict()), 200

@auth_bp.route('/me', methods=['PUT'])
@require_auth
def update_current_user():
    """
    Update the currently authenticated user's profile metadata.
    """
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    user = User.query.get(auth0_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    data = request.get_json()
    if 'name' in data:
        user.name = data['name']
    if 'phone' in data:
        user.phone = data['phone']
        
    try:
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update user profile"}), 500

@auth_bp.route('/sync', methods=['POST'])
@require_auth
def sync_user():
    """
    Endpoint for frontend to call after registration/login.
    Syncs the user's email and details from the frontend/Auth0 to PostgreSQL.
    """
    user_payload = g.current_user
    auth0_id = user_payload.get("sub")
    
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({"error": "Email is required for syncing"}), 400
        
    user = User.query.get(auth0_id)
    if not user:
        user = User(id=auth0_id, email=data['email'])
        if 'name' in data:
            user.name = data['name']
        db.session.add(user)
    else:
        user.email = data['email']
        if 'name' in data:
            user.name = data['name']
            
    try:
        db.session.commit()
        return jsonify(user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to sync user"}), 500
