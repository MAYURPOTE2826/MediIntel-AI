import os
import base64

# Ensure the key is 32 url-safe base64-encoded bytes for Fernet
# In production, this MUST be set in environment variables!
# Example of generating a valid key: Fernet.generate_key()
_dev_key = base64.urlsafe_b64encode(b'mediintel-dev-secret-key-32bytes')
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", _dev_key.decode('utf-8'))
