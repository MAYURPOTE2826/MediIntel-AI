import os
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.database import db
from app.models.medical_report import MedicalReport

SAFETY_BLOCKLIST = [
    "diagnose", "diagnosis", "prescribe", "prescription", "treatment plan",
    "surgery", "cure", "recommend treating", "medical advice"
]

def check_safety(text):
    """Returns True if safe, False if a blocked keyword is found."""
    lower_text = text.lower()
    for keyword in SAFETY_BLOCKLIST:
        if keyword in lower_text:
            return False
    return True

def generate_questions(report_id):
    """
    Generates 5-7 simple, non-medical questions a patient should ask their doctor 
    based on the findings in their medical report.
    """
    report = MedicalReport.query.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
        
    ocr_text = report.raw_ocr_output or str(report.extracted_data)
    if not ocr_text:
        raise ValueError("Report has no OCR data to generate questions from.")
        
    findings_text = report.explanation_text or "No specific findings generated yet."
    
    # Setup LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv('GOOGLE_API_KEY'))
    
    template = """
    You are an AI assistant helping a patient prepare for a doctor's consultation.
    Based on the following medical report findings, list 5-7 simple, non-medical questions 
    the patient should ask their doctor.
    
    CRITICAL REQUIREMENTS:
    1. Questions MUST be clear and patient-friendly (no complex medical jargon).
    2. Questions MUST be focused on impact (e.g., "what does this mean for me?").
    3. Questions MUST be action-oriented (e.g., "what happens next?").
    4. Safety: Questions MUST NEVER imply a diagnosis or treatment. Always defer to the doctor's expertise.
    
    Examples of good questions: 
    - "Will this affect my daily activities?" 
    - "What follow-up tests are needed?"
    
    Report OCR Text:
    {ocr_text}
    
    Report Findings/Explanation:
    {findings_text}
    
    Return your response ONLY as a JSON array of strings. Do not include markdown formatting or backticks.
    Example output format:
    [
        "Will this affect my daily activities?",
        "What follow-up tests are needed?"
    ]
    """
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({"ocr_text": ocr_text, "findings_text": findings_text})
    raw_output = response.content
    
    # Parse the JSON array
    try:
        # Try to find JSON array in case there's extra text
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if json_match:
            questions = json.loads(json_match.group(0))
        else:
            questions = json.loads(raw_output)
    except json.JSONDecodeError:
        # Fallback if parsing fails
        questions = ["What do these findings mean for my overall health?", "What should be our next steps?"]
        
    # Ensure it's a list
    if not isinstance(questions, list):
        questions = ["What do these findings mean for my overall health?", "What should be our next steps?"]
        
    # Apply safety check to each question and filter
    safe_questions = []
    for q in questions:
        if check_safety(q):
            safe_questions.append(q)
            
    # Fallback if too many questions were filtered out
    if len(safe_questions) < 3:
        safe_questions.extend([
            "Could you explain these results in simple terms?",
            "Do I need to make any lifestyle changes based on this?",
            "When should we schedule a follow-up appointment?"
        ])
        
    # Keep only up to 7 questions
    safe_questions = safe_questions[:7]
        
    # Save to DB
    report.generated_questions = safe_questions
    db.session.commit()
    
    return safe_questions
