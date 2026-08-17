import os
import json
import random
from faker import Faker
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

fake = Faker()
Faker.seed(42)
random.seed(42)

# Ensure GOOGLE_API_KEY is available
if not os.environ.get("GOOGLE_API_KEY"):
    print("WARNING: GOOGLE_API_KEY not found. Please set it in .env file.")
    # For testing without key, we could use HuggingFace embeddings, but let's stick to Gemini as planned.

def generate_mock_medical_documents(num_docs=40):
    documents = []
    
    specialties = ["Cardiology", "Endocrinology", "Hematology", "Neurology", "Oncology", "General Practice", "Pathology"]
    sources = ["PubMed", "WHO", "NIH", "CDC", "FDA", "New England Journal of Medicine", "Lancet"]
    
    # Core realistic content templates
    templates = [
        {
            "title": "Complete Blood Count (CBC) Reference Ranges and Interpretation",
            "specialty": "Hematology",
            "keywords": ["CBC", "Hemoglobin", "WBC", "Platelets", "Anemia", "Infection"],
            "content": "A Complete Blood Count (CBC) is a common blood test that evaluates the three major types of cells in the blood: red blood cells, white blood cells, and platelets. Normal Hemoglobin ranges for men are 13.5 to 17.5 grams per deciliter. For women, 12.0 to 15.5 grams per deciliter. Low hemoglobin indicates anemia, while elevated white blood cell (WBC) count (normal 4,500 to 11,000 WBCs per microliter) often suggests an underlying infection or inflammation."
        },
        {
            "title": "Guidelines for Management of Type 2 Diabetes",
            "specialty": "Endocrinology",
            "keywords": ["Diabetes", "HbA1c", "Glucose", "Insulin", "Metformin"],
            "content": "Type 2 diabetes management focuses on lifestyle modifications and pharmacological therapy. The target HbA1c for most non-pregnant adults is <7.0%. Fasting blood glucose targets are typically 80–130 mg/dL. Metformin is the preferred initial pharmacological agent. If HbA1c targets are not met after 3 months, additional agents such as SGLT2 inhibitors or GLP-1 receptor agonists should be considered based on cardiovascular risk factors."
        },
        {
            "title": "Lipid Panel and Cardiovascular Risk Assessment",
            "specialty": "Cardiology",
            "keywords": ["Cholesterol", "LDL", "HDL", "Triglycerides", "Atherosclerosis"],
            "content": "A standard lipid panel measures total cholesterol, LDL (low-density lipoprotein), HDL (high-density lipoprotein), and triglycerides. LDL cholesterol should ideally be less than 100 mg/dL for individuals at low risk, and less than 70 mg/dL for those with established cardiovascular disease. Elevated LDL is a primary driver of atherosclerosis. Statins remain the first-line therapy for LDL reduction."
        },
        {
            "title": "Interpretation of Thyroid Function Tests",
            "specialty": "Endocrinology",
            "keywords": ["TSH", "Free T4", "Thyroid", "Hypothyroidism", "Hyperthyroidism"],
            "content": "Thyroid-stimulating hormone (TSH) is the most sensitive test for thyroid function. Normal TSH is generally 0.4 to 4.0 mIU/L. High TSH with low Free T4 indicates primary hypothyroidism (e.g., Hashimoto's thyroiditis), requiring levothyroxine replacement. Conversely, low TSH with high Free T4 suggests primary hyperthyroidism (e.g., Graves' disease). Subclinical hypothyroidism presents with elevated TSH but normal Free T4."
        },
        {
            "title": "Basic Metabolic Panel (BMP) Clinical Significance",
            "specialty": "General Practice",
            "keywords": ["BMP", "Sodium", "Potassium", "Creatinine", "BUN", "Kidney Function"],
            "content": "The BMP includes electrolytes (Sodium, Potassium, Chloride, CO2), kidney function tests (BUN, Creatinine), and Glucose. Normal Potassium is 3.5 to 5.0 mEq/L; abnormalities can cause cardiac arrhythmias. Elevated Creatinine (normal ~0.7 to 1.3 mg/dL) and Blood Urea Nitrogen (BUN) indicate impaired renal function. GFR (Glomerular Filtration Rate) provides a more accurate measure of kidney stage."
        }
    ]
    
    # Add the core realistic templates
    for i, t in enumerate(templates):
        doc = Document(
            page_content=t["content"],
            metadata={
                "id": f"doc_{i}",
                "title": t["title"],
                "source": random.choice(sources),
                "specialty": t["specialty"],
                "keywords": ", ".join(t["keywords"])
            }
        )
        documents.append(doc)
        
    # Generate additional synthetic documents to reach num_docs
    for i in range(len(templates), num_docs):
        specialty = random.choice(specialties)
        disease = fake.word().capitalize() + " " + fake.word() + " Syndrome"
        keywords = [fake.word() for _ in range(3)] + [specialty]
        
        content = (f"Clinical overview of {disease}. It primarily affects the {fake.word()} system. "
                   f"Diagnosis involves checking {fake.word()} levels. "
                   f"Typical presentation includes {fake.word()} and {fake.word()}. "
                   f"Standard protocols recommend monitoring for {fake.word()} complications. "
                   f"Current findings suggest a strong correlation with elevated {fake.word()} markers in blood tests.")
                   
        doc = Document(
            page_content=content,
            metadata={
                "id": f"doc_{i}",
                "title": f"Clinical Guidelines: {disease}",
                "source": random.choice(sources),
                "specialty": specialty,
                "keywords": ", ".join(keywords)
            }
        )
        documents.append(doc)
        
    return documents

def main():
    print("Generating mock medical documents...")
    docs = generate_mock_medical_documents(50)
    
    print(f"Generated {len(docs)} documents. Initializing embeddings...")
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        print("Creating Qdrant index...")
        vectorstore_path = os.path.join(os.path.dirname(__file__), 'qdrant_db')
        os.makedirs(vectorstore_path, exist_ok=True)
        
        QdrantVectorStore.from_documents(
            docs,
            embeddings,
            path=vectorstore_path,
            collection_name="medical_literature",
        )
        print(f"Successfully saved Qdrant index to {vectorstore_path}")
        
    except Exception as e:
        print(f"Error during ingestion: {e}")
        print("If this is an API key error, make sure GOOGLE_API_KEY is set correctly.")

if __name__ == "__main__":
    main()
