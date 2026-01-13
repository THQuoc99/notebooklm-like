from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# files collection
class FileModel(BaseModel):
    file_id: str
    filename: str
    file_type: str
    s3_path: str
    size: int
    status: str  # uploaded | processing | indexed | failed
    created_at: datetime
    total_page: int = 0  # Default to 0, updated after processing

# chunks collection
class ChunkModel(BaseModel):
    chunk_id: str
    file_id: str
    title: Optional[str]
    content: str
    page_start: int
    page_end: int
    faiss_index_id: int
    embedding_dim: int
    created_at: datetime

# conversations collection
class SourceModel(BaseModel):
    file_id: str
    chunk_id: str
    page_start: int
    page_end: int
    filename: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None  # For hover tooltip display

class MessageModel(BaseModel):
    role: str  # user | assistant
    content: str
    created_at: datetime
    sources: Optional[List[SourceModel]] = None

class ConversationModel(BaseModel):
    conversation_id: str
    messages: List[MessageModel]
    created_at: datetime

# faiss_meta collection
class FaissMetaModel(BaseModel):
    index_name: str
    index_type: str
    embedding_dim: int
    total_vectors: int
    faiss_file_path: str
    last_updated: datetime
