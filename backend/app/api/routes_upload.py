from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pymongo import MongoClient
from typing import List
import uuid
import os
import tempfile
from datetime import datetime
import asyncio
import logging

from app.config import settings
from app.models.pydantic_models import FileModel, ChunkModel
from app.services.s3_service import s3_service
from app.services.text_extract import extract_text
from app.services.chunking import chunker
from app.services.embedding import embedding_service
from app.services.faiss_service import faiss_service

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB
client = MongoClient(settings.MONGO_URL)
db = client[settings.MONGO_DB]
files_col = db['files']
chunks_col = db['chunks']


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file and process it."""
    try:
        # Generate file ID
        file_id = str(uuid.uuid4())
        file_type = file.filename.split('.')[-1].lower()
        
        # Save to temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Upload to S3
        s3_key = f"uploads/{file_id}/{file.filename}"
        s3_path = s3_service.upload_local_file(temp_path, s3_key)
        
        # Save file metadata
        file_model = FileModel(
            file_id=file_id,
            filename=file.filename,
            file_type=file_type,
            s3_path=s3_path,
            size=len(content),
            status="uploaded",
            created_at=datetime.utcnow(),
            total_page=0
        )
        files_col.insert_one(file_model.dict())
        
        # Update status to processing
        files_col.update_one(
            {"file_id": file_id},
            {"$set": {"status": "processing"}}
        )
        
        # Extract text
        pages = extract_text(temp_path, file_type)
        
        # Chunk text
        chunks = chunker.chunk_document(pages)
        
        # Generate embeddings
        chunk_texts = [chunk[0] for chunk in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)
        
        # Add to FAISS
        faiss_ids = faiss_service.add_vectors(embeddings)
        
        # Save chunks to MongoDB
        chunk_models = []
        for i, (content, title, page_start, page_end) in enumerate(chunks):
            chunk_model = ChunkModel(
                chunk_id=str(uuid.uuid4()),
                file_id=file_id,
                title=title,
                content=content,
                page_start=page_start,
                page_end=page_end,
                faiss_index_id=faiss_ids[i],
                embedding_dim=settings.EMBEDDING_DIM,
                created_at=datetime.utcnow()
            )
            chunk_models.append(chunk_model.dict())
        
        chunks_col.insert_many(chunk_models)
        
        # Save FAISS index
        faiss_service.save()
        
        # Update status to indexed
        files_col.update_one(
            {"file_id": file_id},
            {"$set": {"status": "indexed","total_page": len(pages)}}
        )
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "status": "indexed",
            "chunks_count": len(chunk_models)
        }
        
    except Exception as e:
        # Update status to failed
        if 'file_id' in locals():
            files_col.update_one(
                {"file_id": file_id},
                {"$set": {"status": "failed", "error": str(e)}}
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def list_files():
    """List all uploaded files."""
    cursor = files_col.find().sort("created_at", -1)
    files = []
    for doc in cursor:
        doc.pop('_id', None)
        files.append(doc)
    return {"files": files}


@router.get("/files/{file_id}")
async def get_file(file_id: str):
    """Get file details."""
    file_doc = files_col.find_one({"file_id": file_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_doc.pop('_id', None)
    
    # Get chunk count
    chunk_count = chunks_col.count_documents({"file_id": file_id})
    file_doc['chunks_count'] = chunk_count
    
    return file_doc


def process_file_background(file_id: str, temp_path: str, filename: str, file_type: str, s3_path: str, file_size: int):
    """Background task to process file."""
    try:
        logger.info(f"Processing file {file_id}: {filename}")
        
        # Extract text
        logger.info(f"Extracting text from {filename}")
        pages = extract_text(temp_path, file_type)
        logger.info(f"Extracted {len(pages)} pages")
        
        # Chunk text
        logger.info(f"Chunking document {filename}")
        chunks = chunker.chunk_document(pages)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        chunk_texts = [chunk[0] for chunk in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Add to FAISS
        logger.info(f"Adding {len(embeddings)} vectors to FAISS")
        faiss_ids = faiss_service.add_vectors(embeddings)
        logger.info(f"Added vectors with IDs: {faiss_ids[:5] if len(faiss_ids) > 0 else []}")
        
        # Save chunks to MongoDB
        chunk_models = []
        for i, (content, title, page_start, page_end) in enumerate(chunks):
            chunk_model = ChunkModel(
                chunk_id=str(uuid.uuid4()),
                file_id=file_id,
                title=title,
                content=content,
                page_start=page_start,
                page_end=page_end,
                faiss_index_id=faiss_ids[i],
                embedding_dim=settings.EMBEDDING_DIM,
                created_at=datetime.utcnow()
            )
            chunk_models.append(chunk_model.dict())
        
        logger.info(f"Saving {len(chunk_models)} chunks to MongoDB")
        chunks_col.insert_many(chunk_models)
        
        # Save FAISS index
        logger.info("Saving FAISS index")
        faiss_service.save()
        
        # Update status to indexed
        files_col.update_one(
            {"file_id": file_id},
            {"$set": {"status": "indexed", "chunks_count": len(chunk_models)}}
        )
        
        logger.info(f"File {filename} processed successfully: {len(chunk_models)} chunks")
        
        # Clean up temp file
        os.unlink(temp_path)
        
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}", exc_info=True)
        # Update status to failed
        files_col.update_one(
            {"file_id": file_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/upload/batch")
async def upload_files_batch(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    """Upload multiple files and process them in background."""
    results = []
    
    for file in files:
        try:
            # Generate file ID
            file_id = str(uuid.uuid4())
            file_type = file.filename.split('.')[-1].lower()
            
            # Save to temp file first
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            # Upload to S3
            s3_key = f"uploads/{file_id}/{file.filename}"
            s3_path = s3_service.upload_local_file(temp_path, s3_key)
            
            # Save file metadata
            file_model = FileModel(
                file_id=file_id,
                filename=file.filename,
                file_type=file_type,
                s3_path=s3_path,
                size=len(content),
                status="processing",
                created_at=datetime.utcnow()
            )
            files_col.insert_one(file_model.dict())
            
            # Add background task for processing
            if background_tasks:
                background_tasks.add_task(
                    process_file_background,
                    file_id, temp_path, file.filename, file_type, s3_path, len(content)
                )
            
            results.append({
                "file_id": file_id,
                "filename": file.filename,
                "status": "processing",
                "message": "File uploaded, processing in background"
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "results": results
    }


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, background_tasks: BackgroundTasks):
    """Delete file and all associated data including FAISS vectors."""
    try:
        # Check if file exists
        file_doc = files_col.find_one({"file_id": file_id})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get all chunk IDs and their FAISS index IDs before deleting
        chunks_cursor = chunks_col.find({"file_id": file_id})
        faiss_ids = []
        chunk_count = 0
        for chunk in chunks_cursor:
            if "faiss_index_id" in chunk:
                faiss_ids.append(chunk["faiss_index_id"])
            chunk_count += 1
        
        logger.info(f"Found {chunk_count} chunks with {len(faiss_ids)} FAISS IDs to remove")
        
        # Delete from S3
        try:
            s3_service.delete_file(file_doc['s3_path'])
            logger.info(f"Deleted S3 file: {file_doc['s3_path']}")
        except Exception as e:
            logger.warning(f"Failed to delete S3 file: {str(e)}")
        
        # Delete chunks from MongoDB
        chunks_result = chunks_col.delete_many({"file_id": file_id})
        logger.info(f"Deleted {chunks_result.deleted_count} chunks from MongoDB")
        
        # Delete file metadata
        files_col.delete_one({"file_id": file_id})
        logger.info(f"Deleted file metadata for {file_id}")
        
        # Remove vectors from FAISS in background
        if faiss_ids:
            background_tasks.add_task(_remove_faiss_vectors_background, faiss_ids, file_doc['filename'])
        
        return {
            "message": "File deleted successfully",
            "file_id": file_id,
            "filename": file_doc['filename'],
            "chunks_deleted": chunks_result.deleted_count,
            "faiss_ids_to_remove": len(faiss_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _remove_faiss_vectors_background(faiss_ids: List[int], filename: str):
    """Background task to remove FAISS vectors after file deletion."""
    try:
        logger.info(f"Removing {len(faiss_ids)} FAISS vectors for file: {filename}")
        removed_count = faiss_service.remove_ids(faiss_ids)
        logger.info(f"Successfully removed {removed_count} vectors from FAISS")
        
        # Save updated index
        faiss_service.save()
        logger.info(f"FAISS index saved after removing vectors for {filename}")
    except Exception as e:
        logger.error(f"Failed to remove FAISS vectors for {filename}: {e}", exc_info=True)


@router.get("/health")
async def health():
    """Health check."""
    faiss_stats = faiss_service.get_stats()
    return {
        "status": "ok",
        "faiss": faiss_stats,
        "db": "connected"
    }
