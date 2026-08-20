import os
import time
from datetime import datetime, timezone
from PIL import Image
import torch
from transformers import pipeline
from app.monitoring import ai_confidence_histogram, ai_inference_latency_histogram

# We use a base document image classification model as a placeholder for the fine-tuned one
MODEL_NAME = os.environ.get("CLASSIFIER_MODEL_NAME", "microsoft/dit-base-finetuned-rvlcdip")
MODEL_VERSION = os.environ.get("CLASSIFIER_MODEL_VERSION", "v1.0-dit")

# Initialize pipeline globally to avoid reloading on every request
classifier_pipeline = None

def init_classifier():
    global classifier_pipeline
    if classifier_pipeline is None:
        try:
            device = 0 if torch.cuda.is_available() else -1
            print(f"Initializing classifier pipeline with {MODEL_NAME} on device {device}")
            classifier_pipeline = pipeline("image-classification", model=MODEL_NAME, device=device)
        except Exception as e:
            print(f"WARNING: Failed to initialize classifier pipeline: {e}")
            classifier_pipeline = None

# Trigger initialization when module loads (or we could wait for the first request)
init_classifier()

def classify_document(image_path):
    """
    Classifies a document image using a transformers pipeline.
    Returns:
        dict: {
            "document_type": str, # Top prediction
            "confidence": float,  # Top prediction confidence
            "top_3": list,        # List of {"label": str, "score": float}
            "requires_manual_review": bool,
            "latency_ms": float,
            "model_version": str,
            "classified_at": datetime
        }
    """
    if not classifier_pipeline:
        raise RuntimeError("Classifier pipeline is not initialized.")
        
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Failed to open image for classification: {e}")
        
    start_time = time.time()
    
    # Get predictions
    # pipeline returns a list of dicts like [{"label": "...", "score": 0.9}, ...]
    results = classifier_pipeline(image, top_k=3)
    
    latency_ms = (time.time() - start_time) * 1000
    ai_inference_latency_histogram.labels(model_name=MODEL_NAME).observe(latency_ms / 1000.0)
    
    # Process results
    if not results:
        raise ValueError("Classifier returned no results.")
        
    top_prediction = results[0]
    document_type = top_prediction["label"]
    confidence = top_prediction["score"]
    
    ai_confidence_histogram.labels(model_name=MODEL_NAME).observe(confidence)
    
    # Threshold for safety check
    requires_manual_review = confidence < 0.85
    
    return {
        "document_type": document_type,
        "confidence": confidence,
        "top_3": results,
        "requires_manual_review": requires_manual_review,
        "latency_ms": latency_ms,
        "model_version": MODEL_VERSION,
        "classified_at": datetime.now(timezone.utc)
    }
