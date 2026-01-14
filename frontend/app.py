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

if "deleting_files" not in st.session_state:
    st.session_state.deleting_files = set()

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

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
    
    /* Hover citation styling */
    .citation {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 600;
        cursor: help;
        position: relative;
        margin: 0 2px;
        transition: all 0.2s;
    }
    
    .citation:hover {
        background: #1976d2;
        color: white;
        transform: translateY(-1px);
    }
    
    .citation .tooltip {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #2c3e50;
        color: #fff;
        padding: 16px;
        border-radius: 8px;
        width: 350px;
        max-width: 90vw;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
        transition: opacity 0.3s;
        text-align: left;
        font-weight: normal;
        font-size: 13px;
        line-height: 1.5;
    }
    
    .citation:hover .tooltip {
        visibility: visible;
        opacity: 1;
    }
    
    .tooltip::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: #2c3e50 transparent transparent transparent;
    }
    
    .tooltip-header {
        font-weight: 700;
        color: #3498db;
        margin-bottom: 8px;
        font-size: 14px;
        border-bottom: 1px solid #555;
        padding-bottom: 6px;
    }
    
    .tooltip-section {
        margin: 8px 0;
    }
    
    .tooltip-label {
        color: #95a5a6;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 3px;
    }
    
    .tooltip-content {
        color: #ecf0f1;
        margin-bottom: 6px;
    }
    
    .tooltip-excerpt {
        background: #34495e;
        padding: 8px;
        border-radius: 4px;
        font-style: italic;
        color: #bdc3c7;
        max-height: 100px;
        overflow-y: auto;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📚 NotebookLM-like Demo")
st.markdown("Upload tài liệu và hỏi đáp với AI - Powered by RAG + OCR")

# Helper functions
def upload_file_parallel(file, file_key):
    """Upload a single file - runs in thread worker."""
    try:
        files = [("files", (file.name, file.getvalue(), file.type))]
        response = requests.post(f"{API_URL}/upload/batch", files=files, timeout=60)
        
        if response.status_code == 200:
            return {"status": "success", "file_key": file_key, "data": response.json()}
        else:
            return {"status": "error", "file_key": file_key, "message": response.text[:100]}
    except Exception as e:
        return {"status": "error", "file_key": file_key, "message": str(e)[:100]}

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
    """Render answer with citation references and hover tooltips."""
    # Convert [1], [2], [3] to HTML with hover tooltips
    def create_citation_html(match):
        num = match.group(1)
        idx = int(num) - 1
        
        if idx < 0 or idx >= len(sources):
            return match.group(0)
        
        source = sources[idx]
        filename = source.get('filename', 'Unknown')
        page_start = source.get('page_start', '?')
        page_end = source.get('page_end', '?')
        chunk_text = source.get('content', 'N/A')[:200] + "..."
        title = source.get('title', 'N/A')
        
        if page_start == page_end:
            page_label = f"Trang {page_start}"
        else:
            page_label = f"Trang {page_start}-{page_end}"
        
        tooltip_html = f"""
        <div class="tooltip">
            <div class="tooltip-header">📄 Nguồn [{num}]</div>
            <div class="tooltip-section">
                <div class="tooltip-label">Tên file</div>
                <div class="tooltip-content">{filename}</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-label">Số trang</div>
                <div class="tooltip-content">{page_label}</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-label">Tiêu đề đoạn</div>
                <div class="tooltip-content">{title}</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-label">Trích đoạn</div>
                <div class="tooltip-excerpt">{chunk_text}</div>
            </div>
        </div>
        """
        
        return f'<span class="citation">[{num}]{tooltip_html}</span>'
    
    # Replace [1], [2], [3], etc. with citation HTML
    pattern = r'\[(\d+)\]'
    answer_html = re.sub(pattern, create_citation_html, answer_text)
    
    # Render HTML
    st.markdown(answer_html, unsafe_allow_html=True)
    
    # Original source list below (collapsed by default)
    if sources:
        with st.expander("📚 Danh sách nguồn đầy đủ", expanded=False):
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
    
    # Background cleanup: send DELETE for files marked as deleting (non-blocking)
    if st.session_state.deleting_files:
        import threading
        # Copy file IDs to pass to thread (session_state not accessible in background threads)
        files_to_delete = list(st.session_state.deleting_files.copy())
        
        def cleanup_deleted_files(file_ids):
            for file_id in file_ids:
                try:
                    # Fire and forget - no timeout wait
                    requests.delete(f"{API_URL}/files/{file_id}", timeout=0.5)
                except:
                    pass  # Ignore all errors
        
        # Start cleanup thread immediately, don't wait
        cleanup_thread = threading.Thread(target=cleanup_deleted_files, args=(files_to_delete,), daemon=True)
        cleanup_thread.start()
    
    # Auto upload
    st.subheader("Upload File")
    uploaded_files = st.file_uploader(
        "Chọn file (PDF, TXT, DOCX, JPG, PNG)",
        type=["pdf", "txt", "docx", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}",
        help="✨ Chọn file và upload ngay"
    )
    
    # Upload immediately when files selected - no tracking
    if uploaded_files:
        import concurrent.futures
        
        with st.spinner(f"⏳ Đang upload {len(uploaded_files)} file..."):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(upload_file_parallel, file, f"{file.name}_{file.size}"): file 
                          for file in uploaded_files}
                
                success_count = 0
                error_count = 0
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result.get("status") == "success":
                            success_count += 1
                        else:
                            error_count += 1
                    except:
                        error_count += 1
        
        # Show summary
        if success_count > 0:
            st.success(f"✅ Upload thành công: {success_count} file")
        if error_count > 0:
            st.error(f"❌ Upload thất bại: {error_count} file")
        
        # Reset file uploader and refresh file list
        st.session_state.uploader_key += 1
        time.sleep(0.5)  # Wait for backend to process
        st.rerun()
    
    st.divider()
    
    # File list
    st.subheader("📂 Danh Sách File")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.selected_files.clear()
            st.rerun()
    
    # Get and display files
    files = get_files()
    
    # Filter out files being deleted (optimistic UI - hide immediately)
    files = [f for f in files if f.get("file_id") not in st.session_state.deleting_files]
    
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
                    if status == "processing":
                        st.caption("⏳ Đang xử lý...")
                    elif status == "uploaded":
                        st.caption("📤 Đang chờ xử lý...")
                    elif status == "failed":
                        st.caption(f"❌ {file.get('error', '')[:30]}...")
            
            with col_b:
                if st.button("×", key=f"del_{file_id}", help="Xóa file", type="secondary"):
                    # ONLY mark for deletion - NO API call here
                    st.session_state.deleting_files.add(file_id)
                    if file_id in st.session_state.selected_files:
                        st.session_state.selected_files.remove(file_id)
                    
                    # Immediate rerun - file disappears instantly
                    st.rerun()
            
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
                ws_client = WebSocketClient(
                    f"ws://localhost:8000/ws/chat/{st.session_state.conversation_id}"
                )
                ws_client.connect()
                
                full_answer = ""
                sources = []
                
                # Use send() method with JSON payload
                ws_message = {"question": prompt}
                if st.session_state.selected_files:
                    ws_message["file_ids"] = st.session_state.selected_files
                
                ws_client.send(json.dumps(ws_message))
                
                for response in ws_client.receive_stream():
                    msg_type = response.get("type")
                    content = response.get("content")
                    
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
