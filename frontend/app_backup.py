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

if "answer" not in st.session_state:
    st.session_state.answer = ""

if "sources" not in st.session_state:
    st.session_state.sources = []

if "citations" not in st.session_state:
    st.session_state.citations = ""

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

# Custom CSS for better UI
st.markdown("""
<style>
    /* Citation styling */
    .citation {
        color: #0066cc;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        background-color: #e8f4ff;
        cursor: pointer;
        position: relative;
    }
    
    .citation:hover {
        background-color: #d0e8ff;
    }
    
    /* Source card styling */
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
    
    .source-content {
        color: #555;
        font-style: italic;
        font-size: 0.9em;
    }
    
    /* File status badges */
    .status-indexed {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
    }
    
    .status-processing {
        background-color: #fff3cd;
        color: #856404;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
    }
    
    .status-failed {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📚 NotebookLM-like Demo")
st.markdown("Upload tài liệu và hỏi đáp với AI - Powered by RAG")

# Auto upload function
def auto_upload_file(file):
    """Auto upload file immediately when selected."""
    try:
        # Check if already uploaded
        file_key = f"{file.name}_{file.size}"
        if file_key in st.session_state.uploaded_files_tracker:
            return {"status": "skipped", "message": "Already uploaded"}
        
        # Upload
        files = [("files", (file.name, file, file.type))]
        response = requests.post(f"{API_URL}/upload/batch", files=files, timeout=30)
        
        if response.status_code == 200:
            st.session_state.uploaded_files_tracker.add(file_key)
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Function to get files
def get_files():
    """Fetch files from backend."""
    try:
        response = requests.get(f"{API_URL}/files", timeout=5)
        if response.status_code == 200:
            return response.json().get("files", [])
    except:
        pass
    return []

# Function to render citation with hover
def render_answer_with_citations(answer_text, sources):
    """Render answer with clickable citations."""
    if not sources:
        return answer_text
    
    # Build source map
    source_map = {}
    for i, source in enumerate(sources):
        citation_num = i + 1
        filename = source.get('filename', 'Unknown')
        page_start = source.get('page_start', '?')
        page_end = source.get('page_end', '?')
        
        if page_start == page_end:
            page_label = f"Trang {page_start}"
        else:
            page_label = f"Trang {page_start}-{page_end}"
        
        source_map[citation_num] = f"📄 {filename} - {page_label}"
    
    # Display answer
    st.markdown(answer_text)
    
    # Display citation map
    if source_map:
        st.markdown("---")
        st.markdown("**📚 Nguồn tham khảo:**")
        for num, label in source_map.items():
            st.caption(f"[{num}] {label}")

# Sidebar - File Upload and Management
with st.sidebar:
    st.header("📁 Quản lý Tài liệu")
    
    # Auto upload file picker
    st.subheader("Upload File")
    uploaded_files = st.file_uploader(
        "Chọn file (PDF, TXT, DOCX, JPG, PNG)",
        type=["pdf", "txt", "docx", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="file_uploader",
        help="File sẽ tự động upload khi bạn chọn"
    )
    
    # Auto upload when files selected
    if uploaded_files:
        upload_container = st.container()
        with upload_container:
            for file in uploaded_files:
                file_key = f"{file.name}_{file.size}"
                if file_key not in st.session_state.uploaded_files_tracker:
                    with st.spinner(f"⏳ Đang upload {file.name}..."):
                        result = auto_upload_file(file)
                        if result["status"] == "success":
                            st.success(f"✅ {file.name} - Đang xử lý...")
                        elif result["status"] == "error":
                            st.error(f"❌ {file.name} - Lỗi: {result['message'][:50]}")
                        time.sleep(0.1)  # Small delay for UI
    
    st.divider()
    
    # File list with auto refresh
    st.subheader("📂 Danh Sách File")
    
    col_refresh, col_clear = st.columns([1, 1])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.last_refresh = time.time()
            st.rerun()
    
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.uploaded_files_tracker.clear()
            st.session_state.selected_files.clear()
            st.rerun()
    
    # Auto refresh every 10 seconds if files are processing
    current_time = time.time()
    if current_time - st.session_state.last_refresh > 10:
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Get and display files
    files = get_files()
    
    if files:
        st.markdown("**Chọn file làm nguồn trả lời:**")
        
        # Sort: indexed first, then processing, then failed
        status_order = {"indexed": 0, "processing": 1, "uploaded": 2, "failed": 3}
        files_sorted = sorted(files, key=lambda x: status_order.get(x.get("status", ""), 99))
        
        for file in files_sorted:
            file_id = file.get("file_id")
            filename = file.get("filename", "Unknown")
            status = file.get("status", "unknown")
            
            # Status emoji
            status_emoji = {
                "indexed": "✅",
                "processing": "⏳",
                "uploaded": "📤",
                "failed": "❌"
            }.get(status, "❓")
            
            # Container for each file
            file_container = st.container()
            
            with file_container:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Checkbox for scoped retrieval (only for indexed files)
                    if status == "indexed":
                        is_selected = st.checkbox(
                            f"{status_emoji} {filename}",
                            key=f"select_{file_id}",
                            value=file_id in st.session_state.selected_files,
                            help="Chọn để chỉ tìm trong file này"
                        )
                        
                        if is_selected and file_id not in st.session_state.selected_files:
                            st.session_state.selected_files.append(file_id)
                        elif not is_selected and file_id in st.session_state.selected_files:
                            st.session_state.selected_files.remove(file_id)
                    else:
                        st.text(f"{status_emoji} {filename}")
                    
                    # Show additional info
                    if status == "indexed" and "chunks_count" in file:
                        st.caption(f"✓ {file['chunks_count']} chunks | {file.get('total_page', '?')} trang")
                    elif status == "processing":
                        st.caption("⏳ Đang xử lý...")
                    elif status == "failed":
                        error_msg = file.get('error', 'Unknown error')
                        st.caption(f"❌ {error_msg[:40]}...")
                
                with col2:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{file_id}", help="Xóa file"):
                        try:
                            delete_response = requests.delete(f"{API_URL}/files/{file_id}")
                            if delete_response.status_code == 200:
                                if file_id in st.session_state.selected_files:
                                    st.session_state.selected_files.remove(file_id)
                                st.success("✅ Đã xóa!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {delete_response.text[:30]}")
                        except Exception as e:
                            st.error(f"Lỗi: {str(e)[:30]}")
                
                st.markdown("---")
        
        # Show selected files summary
        if st.session_state.selected_files:
            st.info(f"🎯 Đã chọn {len(st.session_state.selected_files)} file làm nguồn")
        else:
            st.info("💡 Chọn file để tìm kiếm có mục tiêu hơn")
    else:
        st.info("📭 Chưa có file nào. Upload file ở trên để bắt đầu!")
    
    # Show upload tracker info
    if st.session_state.uploaded_files_tracker:
        st.caption(f"📊 Đã upload: {len(st.session_state.uploaded_files_tracker)} file trong session này")

# Main chat area
st.header("💬 Hỏi Đáp")

# Show scoped retrieval status
if st.session_state.selected_files:
    st.info(f"🎯 Đang tìm trong {len(st.session_state.selected_files)} file đã chọn")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            # Render answer with citations
            render_answer_with_citations(msg["content"], msg.get("sources", []))
        else:
            st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Đặt câu hỏi về tài liệu..."):
    # Check if there are any indexed files
    files = get_files()
    indexed_files = [f for f in files if f.get("status") == "indexed"]
    
    if not indexed_files:
        st.warning("⚠️ Chưa có file nào được index. Vui lòng upload file trước!")
    else:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get answer from WebSocket
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            sources_placeholder = st.empty()
            
            try:
                # Prepare WebSocket message
                ws_message = {
                    "question": prompt
                }
                
                # Add scoped retrieval if files selected
                if st.session_state.selected_files:
                    ws_message["file_ids"] = st.session_state.selected_files
                
                # Connect to WebSocket
                ws_client = WebSocketClient(
                    f"ws://localhost:8000/ws/chat/{st.session_state.conversation_id}"
                )
                
                full_answer = ""
                sources = []
                citations = ""
                
                # Send question
                ws_client.send(json.dumps(ws_message))
                
                # Receive responses
                for response in ws_client.receive():
                    data = json.loads(response)
                    msg_type = data.get("type")
                    content = data.get("content")
                    
                    if msg_type == "citations":
                        # Received citation map
                        citations = content
                        st.caption("📚 Nguồn:")
                        st.caption(citations)
                    
                    elif msg_type == "token":
                        # Stream answer tokens
                        full_answer += content
                        message_placeholder.markdown(full_answer + "▌")
                    
                    elif msg_type == "sources":
                        # Received source details
                        sources = content
                    
                    elif msg_type == "done":
                        # Completed
                        message_placeholder.markdown(full_answer)
                        break
                    
                    elif msg_type == "error":
                        st.error(f"❌ Lỗi: {content}")
                        break
                    
                    elif msg_type == "info":
                        st.info(content)
                        break
                
                # Display sources with expandable details
                if sources:
                    with sources_placeholder.expander("📖 Chi tiết nguồn tham khảo"):
                        for i, source in enumerate(sources):
                            filename = source.get('filename', 'Unknown')
                            page_start = source.get('page_start', '?')
                            page_end = source.get('page_end', '?')
                            
                            if page_start == page_end:
                                page_label = f"Trang {page_start}"
                            else:
                                page_label = f"Trang {page_start}-{page_end}"
                            
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-header">[{i+1}] {filename} - {page_label}</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Save assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_answer,
                    "sources": sources
                })
                
                ws_client.close()
                
            except Exception as e:
                st.error(f"❌ Lỗi kết nối: {str(e)}")
                st.info("💡 Đảm bảo backend đang chạy tại http://localhost:8000")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"🆔 Conversation: {st.session_state.conversation_id[:8]}...")
with col2:
    st.caption(f"💬 Messages: {len(st.session_state.messages)}")
with col3:
    if st.button("🔄 New Chat"):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.sources = []
        st.session_state.citations = ""
        st.rerun()

# Chat input
question = st.chat_input("Đặt câu hỏi về tài liệu...")

if question:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })
    
    # Display user message
    with st.chat_message("user"):
        st.write(question)
    
    # Display assistant response with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        sources = []
        
        # WebSocket streaming
        ws_client = WebSocketClient(
            f"ws://localhost:8000/ws/chat/{st.session_state.conversation_id}"
        )
        
        try:
            ws_client.connect()
            ws_client.send_question(question)
            
            # Stream tokens with immediate UI update and cursor
            for message in ws_client.receive_stream():
                msg_type = message.get("type")
                
                if msg_type == "token":
                    token = message.get("content", "")
                    full_response += token
                    # Update immediately with cursor for real-time effect
                    message_placeholder.markdown(full_response + "▌")
                    # Small sleep to allow Streamlit to flush UI updates
                    time.sleep(0.01)
                
                elif msg_type == "sources":
                    sources = message.get("content", [])
                
                elif msg_type == "done":
                    break
                
                elif msg_type == "error":
                    st.error(f"Lỗi: {message.get('content')}")
                    break
                
                elif msg_type == "info":
                    st.info(message.get('content'))
            
            ws_client.close()
            
            # Final display without cursor
            message_placeholder.markdown(full_response)
            
            # Show sources
            if sources:
                with st.expander("📖 Nguồn tham khảo"):
                    for source in sources:
                        st.markdown(f"- **{source.get('filename', 'Unknown')}** "
                                  f"(Trang {source['page_start']}-{source['page_end']})")
            
            # Save to session
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources
            })
        
        except Exception as e:
            st.error(f"❌ Lỗi kết nối: {str(e)}")

# Footer
st.divider()
st.caption(f"Conversation ID: {st.session_state.conversation_id}")

# Reset button
if st.button("🔄 Reset Chat"):
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()
