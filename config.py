import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing! Set it in your .env file.")
    
    # Use a currently supported Gemini model for both direct calls and Cognee.
    GEMINI_MODEL = "gemini-2.5-flash"
    
    # For Cognee's internal LLM integration, use "google"
    DEFAULT_LLM = "google"   # <-- Add this line

    # Use Gemini-native embeddings through LiteLLM instead of a local engine.
    COGNEE_EMBEDDING_PROVIDER = os.getenv("COGNEE_EMBEDDING_PROVIDER", "gemini")
    COGNEE_EMBEDDING_MODEL = os.getenv(
        "COGNEE_EMBEDDING_MODEL", "gemini/gemini-embedding-001"
    )
    
    COGNEE_VECTOR_STORE = os.getenv("COGNEE_VECTOR_STORE", "qdrant")
    COGNEE_GRAPH_STORE = os.getenv("COGNEE_GRAPH_STORE", "networkx")