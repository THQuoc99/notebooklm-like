import streamlit as st
import requests
import json
import uuid
import time
import re
from datetime import datetime
from ws_client import WebSocketClient

# Config
API_URL = "http://localhost:8000"

# Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if "uploaded_files_tracker" not in st.session_state:
    st.session_state.uploaded_files_tracker = set()

# Page config
st.set_page_config(
    page_title="NotebookLM-like Demo",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .source-card {
        background-color: #f8f9fa;
        border-left: 4px solid #0066cc;
        padding: 12px;
        margin: 8px 0;
        border-radius: 6px;
    }
    
    .source-header {
        font-weight: 600;
        color: #0066cc;
        margin-bottom: 6px;
    }
    
    .stCheckbox {
        padding: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📚 NotebookLM-like Demo")
st.markdown("Upload tài liệu và hỏi đáp với AI - Powered by RAG + OCR")

# Helper functions
def auto_upload_file(file):
    """Auto upload file immediately when selected."""
    try:
        file_key = f"{file.name}_{file.size}"
        if file_key in st.session_state.uploaded_files_tracker:
            return {"status": "skipped"}
        
        files = [("files", (file.name, file, file.type))]
        response = requests.post(f"{API_URL}/upload/batch", files=files, timeout=30)
        
        if response.status_code == 200:
            st.session_state.uploaded_files_tracker.add(file_key)
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_files():
    """Fetch files from backend."""
    try:
        response = requests.get(f"{API_URL}/files", timeout=5)
        if response.status_code == 200:
            return response.json().get("files", [])
    except:
        pass
    return []

def render_answer_with_citations(answer_text, sources):
    """Render answer with citation references."""
    st.markdown(answer_text)
    
    if sources:
        st.markdown("---")
        st.markdown("**📚 Nguồn tham khảo:**")
        for i, source in enumerate(sources):
            filename = source.get('filename', 'Unknown')
            page_start = source.get('page_start', '?')
            page_end = source.get('page_end', '?')
            
            if page_start == page_end:
                page_label = f"Trang {page_start}"
            else:
                page_label = f"Trang {page_start}-{page_end}"
            
            st.caption(f"[{i+1}] 📄 {filename} - {page_label}")

# Sidebar - File Management
with st.sidebar:
    st.header("📁 Quản lý Tài liệu")
    
    # Auto upload
    st.subheader("Upload File")
    uploaded_files = st.file_uploader(
        "Chọn file (PDF, TXT, DOCX, JPG, PNG)",
        type=["pdf", "txt", "docx", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="file_uploader",
        help="✨ File sẽ tự động upload khi bạn chọn"
    )
    
    # Auto upload when files selected
    if uploaded_files:
        for file in uploaded_files:
            file_key = f"{file.name}_{file.size}"
            if file_key not in st.session_state.uploaded_files_tracker:
                with st.spinner(f"⏳ Đang upload {file.name}..."):
                    result = auto_upload_file(file)
                    if result["status"] == "success":
                        st.success(f"✅ {file.name}")
                    elif result["status"] == "error":
                        st.error(f"❌ {file.name}: {result['message'][:40]}")
    
    st.divider()
    
    # File list
    st.subheader("📂 Danh Sách File")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.last_refresh = time.time()
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.uploaded_files_tracker.clear()
            st.session_state.selected_files.clear()
            st.rerun()
    
    # Auto refresh every 10 seconds
    if time.time() - st.session_state.last_refresh > 10:
        st.session_state.last_refresh = time.time()
        st.rerun()
    
    # Get and display files
    files = get_files()
    
    if files:
        st.markdown("**Chọn file làm nguồn:**")
        
        # Sort: indexed first
        status_order = {"indexed": 0, "processing": 1, "uploaded": 2, "failed": 3}
        files_sorted = sorted(files, key=lambda x: status_order.get(x.get("status", ""), 99))
        
        for file in files_sorted:
            file_id = file.get("file_id")
            filename = file.get("filename", "Unknown")
            status = file.get("status", "unknown")
            
            status_emoji = {
                "indexed": "✅",
                "processing": "⏳",
                "uploaded": "📤",
                "failed": "❌"
            }.get(status, "❓")
            
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                if status == "indexed":
                    is_selected = st.checkbox(
                        f"{status_emoji} {filename}",
                        key=f"sel_{file_id}",
                        value=file_id in st.session_state.selected_files
                    )
                    
                    if is_selected and file_id not in st.session_state.selected_files:
                        st.session_state.selected_files.append(file_id)
                    elif not is_selected and file_id in st.session_state.selected_files:
                        st.session_state.selected_files.remove(file_id)
                    
                    st.caption(f"✓ {file.get('chunks_count', 0)} chunks | {file.get('total_page', 0)} trang")
                else:
                    st.text(f"{status_emoji} {filename}")
                    if status == "failed":
                        st.caption(f"❌ {file.get('error', '')[:30]}...")
            
            with col_b:
                if st.button("🗑️", key=f"del_{file_id}"):
                    try:
                        requests.delete(f"{API_URL}/files/{file_id}")
                        if file_id in st.session_state.selected_files:
                            st.session_state.selected_files.remove(file_id)
                        st.rerun()
                    except:
                        pass
            
            st.markdown("---")
        
        if st.session_state.selected_files:
            st.info(f"🎯 {len(st.session_state.selected_files)} file được chọn")
        else:
            st.info("💡 Chọn file để tìm kiếm có mục tiêu")
    else:
        st.info("📭 Chưa có file nào")

# Main chat area
st.header("💬 Hỏi Đáp")

if st.session_state.selected_files:
    st.info(f"🎯 Đang tìm trong {len(st.session_state.selected_files)} file đã chọn")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_answer_with_citations(msg["content"], msg.get("sources", []))
        else:
            st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Đặt câu hỏi về tài liệu..."):
    files = get_files()
    indexed_files = [f for f in files if f.get("status") == "indexed"]
    
    if not indexed_files:
        st.warning("⚠️ Chưa có file nào được index!")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get answer
        with st.chat_message("assistant"):
            msg_placeholder = st.empty()
            src_placeholder = st.empty()
            
            try:
                ws_message = {"question": prompt}
                if st.session_state.selected_files:
                    ws_message["file_ids"] = st.session_state.selected_files
                
                ws_client = WebSocketClient(
                    f"ws://localhost:8000/ws/chat/{st.session_state.conversation_id}"
                )
                
                full_answer = ""
                sources = []
                
                ws_client.send(json.dumps(ws_message))
                
                for response in ws_client.receive():
                    data = json.loads(response)
                    msg_type = data.get("type")
                    content = data.get("content")
                    
                    if msg_type == "citations":
                        st.caption("📚 Nguồn:")
                        st.caption(content)
                    elif msg_type == "token":
                        full_answer += content
                        msg_placeholder.markdown(full_answer + "▌")
                    elif msg_type == "sources":
                        sources = content
                    elif msg_type == "done":
                        msg_placeholder.markdown(full_answer)
                        break
                    elif msg_type == "error":
                        st.error(f"❌ {content}")
                        break
                
                # Display sources
                if sources:
                    with src_placeholder.expander("📖 Chi tiết nguồn"):
                        for i, src in enumerate(sources):
                            fname = src.get('filename', 'Unknown')
                            p_start = src.get('page_start', '?')
                            p_end = src.get('page_end', '?')
                            page_label = f"Trang {p_start}" if p_start == p_end else f"Trang {p_start}-{p_end}"
                            
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-header">[{i+1}] {fname} - {page_label}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_answer,
                    "sources": sources
                })
                
                ws_client.close()
                
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"🆔 ID: {st.session_state.conversation_id[:8]}...")
with col2:
    st.caption(f"💬 {len(st.session_state.messages)} tin nhắn")
with col3:
    if st.button("🔄 Chat mới"):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
