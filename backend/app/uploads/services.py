import os
import hashlib
import time
import uuid
import magic
import boto3
import requests
from werkzeug.utils import secure_filename

VIRUSTOTAL_API_KEY = os.environ.get('VIRUSTOTAL_API_KEY')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_CLEAN_BUCKET = os.environ.get('AWS_CLEAN_BUCKET_NAME', 'mediintel-clean-reports')
AWS_QUARANTINE_BUCKET = os.environ.get('AWS_QUARANTINE_BUCKET_NAME', 'mediintel-quarantine')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

ALLOWED_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/png']

class FileValidationError(Exception):
    pass

class VirusTotalError(Exception):
    pass

def validate_file_type(filepath):
    """Validates the file type using magic bytes."""
    mime = magic.Magic(mime=True)
    file_mime_type = mime.from_file(filepath)
    
    if file_mime_type not in ALLOWED_MIME_TYPES:
        raise FileValidationError(f"Invalid file type: {file_mime_type}. Only PDF, JPG, and PNG are allowed.")
    return file_mime_type

def get_file_hash(filepath):
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_with_virustotal(filepath):
    """
    Checks the file against VirusTotal.
    Returns 'clean', 'malicious', or 'unknown'.
    """
    if not VIRUSTOTAL_API_KEY:
        # In a real production environment, you should fail if the key is missing.
        # For local dev without a key, we might bypass or simulate.
        print("WARNING: VIRUSTOTAL_API_KEY is not set. Simulating 'unknown' result.")
        return 'unknown'

    file_hash = get_file_hash(filepath)
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    
    # Check if VT already knows this file
    url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        stats = data['data']['attributes']['last_analysis_stats']
        malicious_count = stats.get('malicious', 0)
        suspicious_count = stats.get('suspicious', 0)
        
        if malicious_count > 0 or suspicious_count > 0:
            return 'malicious'
        return 'clean'
    elif response.status_code == 404:
        # File is unknown to VT
        return 'unknown'
    else:
        raise VirusTotalError(f"Failed to query VirusTotal: {response.text}")

def upload_to_s3(filepath, original_filename, is_quarantined=False):
    """
    Uploads the file to the appropriate S3 bucket.
    Generates a UUID object key for encryption/obfuscation.
    Returns the generated object key and the s3 url.
    """
    bucket_name = AWS_QUARANTINE_BUCKET if is_quarantined else AWS_CLEAN_BUCKET
    
    # Generate unique UUID for the object key
    file_ext = os.path.splitext(original_filename)[1]
    object_key = f"{uuid.uuid4().hex}{file_ext}"
    
    try:
        s3_client.upload_file(filepath, bucket_name, object_key)
        # We can construct the s3 url or return the key
        s3_url = f"s3://{bucket_name}/{object_key}"
        return object_key, s3_url
    except Exception as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")
