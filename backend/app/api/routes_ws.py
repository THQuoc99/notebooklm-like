from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pymongo import MongoClient
import json
import uuid
from datetime import datetime
from typing import Optional, List

from app.config import settings
from app.models.pydantic_models import MessageModel, SourceModel
from app.services.embedding import embedding_service
from app.services.faiss_service import faiss_service
from app.services.llm_service import llm_service
from app.services.conversation import conversation_service
from app.services.rag_service import rag_service

router = APIRouter()

# MongoDB
client = MongoClient(settings.MONGO_URL)
db = client[settings.MONGO_DB]
chunks_col = db['chunks']
files_col = db['files']


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat with source citations."""
    await websocket.accept()
    
    try:
        while True:
            # Receive question
            data = await websocket.receive_text()
            message_data = json.loads(data)
            question = message_data.get("question", "")
            file_ids = message_data.get("file_ids")  # Optional: scoped retrieval
            
            if not question:
                await websocket.send_json({"type": "error", "content": "Empty question"})
                continue
            
            # Get conversation history
            history = conversation_service.get_history(conversation_id, limit=settings.MAX_HISTORY)
            
            # Retrieve contexts with scoped retrieval support
            contexts, sources = rag_service.retrieve_contexts(
                question=question,
                top_k=settings.TOP_K,
                file_ids=file_ids  # Can be None for all files, or list of file_ids
            )
            
            if not contexts:
                await websocket.send_json({
                    "type": "info", 
                    "content": "Không tìm thấy thông tin liên quan trong tài liệu"
                })
                continue
            
            # Format contexts with citation numbers [1], [2], etc.
            contexts_with_citations, citation_map = rag_service.format_contexts_with_citations(contexts)
            
            # Send citation map to client first
            await websocket.send_json({
                "type": "citations",
                "content": citation_map
            })
            
            # Save user message
            user_msg = MessageModel(
                role="user",
                content=question,
                created_at=datetime.utcnow()
            )
            conversation_service.add_message(conversation_id, user_msg)
            
            # Stream answer with citations
            full_answer = ""
            async for chunk in llm_service.answer_question_stream(question, contexts_with_citations, history):
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
            
            # Send sources detail for hover tooltips
            await websocket.send_json({
                "type": "sources",
                "content": [s.dict() for s in sources]
            })
            
    except WebSocketDisconnect:
        print(f"Client disconnected from conversation {conversation_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "content": str(e)})
            
    except WebSocketDisconnect:
        print(f"Client disconnected from conversation {conversation_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "content": str(e)})
