import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# Global state for vectorstore to avoid re-initializing
_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        qdrant_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'qdrant_db')
        client = QdrantClient(path=qdrant_path)
        _vectorstore = QdrantVectorStore(
            client=client,
            collection_name="medical_literature",
            embedding=embeddings
        )
    return _vectorstore

def process_chat_message(report, message, history):
    """
    Processes a chat message using RAG and a Medical Report's context.
    - report: MedicalReport model instance
    - message: str (user's question)
    - history: list of dicts [{"role": "user"|"assistant", "content": "..."}]
    """
    # 1. Retrieve related documents from Qdrant
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(message)
    
    # 2. Format context from documents
    context_text = "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')} ({doc.metadata.get('title', 'Untitled')})\n{doc.page_content}" for doc in docs])
    
    # 3. Format report details
    report_context = ""
    if report.extracted_data:
        report_context = f"Patient Report Extracted Data:\n{json.dumps(report.extracted_data, indent=2)}"
    
    # 4. Construct System Prompt (SAFETY CRITICAL)
    system_prompt = f"""You are a helpful, empathetic, and knowledgeable AI medical assistant interacting with a patient about their medical report.

CRITICAL SAFETY RULES:
1. NEVER diagnose the patient.
2. NEVER prescribe treatments or medications.
3. ALWAYS remind the user to 'Consult your doctor' or a healthcare professional for medical advice.
4. Block dangerous queries (e.g., self-harm, instructions to create dangerous substances). If asked, refuse to answer and suggest seeking immediate emergency help.
5. Base your answers on the provided Medical Literature and Patient Report Extracted Data.
6. When using information from the Medical Literature, CITE YOUR SOURCES inline using the source names provided.
7. Maintain a professional and reassuring tone.

{report_context}

MEDICAL LITERATURE (Context):
{context_text}
"""
    
    # 5. Prepare conversation history for LangChain
    messages = [SystemMessage(content=system_prompt)]
    
    for msg in history[-10:]: # Keep last 10 turns
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content", "")))
            
    messages.append(HumanMessage(content=message))
    
    # 6. Call LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv('GOOGLE_API_KEY'), temperature=0.2)
    response = llm.invoke(messages)
    
    return response.content
