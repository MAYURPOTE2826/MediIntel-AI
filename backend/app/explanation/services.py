import os
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from app.database import db
from app.models.medical_report import MedicalReport
from app.translation.services import translate_text

# Keywords that should flag a violation
SAFETY_BLOCKLIST = [
    "diagnose", "diagnosis", "prescribe", "prescription", "treatment plan",
    "surgery", "cure", "recommend treating", "medical advice"
]

MANDATORY_DISCLAIMER = "\n\nConsult a qualified healthcare professional for medical advice.\nConfidence \u2260 Medical Certainty. For guidance only."

# Path to the FAISS index
VECTORSTORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'vectorstore')

_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        try:
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            _vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            print(f"WARNING: Failed to load FAISS index: {e}")
            _vectorstore = None
    return _vectorstore

def check_safety(text):
    """Returns True if safe, False if a blocked keyword is found."""
    lower_text = text.lower()
    for keyword in SAFETY_BLOCKLIST:
        if keyword in lower_text:
            return False
    return True

def generate_explanation(report_id, target_language='en'):
    """
    Generates a simple medical explanation from OCR findings using RAG.
    """
    report = MedicalReport.query.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
        
    if not report.raw_ocr_output and not report.extracted_data:
        raise ValueError("Report has no OCR data to explain")
        
    ocr_text = report.raw_ocr_output or str(report.extracted_data)
    
    vectorstore = get_vectorstore()
    if not vectorstore:
        raise RuntimeError("Vectorstore not available for RAG.")
        
    # Setup Langchain RAG
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.getenv('GOOGLE_API_KEY'))
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # Retrieve documents explicitly to save citations
    docs = retriever.invoke(ocr_text)
    context_text = "\n\n".join([f"Source: {d.metadata.get('title', 'Unknown')} - {d.page_content}" for d in docs])
    
    citations = [{"title": d.metadata.get('title', 'Unknown'), "source": d.metadata.get('source', 'Unknown')} for d in docs]
    
    template = """
You are an AI assistant designed to help patients understand their medical reports.
Your primary directive is to provide clear, simple explanations (2-3 paragraphs) of the findings.
You MUST NEVER diagnose a condition, prescribe medication, or recommend surgery or specific treatment plans.
Use the provided trusted medical literature to explain the findings.

Trusted Literature Context:
{context}

Patient Report Findings (OCR Text):
{report_text}

You MUST return your response as a valid JSON object with the following structure:
{{
  "explanation": "Your 2-3 paragraph simple explanation here.",
  "explanation_confidence": 95.5,
  "specialist_recommendation_confidence": 85.0,
  "key_findings_confidence": 92.0
}}
The confidence values should be numbers between 0.0 and 100.0.
Provide ONLY the JSON object, with no markdown formatting or backticks.
"""
    prompt = PromptTemplate.from_template(template)
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"context": context_text, "report_text": ocr_text})
        raw_output = response.content
        
        import re
        import json
        
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if not json_match:
            # Fallback if parsing fails
            parsed_output = {
                "explanation": raw_output,
                "explanation_confidence": 0.0,
                "specialist_recommendation_confidence": 0.0,
                "key_findings_confidence": 0.0
            }
        else:
            try:
                parsed_output = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                parsed_output = {
                    "explanation": raw_output,
                    "explanation_confidence": 0.0,
                    "specialist_recommendation_confidence": 0.0,
                    "key_findings_confidence": 0.0
                }
                
        output_text = parsed_output.get("explanation", "")
        exp_conf = float(parsed_output.get("explanation_confidence", 0.0))
        spec_conf = float(parsed_output.get("specialist_recommendation_confidence", 0.0))
        key_conf = float(parsed_output.get("key_findings_confidence", 0.0))
        
        ocr_conf = (report.confidence_score or 0.0) * 100 if (report.confidence_score and report.confidence_score <= 1.0) else (report.confidence_score or 0.0)
        class_conf = (report.classification_confidence or 0.0) * 100 if (report.classification_confidence and report.classification_confidence <= 1.0) else (report.classification_confidence or 0.0)
        
        composite_score = (ocr_conf * 0.30) + (class_conf * 0.25) + (exp_conf * 0.25) + (key_conf * 0.20)
        
        # Safety Check
        is_safe = check_safety(output_text)
        if not is_safe:
            # Fallback safe response if generation fails safety check
            output_text = "I apologize, but I cannot provide an explanation that contains diagnostic or prescriptive language. Please discuss these findings directly with your doctor."
        
        # Append Mandatory Disclaimer
        if MANDATORY_DISCLAIMER.strip() not in output_text:
            output_text += MANDATORY_DISCLAIMER
            
        # Translate to target language using Google Translate API (with medical glossary)
        output_text = translate_text(output_text, target_language)
            
        # 10% Manual QA
        requires_qa = random.random() < 0.10
        
        # Save to DB
        report.explanation_text = output_text
        report.explanation_citations = citations
        report.explanation_manual_qa_required = requires_qa
        report.explanation_confidence = exp_conf
        report.specialist_recommendation_confidence = spec_conf
        report.key_findings_confidence = key_conf
        report.composite_confidence_score = composite_score
        db.session.commit()
        
        return {
            "explanation": output_text,
            "citations": citations,
            "qa_flagged": requires_qa,
            "safety_passed": is_safe,
            "metrics": {
                "ocr_quality": round(ocr_conf, 2),
                "report_type_detection": round(class_conf, 2),
                "explanation_confidence": round(exp_conf, 2),
                "specialist_recommendation_confidence": round(spec_conf, 2),
                "key_findings_confidence": round(key_conf, 2),
                "composite_score": round(composite_score, 2)
            }
        }
        
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Explanation generation failed: {e}")
