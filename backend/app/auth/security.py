import json
import os
from functools import wraps
from flask import request, jsonify, g
import jwt
import requests

AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
API_AUDIENCE = os.environ.get("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                        "description": "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description": "Authorization header must start with Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description": "Authorization header must be Bearer token"}, 401)

    token = parts[1]
    return token

def require_auth(f):
    """Determines if the Access Token is valid"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = get_token_auth_header()
        except AuthError as e:
            return jsonify(e.error), e.status_code

        jsonurl = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        jwks = jsonurl.json()
        
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.JWTError:
            return jsonify({"code": "invalid_header", "description": "Invalid header. Use an RS256 signed JWT Access Token"}), 401
            
        if unverified_header["alg"] != "RS256":
            return jsonify({"code": "invalid_header", "description": "Invalid header. Use an RS256 signed JWT Access Token"}), 401

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(rsa_key)),
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/"
                )
            except jwt.ExpiredSignatureError:
                return jsonify({"code": "token_expired", "description": "token is expired"}), 401
            except jwt.JWTClaimsError:
                return jsonify({"code": "invalid_claims", "description": "incorrect claims, please check the audience and issuer"}), 401
            except Exception:
                return jsonify({"code": "invalid_header", "description": "Unable to parse authentication token."}), 401

            g.current_user = payload
            return f(*args, **kwargs)
        return jsonify({"code": "invalid_header", "description": "Unable to find appropriate key"}), 401
    return decorated
