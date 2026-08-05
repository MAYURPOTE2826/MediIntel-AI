import logging

# Define the mapping from report type to specialties, base scores, and reasoning.
SPECIALTY_MAPPING = {
    "Blood Report": [
        {"specialty": "Hematologist", "base_score": 98, "reasoning": "Specializes in diagnosing and treating blood disorders."},
        {"specialty": "Internist", "base_score": 95, "reasoning": "Primary care physician skilled in diagnosing broad systemic issues from blood work."},
        {"specialty": "Endocrinologist", "base_score": 85, "reasoning": "Specialist for hormonal or metabolic abnormalities indicated in blood work."}
    ],
    "ECG": [
        {"specialty": "Cardiologist", "base_score": 99, "reasoning": "Specialist in diagnosing heart rhythms and cardiovascular diseases."},
        {"specialty": "Electrophysiologist", "base_score": 90, "reasoning": "Sub-specialist in the electrical activity of the heart."}
    ],
    "Chest X-ray": [
        {"specialty": "Pulmonologist", "base_score": 95, "reasoning": "Specializes in the respiratory system and lung conditions."},
        {"specialty": "Radiologist", "base_score": 92, "reasoning": "Expert in reading and interpreting medical imaging like X-rays."},
        {"specialty": "Cardiologist", "base_score": 85, "reasoning": "Relevant if the X-ray indicates heart enlargement or fluid around the heart."}
    ],
    "MRI/CT": [
        {"specialty": "Radiologist", "base_score": 98, "reasoning": "Expert in interpreting complex imaging like MRI and CT scans."},
        {"specialty": "Neurologist", "base_score": 85, "reasoning": "Relevant if the scan is of the brain or spine."},
        {"specialty": "Orthopedist", "base_score": 85, "reasoning": "Relevant if the scan is focused on bones, joints, or musculoskeletal issues."}
    ]
}

def recommend_specialists(report_type: str, classifier_confidence: float = 1.0) -> dict:
    """
    Recommends top medical specialists based on the report type.
    
    Workflow:
    (1) Get report_type
    (2) Look up recommended specialties (pre-built mapping)
    (3) Score each specialty on relevance (0-100)
    (4) Return top-3 specialists with reasoning
    
    Safety Check: Recommendation is informational only; not a substitute for doctor consultation.
    """
    
    # Normalize report type for mapping
    report_type_lower = report_type.lower()
    mapping_key = report_type
    
    if "blood" in report_type_lower:
        mapping_key = "Blood Report"
    elif "ecg" in report_type_lower or "ekg" in report_type_lower:
        mapping_key = "ECG"
    elif "x-ray" in report_type_lower or "xray" in report_type_lower:
        mapping_key = "Chest X-ray"
    elif "mri" in report_type_lower or "ct" in report_type_lower:
        mapping_key = "MRI/CT"
        
    recommended = SPECIALTY_MAPPING.get(mapping_key, [])
    
    # Default generic recommendation if not found
    if not recommended:
        recommended = [
            {"specialty": "General Practitioner", "base_score": 80, "reasoning": "A general practitioner can help interpret initial findings and refer you to a specialist if needed."},
            {"specialty": "Internist", "base_score": 75, "reasoning": "Can provide comprehensive care and help determine the next steps."}
        ]
    
    # Score and sort
    results = []
    for rec in recommended:
        # Score based on base relevance and classifier confidence
        final_score = min(100.0, max(0.0, rec["base_score"] * classifier_confidence))
        
        results.append({
            "specialty": rec["specialty"],
            "score": round(final_score, 2),
            "reasoning": rec["reasoning"]
        })
        
    # Sort by score descending and get top 3
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:3]
    
    return {
        "report_type_input": report_type,
        "mapped_category": mapping_key,
        "recommendations": results,
        "safety_disclaimer": "Safety Check: This recommendation is informational only and is not a substitute for professional doctor consultation, medical advice, diagnosis, or treatment."
    }
