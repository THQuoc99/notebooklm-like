import PyPDF2
import docx
from typing import List, Tuple


def extract_text_from_pdf(file_path: str) -> List[Tuple[int, str]]:
    """Extract text from PDF with page numbers.
    Returns: List of (page_number, text) tuples
    """
    pages = []
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            pages.append((page_num + 1, text))
    return pages


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


def extract_text(file_path: str, file_type: str) -> List[Tuple[int, str]]:
    """Main extraction function. Returns list of (page_num, text) tuples."""
    if file_type.lower() == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type.lower() == "txt":
        return extract_text_from_txt(file_path)
    elif file_type.lower() in ["docx", "doc"]:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
