import streamlit as st
import requests
import json
import uuid
import time
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

# Page config
st.set_page_config(
    page_title="NotebookLM-like Demo",
    page_icon="📚",
    layout="wide"
)

# Title
st.title("📚 NotebookLM-like Demo")
st.markdown("Upload tài liệu và hỏi đáp với AI")

# Sidebar - File Upload
with st.sidebar:
    st.header("📁 Upload Tài Liệu")
    
    # Multiple file uploader
    uploaded_files = st.file_uploader(
        "Chọn file (PDF, TXT, DOCX)",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.info(f"📄 Đã chọn {len(uploaded_files)} file")
        
        if st.button("🚀 Upload & Index All"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("Đang xử lý tài liệu..."):
                try:
                    # Prepare files for upload
                    files = [("files", (f.name, f, f.type)) for f in uploaded_files]
                    
                    status_text.text("Uploading files to server...")
                    response = requests.post(f"{API_URL}/upload/batch", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        progress_bar.progress(100)
                        
                        # Show results
                        st.success(f"✅ Upload thành công {result['total']} file!")
                        
                        # Show detailed results
                        for idx, file_result in enumerate(result['results']):
                            if file_result['status'] == 'processing':
                                st.info(f"⏳ {file_result['filename']} - Đang xử lý...")
                            elif file_result['status'] == 'failed':
                                st.error(f"❌ {file_result['filename']} - Lỗi: {file_result.get('error')}")
                        
                        st.info("💡 File đang được xử lý ở background. Refresh danh sách file sau vài giây.")
                    else:
                        st.error(f"❌ Lỗi: {response.text}")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
    
    st.divider()
    
    # List files
    st.header("📂 Danh Sách File")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/files")
        if response.status_code == 200:
            files_data = response.json()
            files = files_data.get("files", [])
            
            if files:
                for file in files:
                    status_emoji = {
                        "indexed": "✅",
                        "processing": "⏳",
                        "uploaded": "📤",
                        "failed": "❌"
                    }.get(file["status"], "❓")
                    
                    # Create columns for file info and delete button
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.text(f"{status_emoji} {file['filename']}")
                        st.caption(f"Status: {file['status']}")
                        
                        # Show chunks count if indexed
                        if file['status'] == 'indexed' and 'chunks_count' in file:
                            st.caption(f"Chunks: {file['chunks_count']}")
                        
                        # Show error if failed
                        if file['status'] == 'failed' and 'error' in file:
                            st.caption(f"Error: {file['error'][:50]}...")
                    
                    with col2:
                        # Delete button
                        if st.button("❌", key=f"delete_{file['file_id']}", help="Xóa file"):
                            try:
                                delete_response = requests.delete(f"{API_URL}/files/{file['file_id']}")
                                if delete_response.status_code == 200:
                                    st.success("✅ Đã xóa!")
                                    st.rerun()
                                else:
                                    st.error(f"Lỗi xóa: {delete_response.text}")
                            except Exception as e:
                                st.error(f"Lỗi: {str(e)}")
            else:
                st.info("Chưa có file nào")
    except Exception as e:
        st.error(f"Không thể tải danh sách file: {str(e)}")

# Main chat area
st.header("💬 Hỏi Đáp")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        # Show sources for assistant messages
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📖 Nguồn tham khảo"):
                for source in msg["sources"]:
                    st.markdown(f"- **{source.get('filename', 'Unknown')}** "
                              f"(Trang {source['page_start']}-{source['page_end']})")

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
