# test_poppler.py
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError

pdf_path = r"C:\Users\Admin\Downloads\Quan tri hoc_Phan 3'.pdf"  # replace with a small PDF you have

try:
    images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
    print("Poppler OK: images generated =", len(images))
except PDFInfoNotInstalledError as e:
    print("Poppler not found (PDFInfoNotInstalledError):", e)
except Exception as e:
    print("Other error:", e)