from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pymongo import MongoClient
import json
import uuid
from datetime import datetime

from app.config import settings
from app.models.pydantic_models import MessageModel, SourceModel
from app.services.embedding import embedding_service
from app.services.faiss_service import faiss_service
from app.services.llm_service import llm_service
from app.services.conversation import conversation_service

router = APIRouter()

# MongoDB
client = MongoClient(settings.MONGO_URL)
db = client[settings.MONGO_DB]
chunks_col = db['chunks']
files_col = db['files']


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    try:
        while True:
            # Receive question
            data = await websocket.receive_text()
            message_data = json.loads(data)
            question = message_data.get("question", "")
            
            if not question:
                await websocket.send_json({"type": "error", "content": "Empty question"})
                continue
            
            # Get conversation history
            history = conversation_service.get_history(conversation_id, limit=settings.MAX_HISTORY)
            
            # Embed question
            question_embedding = embedding_service.embed_text(question)
            question_vector = embedding_service.normalize_vector(question_embedding)

            # If embedding failed or is empty, return error to client
            if question_vector.size == 0:
                await websocket.send_json({"type": "error", "content": "Embedding failed or empty"})
                continue

            # Search FAISS
            indices, scores = faiss_service.search(question_vector.tolist(), k=settings.TOP_K)

            # Guard if search returns empty
            if not indices or not scores:
                await websocket.send_json({"type": "info", "content": "No relevant contexts found"})
                indices, scores = [], []
            
            # Get chunks from MongoDB
            contexts = []
            sources = []
            
            for idx, score in zip(indices, scores):
                chunk = chunks_col.find_one({"faiss_index_id": int(idx)})
                if chunk:
                    # Get file info
                    file_doc = files_col.find_one({"file_id": chunk['file_id']})
                    filename = file_doc['filename'] if file_doc else "Unknown"
                    
                    contexts.append({
                        "content": chunk['content'],
                        "title": chunk.get('title'),
                        "page_start": chunk['page_start'],
                        "page_end": chunk['page_end'],
                        "filename": filename
                    })
                    
                    sources.append(SourceModel(
                        file_id=chunk['file_id'],
                        chunk_id=chunk['chunk_id'],
                        page_start=chunk['page_start'],
                        page_end=chunk['page_end'],
                        filename=filename
                    ))
            
            # Save user message
            user_msg = MessageModel(
                role="user",
                content=question,
                created_at=datetime.utcnow()
            )
            conversation_service.add_message(conversation_id, user_msg)
            
            # Stream answer
            full_answer = ""
            async for chunk in llm_service.answer_question_stream(question, contexts, history):
                await websocket.send_json(chunk)
                if chunk["type"] == "token":
                    full_answer += chunk["content"]
            
            # Save assistant message with sources
            assistant_msg = MessageModel(
                role="assistant",
                content=full_answer,
                created_at=datetime.utcnow(),
                sources=sources
            )
            conversation_service.add_message(conversation_id, assistant_msg)
            
            # Send sources
            await websocket.send_json({
                "type": "sources",
                "content": [s.dict() for s in sources]
            })
            
    except WebSocketDisconnect:
        print(f"Client disconnected from conversation {conversation_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "content": str(e)})
