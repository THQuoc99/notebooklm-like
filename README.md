# NotebookLM-like MVP

Dự án NotebookLM-like MVP - Hệ thống hỏi đáp thông minh dựa trên tài liệu với RAG (Retrieval-Augmented Generation).

## 🎯 Tính năng

- ✅ Upload tài liệu (PDF, TXT, DOCX)
- ✅ **Upload nhiều file song song (Batch Upload)**
- ✅ **Background processing** - Xử lý file không block UI
- ✅ Trích xuất và chunking thông minh
- ✅ Vector embedding với OpenAI
- ✅ FAISS vector search
- ✅ Real-time streaming chat
- ✅ Trích dẫn nguồn (file + page)
- ✅ GraphQL API

## 🏗️ Tech Stack

**Backend:**
- FastAPI (REST + WebSocket)
- Strawberry GraphQL
- MongoDB (metadata storage)
- FAISS (vector search)
- AWS S3 (file storage)
- OpenAI API (embedding + chat)

**Frontend:**
- Streamlit
- WebSocket client

## 📁 Cấu trúc dự án

```
notebooklm/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configuration
│   │   ├── utils.py             # Utilities
│   │   ├── api/
│   │   │   ├── routes_upload.py # Upload & indexing
│   │   │   └── routes_ws.py     # WebSocket chat
│   │   ├── graphql/
│   │   │   └── schema.py        # GraphQL schema
│   │   ├── models/
│   │   │   └── pydantic_models.py
│   │   └── services/
│   │       ├── s3_service.py    # S3 upload
│   │       ├── text_extract.py  # Text extraction
│   │       ├── chunking.py      # Smart chunking
│   │       ├── embedding.py     # OpenAI embedding
│   │       ├── faiss_service.py # FAISS operations
│   │       ├── llm_service.py   # Q&A + streaming
│   │       └── conversation.py  # History management
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app.py                   # Streamlit app
│   ├── ws_client.py             # WebSocket client
│   └── requirements.txt
└── data/
    └── faiss_index/             # FAISS index storage
```

## 🚀 Cài đặt và chạy

### 1. Cấu hình môi trường

Tạo file `.env` trong thư mục `backend/`:

```env
# MongoDB
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/?appName=cluster
MONGO_DB=notebooklm_db

# OpenAI API
api_key=your-openai-api-key
base_url=https://api.openai.com/v1
GENERATIVE_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-large
dimension=3072

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-southeast-2
AWS_S3_BUCKET=your-bucket-name
```

### 2. Cài đặt Backend

```bash
cd backend
pip install -r requirements.txt
```

### 3. Chạy Backend

```bash
cd backend
python -m app.main
```

hoặc

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ chạy tại: `http://localhost:8000`

### 4. Cài đặt Frontend

```bash
cd frontend
pip install -r requirements.txt
```

### 5. Chạy Frontend

```bash
cd frontend
streamlit run app.py
```

Frontend sẽ chạy tại: `http://localhost:8501`

## 📚 API Endpoints

### REST API

- `POST /upload` - Upload và index 1 file (synchronous)
- `POST /upload/batch` - **Upload nhiều file song song** (background processing)
- `GET /files` - Danh sách files
- `GET /files/{file_id}` - Chi tiết file
- `GET /health` - Health check

### WebSocket

- `ws://localhost:8000/ws/chat/{conversation_id}` - Real-time chat

### GraphQL

- `http://localhost:8000/graphql` - GraphQL playground

**Queries:**
```graphql
query {
  files {
    file_id
    filename
    status
  }
  
  conversation(conversation_id: "conv-id") {
    messages {
      role
      content
      sources {
        filename
        page_start
        page_end
      }
    }
  }
}
```

## 🔧 Workflow

### Upload & Index Flow

1. User upload file → FastAPI REST
2. Upload to S3
3. Extract text (PDF/TXT/DOCX)
4. Smart chunking (300-400 tokens)
5. Generate embeddings (OpenAI)
6. Add to FAISS index
7. Save metadata to MongoDB

### Q&A Flow

1. User sends question → WebSocket
2. Embed question
3. Search FAISS (top-K)
4. Fetch chunks from MongoDB
5. Build RAG prompt
6. Stream answer from LLM
7. Return sources
8. Save conversation

## 📝 MongoDB Collections

### files
```json
{
  "file_id": "uuid",
  "filename": "doc.pdf",
  "file_type": "pdf",
  "s3_path": "s3://bucket/uploads/...",
  "size": 123456,
  "status": "indexed",
  "created_at": "2026-01-08T..."
}
```

### chunks
```json
{
  "chunk_id": "uuid",
  "file_id": "uuid",
  "title": "CHAPTER 1",
  "content": "...",
  "page_start": 1,
  "page_end": 2,
  "faiss_index_id": 42,
  "embedding_dim": 3072,
  "created_at": "2026-01-08T..."
}
```

### conversations
```json
{
  "conversation_id": "uuid",
  "messages": [
    {
      "role": "user",
      "content": "What is...?",
      "created_at": "2026-01-08T..."
    },
    {
      "role": "assistant",
      "content": "Answer...",
      "sources": [...],
      "created_at": "2026-01-08T..."
    }
  ],
  "created_at": "2026-01-08T..."
}
```

### faiss_meta
```json
{
  "index_name": "notebooklm_index",
  "index_type": "IVF_FLAT",
  "embedding_dim": 3072,
  "total_vectors": 1500,
  "faiss_file_path": "/data/faiss/notebooklm.index",
  "last_updated": "2026-01-08T..."
}
```

## 🎨 Features Detail

### Smart Chunking
- Không cắt giữa câu
- Semantic grouping
- 300-400 tokens per chunk
- Overlap 1-2 câu
- Detect headings
- Preserve context

### RAG (Retrieval-Augmented Generation)
- Cosine similarity search
- Top-K retrieval (default: 5)
- Context-aware prompting
- Source citation
- Conversation history

### Real-time Streaming
- WebSocket connection
- Token-by-token streaming
- Source display
- Error handling

## 🧪 Testing

Test MongoDB connection:
```bash
cd backend/app/test
python testmongoDB.py
```

Test S3 upload:
```bash
cd backend/app/test
python test_upload.py
```

## 🔐 Security Notes

- ⚠️ `.env` file chứa credentials - KHÔNG commit lên Git
- ✅ Đã test MongoDB và S3 connection thành công
- ✅ CORS enabled cho development

## 📈 Future Enhancements

- [ ] Authentication & Authorization
- [ ] Multi-user support
- [ ] File management (delete, update)
- [ ] Advanced chunking strategies
- [ ] Multi-language support
- [ ] PDF highlighting
- [ ] Export conversations
- [ ] Analytics dashboard

## 📄 License

MIT License

## 👥 Contributors

Dự án thực tập 2 tuần - NotebookLM MVP

---

**Note:** Đây là phiên bản MVP (Minimum Viable Product) với đầy đủ chức năng cơ bản. Có thể mở rộng và tối ưu sau.
"# notebooklm-like" 
