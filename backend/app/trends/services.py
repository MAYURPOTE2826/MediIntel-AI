import os
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.database import db
from app.models.medical_report import MedicalReport

# Reuse the safety blocklist
SAFETY_BLOCKLIST = [
    "diagnose", "diagnosis", "prescribe", "prescription", "treatment plan",
    "surgery", "cure", "recommend treating", "medical advice"
]

MANDATORY_DISCLAIMER = "\n\nConsult a qualified healthcare professional for medical advice.\nTrend analysis is informational only. For guidance only."

def check_safety(text):
    """Returns True if safe, False if a blocked keyword is found."""
    lower_text = text.lower()
    for keyword in SAFETY_BLOCKLIST:
        if keyword in lower_text:
            return False
    return True

def extract_and_compare_trends(report_id_1, report_id_2):
    """
    Extracts metrics from two reports and compares them.
    Report 1 is assumed to be the older (baseline) report.
    Report 2 is assumed to be the newer (follow-up) report.
    """
    report1 = MedicalReport.query.get(report_id_1)
    report2 = MedicalReport.query.get(report_id_2)
    
    if not report1 or not report2:
        raise ValueError("One or both reports not found")
        
    text1 = report1.raw_ocr_output or str(report1.extracted_data or "")
    text2 = report2.raw_ocr_output or str(report2.extracted_data or "")
    
    if not text1 or not text2:
        raise ValueError("Both reports must have OCR data to compare")
        
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=os.getenv('GOOGLE_API_KEY'))
    
    template = """
You are an AI assistant designed to help patients understand the trends between two of their medical reports.
Your primary directive is to extract all comparable metrics from both reports, compare them, and determine if they are improving, declining, or stable.
You MUST NEVER diagnose a condition, prescribe medication, or recommend surgery or specific treatment plans. Be clinically-aware when determining 'improved', 'declined', or 'stable' (e.g. a decrease in high cholesterol is 'improved', a decrease in hemoglobin might be 'declined').

Report 1 (Baseline / Older) OCR Text:
{report1_text}

Report 2 (Follow-up / Newer) OCR Text:
{report2_text}

You MUST return your response as a valid JSON object with the following structure:
{{
  "trend_sentence": "A single sentence summarizing the overall trend between these two reports (e.g. 'Your glucose and cholesterol levels have improved since your last visit.').",
  "metrics": [
    {{
      "name": "Name of the metric (e.g., Glucose, HDL Cholesterol)",
      "value_1": "Value in Report 1 (include units)",
      "value_2": "Value in Report 2 (include units)",
      "status": "improved" | "declined" | "stable"
    }}
  ]
}}

Extract ALL comparable metrics you can find. If a metric is only in one report, ignore it.
Provide ONLY the JSON object, with no markdown formatting or backticks.
"""
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "report1_text": text1,
            "report2_text": text2
        })
        raw_output = response.content
        
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to parse JSON from LLM response")
            
        parsed_output = json.loads(json_match.group(0))
        
        trend_sentence = parsed_output.get("trend_sentence", "")
        metrics = parsed_output.get("metrics", [])
        
        # Safety Check
        is_safe = check_safety(trend_sentence)
        if not is_safe:
            trend_sentence = "I apologize, but I cannot provide a trend summary that contains diagnostic or prescriptive language. Please discuss these findings directly with your doctor."
        
        # Append Mandatory Disclaimer
        if MANDATORY_DISCLAIMER.strip() not in trend_sentence:
            trend_sentence += MANDATORY_DISCLAIMER
            
        return {
            "trend_sentence": trend_sentence,
            "metrics": metrics,
            "safety_passed": is_safe
        }
        
    except Exception as e:
        raise RuntimeError(f"Trend extraction failed: {e}")
