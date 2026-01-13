import PyPDF2
import docx
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import logging
from typing import List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def assess_text_quality(text: str) -> dict:
    """Assess quality of extracted text to determine if OCR is needed.
    Returns: dict with quality metrics
    """
    if not text or len(text.strip()) == 0:
        return {"quality": "empty", "char_count": 0, "needs_ocr": True}
    
    char_count = len(text.strip())
    word_count = len(text.split())
    
    # Check for garbled/nonsense characters
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    special_ratio = special_chars / char_count if char_count > 0 else 0
    
    # Determine quality
    if char_count < 50:
        quality = "very_low"
        needs_ocr = True
    elif char_count < 200 or special_ratio > 0.3:
        quality = "low"
        needs_ocr = True
    elif special_ratio > 0.15:
        quality = "medium"
        needs_ocr = True
    else:
        quality = "good"
        needs_ocr = False
    
    return {
        "quality": quality,
        "char_count": char_count,
        "word_count": word_count,
        "special_ratio": special_ratio,
        "needs_ocr": needs_ocr
    }


def ocr_page_image(image: Image.Image, page_num: int) -> str:
    """Perform OCR on a single page image.
    Returns: extracted text
    """
    try:
        # Configure tesseract for better results
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, lang='vie+eng', config=custom_config)
        logger.info(f"OCR extracted {len(text)} chars from page {page_num}")
        return text
    except Exception as e:
        logger.error(f"OCR failed for page {page_num}: {e}")
        return ""


def extract_text_from_pdf(file_path: str, use_ocr: bool = True) -> List[Tuple[int, str]]:
    """Extract text from PDF with intelligent OCR fallback.
    Detects PDF type (text-based, scanned, mixed) and applies appropriate extraction.
    
    Args:
        file_path: Path to PDF file
        use_ocr: Enable OCR for scanned/low-quality pages
    
    Returns: List of (page_number, text) tuples
    """
    pages = []
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            logger.info(f"Processing PDF '{os.path.basename(file_path)}' with {total_pages} pages")
            
            # First pass: extract text with PyPDF2
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                
                try:
                    text = page.extract_text()
                except Exception as extract_err:
                    logger.error(f"Page {page_num + 1}: PyPDF2 extraction failed: {extract_err}")
                    text = ""
                
                # Assess text quality
                quality = assess_text_quality(text)
                
                if use_ocr and quality["needs_ocr"]:
                    logger.info(f"Page {page_num + 1}: Low quality text detected (quality={quality['quality']}, chars={quality['char_count']}). Applying OCR...")
                    
                    # Convert this page to image and OCR
                    try:
                        images = convert_from_path(
                            file_path,
                            first_page=page_num + 1,
                            last_page=page_num + 1,
                            dpi=300
                        )
                        
                        if images:
                            ocr_text = ocr_page_image(images[0], page_num + 1)
                            
                            # Combine parsed + OCR text
                            combined_text = text + "\n" + ocr_text if text.strip() else ocr_text
                            pages.append((page_num + 1, combined_text))
                            logger.info(f"Page {page_num + 1}: Combined text (parsed + OCR) = {len(combined_text)} chars")
                        else:
                            logger.warning(f"Page {page_num + 1}: No images generated from PDF page")
                            pages.append((page_num + 1, text))
                    except Exception as e:
                        logger.error(f"OCR failed for page {page_num + 1}: {e}. Using parsed text.")
                        pages.append((page_num + 1, text))
                else:
                    pages.append((page_num + 1, text))
                    logger.info(f"Page {page_num + 1}: Good quality text ({quality['char_count']} chars)")
            
            # Check if any page has content
            total_chars = sum(len(text) for _, text in pages)
            logger.info(f"PDF extraction complete: {len(pages)} pages processed, {total_chars} total chars")
            
            if total_chars == 0:
                logger.error(f"WARNING: PDF '{os.path.basename(file_path)}' extracted 0 characters across all pages!")
            
            return pages
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF '{os.path.basename(file_path)}': {e}")
        raise


def extract_text_from_txt(file_path: str) -> List[Tuple[int, str]]:
    """Extract text from TXT file. Returns as single page."""
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return [(1, text)]


def extract_text_from_docx(file_path: str) -> List[Tuple[int, str]]:
    """Extract text from DOCX file. Returns as single page."""
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return [(1, text)]


def extract_text_from_image(file_path: str) -> List[Tuple[int, str]]:
    """Extract text from image file using OCR.
    Returns: List with single (page_number, text) tuple
    """
    try:
        image = Image.open(file_path)
        text = ocr_page_image(image, 1)
        return [(1, text)]
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        raise


def extract_text(file_path: str, file_type: str, enable_ocr: bool = True) -> List[Tuple[int, str]]:
    """Main extraction function with OCR support.
    
    Args:
        file_path: Path to file
        file_type: File extension (pdf, txt, docx, jpg, png)
        enable_ocr: Enable OCR for PDF and images
    
    Returns: List of (page_num, text) tuples
    """
    file_type_lower = file_type.lower()
    
    if file_type_lower == "pdf":
        return extract_text_from_pdf(file_path, use_ocr=enable_ocr)
    elif file_type_lower == "txt":
        return extract_text_from_txt(file_path)
    elif file_type_lower in ["docx", "doc"]:
        return extract_text_from_docx(file_path)
    elif file_type_lower in ["jpg", "jpeg", "png", "bmp", "tiff"]:
        if enable_ocr:
            return extract_text_from_image(file_path)
        else:
            raise ValueError(f"OCR is disabled but image file provided: {file_type}")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
