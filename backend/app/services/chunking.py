import re
from typing import List, Tuple, Optional
from app.config import settings
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)
class TextChunker:
    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.overlap = overlap or settings.CHUNK_OVERLAP
        
        # Initialize LangChain's RecursiveCharacterTextSplitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size * 4,  # Convert tokens to chars (rough estimate)
            chunk_overlap=self.overlap * 4,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],  # Priority order for splitting
            is_separator_regex=False
        )
        
    def detect_heading(self, text: str) -> Optional[str]:
        """Detect if text starts with a heading."""
        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            # Check if first line is short and might be a heading
            if len(first_line) < 100 and (
                first_line.isupper() or 
                re.match(r'^(CHƯƠNG|PHẦN|MỤC|CHAPTER|SECTION)\s+\d+', first_line, re.IGNORECASE) or
                re.match(r'^\d+\.', first_line)
            ):
                return first_line
        return None
    
    def chunk_text(self, text: str, page_num: int) -> List[Tuple[str, Optional[str], int, int]]:
        """
        Chunk text using LangChain's RecursiveCharacterTextSplitter.
        Returns: List of (content, title, page_start, page_end) tuples
        """
        # Skip empty or whitespace-only text
        if not text or not text.strip():
            logger.warning(f"Page {page_num}: Empty or whitespace-only text, skipping")
            return []
        
        # Detect title from beginning of text
        title = self.detect_heading(text)
        
        # Split text into chunks using LangChain
        chunks_text = self.text_splitter.split_text(text)
        
        if not chunks_text:
            logger.warning(f"Page {page_num}: No chunks created from {len(text)} chars")
            return []
        
        # Format as tuples with metadata
        chunks = []
        for chunk_content in chunks_text:
            # Try to detect section-specific title in each chunk
            chunk_title = self.detect_heading(chunk_content) or title
            chunks.append((chunk_content, chunk_title, page_num, page_num))
        
        logger.info(f"Page {page_num}: Created {len(chunks)} chunks from {len(text)} chars")
        return chunks
    
    def chunk_document(self, pages: List[Tuple[int, str]]) -> List[Tuple[str, Optional[str], int, int]]:
        """
        Chunk entire document.
        Args: pages - List of (page_num, text) tuples
        Returns: List of (content, title, page_start, page_end) tuples
        """
        all_chunks = []
        for page_num, text in pages:
            chunks = self.chunk_text(text, page_num)
            all_chunks.extend(chunks)
        return all_chunks


chunker = TextChunker()
