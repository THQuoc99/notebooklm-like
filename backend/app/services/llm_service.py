from openai import OpenAI
from typing import List, AsyncGenerator
from app.config import settings
from app.models.pydantic_models import MessageModel, SourceModel


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.GENERATIVE_MODEL
    
    def build_rag_prompt(self, question: str, contexts: List[dict], history: List[MessageModel] = None) -> List[dict]:
        """
        Build RAG prompt with context and history.
        contexts: List of {content, title, page_start, page_end, filename}
        """
        # Build context string with sensible page-range formatting
        context_parts: List[str] = []
        for ctx in contexts:
            filename = ctx.get('filename', 'Unknown')
            page_start = ctx.get('page_start')
            page_end = ctx.get('page_end')

            # Format page label: if start==end or end missing, show single page
            if page_start is None and page_end is None:
                page_label = ""
            elif page_end is None or str(page_start) == str(page_end):
                page_label = f"Trang {page_start}"
            else:
                page_label = f"Trang {page_start}-{page_end}"

            header = f"[Nguồn: {filename}"
            if page_label:
                header += f" - {page_label}"
            header += "]\n"

            title = ctx.get('title', 'N/A')
            content = ctx.get('content', '')
            context_parts.append(f"{header}Tiêu đề: {title}\nNội dung: {content}")

        context_str = "\n\n".join(context_parts)
        
        system_prompt = """Bạn là trợ lý AI thông minh, nhiệm vụ của bạn là trả lời câu hỏi dựa trên tài liệu được cung cấp.

NGUYÊN TẮC:
- Chỉ trả lời dựa trên thông tin trong tài liệu
- Nếu không tìm thấy thông tin, nói rõ "Tôi không tìm thấy thông tin này trong tài liệu"
- Trích dẫn nguồn (tên file và số trang) khi trả lời
- Trả lời ngắn gọn, súc tích
- Không bịa đặt thông tin"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history (last 5 messages)
        if history:
            for msg in history[-settings.MAX_HISTORY:]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current question with context
        user_message = f"""Tài liệu tham khảo:
{context_str}

Câu hỏi: {question}"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def answer_question_stream(self, question: str, contexts: List[dict], history: List[MessageModel] = None):
        """
        Stream answer tokens.
        Yields: dict with type and content
        """
        messages = self.build_rag_prompt(question, contexts, history)
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            for chunk in stream:
                try:
                    # Some streaming chunks may not have choices or delta/content
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        content = None
                        # Support both dict-like and object-like chunks
                        if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                            content = choice.delta.content
                        elif isinstance(choice, dict):
                            content = choice.get('delta', {}).get('content')

                        if content:
                            yield {
                                "type": "token",
                                "content": content
                            }
                except Exception:
                    # Skip malformed chunk
                    continue
            
            yield {"type": "done", "content": ""}
            
        except Exception as e:
            yield {"type": "error", "content": str(e)}
    
    def answer_question(self, question: str, contexts: List[dict], history: List[MessageModel] = None) -> str:
        """Non-streaming answer (for testing)."""
        messages = self.build_rag_prompt(question, contexts, history)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content


llm_service = LLMService()
