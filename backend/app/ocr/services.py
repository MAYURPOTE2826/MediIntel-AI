import os
import uuid
import re
import json
import redis
import boto3
from urllib.parse import urlparse
from app.database import db
from app.models.medical_report import MedicalReport
from paddleocr import PaddleOCR
from app.classifier.services import classify_document
from app.translation.services import translate_text
# Configure Redis cache (Fallback if not configured, or we can use a simpler approach)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
try:
    cache = redis.from_url(REDIS_URL)
    cache.ping()
except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError):
    print("WARNING: Redis not connected. Caching will be disabled.")
    cache = None

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

TEMP_OCR_DIR = os.path.join(os.getcwd(), 'tmp_uploads', 'ocr')
os.makedirs(TEMP_OCR_DIR, exist_ok=True)

# Initialize PaddleOCR globally so it's not re-loaded on every request
# We only need English for now, use angle classifier
try:
    ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
except Exception as e:
    print(f"WARNING: PaddleOCR failed to initialize: {e}")
    ocr_engine = None

def download_from_s3(s3_url, local_path):
    """Downloads a file from S3 given its s3:// URL."""
    parsed = urlparse(s3_url)
    bucket = parsed.netloc
    key = parsed.path.lstrip('/')
    s3_client.download_file(bucket, key, local_path)

def extract_structured_data(ocr_results):
    """
    Parses OCR results to extract patient name, age, test dates, values.
    Applies >0.7 confidence filter.
    Returns extracted dict and manual review flag.
    ocr_results format: [[[[x,y],...], ("text", confidence)], ...]
    """
    extracted_data = {
        "patient_name": None,
        "age": None,
        "test_date": None,
        "lab_values": {}
    }
    requires_manual_review = False
    
    # Flatten text lines and confidences
    text_lines = []
    raw_confidence_scores = []
    
    if not ocr_results or not isinstance(ocr_results, list):
        return extracted_data, True, "", raw_confidence_scores
        
    for res in ocr_results:
        if not res:
            continue
        for line in res:
            if not line or len(line) < 2:
                continue
            box, (text, confidence) = line
            
            raw_confidence_scores.append({"text": text, "confidence": confidence})
            
            if confidence < 0.7:
                requires_manual_review = True
            else:
                text_lines.append(text)
            
    full_text = " ".join(text_lines)
    
    # Basic heuristic extraction
    # Name extraction (Naive)
    # Stop matching if we hit 'Age', 'Date', or other keywords
    name_match = re.search(r'(?i)name[:\-\s]+([A-Za-z\s]+?)(?=\s+(?:age|date|dob|gender|sex|$))', full_text)
    if name_match:
        extracted_data["patient_name"] = name_match.group(1).strip()
        
    # Age extraction
    age_match = re.search(r'(?i)age[:\-\s]+(\d+)', full_text)
    if age_match:
        extracted_data["age"] = int(age_match.group(1))
        
    # Date extraction (MM/DD/YYYY or similar)
    date_match = re.search(r'(?i)date[:\-\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', full_text)
    if date_match:
        extracted_data["test_date"] = date_match.group(1)
        
    # Example Lab values extraction
    lab_keywords = ['hemoglobin', 'wbc', 'rbc', 'platelets', 'glucose']
    for keyword in lab_keywords:
        match = re.search(rf'(?i){keyword}\s*[:\-]?\s*([\d\.]+)', full_text)
        if match:
            extracted_data["lab_values"][keyword] = match.group(1)

    return extracted_data, requires_manual_review, full_text, raw_confidence_scores

def process_ocr_task(report_id, target_language='en'):
    """
    Core function for processing OCR.
    Can be called synchronously or via a task queue.
    """
    report = MedicalReport.query.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
        
    if not report.file_url:
        raise ValueError("Report has no file URL")
        
    # Check cache first
    cache_key = f"ocr_result:{report.file_url}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
            
    temp_filename = f"{uuid.uuid4()}_{os.path.basename(report.file_url)}"
    temp_filepath = os.path.join(TEMP_OCR_DIR, temp_filename)
    
    try:
        # 1. Download file
        download_from_s3(report.file_url, temp_filepath)
        
        # 2. Run PaddleOCR
        if not ocr_engine:
            raise RuntimeError("PaddleOCR engine is not initialized.")
            
        result = ocr_engine.ocr(temp_filepath, cls=True)
        
        # 3. Extract Data & Apply Filters
        extracted_data, requires_manual_review, raw_text, raw_scores = extract_structured_data(result)
        
        # Translate OCR Text
        translated_raw_text = translate_text(raw_text, target_language)
        
        # Calculate average confidence for OCR
        avg_conf = 0.0
        if raw_scores:
            avg_conf = sum(item["confidence"] for item in raw_scores) / len(raw_scores)
            
        # 4. Run Document Classifier
        try:
            classification_result = classify_document(temp_filepath)
            
            report.document_type = classification_result["document_type"]
            # also update legacy report_type if needed, or just let document_type take over
            report.report_type = classification_result["document_type"]
            report.classification_confidence = classification_result["confidence"]
            report.classification_results = classification_result["top_3"]
            report.classification_model_version = classification_result["model_version"]
            report.classified_at = classification_result["classified_at"]
            
            # Update requires_manual_review based on classifier confidence
            if classification_result["requires_manual_review"]:
                requires_manual_review = True
                
        except Exception as e:
            print(f"WARNING: Classification failed: {e}")
            
        # 5. Save to DB
        report.extracted_data = extracted_data
        report.requires_manual_review = requires_manual_review
        report.raw_ocr_output = translated_raw_text
        report.confidence_score = avg_conf
        db.session.commit()
        
        # 6. Cache result for 7 days (604800 seconds)
        response_data = {
            "extracted_data": extracted_data,
            "requires_manual_review": requires_manual_review,
            "raw_text": translated_raw_text,
            "raw_confidence_scores": raw_scores,
            "average_confidence": avg_conf,
            "classification": {
                "document_type": report.document_type,
                "confidence": report.classification_confidence,
                "top_3": report.classification_results
            } if hasattr(report, 'document_type') and report.document_type else None
        }
        if cache:
            cache.setex(cache_key, 604800, json.dumps(response_data))
            
        return response_data
        
    finally:
        # Ensure temp file is deleted immediately after processing
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
