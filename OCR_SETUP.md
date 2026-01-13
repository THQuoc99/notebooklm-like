# Hướng dẫn cài đặt OCR cho NotebookLM

Hệ thống NotebookLM đã được nâng cấp để hỗ trợ OCR (Optical Character Recognition) cho PDF scan và PDF hỗn hợp (text + image). Tài liệu này hướng dẫn cài đặt các dependencies cần thiết.

---

## 📋 Yêu cầu hệ thống

### Windows

- Python 3.8+
- Tesseract OCR
- Poppler (cho pdf2image)

### Linux (Ubuntu/Debian)

- Python 3.8+
- tesseract-ocr
- poppler-utils

### macOS

- Python 3.8+
- Tesseract (via Homebrew)
- Poppler (via Homebrew)

---

## 🔧 Cài đặt chi tiết

### 1. Windows

#### Bước 1: Cài đặt Tesseract OCR

1. **Download Tesseract installer:**
   - Truy cập: https://github.com/UB-Mannheim/tesseract/wiki
   - Tải bản mới nhất (ví dụ: `tesseract-ocr-w64-setup-5.3.3.exe`)

2. **Cài đặt:**
   - Chạy installer
   - **QUAN TRỌNG**: Chọn "Additional language data" → Chọn `vie` (Tiếng Việt) và `eng` (English)
   - Ghi nhớ đường dẫn cài đặt (thường là `C:\Program Files\Tesseract-OCR`)

3. **Thêm vào PATH:**
   ```cmd
   setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
   ```

4. **Kiểm tra:**
   ```cmd
   tesseract --version
   ```

#### Bước 2: Cài đặt Poppler

1. **Download Poppler:**
   - Truy cập: https://github.com/oschwartz10612/poppler-windows/releases/
   - Tải bản mới nhất (ví dụ: `Release-23.11.0-0.zip`)

2. **Giải nén:**
   - Giải nén vào `C:\poppler` (hoặc thư mục bạn chọn)
   - Đảm bảo có folder `bin` bên trong chứa `pdftoppm.exe`

3. **Thêm vào PATH:**
   ```cmd
   setx PATH "%PATH%;C:\poppler\Library\bin"
   ```

4. **Kiểm tra:**
   ```cmd
   pdftoppm -h
   ```

#### Bước 3: Cài Python packages

```cmd
cd "d:\Dự án TT\notebooklm\backend"
pip install -r requirements.txt
```

---

### 2. Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Cài Tesseract với ngôn ngữ Việt và English
sudo apt install -y tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng

# Cài Poppler
sudo apt install -y poppler-utils

# Kiểm tra
tesseract --version
pdftoppm -h

# Cài Python packages
cd ~/notebooklm/backend
pip install -r requirements.txt
```

---

### 3. macOS

```bash
# Cài Homebrew (nếu chưa có)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Cài Tesseract
brew install tesseract

# Cài ngôn ngữ Việt
brew install tesseract-lang

# Cài Poppler
brew install poppler

# Kiểm tra
tesseract --version
pdftoppm -h

# Cài Python packages
cd ~/notebooklm/backend
pip install -r requirements.txt
```

---

## 🧪 Kiểm tra cài đặt

### Test Tesseract

Tạo file `test_ocr.py`:

```python
import pytesseract
from PIL import Image

# Test cơ bản
print("Tesseract version:", pytesseract.get_tesseract_version())

# Test với ảnh (nếu có)
# image = Image.open("test.png")
# text = pytesseract.image_to_string(image, lang='vie+eng')
# print("Extracted text:", text)
```

Chạy:
```bash
python test_ocr.py
```

### Test PDF2Image

Tạo file `test_pdf2image.py`:

```python
from pdf2image import convert_from_path

# Test với PDF (thay đường dẫn phù hợp)
# images = convert_from_path('test.pdf', dpi=300)
# print(f"Converted {len(images)} pages")
# images[0].save('page_1.png')

print("pdf2image imported successfully!")
```

---

## 🚀 Sử dụng

Sau khi cài đặt thành công, hệ thống tự động:

1. **Phát hiện PDF text-based**: Chỉ extract text thông thường
2. **Phát hiện PDF scan**: Tự động OCR toàn bộ
3. **Phát hiện PDF hỗn hợp**: OCR chọn lọc cho các trang chất lượng kém

### Tắt OCR (nếu cần)

Trong `text_extract.py`, set `use_ocr=False`:

```python
# Tắt OCR cho PDF
pages = extract_text_from_pdf(file_path, use_ocr=False)
```

---

## ⚙️ Cấu hình nâng cao

### Tùy chỉnh Tesseract config

Trong [text_extract.py](backend/app/services/text_extract.py):

```python
# Thay đổi config OCR
custom_config = r'--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
text = pytesseract.image_to_string(image, lang='vie+eng', config=custom_config)
```

**PSM modes:**
- `3`: Fully automatic page segmentation (default)
- `6`: Uniform block of text
- `11`: Sparse text
- `12`: Sparse text with OSD

### Tăng DPI cho chất lượng OCR tốt hơn

```python
images = convert_from_path(file_path, dpi=600)  # Tăng từ 300 lên 600
```

**Lưu ý**: DPI cao hơn = xử lý chậm hơn nhưng chính xác hơn.

---

## ❓ Troubleshooting

### Lỗi: `TesseractNotFoundError`

**Windows:**
```cmd
# Set TESSDATA_PREFIX
setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata"
```

**Linux/macOS:**
```bash
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
```

### Lỗi: `Unable to get page count. Is poppler installed?`

- **Windows**: Kiểm tra PATH có chứa `poppler/Library/bin`
- **Linux**: `sudo apt install poppler-utils`
- **macOS**: `brew install poppler`

### OCR chậm hoặc out of memory

1. Giảm DPI xuống 150-200
2. Xử lý từng trang thay vì toàn bộ document
3. Cân nhắc dùng multiprocessing

---

## 📚 Tài liệu tham khảo

- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
- pytesseract: https://pypi.org/project/pytesseract/
- pdf2image: https://pypi.org/project/pdf2image/
- Poppler: https://poppler.freedesktop.org/

---

## 🎯 Kết luận

Sau khi cài đặt xong:
- ✅ Hệ thống tự động phát hiện loại PDF
- ✅ OCR chỉ áp dụng khi cần thiết
- ✅ Hỗ trợ cả tiếng Việt và tiếng Anh
- ✅ Extract text từ ảnh JPG/PNG

**Next steps**: Chạy `run_backend.bat` và test upload PDF scan!
