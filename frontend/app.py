import streamlit as st
import streamlit.components.v1 as components
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
        display: inline-block !important;
        background: #e3f2fd !important;
        color: #1976d2 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        cursor: help !important;
        position: relative !important;
        margin: 0 2px !important;
        transition: all 0.2s !important;
    }
    
    .citation:hover {
        background: #1976d2 !important;
        color: white !important;
        transform: translateY(-1px) !important;
    }
    
    .citation .tooltip {
        visibility: hidden !important;
        opacity: 0 !important;
        position: absolute !important;
        bottom: 130% !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        background-color: #2c3e50 !important;
        color: #fff !important;
        padding: 16px !important;
        border-radius: 8px !important;
        width: 350px !important;
        max-width: 90vw !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        z-index: 9999 !important;
        transition: opacity 0.3s !important;
        text-align: left !important;
        font-weight: normal !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        pointer-events: none !important;
    }
    
    .citation:hover .tooltip {
        visibility: visible !important;
        opacity: 1 !important;
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
    if sources:
        answer_html = make_answer_html(answer_text, sources)
        components.html(build_answer_html(answer_html), height=600, scrolling=False)
    else:
        st.markdown(answer_text)


def build_answer_html(answer_html: str, include_wrapper: bool = True) -> str:
    """Build full HTML string (CSS + answer) for rendering in iframe.

    `answer_html` is expected to already contain citation <span> markup.
    """
    css = """
    <style>
        body { margin: 0; padding: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; }
        .citation { display: inline-block; background: #e3f2fd; color: #1976d2; padding: 0px 3px; border-radius: 2px; font-weight: 600; cursor: help; position: relative; margin: 0; transition: all 0.2s ease; box-shadow: 0 1px 1px rgba(0,0,0,0.06); font-size: 10px; line-height: 1.2; vertical-align: baseline; }
        .citation:hover { background: #1976d2; color: white; box-shadow: 0 2px 4px rgba(25,118,210,0.25); }
        .citation .tooltip { visibility: hidden; opacity: 0; position: absolute; bottom: 150%; left: 50%; transform: translateX(-50%) translateY(8px); background: #ffffff; color: #2c3e50; padding: 8px; border-radius: 6px; width: 300px; max-width: 90vw; max-height: 80vh; overflow-y: auto; box-shadow: 0 8px 30px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.06); z-index: 9999; transition: all 0.25s ease, visibility 0s linear 0.4s; text-align: left; font-weight: normal; font-size: 11px; line-height: 1.3; pointer-events: auto; }
        .citation:hover .tooltip, .citation .tooltip:hover { visibility: visible; opacity: 1; transform: translateX(-50%) translateY(0); transition-delay: 0s; }
        .tooltip::after { content: ""; position: absolute; top: 100%; left: 50%; margin-left: -6px; border-width: 6px; border-style: solid; border-color: #ffffff transparent transparent transparent; }
        .tooltip-header { font-weight: 700; color: #1976d2; margin-bottom: 6px; font-size: 11px; padding-bottom: 4px; border-bottom: 1.5px solid #e3f2fd; }
        .tooltip-section { margin: 3px 0; padding: 2px 0; border-bottom: 1px solid #f8f8f8; }
        .tooltip-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .tooltip-label { color: #8a94a0; font-size: 8px; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 1px; font-weight: 600; line-height: 1.2; }
        .tooltip-content { color: #2c3e50; margin: 0; font-weight: 500; font-size: 11px; line-height: 1.25; }
        .tooltip-excerpt { background: #f8f9fa; padding: 6px 8px; margin-top: 1px; border-radius: 4px; color: #4a5568; font-size: 10px; border-left: 2px solid #1976d2; white-space: pre-wrap; word-wrap: break-word; line-height: 1.4; max-height: 180px; overflow-y: auto; }
        .tooltip-excerpt::-webkit-scrollbar { width: 4px; }
        .tooltip-excerpt::-webkit-scrollbar-track { background: #e9ecef; border-radius: 8px; }
        .tooltip-excerpt::-webkit-scrollbar-thumb { background: #1976d2; border-radius: 8px; }
        .answer-text { font-size: 15px; line-height: 1.8; color: #2c3e50; white-space: pre-wrap; }
        .answer-text strong { color: #1976d2; }
        .answer-text ul, .answer-text ol { margin: 8px 0; padding-left: 24px; }
        .answer-text li { margin: 6px 0; }
    </style>
    """

    if include_wrapper:
        # Add script for smooth tooltip interaction with hover capability
        script = """
        <script>
        (function(){
            const citations = document.querySelectorAll('.citation');
            citations.forEach(c => {
                let hideTimeout;
                const t = c.querySelector('.tooltip');
                if(!t) return;
                
                const showTooltip = () => {
                    clearTimeout(hideTimeout);
                    t.style.visibility='visible'; 
                    t.style.opacity='1';
                    t.style.transform='translateX(-50%) translateY(0)';
                    t.style.transitionDelay='0s';
                };
                
                const hideTooltip = () => {
                    hideTimeout = setTimeout(() => {
                        t.style.visibility='hidden'; 
                        t.style.opacity='0';
                        t.style.transform='translateX(-50%) translateY(10px)';
                    }, 300);
                };
                
                c.addEventListener('mouseenter', showTooltip);
                c.addEventListener('mouseleave', hideTooltip);
                t.addEventListener('mouseenter', showTooltip);
                t.addEventListener('mouseleave', hideTooltip);
            });
        })();
        </script>
        """

        return f"""{css}<div class=\"answer-text\">{answer_html}</div>{script}"""
    else:
        return answer_html


def make_answer_html(answer_text: str, sources: list) -> str:
    """Convert answer_text containing [1],[2]... into HTML with tooltip spans using sources list."""
    def create_citation_html(match):
        num = match.group(1)
        idx = int(num) - 1
        if idx < 0 or idx >= len(sources):
            return match.group(0)
        source = sources[idx]
        filename = source.get('filename', 'Unknown')
        page_start = source.get('page_start', '?')
        page_end = source.get('page_end', '?')
        chunk_text = (source.get('content', 'N/A') or '')[:300]
        title = source.get('title', 'N/A')
        
        if page_start == page_end:
            page_label = f"Trang {page_start}"
        else:
            page_label = f"Trang {page_start}-{page_end}"
        
        # Clean title display
        title_display = title if title and title != 'N/A' and title != 'None' else '<em>Không có tiêu đề</em>'
        
        tooltip_html = f"""
        <div class="tooltip">
            <div class="tooltip-header">📄 Nguồn #{num}</div>
            <div class="tooltip-section">
                <div class="tooltip-label">📁 Tên File</div>
                <div class="tooltip-content">{filename}</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-label">📊 Trang</div>
                <div class="tooltip-content">{page_label}</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-label">📝 Tiêu Đề</div>
                <div class="tooltip-content">{title_display}</div>
            </div>
            <div class="tooltip-section">
                <div class="tooltip-label">💬 Nội Dung</div>
                <div class="tooltip-excerpt">{chunk_text}</div>
            </div>
        </div>
        """
        return f'<span class="citation">[{num}]{tooltip_html}</span>'

    pattern = r'\[(\d+)\]'
    return re.sub(pattern, create_citation_html, answer_text)

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
                        msg_placeholder.caption("📚 Nguồn tham khảo")
                    elif msg_type == "token":
                        full_answer += content
                        # Only show plain text during streaming
                        msg_placeholder.markdown(full_answer + "▌")
                    elif msg_type == "sources":
                        sources = content
                    elif msg_type == "done":
                        # Clear placeholder and render final version with citations
                        msg_placeholder.empty()
                        if sources:
                            components.html(
                                build_answer_html(make_answer_html(full_answer, sources)), 
                                height=600, 
                                scrolling=False
                            )
                        else:
                            st.markdown(full_answer)
                        break
                    elif msg_type == "error":
                        st.error(f"❌ {content}")
                        break
                
                # Save to chat history
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
