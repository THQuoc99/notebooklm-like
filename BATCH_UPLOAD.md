# Batch Upload Feature - Hướng dẫn

## 🎯 Tính năng Upload nhiều file song song

Hệ thống đã được nâng cấp để hỗ trợ upload nhiều file cùng lúc với background processing.

## ✨ Điểm nổi bật

### 1. Upload nhiều file cùng lúc
- Chọn nhiều file PDF, TXT, DOCX cùng lúc
- Upload tất cả trong 1 request
- Không bị giới hạn số lượng file

### 2. Background Processing
- File được xử lý ở background
- Không block UI khi đang index
- Có thể tiếp tục chat trong lúc upload

### 3. Real-time Status
- Theo dõi status từng file: `processing`, `indexed`, `failed`
- Button Refresh để cập nhật danh sách
- Hiển thị số chunks đã tạo

## 🚀 Cách sử dụng

### Trong Streamlit UI:

1. **Chọn nhiều file:**
   - Click vào file uploader
   - Giữ `Ctrl` (Windows) hoặc `Cmd` (Mac) và click chọn nhiều file
   - Hoặc chọn tất cả file trong 1 folder

2. **Upload:**
   - Click "🚀 Upload & Index All"
   - Hệ thống sẽ upload tất cả file
   - Hiển thị progress và status từng file

3. **Theo dõi tiến trình:**
   - File hiển thị status `⏳ processing`
   - Click "🔄 Refresh" để cập nhật
   - Sau vài giây status chuyển thành `✅ indexed`

4. **Chat với tài liệu:**
   - Có thể chat ngay khi 1 số file đã indexed
   - Không cần đợi tất cả file xong

## 📡 API Usage

### Batch Upload API

**Endpoint:** `POST /upload/batch`

**Request:**
```bash
curl -X POST http://localhost:8000/upload/batch \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "files=@document3.txt"
```

**Response:**
```json
{
  "total": 3,
  "results": [
    {
      "file_id": "uuid-1",
      "filename": "document1.pdf",
      "status": "processing",
      "message": "File uploaded, processing in background"
    },
    {
      "file_id": "uuid-2",
      "filename": "document2.pdf",
      "status": "processing",
      "message": "File uploaded, processing in background"
    },
    {
      "file_id": "uuid-3",
      "filename": "document3.txt",
      "status": "processing",
      "message": "File uploaded, processing in background"
    }
  ]
}
```

### Kiểm tra status

**Endpoint:** `GET /files`

```bash
curl http://localhost:8000/files
```

**Response:**
```json
{
  "files": [
    {
      "file_id": "uuid-1",
      "filename": "document1.pdf",
      "status": "indexed",
      "chunks_count": 45
    },
    {
      "file_id": "uuid-2",
      "filename": "document2.pdf",
      "status": "processing"
    }
  ]
}
```

## 🔧 Technical Details

### Backend Processing Flow

1. **Upload Phase:**
   - Client gửi nhiều file
   - Server nhận và save to S3 ngay
   - Trả về response với status `processing`

2. **Background Processing:**
   - Extract text từ file
   - Chunking thông minh
   - Generate embeddings (OpenAI)
   - Add to FAISS index
   - Save chunks to MongoDB
   - Update status thành `indexed`

3. **Error Handling:**
   - Nếu file lỗi → status = `failed`
   - Lưu error message vào DB
   - Các file khác vẫn tiếp tục xử lý

### Database Status Flow

```
uploaded → processing → indexed
                      ↘ failed (nếu có lỗi)
```

## ⚡ Performance Tips

### Tối ưu upload nhiều file:

1. **Số lượng file:**
   - Khuyến nghị: 5-10 files/batch
   - Maximum: Không giới hạn nhưng nên chia nhỏ

2. **Kích thước file:**
   - PDF: < 50MB mỗi file
   - TXT/DOCX: < 10MB mỗi file

3. **Theo dõi tiến trình:**
   - Refresh mỗi 10-15 giây
   - Hoặc dùng GraphQL subscription (future)

## 🔍 Troubleshooting

### File bị stuck ở "processing"
```bash
# Kiểm tra logs backend
# File có thể đang được xử lý hoặc gặp lỗi

# Check file detail
curl http://localhost:8000/files/{file_id}
```

### Upload nhiều file bị timeout
- Giảm số lượng file mỗi batch
- Tăng timeout setting trong requests
- Upload từng batch nhỏ hơn

### FAISS index bị corrupt
```bash
# Delete index và rebuild
cd D:\Dự án TT\notebooklm\data\faiss_index
del notebooklm.index

# Restart backend để tạo index mới
```

## 📊 Monitoring

### Kiểm tra FAISS stats

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "faiss": {
    "total_vectors": 1250,
    "dimension": 3072,
    "is_trained": true
  },
  "db": "connected"
}
```

## 🎨 UI Features

### Streamlit Interface:

- ✅ Multiple file selector
- ✅ Progress indicator
- ✅ Status badges (✅ indexed, ⏳ processing, ❌ failed)
- ✅ Refresh button
- ✅ Chunks count display
- ✅ Error messages

## 🚀 Future Enhancements

- [ ] WebSocket real-time status updates
- [ ] Progress percentage per file
- [ ] Pause/Resume processing
- [ ] Priority queue
- [ ] Parallel processing (multiple workers)
- [ ] File preview before upload
- [ ] Drag & drop upload

---

**Note:** Background processing giúp UI luôn responsive, người dùng có thể chat ngay cả khi đang upload file mới.
