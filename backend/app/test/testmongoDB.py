from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
import datetime

# -----------------------------
# 1. Kết nối MongoDB
# -----------------------------
uri = "mongodb+srv://hquoccun_db_user:9DPhw94igRTkaKay@notebooklm-cluster.ogaa4cj.mongodb.net/?appName=notebooklm-cluster"

client = MongoClient(uri, server_api=ServerApi('1'))

# Kiểm tra kết nối
try:
    client.admin.command('ping')
    print("✅ Kết nối MongoDB thành công!")
except Exception as e:
    print("❌ Kết nối thất bại:", e)

# Chọn database
db = client['notebooklm_db']

# -----------------------------
# 2. Tạo collection + index
# -----------------------------
files_col = db['files']
chunks_col = db['chunks']
conversations_col = db['conversations']
faiss_meta_col = db['faiss_meta']

# -----------------------------
# Drop toàn bộ collection
# -----------------------------
files_col.drop()
chunks_col.drop()
conversations_col.drop()
faiss_meta_col.drop()

print("✅ Đã drop toàn bộ collection")
