"""
RAG Service with scoped retrieval and source citation support.
"""
from typing import List, Optional, Tuple, Dict
from pymongo import MongoClient
import logging

from app.config import settings
from app.services.embedding import embedding_service
from app.services.faiss_service import faiss_service
from app.models.pydantic_models import SourceModel

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URL)
        self.db = self.client[settings.MONGO_DB]
        self.chunks_col = self.db['chunks']
        self.files_col = self.db['files']
    
    def retrieve_contexts(
        self, 
        question: str, 
        top_k: int = 5,
        file_ids: Optional[List[str]] = None
    ) -> Tuple[List[Dict], List[SourceModel]]:
        """
        Retrieve relevant contexts with optional file filtering (scoped retrieval).
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve
            file_ids: Optional list of file IDs to restrict search (scoped retrieval)
        
        Returns:
            Tuple of (contexts, sources) where:
            - contexts: List of dicts with content, title, page info, filename
            - sources: List of SourceModel for citation tracking
        """
        # Generate query embedding
        query_embedding = embedding_service.embed_texts([question])[0]
        
        # Search FAISS (if scoped, search more to allow filtering)
        search_k = top_k * 10 if file_ids else top_k
        faiss_indices, scores = faiss_service.search(query_embedding, k=search_k)
        
        # Get chunks from MongoDB
        chunks_cursor = self.chunks_col.find({
            "faiss_index_id": {"$in": faiss_indices}
        })
        
        # Build lookup dict
        chunks_by_faiss_id = {}
        for chunk in chunks_cursor:
            chunks_by_faiss_id[chunk['faiss_index_id']] = chunk
        
        # Build contexts in relevance order
        contexts = []
        sources = []
        
        for faiss_id, score in zip(faiss_indices, scores):
            if faiss_id not in chunks_by_faiss_id:
                continue
            
            chunk = chunks_by_faiss_id[faiss_id]
            
            # Apply file filter if specified (scoped retrieval)
            if file_ids and chunk['file_id'] not in file_ids:
                continue
            
            # Get filename
            file_doc = self.files_col.find_one({"file_id": chunk['file_id']})
            filename = file_doc['filename'] if file_doc else "Unknown"
            
            # Build context
            context = {
                "content": chunk['content'],
                "title": chunk.get('title'),
                "page_start": chunk['page_start'],
                "page_end": chunk['page_end'],
                "filename": filename,
                "score": float(score)
            }
            contexts.append(context)
            
            # Build source
            source = SourceModel(
                file_id=chunk['file_id'],
                chunk_id=chunk['chunk_id'],
                page_start=chunk['page_start'],
                page_end=chunk['page_end'],
                filename=filename,
                title=chunk.get('title'),
                content=chunk.get('content')  # For hover tooltip
            )
            sources.append(source)
            
            # Stop when we have enough
            if len(contexts) >= top_k:
                break
        
        logger.info(f"Retrieved {len(contexts)} contexts (scoped: {file_ids is not None})")
        return contexts, sources
    
    def format_contexts_with_citations(self, contexts: List[Dict]) -> Tuple[List[Dict], str]:
        """
        Format contexts with citation numbers [1], [2], etc.
        
        Args:
            contexts: List of context dicts
        
        Returns:
            Tuple of (contexts_with_citations, citation_map_text)
        """
        citation_map = []
        contexts_with_citations = []
        
        for i, ctx in enumerate(contexts):
            citation_num = i + 1
            filename = ctx.get('filename', 'Unknown')
            page_start = ctx.get('page_start')
            page_end = ctx.get('page_end')
            
            # Format page label
            if page_start is None and page_end is None:
                page_label = ""
            elif page_end is None or str(page_start) == str(page_end):
                page_label = f"Trang {page_start}"
            else:
                page_label = f"Trang {page_start}-{page_end}"
            
            # Citation header
            citation_text = f"[{citation_num}] {filename}"
            if page_label:
                citation_text += f" - {page_label}"
            
            citation_map.append(citation_text)
            
            # Add citation number to context
            ctx_with_citation = ctx.copy()
            ctx_with_citation['citation_number'] = citation_num
            contexts_with_citations.append(ctx_with_citation)
        
        citation_map_text = "\n".join(citation_map)
        return contexts_with_citations, citation_map_text


rag_service = RAGService()
