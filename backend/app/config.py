import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # MongoDB
    MONGO_URL: str = os.getenv("MONGO_URL", "")
    MONGO_DB: str = os.getenv("MONGO_DB", "notebooklm_db")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("api_key", "")
    OPENAI_BASE_URL: str = os.getenv("base_url", "https://api.openai.com/v1")
    GENERATIVE_MODEL: str = os.getenv("GENERATIVE_MODEL", "gpt-3.5-turbo")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    EMBEDDING_DIM: int = int(os.getenv("dimension", "3072"))
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-2")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    # Poppler
    POPPLER_PATH: str = os.getenv("POPPLER_PATH", "")
    
    # FAISS
    # Prefer environment override. If not set, use a path relative to the backend folder.
    # This makes it easier to move the project and keeps the index inside the repo layout.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # .../backend/app
    BACKEND_ROOT = os.path.dirname(BASE_DIR)  # .../backend
    FAISS_INDEX_PATH: str = os.getenv(
        "FAISS_INDEX_PATH",
        os.path.join(BACKEND_ROOT, "data", "faiss_index", "notebooklm.index")
    )
    FAISS_INDEX_TYPE: str = "IVF_FLAT"
    
    # Chunking
    CHUNK_SIZE: int = 300  # tokens (reduced for free API limit)
    CHUNK_OVERLAP: int = 50  # tokens
    
    # RAG
    TOP_K: int = 3  # reduced from 5 to fit 4096 token limit
    MAX_HISTORY: int = 3  # reduced from 5 to fit 4096 token limit

settings = Settings()
