"""
Frontend Example: Source Citation với Hover Tooltip

File này cung cấp ví dụ implement cho Streamlit hoặc pure HTML/JS
để hiển thị source citations với hover tooltip giống NotebookLM.
"""

# ==========================================
# PHẦN 1: STREAMLIT IMPLEMENTATION
# ==========================================

"""
Streamlit hiện tại không hỗ trợ native hover tooltips cho markdown.
Cần dùng custom HTML/CSS/JS component.

Approach: Sử dụng st.markdown với unsafe_allow_html=True
"""

import streamlit as st
import re
from typing import List, Dict

def parse_citations_from_answer(answer_text: str) -> List[int]:
    """Extract citation numbers từ answer text.
    
    Example: "Transformer ra đời năm 2017 [1] và đã thay đổi NLP [2]."
    Returns: [1, 2]
    """
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, answer_text)
    return [int(m) for m in matches]


def render_citation_with_tooltip(answer_text: str, sources: List[Dict]) -> str:
    """Render answer text với citation tooltips.
    
    Args:
        answer_text: "Transformer [1] là mô hình mạng neural [2]."
        sources: [
            {
                "filename": "transformer.pdf",
                "page_start": 3,
                "page_end": 4,
                "content": "Transformer is a novel..."
            },
            ...
        ]
    
    Returns:
        HTML string với tooltips
    """
    
    # CSS for tooltip
    css = """
    <style>
    .citation {
        color: #0066cc;
        cursor: pointer;
        position: relative;
        text-decoration: none;
        font-weight: 600;
        padding: 2px 4px;
        border-radius: 3px;
        background-color: #e8f4ff;
    }
    
    .citation:hover {
        background-color: #d0e8ff;
    }
    
    .tooltip {
        visibility: hidden;
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        
        background-color: #2c2c2c;
        color: #ffffff;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        
        width: 350px;
        max-width: 90vw;
        
        font-size: 13px;
        line-height: 1.5;
        text-align: left;
    }
    
    .tooltip::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #2c2c2c transparent transparent transparent;
    }
    
    .citation:hover .tooltip {
        visibility: visible;
    }
    
    .tooltip-header {
        font-weight: 700;
        color: #4da6ff;
        margin-bottom: 6px;
        font-size: 14px;
    }
    
    .tooltip-content {
        color: #e0e0e0;
        margin-top: 8px;
        font-style: italic;
        max-height: 150px;
        overflow-y: auto;
        border-left: 2px solid #4da6ff;
        padding-left: 8px;
    }
    
    .tooltip-page {
        color: #b3b3b3;
        font-size: 12px;
    }
    </style>
    """
    
    # Build source map
    source_map = {}
    for i, source in enumerate(sources):
        citation_num = i + 1
        filename = source.get('filename', 'Unknown')
        page_start = source.get('page_start')
        page_end = source.get('page_end')
        content = source.get('content', '')
        
        # Format page
        if page_start and page_end and page_start != page_end:
            page_label = f"Trang {page_start}-{page_end}"
        elif page_start:
            page_label = f"Trang {page_start}"
        else:
            page_label = ""
        
        # Truncate content for tooltip
        content_preview = content[:200] + "..." if len(content) > 200 else content
        
        tooltip_html = f"""
        <span class="tooltip">
            <div class="tooltip-header">📄 {filename}</div>
            <div class="tooltip-page">{page_label}</div>
            <div class="tooltip-content">"{content_preview}"</div>
        </span>
        """
        
        source_map[citation_num] = tooltip_html
    
    # Replace [N] with clickable citation
    def replace_citation(match):
        num = int(match.group(1))
        if num in source_map:
            return f'<span class="citation">[{num}]{source_map[num]}</span>'
        return match.group(0)
    
    html_text = re.sub(r'\[(\d+)\]', replace_citation, answer_text)
    
    return css + f'<div style="line-height: 1.8;">{html_text}</div>'


# ==========================================
# EXAMPLE USAGE IN STREAMLIT
# ==========================================

def streamlit_example():
    """Example Streamlit app với citation tooltips."""
    
    st.title("NotebookLM-like Source Citations")
    
    # Giả lập answer từ AI
    answer = """
    Mô hình Transformer được giới thiệu lần đầu vào năm 2017 [1] và đã tạo ra 
    bước đột phá trong lĩnh vực xử lý ngôn ngữ tự nhiên [2]. Kiến trúc này dựa 
    hoàn toàn trên cơ chế attention [1] mà không cần RNN hay CNN [3].
    """
    
    # Giả lập sources từ backend
    sources = [
        {
            "filename": "attention_is_all_you_need.pdf",
            "page_start": 1,
            "page_end": 2,
            "content": "The Transformer is a novel neural network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
        },
        {
            "filename": "nlp_review_2020.pdf",
            "page_start": 15,
            "page_end": 15,
            "content": "Transformer models have revolutionized NLP, achieving state-of-the-art results across numerous benchmarks including machine translation, text generation, and question answering."
        },
        {
            "filename": "deep_learning_book.pdf",
            "page_start": 342,
            "page_end": 345,
            "content": "Unlike traditional sequence models that rely on RNNs or CNNs, the Transformer architecture uses only attention mechanisms to capture dependencies between input and output."
        }
    ]
    
    # Render với tooltips
    html_output = render_citation_with_tooltip(answer, sources)
    st.markdown(html_output, unsafe_allow_html=True)
    
    st.divider()
    
    # Display source list
    st.subheader("📚 Nguồn tham khảo:")
    for i, source in enumerate(sources):
        with st.expander(f"[{i+1}] {source['filename']} - Trang {source['page_start']}"):
            st.write(source['content'])


# ==========================================
# PHẦN 2: PURE HTML/JS IMPLEMENTATION
# ==========================================

"""
Nếu dùng custom frontend (React, Vue, vanilla JS), đây là HTML/JS example:
"""

HTML_JS_EXAMPLE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Source Citation Hover</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.8;
        }
        
        .answer-text {
            font-size: 16px;
            color: #333;
        }
        
        .citation {
            color: #0066cc;
            cursor: pointer;
            position: relative;
            text-decoration: none;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            background-color: #e8f4ff;
            transition: all 0.2s;
        }
        
        .citation:hover {
            background-color: #d0e8ff;
            box-shadow: 0 2px 4px rgba(0, 102, 204, 0.2);
        }
        
        .tooltip {
            visibility: hidden;
            opacity: 0;
            position: absolute;
            z-index: 1000;
            bottom: 130%;
            left: 50%;
            transform: translateX(-50%);
            transition: opacity 0.3s, visibility 0.3s;
            
            background-color: #2c2c2c;
            color: #ffffff;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
            
            width: 400px;
            max-width: 90vw;
            
            font-size: 14px;
            line-height: 1.6;
            text-align: left;
        }
        
        .tooltip::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -8px;
            border-width: 8px;
            border-style: solid;
            border-color: #2c2c2c transparent transparent transparent;
        }
        
        .citation:hover .tooltip {
            visibility: visible;
            opacity: 1;
        }
        
        .tooltip-header {
            font-weight: 700;
            color: #4da6ff;
            margin-bottom: 8px;
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .tooltip-page {
            color: #b3b3b3;
            font-size: 13px;
            margin-bottom: 8px;
        }
        
        .tooltip-content {
            color: #e0e0e0;
            margin-top: 10px;
            font-style: italic;
            max-height: 180px;
            overflow-y: auto;
            border-left: 3px solid #4da6ff;
            padding-left: 12px;
            font-size: 13px;
        }
        
        .tooltip-content::-webkit-scrollbar {
            width: 6px;
        }
        
        .tooltip-content::-webkit-scrollbar-thumb {
            background-color: #4da6ff;
            border-radius: 3px;
        }
        
        .sources-section {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
        }
        
        .source-item {
            background-color: #f9f9f9;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 6px;
            border-left: 4px solid #0066cc;
        }
        
        .source-header {
            font-weight: 600;
            color: #0066cc;
            margin-bottom: 8px;
        }
        
        .source-content {
            color: #555;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>🤖 AI Assistant với Source Citations</h1>
    
    <div class="answer-text" id="answer">
        <!-- Answer sẽ được render bởi JS -->
    </div>
    
    <div class="sources-section">
        <h2>📚 Nguồn tham khảo</h2>
        <div id="sources-list"></div>
    </div>

    <script>
        // Data từ backend (WebSocket hoặc API)
        const answerData = {
            text: "Mô hình Transformer được giới thiệu lần đầu vào năm 2017 [1] và đã tạo ra bước đột phá trong lĩnh vực xử lý ngôn ngữ tự nhiên [2]. Kiến trúc này dựa hoàn toàn trên cơ chế attention [1] mà không cần RNN hay CNN [3].",
            sources: [
                {
                    filename: "attention_is_all_you_need.pdf",
                    page_start: 1,
                    page_end: 2,
                    content: "The Transformer is a novel neural network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
                },
                {
                    filename: "nlp_review_2020.pdf",
                    page_start: 15,
                    page_end: 15,
                    content: "Transformer models have revolutionized NLP, achieving state-of-the-art results across numerous benchmarks."
                },
                {
                    filename: "deep_learning_book.pdf",
                    page_start: 342,
                    page_end: 345,
                    content: "Unlike traditional sequence models that rely on RNNs or CNNs, the Transformer architecture uses only attention mechanisms."
                }
            ]
        };

        function renderAnswerWithCitations(answerText, sources) {
            const sourceMap = {};
            
            // Build source map
            sources.forEach((source, index) => {
                const citationNum = index + 1;
                const pageLabel = source.page_start === source.page_end 
                    ? `Trang ${source.page_start}`
                    : `Trang ${source.page_start}-${source.page_end}`;
                
                const contentPreview = source.content.length > 200 
                    ? source.content.substring(0, 200) + "..."
                    : source.content;
                
                sourceMap[citationNum] = {
                    filename: source.filename,
                    pageLabel: pageLabel,
                    content: contentPreview
                };
            });
            
            // Replace [N] với citation elements
            const html = answerText.replace(/\[(\d+)\]/g, (match, num) => {
                const citationNum = parseInt(num);
                if (sourceMap[citationNum]) {
                    const source = sourceMap[citationNum];
                    return `
                        <span class="citation">
                            [${citationNum}]
                            <span class="tooltip">
                                <div class="tooltip-header">
                                    📄 ${source.filename}
                                </div>
                                <div class="tooltip-page">${source.pageLabel}</div>
                                <div class="tooltip-content">"${source.content}"</div>
                            </span>
                        </span>
                    `;
                }
                return match;
            });
            
            return html;
        }

        function renderSources(sources) {
            return sources.map((source, index) => `
                <div class="source-item">
                    <div class="source-header">
                        [${index + 1}] ${source.filename} - Trang ${source.page_start}
                    </div>
                    <div class="source-content">"${source.content}"</div>
                </div>
            `).join('');
        }

        // Render
        document.getElementById('answer').innerHTML = renderAnswerWithCitations(
            answerData.text, 
            answerData.sources
        );
        
        document.getElementById('sources-list').innerHTML = renderSources(
            answerData.sources
        );
    </script>
</body>
</html>
"""

# ==========================================
# PHẦN 3: INTEGRATION VỚI WEBSOCKET
# ==========================================

"""
Cách tích hợp với WebSocket từ backend:
"""

import asyncio
import websockets
import json

async def websocket_client_example():
    """Example client nhận citations qua WebSocket."""
    
    uri = "ws://localhost:8000/ws/chat/conversation-123"
    
    async with websockets.connect(uri) as websocket:
        # Gửi câu hỏi
        message = {
            "question": "Transformer là gì?",
            "file_ids": ["file-id-1", "file-id-2"]  # Optional scoped retrieval
        }
        await websocket.send(json.dumps(message))
        
        # Nhận responses
        citation_map = ""
        answer_text = ""
        sources = []
        
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            content = data.get("content")
            
            if msg_type == "citations":
                # Nhận citation map
                citation_map = content
                print("Citations received:")
                print(citation_map)
                
            elif msg_type == "token":
                # Stream answer tokens
                answer_text += content
                # Update UI real-time
                
            elif msg_type == "sources":
                # Nhận source details
                sources = content
                print(f"Received {len(sources)} sources")
                
            elif msg_type == "done":
                # Hoàn thành
                print("Answer complete!")
                
                # Render final answer với tooltips
                html_output = render_citation_with_tooltip(answer_text, sources)
                # Display trong UI
                
                break
            
            elif msg_type == "error":
                print(f"Error: {content}")
                break


# ==========================================
# RUN EXAMPLES
# ==========================================

if __name__ == "__main__":
    print("Streamlit Example:")
    print("Run: streamlit run frontend_source_hover_example.py")
    print()
    print("HTML/JS Example saved in HTML_JS_EXAMPLE variable")
    print()
    print("WebSocket Example:")
    print("Run: python frontend_source_hover_example.py")
    
    # Uncomment để chạy WebSocket example
    # asyncio.run(websocket_client_example())
