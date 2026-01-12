import strawberry
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient

from app.config import settings

# MongoDB
client = MongoClient(settings.MONGO_URL)
db = client[settings.MONGO_DB]
files_col = db['files']
chunks_col = db['chunks']
conversations_col = db['conversations']


@strawberry.type
class File:
    file_id: str
    filename: str
    file_type: str
    s3_path: str
    size: int
    status: str
    created_at: str


@strawberry.type
class Source:
    file_id: str
    chunk_id: str
    page_start: int
    page_end: int
    filename: Optional[str] = None


@strawberry.type
class Message:
    role: str
    content: str
    created_at: str
    sources: Optional[List[Source]] = None


@strawberry.type
class Conversation:
    conversation_id: str
    messages: List[Message]
    created_at: str


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, GraphQL for NotebookLM"
    
    @strawberry.field
    def files(self) -> List[File]:
        """Get all files."""
        cursor = files_col.find().sort("created_at", -1)
        files = []
        for doc in cursor:
            files.append(File(
                file_id=doc['file_id'],
                filename=doc['filename'],
                file_type=doc['file_type'],
                s3_path=doc['s3_path'],
                size=doc['size'],
                status=doc['status'],
                created_at=doc['created_at'].isoformat()
            ))
        return files
    
    @strawberry.field
    def file(self, file_id: str) -> Optional[File]:
        """Get specific file."""
        doc = files_col.find_one({"file_id": file_id})
        if doc:
            return File(
                file_id=doc['file_id'],
                filename=doc['filename'],
                file_type=doc['file_type'],
                s3_path=doc['s3_path'],
                size=doc['size'],
                status=doc['status'],
                created_at=doc['created_at'].isoformat()
            )
        return None
    
    @strawberry.field
    def conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        doc = conversations_col.find_one({"conversation_id": conversation_id})
        if doc:
            messages = []
            for msg in doc.get('messages', []):
                sources = None
                if msg.get('sources'):
                    sources = [
                        Source(
                            file_id=s['file_id'],
                            chunk_id=s['chunk_id'],
                            page_start=s['page_start'],
                            page_end=s['page_end'],
                            filename=s.get('filename')
                        )
                        for s in msg['sources']
                    ]
                
                messages.append(Message(
                    role=msg['role'],
                    content=msg['content'],
                    created_at=msg['created_at'].isoformat(),
                    sources=sources
                ))
            
            return Conversation(
                conversation_id=doc['conversation_id'],
                messages=messages,
                created_at=doc['created_at'].isoformat()
            )
        return None
    
    @strawberry.field
    def conversations(self, limit: int = 10) -> List[Conversation]:
        """List recent conversations."""
        cursor = conversations_col.find().sort("created_at", -1).limit(limit)
        conversations = []
        for doc in cursor:
            messages = []
            for msg in doc.get('messages', []):
                sources = None
                if msg.get('sources'):
                    sources = [
                        Source(
                            file_id=s['file_id'],
                            chunk_id=s['chunk_id'],
                            page_start=s['page_start'],
                            page_end=s['page_end'],
                            filename=s.get('filename')
                        )
                        for s in msg['sources']
                    ]
                
                messages.append(Message(
                    role=msg['role'],
                    content=msg['content'],
                    created_at=msg['created_at'].isoformat(),
                    sources=sources
                ))
            
            conversations.append(Conversation(
                conversation_id=doc['conversation_id'],
                messages=messages,
                created_at=doc['created_at'].isoformat()
            ))
        
        return conversations


schema = strawberry.Schema(query=Query)
