Dưới đây tôi sẽ **tóm gọn và chuẩn hóa toàn bộ chi tiết dự
án NotebookLM-like MVP** mà bạn chuẩn bị lập trình, với  **logic rõ ràng, từng
bước, đầy đủ công nghệ, database, luồng xử lý, API, chunking, FAISS và realtime
streaming** , phù hợp để bắt tay code ngay. Tôi cũng giữ  **scope tối thiểu
cho 2 tuần thực tập** .

---

**NotebookLM-like MVP – Project Plan Chuẩn**

**1. Mục tiêu dự án (MVP)**

* Người
  dùng upload tài liệu → Hệ thống hiểu nội dung → Hỏi đáp → Trả lời realtime
  → Trích dẫn nguồn (file + page).
* **Scope
  giới hạn 2 tuần, bỏ qua:**
  * Quản
    lý user/auth
  * Multi-notebook
  * Semantic
    graph
  * Highlight
    PDF nâng cao
  * Vector
    DB ngoài FAISS

---

**2. Stack công nghệ (CHỐT)**

**Backend**

* Python
* FastAPI
  (REST + WebSocket)
* Strawberry
  GraphQL (UI data)
* MongoDB
  (4 collection: files, chunks, conversations, faiss_meta)
* FAISS
  IVF_FLAT (local, L2 normalized, cosine similarity)
* AWS
  S3 (lưu file upload)
* OpenAI
  API (Embedding + Chat Completion)

**Frontend**

* Streamlit
* WebSocket
  client (realtime streaming)
* Realtime
  render câu trả lời + nguồn

---

**3. Database Design (CHỐT)**

**3.1. Collection Files**

* Lưu
  metadata file upload, **không lưu vector**

{

  "file_id":
"uuid",

"filename": "file.pdf",

"file_type": "pdf",

  "s3_path":
"s3://bucket/file.pdf",

  "size":
2458123,

  "status":
"indexed",  // uploaded |
processing | indexed | failed

"created_at": ISODate()

}

* Vai
  trò:
  * Liệt
    kê file đã upload
  * Kiểm
    tra file đã embedding chưa
  * Trace
    nguồn câu trả lời

---

**3.2. Collection Chunks (QUAN TRỌNG NHẤT)**

* Mỗi
  chunk = 1 vector trong FAISS

{

"chunk_id": "uuid-chunk-001",

  "file_id":
"uuid-file-001",

  "title":
"CHƯƠNG 2: PHƯƠNG PHÁP...",

  "content":
"Phương pháp nghiên cứu là...",

"page_start": 3,

"page_end": 4,

"faiss_index_id": 128,

"embedding_dim": 3072,

"created_at": ISODate()

}

* Vai
  trò:
  * FAISS
    **chỉ lưu vector** , MongoDB là nguồn text
  * Liên
    kết faiss_index_id → vector trong FAISS
  * Biết
    chunk thuộc file nào (file_id)
  * Giữ
    context + metadata (title, page)

---

**3.3. Collection Conversations**

* Lưu
  history câu hỏi + câu trả lời

{

"conversation_id": "conv-001",

"messages": [

    {

"role": "user",

"content": "Phương pháp nghiên cứu là gì?",

"created_at": ISODate()

    },

    {

"role": "assistant",

"content": "Phương pháp nghiên cứu là...",

"sources": [

    {

"file_id": "uuid-file-001",

"chunk_id": "uuid-chunk-001",

"page_start": 3,

"page_end": 3

    }

    ],

"created_at": ISODate()

    }

  ],

"created_at": ISODate()

}

* Vai
  trò:
  * Follow-up
    question
  * Trace
    nguồn
* Giới hạn
  history 5–7 lượt gần nhất

---

**3.4. Collection FAISS Meta (RẤT KHUYẾN NGHỊ)**

{

"index_name": "notebooklm_index",

"index_type": "IVF_FLAT",

"embedding_dim": 3072,

"total_vectors": 3521,

"faiss_file_path": "/data/faiss/notebooklm.index",

"last_updated": ISODate()

}

* Vai
  trò:
  * Load
    đúng index khi restart server
  * Debug
    vector mismatch
  * Dễ
    migrate / scale

---

**4. FAISS & Mongo liên kết**

* Flow
  indexing:

File → Chunk → Embedding → FAISS.add()

↓

faiss_index_id

↓

MongoDB.chunks

* FAISS
  **không lưu text** , Mongo lưu text & metadata
* Index
  type: IVF_FLAT
* Metric:
  INNER_PRODUCT
* Similarity:
  cosine (normalize L2)
* Embedding
  dim: 3072 (text-embedding-3-large)

---

**5. Chunking – Tiêu chuẩn**

| **Tiêu chí**   | **Bắt buộc** |
| ---------------------- | -------------------- |
| Không cắt giữa câu | ✅                   |
| Semantic grouping      | ✅                   |
| 300–400 tokens        | ✅                   |
| Overlap 1–2 câu      | ✅                   |
| Reset khi gặp heading | ⭐                   |
| Chunk đọc độc lập | ⭐                   |
| Heading gắn metadata  | ⭐                   |
| Page start / end       | ⭐                   |

* Không:
  * split("\n\n")
  * Chunk
    theo page cứng
  * Chunk
    không có title + page

---

**6. Luồng xử lý toàn bộ hệ thống**

**6.1. Upload & Index**

[Streamlit UI]

    |

    | 1. Upload file

    v

[FastAPI REST]

    |

    | 2. Upload file
song song

    v

[S3]

    |

    v

[Text Extractor]

    |

[Chunking]

    |

[Embedding API]

    |

[FAISS.add()]

    |

[MongoDB]

**Kết quả:**

* File
  trong S3
* Chunk
  text + metadata trong Mongo
* Vector
  trong FAISS

---

**6.2. Hỏi đáp (RAG core)**

[Streamlit UI] → [FastAPI WebSocket] → [Embedding question]
→ [FAISS search top-K] → [MongoDB fetch chunk] → [OpenAI LLM] → [Stream token]
→ [UI realtime]

---

**6.3. Follow-up question**

* Dùng
  conversation history + top-K chunks
* LLM
  trả lời dựa trên context
* Không
  cần semantic memory phức tạp cho MVP

---

**7. Backend API Structure**

**REST (FastAPI)**

| **Endpoint** | **Mục đích** |
| ------------------ | --------------------- |
| POST /upload       | Upload file           |
| GET /files         | List file             |
| GET /health        | Health check          |
| POST /webhook      | (tuỳ chọn)          |

**GraphQL (Strawberry)**

| **Query / Mutation** | **Mục đích** |
| -------------------------- | --------------------- |
| files                      | Lấy danh sách file  |
| conversation(id)           | Lấy chat history     |
| askQuestion                | Trigger Q&A           |

Lưu ý: GraphQL  **không stream** , chỉ query / mutation.
Streaming token → WebSocket

---

**8. Realtime streaming (WebSocket + Streamlit)**

**Flow**

1. FE gọi
   askQuestion
2. BE tạo
   request_id
3. Async
   process_question
4. FE mở
   ws/{request_id}
5. BE
   stream từng token
6. FE
   render realtime

**Pseudo-code FE**

def start_ws_stream(request_id: str):

st.session_state.answer = ""

    ws_url =
f"ws://localhost:8000/ws/{request_id}"

    def on_message(ws,
message):

    data =
json.loads(message)

    if
data["type"] == "token":

st.session_state.answer += data["content"]

    st.rerun()

    elif
data["type"] == "done":

    ws.close()

    ws =
WebSocketApp(ws_url, on_message=on_message)

    ws.run_forever()

---

**9. Prompt Logic (RAG)**

* Context
  = top-K chunks (5–7) + conversation history ngắn
* Assistant:
  * Trả
    lời dựa trên context
  * Không
    bịa
  * Gắn
    nguồn (file + page)

---

**10. Tuần 1 (Priority)**

* Chunking
  pipeline
* Embedding
  pipeline
* FAISS
  lifecycle (add, save, load)
* Mongo
  schema + CRUD
* Upload
  & Index

**11. Tuần 2 (Priority)**

* RAG
  Q&A
* Streaming
  WebSocket
* Streamlit
  UI
* Trace
  source
* Demo
  & polish

---

**12. Pydantic Models**

class FileModel(BaseModel):

    file_id: str

    filename: str

    file_type: str

    s3_path: str

    size: int

    status: str

    created_at:
datetime

class ChunkModel(BaseModel):

    chunk_id: str

    file_id: str

    title:
Optional[str]

    content: str

    page_start: int

    page_end: int

    faiss_index_id:
int

    embedding_dim: int

    created_at:
datetime

class MessageModel(BaseModel):

    role: str

    content: str

    created_at:
datetime

    sources:
Optional[List[dict]] = None

class ConversationModel(BaseModel):

    conversation_id:
str

    messages:
List[MessageModel]

    created_at:
datetime

class FaissMetaModel(BaseModel):

    index_name: str

    index_type: str

    embedding_dim: int

    total_vectors: int

    faiss_file_path:
str

    last_updated:
datetime

---

**13. Lưu ý khác**

* Embedding
  model: "text-embedding-3-large" → dim=3072
* Similarity:
  cosine (normalize L2)
* FAISS
  IVF_FLAT, không rebuild nếu index tồn tại
* Mongo
  giữ **nguồn text duy nhất** để trace

---

Nếu bạn muốn, tôi có thể  **vẽ luôn một sơ đồ tổng thể flow

+ database + FAISS + WebSocket** , để nhìn  **tất cả module + luồng data trong
  một hình** , cực kỳ trực quan trước khi code.

CẤU TRÚC THƯ MỤC :
