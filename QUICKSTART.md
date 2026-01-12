# 🚀 Hướng dẫn chạy nhanh

## 🎯 Cách nhanh nhất (Windows)

### Chạy cả Backend + Frontend cùng lúc

Double-click file: `run_all.bat`

### Hoặc chạy riêng lẻ

- Backend: Double-click `run_backend.bat`
- Frontend: Double-click `run_frontend.bat`

### Cài đặt dependencies

- Backend: Double-click `install_backend.bat`
- Frontend: Double-click `install_frontend.bat`

---

## 📝 Hướng dẫn chi tiết (Manual)

## Bước 1: Kiểm tra .env file

```bash
cd D:\Dự án TT\notebooklm\backend
# Đảm bảo file .env có đầy đủ thông tin
```

## Bước 2: Kích hoạt và cài đặt dependencies

### Backend

```bash
cd D:\Dự án TT\notebooklm\backend

# Kích hoạt virtual environment
venv\Scripts\activate

# Cài đặt dependencies (nếu chưa cài)
pip install -r requirements.txt
```

### Frontend

```bash
cd D:\Dự án TT\notebooklm\frontend

# Kích hoạt virtual environment
venv\Scripts\activate

# Cài đặt dependencies (nếu chưa cài)
pip install -r requirements.txt
```

## Bước 3: Chạy Backend

Mở terminal 1:

```bash
cd D:\Dự án TT\notebooklm\backend

# Kích hoạt venv
venv\Scripts\activate

# Chạy server
python -m app.main
```

Hoặc dùng uvicorn:

```bash
cd D:\Dự án TT\notebooklm\backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ chạy tại: http://localhost:8000

## Bước 4: Chạy Frontend

Mở terminal 2:

```bash
cd D:\Dự án TT\notebooklm\frontend

# Kích hoạt venv
venv\Scripts\activate

# Chạy Streamlit
streamlit run app.py
```

Frontend sẽ tự động mở browser tại: http://localhost:8501

## Bước 5: Test

1. Vào Streamlit UI (http://localhost:8501)
2. Upload file PDF/TXT/DOCX ở sidebar
3. Click "Upload & Index"
4. Đợi xử lý xong
5. Đặt câu hỏi trong chat
6. Xem kết quả real-time streaming

## 🔍 Kiểm tra API

### Health check

```bash
curl http://localhost:8000/health
```

### List files

```bash
curl http://localhost:8000/files
```

### GraphQL Playground

Mở browser: http://localhost:8000/graphql

## ⚠️ Troubleshooting

### Lỗi venv không kích hoạt được

```bash
# Nếu gặp lỗi PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Hoặc dùng CMD thay vì PowerShell
```

### Lỗi module not found

```bash
# Đảm bảo đã kích hoạt venv trước
venv\Scripts\activate

# Cài lại dependencies
pip install -r requirements.txt
```

### Lỗi MongoDB connection

- Kiểm tra MONGO_URL trong .env
- Ping MongoDB cluster

### Lỗi S3 upload

- Kiểm tra AWS credentials trong .env
- Kiểm tra bucket name và region

### Lỗi OpenAI API

- Kiểm tra api_key trong .env
- Kiểm tra base_url

### Lỗi FAISS

- Kiểm tra thư mục data/faiss_index/ tồn tại
- Delete file .index nếu corrupt

## 📁 Thư mục quan trọng

- Backend: `D:\Dự án TT\notebooklm\backend`
- Frontend: `D:\Dự án TT\notebooklm\frontend`
- FAISS Index: `D:\Dự án TT\notebooklm\data\faiss_index`
- Env: `D:\Dự án TT\notebooklm\backend\.env`
- Backend venv: `D:\Dự án TT\notebooklm\backend\venv`
- Frontend venv: `D:\Dự án TT\notebooklm\frontend\venv`

## 🎯 URL quan trọng

- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- GraphQL: http://localhost:8000/graphql
- Health: http://localhost:8000/health

## 📜 Batch Scripts có sẵn

- `run_all.bat` - Chạy cả backend + frontend
- `run_backend.bat` - Chỉ chạy backend
- `run_frontend.bat` - Chỉ chạy frontend
- `install_backend.bat` - Cài dependencies backend
- `install_frontend.bat` - Cài dependencies frontend
