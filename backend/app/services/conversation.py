from pymongo import MongoClient
from typing import List, Optional
from datetime import datetime
from app.config import settings
from app.models.pydantic_models import ConversationModel, MessageModel


class ConversationService:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URL)
        self.db = self.client[settings.MONGO_DB]
        self.conversations = self.db['conversations']
    
    def create_conversation(self, conversation_id: str) -> ConversationModel:
        """Create new conversation."""
        conversation = ConversationModel(
            conversation_id=conversation_id,
            messages=[],
            created_at=datetime.utcnow()
        )
        self.conversations.insert_one(conversation.dict())
        return conversation
    
    def add_message(self, conversation_id: str, message: MessageModel):
        """Add message to conversation."""
        # Check if conversation exists
        existing = self.get_conversation(conversation_id)
        
        if not existing:
            # Create new conversation first
            self.create_conversation(conversation_id)
        
        # Then add message
        self.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationModel]:
        """Get conversation by ID."""
        data = self.conversations.find_one({"conversation_id": conversation_id})
        if data:
            data.pop('_id', None)
            return ConversationModel(**data)
        return None
    
    def get_history(self, conversation_id: str, limit: int = None) -> List[MessageModel]:
        """Get conversation history."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            messages = conversation.messages
            if limit:
                return messages[-limit:]
            return messages
        return []
    
    def list_conversations(self, limit: int = 10) -> List[ConversationModel]:
        """List recent conversations."""
        cursor = self.conversations.find().sort("created_at", -1).limit(limit)
        conversations = []
        for data in cursor:
            data.pop('_id', None)
            conversations.append(ConversationModel(**data))
        return conversations


conversation_service = ConversationService()
