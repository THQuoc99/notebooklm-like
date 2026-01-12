from openai import OpenAI
from typing import List
import numpy as np
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.EMBEDDING_MODEL
        self.dim = settings.EMBEDDING_DIM
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for list of texts."""
        # Validate and filter inputs
        if not texts:
            return []

        cleaned_texts = [t for t in texts if isinstance(t, str) and t.strip()]
        if not cleaned_texts:
            return []

        embeddings = []
        # Batch requests to avoid too-large payloads
        batch_size = 100
        for i in range(0, len(cleaned_texts), batch_size):
            batch = cleaned_texts[i:i+batch_size]
            try:
                logger.info(f"Requesting embeddings for batch {i}//{len(cleaned_texts)} size={len(batch)}")
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                # Response data may be a sequence of objects with .embedding
                for item in response.data:
                    embeddings.append(item.embedding)
            except Exception as e:
                logger.error(f"Embedding API error for batch starting at {i}: {e}", exc_info=True)
                raise

        return embeddings
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if not text or not isinstance(text, str):
            return []
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding API error for single text: {e}", exc_info=True)
            raise
    
    def normalize_vector(self, vector: List[float]) -> np.ndarray:
        """Normalize vector for cosine similarity (L2 normalization)."""
        vec = np.array(vector, dtype='float32')
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


embedding_service = EmbeddingService()
