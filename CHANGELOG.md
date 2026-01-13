# 📋 Changelog - NotebookLM Updates

## ✨ Các tính năng mới đã thêm (theo bổ sung.md)

### 1. 🔍 OCR Support - Xử lý PDF Scan & Hỗn hợp

**File thay đổi:** `backend/app/services/text_extract.py`

**Tính năng:**
- ✅ Tự động phát hiện loại PDF (text-based / scan / hỗn hợp)
- ✅ OCR tự động cho trang chất lượng kém
- ✅ Đánh giá chất lượng text để quyết định OCR
- ✅ Hỗ trợ cả tiếng Việt và tiếng Anh
- ✅ Extract text từ ảnh (JPG, PNG, BMP, TIFF)

**Dependencies mới:**
```
pytesseract==0.3.10
pdf2image==1.17.0
Pillow==10.2.0
```

**Cách sử dụng:**
1. Cài đặt Tesseract OCR và Poppler (xem `OCR_SETUP.md`)
2. Upload PDF scan → Hệ thống tự động OCR
3. Upload PDF hỗn hợp → OCR chọn lọc theo trang

---

### 2. 🗑️ Xóa File Background (Async Deletion)

**File thay đổi:** `backend/app/api/routes_upload.py`

**Endpoint mới:**
```http
DELETE /files/{file_id}
```

**Tính năng:**
- ✅ Xóa file không block UI
- ✅ Xóa metadata trong MongoDB
- ✅ Xóa chunks liên quan
- ✅ Xóa vectors trong FAISS (background task)
- ✅ Xóa file gốc trên S3

**Cách sử dụng:**
```python
# Frontend call
response = requests.delete(f"http://localhost:8000/files/{file_id}")
```

---

### 3. 🎯 Scoped Retrieval - Lọc nguồn theo file

**File mới:** `backend/app/services/rag_service.py`

**Tính năng:**
- ✅ Cho phép chọn file làm nguồn trả lời
- ✅ Filter chunks theo file_ids
- ✅ Tăng độ chính xác khi có nhiều tài liệu

**Cách sử dụng (WebSocket):**
```json
{
  "question": "Transformer là gì?",
  "file_ids": ["file-uuid-1", "file-uuid-2"]  // Optional
}
```

**Cách sử dụng (API):**
```python
contexts, sources = rag_service.retrieve_contexts(
    question="...",
    top_k=5,
    file_ids=["file-id-1", "file-id-2"]  # Hoặc None cho tất cả
)
```

---

### 4. 📚 Source Citations với Hover Tooltip

**Files thay đổi:**
- `backend/app/services/rag_service.py`
- `backend/app/services/llm_service.py`
- `backend/app/api/routes_ws.py`

**Tính năng:**
- ✅ Đánh số nguồn [1], [2], [3] trong câu trả lời
- ✅ Gửi citation map cho frontend
- ✅ Hỗ trợ hover tooltip (cần frontend implementation)

**Format trả lời:**
```
Transformer được giới thiệu năm 2017 [1] và đã cách mạng hóa NLP [2].
```

**WebSocket messages mới:**
```json
// Message 1: Citation map
{
  "type": "citations",
  "content": "[1] transformer.pdf - Trang 3-4\n[2] nlp_review.pdf - Trang 10"
}

// Message 2: Answer tokens (như cũ)
{
  "type": "token",
  "content": "Transformer là..."
}

// Message 3: Source details
{
  "type": "sources",
  "content": [
    {
      "file_id": "...",
      "chunk_id": "...",
      "page_start": 3,
      "page_end": 4,
      "filename": "transformer.pdf"
    }
  ]
}
```

---

### 5. 📤 Batch Upload - Upload nhiều file song song

**Endpoint đã có:** `POST /upload/batch`

**Tính năng:**
- ✅ Upload nhiều file cùng lúc
- ✅ Xử lý parallel trong background
- ✅ Trả về status từng file

**Cách sử dụng:**
```python
files = [
    ('files', open('doc1.pdf', 'rb')),
    ('files', open('doc2.pdf', 'rb')),
    ('files', open('doc3.pdf', 'rb'))
]
response = requests.post(
    "http://localhost:8000/upload/batch",
    files=files
)
```

---

## 🔄 Các thay đổi Backend API

### WebSocket `/ws/chat/{conversation_id}`

**Input message cũ:**
```json
{
  "question": "Câu hỏi của bạn"
}
```

**Input message mới (với scoped retrieval):**
```json
{
  "question": "Câu hỏi của bạn",
  "file_ids": ["file-id-1", "file-id-2"]  // Optional
}
```

**Output messages mới:**
1. `type: "citations"` - Citation map
2. `type: "token"` - Answer streaming
3. `type: "sources"` - Source details
4. `type: "done"` - Hoàn thành

---

## 📦 Dependencies Updates

**requirements.txt mới:**
```diff
+ # OCR & Image Processing
+ pytesseract==0.3.10
+ pdf2image==1.17.0
+ Pillow==10.2.0
```

**Cài đặt:**
```bash
pip install -r requirements.txt
```

**System requirements:**
- Tesseract OCR (xem `OCR_SETUP.md`)
- Poppler utils (xem `OCR_SETUP.md`)

---

## 🎨 Frontend Cần Thực Hiện

### 1. Auto Upload khi chọn file

**Hiện tại:** User chọn file → Click "Upload"
**Cần:** User chọn file → Auto upload ngay

**Implementation:**
```python
# Streamlit
uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
if uploaded_files:
    for file in uploaded_files:
        # Auto upload ngay
        upload_file(file)
```

### 2. File Selection UI (Scoped Retrieval)

**Cần thêm:**
- Checkbox để chọn files làm nguồn
- Gửi `file_ids` trong WebSocket message

**Example UI:**
```
☑ document1.pdf
☑ document2.pdf  
☐ document3.pdf
```

### 3. Source Citation Hover Tooltip

**Khi nhận WebSocket:**
```json
{
  "type": "citations",
  "content": "[1] file.pdf - Trang 3"
}
```

**Render:**
- Parse citations
- Khi hover vào [1], [2] → Hiển thị tooltip với:
  - Tên file
  - Số trang
  - Trích đoạn (từ sources)

### 4. Auto Refresh File List

**Cần:** Polling hoặc WebSocket để refresh danh sách file

**Implementation:**
```python
# Polling mỗi 5s
import time
while True:
    files = get_files_list()
    st.rerun()
    time.sleep(5)
```

---

## 🧪 Testing

### Test OCR

1. Upload PDF scan
2. Kiểm tra logs: "OCR extracted X chars from page Y"
3. Verify chunks có nội dung

### Test Scoped Retrieval

1. Upload 2 files khác topic
2. Gửi message với `file_ids` chỉ 1 file
3. Verify answer chỉ từ file đó

### Test Source Citations

1. Đặt câu hỏi
2. Kiểm tra WebSocket message có `type: "citations"`
3. Verify answer có [1], [2], [3]

### Test Delete

1. Delete 1 file
2. Verify:
   - File metadata xóa khỏi MongoDB
   - Chunks xóa
   - FAISS index giảm vectors
   - S3 file xóa

---

## 📚 Tài liệu liên quan

- [OCR_SETUP.md](../OCR_SETUP.md) - Hướng dẫn cài đặt OCR
- [bổ sung.md](../bổ sung.md) - Yêu cầu chi tiết
- [README.md](../README.md) - Tổng quan project

---

## 🚀 Next Steps

### Backend (Hoàn thành ✅)
- ✅ OCR support
- ✅ Scoped retrieval
- ✅ Source citations
- ✅ Async file deletion
- ✅ Batch upload

### Frontend (Cần thực hiện 🔜)
- 🔜 Auto upload on file select
- 🔜 File selection checkboxes (scoped retrieval)
- 🔜 Citation hover tooltips
- 🔜 Auto refresh file list
- 🔜 Delete file button với confirmation
- 🔜 UI giống NotebookLM (theo ảnh trong bổ sung.md)

---

**Last Updated:** January 13, 2026
**Version:** 2.0.0
